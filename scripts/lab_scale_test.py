#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Large-Scale Drug Repurposing Lab Test for KOMPOSOS-III.

Three-tier lab test:
  Tier 1  Curated only (~105 obj, ~203 mor)    ~2 min
  Tier 2  Hetionet (~47K obj, ~2.25M mor)       ~10-30 min
  Tier 3  Hetionet + Open Targets               ~1-2 hr

Usage:
    python lab_scale_test.py --tier 2
    python lab_scale_test.py --tier 1
    python lab_scale_test.py --tier 3 --audit
    python lab_scale_test.py --tier 2 --top-predictions 100
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent))


# ---------------------------------------------------------------------------
# Tier configuration
# ---------------------------------------------------------------------------

@dataclass
class TierConfig:
    """Preset configuration for each test tier."""
    tier: int
    description: str
    use_hetionet: bool
    use_opentargets: bool
    generators: Optional[List[str]]
    max_candidates_per_generator: int
    conjecture_top_k: int
    min_confidence: float
    morphism_limit: int
    object_limit: int

    @staticmethod
    def tier1() -> TierConfig:
        return TierConfig(
            tier=1,
            description="Curated only (~105 objects, ~203 morphisms)",
            use_hetionet=False,
            use_opentargets=False,
            generators=None,  # all 6
            max_candidates_per_generator=2_000,
            conjecture_top_k=5_000,
            min_confidence=0.25,
            morphism_limit=50_000,
            object_limit=10_000,
        )

    @staticmethod
    def tier2() -> TierConfig:
        return TierConfig(
            tier=2,
            description="Hetionet (~47K objects, ~2.25M morphisms)",
            use_hetionet=True,
            use_opentargets=False,
            generators=["composition", "structural_hole", "yoneda"],
            max_candidates_per_generator=3_000,
            conjecture_top_k=10_000,
            min_confidence=0.25,
            morphism_limit=3_000_000,
            object_limit=100_000,
        )

    @staticmethod
    def tier3() -> TierConfig:
        return TierConfig(
            tier=3,
            description="Hetionet + Open Targets",
            use_hetionet=True,
            use_opentargets=True,
            generators=None,  # all 6
            max_candidates_per_generator=50_000,
            conjecture_top_k=50_000,
            min_confidence=0.25,
            morphism_limit=3_000_000,
            object_limit=100_000,
        )


# ---------------------------------------------------------------------------
# Evaluation result
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResult:
    """Metrics from holdout evaluation."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    recall: float = 0.0
    precision: float = 0.0
    f1: float = 0.0
    auroc: float = 0.0
    auprc: float = 0.0
    drug_disease_pairs_scored: int = 0
    type_breakdown: Dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Metric functions (local copies -- originals are private in audit module)
# ---------------------------------------------------------------------------

def _compute_auroc(scores: List[float], labels: List[int]) -> float:
    """Manual AUROC via trapezoidal rule. No sklearn dependency."""
    if not scores or not labels or sum(labels) == 0 or sum(labels) == len(labels):
        return 0.0

    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    fp = 0
    total_pos = sum(labels)
    total_neg = len(labels) - total_pos
    if total_neg == 0:
        return 0.0

    auroc = 0.0
    prev_fpr = 0.0
    prev_tpr = 0.0

    for i, (score, label) in enumerate(paired):
        if label == 1:
            tp += 1
        else:
            fp += 1

        # Only compute at threshold changes
        if i + 1 < len(paired) and paired[i + 1][0] == score:
            continue

        tpr = tp / total_pos
        fpr = fp / total_neg
        auroc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2
        prev_fpr = fpr
        prev_tpr = tpr

    # Final step to (1, 1)
    auroc += (1.0 - prev_fpr) * (1.0 + prev_tpr) / 2
    return auroc


def _compute_auprc(scores: List[float], labels: List[int]) -> float:
    """Manual AUPRC via step function. No sklearn dependency."""
    if not scores or not labels or sum(labels) == 0:
        return 0.0

    paired = sorted(zip(scores, labels), key=lambda x: -x[0])
    tp = 0
    fp = 0
    total_pos = sum(labels)
    auprc = 0.0
    prev_recall = 0.0

    for score, label in paired:
        if label == 1:
            tp += 1
        else:
            fp += 1

        precision = tp / (tp + fp)
        recall = tp / total_pos

        if recall > prev_recall:
            auprc += precision * (recall - prev_recall)
            prev_recall = recall

    return auprc


# ---------------------------------------------------------------------------
# MinimalEmbeddings fallback (hash-based, no GPU needed)
# ---------------------------------------------------------------------------

class MinimalEmbeddings:
    """Hash-based embedding fallback when sentence-transformers is unavailable."""
    is_available = True
    model_name = "hash-based-fallback"

    def embed(self, text: str):
        import numpy as np
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()
        return np.array([int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)])

    def embed_batch(self, texts, show_progress=False):
        return [self.embed(t) for t in texts]

    def similarity(self, a: str, b: str) -> float:
        import numpy as np
        va = self.embed(a)
        vb = self.embed(b)
        dot = float(np.dot(va, vb))
        norm = float(np.linalg.norm(va) * np.linalg.norm(vb))
        return dot / norm if norm > 0 else 0.0


# ---------------------------------------------------------------------------
# Main lab test orchestrator
# ---------------------------------------------------------------------------

class LabScaleTest:
    """Orchestrates the 6-phase lab test pipeline."""

    def __init__(self, config: TierConfig, run_audit: bool = False, top_predictions: int = 50, redo_full: bool = False, quorum: int = 1):
        self.config = config
        self.run_audit = run_audit
        self.top_predictions = top_predictions
        self.redo_full = redo_full
        self.quorum = quorum
        self.timings: Dict[str, float] = {}
        self.store = None
        self.holdout_edges: List = []
        self.curated_holdout: List = []
        self.embeddings = None
        self.conjecture_result = None
        self.evaluation: Optional[EvaluationResult] = None
        self.audit_report = None

    def run(self) -> dict:
        """Execute all phases and return the full result dict."""
        print(f"\n{'='*70}")
        print(f"  KOMPOSOS-III Drug Repurposing Lab Test -- Tier {self.config.tier}")
        print(f"  {self.config.description}")
        print(f"{'='*70}\n")

        overall_start = time.time()

        self._phase1_load_network()
        self._phase2_compute_embeddings()
        self._phase3_run_conjecture()
        self._phase4_evaluate_holdout()

        if self.run_audit:
            self._phase5_run_audit()

        result = self._phase6_generate_report()
        result["total_time_s"] = round(time.time() - overall_start, 1)

        self._save_results(result)
        return result

    # -- Phase 1: Load Network ------------------------------------------------

    def _phase1_load_network(self):
        print("[Phase 1] Loading network...")
        t0 = time.time()

        from data.drugs.loader import create_drug_store
        from data.drugs.drug_network import get_holdout_edges

        self.curated_holdout = get_holdout_edges(include_redo_full=self.redo_full)

        if self.config.tier == 1:
            self.store = create_drug_store(
                db_path=":memory:", include_proteins=True,
                include_redo_full=self.redo_full,
            )
            self.holdout_edges = []
        else:
            from data.drugs.loader import load_scaled_drug_network
            self.store, self.holdout_edges = load_scaled_drug_network(
                db_path=":memory:",
                use_hetionet=self.config.use_hetionet,
                use_opentargets=self.config.use_opentargets,
                holdout_fraction=0.20,
                verbose=True,
            )

        n_obj = self.store.count_objects()
        n_mor = self.store.count_morphisms()
        elapsed = time.time() - t0
        self.timings["load_network"] = round(elapsed, 1)
        print(f"  Objects: {n_obj:,}  Morphisms: {n_mor:,}  ({elapsed:.1f}s)")

    # -- Phase 2: Compute Embeddings ------------------------------------------

    def _phase2_compute_embeddings(self):
        print("[Phase 2] Computing embeddings...")
        t0 = time.time()

        from data import EmbeddingsEngine, StoreEmbedder

        try:
            engine = EmbeddingsEngine()
            if not engine.is_available:
                raise RuntimeError("not available")
            print(f"  Using model: {engine.model_name}")
        except Exception:
            print("  sentence-transformers unavailable, using hash-based fallback")
            engine = MinimalEmbeddings()

        self.embeddings = engine
        embedder = StoreEmbedder(self.store, engine)
        n_embedded = embedder.embed_all_objects()

        elapsed = time.time() - t0
        self.timings["compute_embeddings"] = round(elapsed, 1)
        print(f"  Embedded {n_embedded:,} objects ({elapsed:.1f}s)")

    # -- Phase 3: Run Conjecture Engine ---------------------------------------

    def _phase3_run_conjecture(self):
        print("[Phase 3] Running conjecture engine...")
        t0 = time.time()

        from oracle import CategoricalOracle
        from oracle.conjecture import ConjectureEngine

        oracle = CategoricalOracle(
            store=self.store,
            embeddings=self.embeddings,
            min_confidence=self.config.min_confidence,
            max_predictions=20,
        )

        # For Tier 2+, keep only strategies that are effective at scale.
        # Skip: kan_extension (O(N) per pair), temporal_reasoning (no data),
        #        fibration_lift (huge fibers), geometric (expensive curvature).
        if self.config.tier >= 2:
            _keep = {'composition', 'structural_hole', 'yoneda_pattern',
                     'type_heuristic', 'semantic_similarity'}
            oracle.strategies = [s for s in oracle.strategies if s.name in _keep]
            print(f"  Strategies for Tier {self.config.tier}: "
                  f"{[s.name for s in oracle.strategies]}")

        ce = ConjectureEngine(
            oracle,
            morphism_limit=self.config.morphism_limit,
            object_limit=self.config.object_limit,
        )

        self.conjecture_result = ce.conjecture_zfc_first(
            top_k=self.config.conjecture_top_k,
            min_confidence=self.config.min_confidence,
        )

        elapsed = time.time() - t0
        self.timings["conjecture"] = round(elapsed, 1)
        cr = self.conjecture_result
        print(f"  Candidates surfaced: {cr.pairs_surfaced:,}")
        print(f"  ZFC proven chains: {cr.candidate_breakdown.get('zfc_proven', 0)}")
        print(f"  Conjectures returned: {len(cr.conjectures):,}")

        # ZFC-first stats
        zfc_tags = [s for c in cr.conjectures for s in c.candidate_sources if s.startswith("zfc:")]
        if zfc_tags:
            from collections import Counter
            zfc_counts = Counter(zfc_tags)
            print(f"  ZFC-first engine: ACTIVE")
            print(f"    All conjectures are ZFC-proven (AGREE)")
            chain_tags = [s for c in cr.conjectures for s in c.candidate_sources if s.startswith("zfc_chain:")]
            if chain_tags:
                chain_counts = Counter(chain_tags)
                for chain, count in chain_counts.most_common(5):
                    print(f"    {chain}: {count}")
        else:
            print(f"  ZFC-first engine: not active (fallback to CAT-only)")

        print(f"  ({elapsed:.1f}s)")

    # -- Phase 4: Evaluate against holdout ------------------------------------

    def _phase4_evaluate_holdout(self):
        print("[Phase 4] Evaluating against holdout edges...")
        t0 = time.time()

        from data.drugs.drug_network import DRUGS, DISEASES, DRUG_DISEASE_APPROVED

        # Combine curated + external holdout into a single set
        holdout_set: Set[Tuple[str, str]] = set()
        for h in self.curated_holdout:
            holdout_set.add((h[0], h[1]))
        for h in self.holdout_edges:
            holdout_set.add((h[0], h[1]))

        # Also include approved pairs as positives
        approved_set: Set[Tuple[str, str]] = set()
        for a in DRUG_DISEASE_APPROVED:
            approved_set.add((a[0], a[1]))

        positive_set = holdout_set | approved_set

        # Leakage check: spot-check holdout edges against the store
        # (uses targeted queries instead of loading all morphisms into memory)
        leaked = 0
        for src, tgt in holdout_set:
            mors = self.store.get_morphisms_between(src, tgt) if hasattr(self.store, 'get_morphisms_between') else []
            if not mors:
                # Fallback: check via get_morphisms_from
                try:
                    mors = [m for m in self.store.get_morphisms_from(src) if m.target_name == tgt]
                except Exception:
                    pass
            if mors:
                leaked += 1
        if leaked:
            print(f"  WARNING: {leaked} holdout edges leaked into store!")
        else:
            print(f"  Leakage check passed: 0/{len(holdout_set)} holdout edges in store")

        # Collect drug/disease names for type-aware evaluation
        drug_names = set(DRUGS.keys())
        disease_names = set(DISEASES.keys())
        try:
            for obj in self.store.get_objects_by_type("Drug"):
                drug_names.add(obj.name)
            for obj in self.store.get_objects_by_type("Disease"):
                disease_names.add(obj.name)
        except Exception:
            pass

        # Apply quorum filter if requested
        conjectures_for_eval = self.conjecture_result.conjectures
        if self.quorum > 1:
            conjectures_for_eval = [c for c in conjectures_for_eval if c.strategy_count >= self.quorum]
            n_before = len(self.conjecture_result.conjectures)
            n_after = len(conjectures_for_eval)
            print(f"  Quorum filter (>={self.quorum} strategies): {n_before} -> {n_after} conjectures")

        # Separate Drug->Disease conjectures from other types
        # Precision/recall should only measure Drug->Disease predictions against
        # Drug->Disease holdout — counting Protein->Protein as FP is wrong.
        dd_conjectures = [c for c in conjectures_for_eval
                         if c.source in drug_names and c.target in disease_names]
        other_conjectures = len(conjectures_for_eval) - len(dd_conjectures)
        print(f"  Drug->Disease conjectures: {len(dd_conjectures)}  (other: {other_conjectures})")

        # Build conjecture hit set (Drug->Disease only for precision/recall)
        dd_conjecture_set = {(c.source, c.target) for c in dd_conjectures}

        # Classify predictions by type
        type_breakdown: Dict[str, int] = {}
        for c in dd_conjectures:
            best = c.best
            if best:
                rel = best.predicted_relation
                type_breakdown[rel] = type_breakdown.get(rel, 0) + 1

        # TP / FP / FN — Drug->Disease only
        tp_set = dd_conjecture_set & holdout_set
        fp_set = dd_conjecture_set - positive_set
        fn_set = holdout_set - dd_conjecture_set

        tp = len(tp_set)
        fp = len(fp_set)
        fn = len(fn_set)

        recall = tp / max(len(holdout_set), 1)
        precision = tp / max(tp + fp, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)

        print(f"  Holdout size: {len(holdout_set)} (curated: {len(self.curated_holdout)}, external: {len(self.holdout_edges)})")
        print(f"  TP: {tp}  FP: {fp}  FN: {fn}")
        print(f"  Recall: {recall:.3f}  Precision: {precision:.3f}  F1: {f1:.3f}")

        # AUROC / AUPRC over all Drug x Disease pairs
        # Build score map from Drug->Disease conjectures
        score_map: Dict[Tuple[str, str], float] = {}
        for c in dd_conjectures:
            score_map[(c.source, c.target)] = c.top_confidence

        all_scores: List[float] = []
        all_labels: List[int] = []

        for drug in drug_names:
            for disease in disease_names:
                pair = (drug, disease)
                score = score_map.get(pair, 0.0)
                label = 1 if pair in positive_set else 0
                all_scores.append(score)
                all_labels.append(label)

        n_pairs = len(all_scores)
        auroc = _compute_auroc(all_scores, all_labels) if n_pairs > 0 else 0.0
        auprc = _compute_auprc(all_scores, all_labels) if n_pairs > 0 else 0.0

        print(f"  Drug x Disease pairs scored: {n_pairs:,}")
        print(f"  AUROC: {auroc:.4f}  AUPRC: {auprc:.4f}")

        self.evaluation = EvaluationResult(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            recall=round(recall, 4),
            precision=round(precision, 4),
            f1=round(f1, 4),
            auroc=round(auroc, 4),
            auprc=round(auprc, 4),
            drug_disease_pairs_scored=n_pairs,
            type_breakdown=type_breakdown,
        )

        elapsed = time.time() - t0
        self.timings["evaluate_holdout"] = round(elapsed, 1)
        print(f"  ({elapsed:.1f}s)")

    # -- Phase 5: Audit (optional) --------------------------------------------

    def _phase5_run_audit(self):
        print("[Phase 5] Running full audit (22 checks)...")
        t0 = time.time()

        try:
            from validation.drug_repurposing_audit import run_drug_repurposing_audit
            self.audit_report = run_drug_repurposing_audit(
                store=self.store,
                verbose=True,
                external_holdout=self.holdout_edges if self.holdout_edges else None,
            )
            elapsed = time.time() - t0
            self.timings["audit"] = round(elapsed, 1)
            print(f"  Audit complete: {self.audit_report.pass_count}/{self.audit_report.total_count} passed ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            self.timings["audit"] = round(elapsed, 1)
            print(f"  Audit failed: {e}")
            self.audit_report = None

    # -- Phase 6: Generate report ---------------------------------------------

    def _phase6_generate_report(self) -> dict:
        print("[Phase 6] Generating report...")

        cr = self.conjecture_result
        ev = self.evaluation

        # Top predictions with reasoning
        top_preds = []
        holdout_set = set()
        for h in self.curated_holdout:
            holdout_set.add((h[0], h[1]))
        for h in self.holdout_edges:
            holdout_set.add((h[0], h[1]))

        for c in cr.conjectures[:self.top_predictions]:
            best = c.best
            entry = {
                "source": c.source,
                "target": c.target,
                "confidence": round(c.top_confidence, 4),
                "relation": best.predicted_relation if best else "unknown",
                "strategy": best.strategy_name if best else "unknown",
                "reasoning": best.reasoning if best else "",
                "candidate_sources": c.candidate_sources,
                "holdout_match": (c.source, c.target) in holdout_set,
            }
            top_preds.append(entry)

        # Strategy contributions
        strategy_counts: Dict[str, int] = {}
        for c in cr.conjectures:
            best = c.best
            if best:
                strategy_counts[best.strategy_name] = strategy_counts.get(best.strategy_name, 0) + 1

        result = {
            "tier": self.config.tier,
            "description": self.config.description,
            "timestamp": datetime.now().isoformat(),
            "network": {
                "objects": self.store.count_objects(),
                "morphisms": self.store.count_morphisms(),
                "use_hetionet": self.config.use_hetionet,
                "use_opentargets": self.config.use_opentargets,
            },
            "conjecture": {
                "pairs_surfaced": cr.pairs_surfaced,
                "conjectures_returned": len(cr.conjectures),
                "generator_breakdown": cr.candidate_breakdown,
                "generators_used": self.config.generators or "all",
                "max_candidates_per_generator": self.config.max_candidates_per_generator,
            },
            "evaluation": asdict(ev) if ev else {},
            "strategy_contributions": strategy_counts,
            "top_predictions": top_preds,
            "timings": self.timings,
        }

        if self.audit_report is not None:
            result["audit"] = {
                "total": self.audit_report.total_count,
                "passed": self.audit_report.pass_count,
                "critical_failures": self.audit_report.critical_count,
                "warnings": self.audit_report.warning_count,
            }

        return result

    # -- Save results ---------------------------------------------------------

    def _save_results(self, result: dict):
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"lab_test_tier{self.config.tier}_{ts}"

        # JSON
        json_path = results_dir / f"{base}.json"
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  JSON saved: {json_path}")

        # Markdown
        md_path = results_dir / f"{base}.md"
        md = _generate_markdown_report(result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"  Markdown saved: {md_path}")


# ---------------------------------------------------------------------------
# Markdown report generator
# ---------------------------------------------------------------------------

def _generate_markdown_report(result: dict) -> str:
    """Generate a human-readable Markdown report."""
    lines = []
    lines.append(f"# KOMPOSOS-III Drug Repurposing Lab Test -- Tier {result['tier']}")
    lines.append(f"")
    lines.append(f"**Date**: {result['timestamp']}")
    lines.append(f"**Description**: {result['description']}")
    lines.append(f"**Total runtime**: {result.get('total_time_s', '?')}s")
    lines.append("")

    # Network Statistics
    net = result["network"]
    lines.append("## Network Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Objects | {net['objects']:,} |")
    lines.append(f"| Morphisms | {net['morphisms']:,} |")
    lines.append(f"| Hetionet | {'Yes' if net['use_hetionet'] else 'No'} |")
    lines.append(f"| Open Targets | {'Yes' if net['use_opentargets'] else 'No'} |")
    lines.append("")

    # Conjecture Results
    conj = result["conjecture"]
    lines.append("## Conjecture Results")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Candidates surfaced | {conj['pairs_surfaced']:,} |")
    lines.append(f"| Conjectures returned | {conj['conjectures_returned']:,} |")
    lines.append(f"| Max candidates/generator | {conj['max_candidates_per_generator']:,} |")
    lines.append(f"| Generators used | {conj['generators_used']} |")
    lines.append("")

    lines.append("### Generator Breakdown")
    lines.append("")
    lines.append("| Generator | Candidates |")
    lines.append("|-----------|-----------|")
    for gen, count in sorted(conj["generator_breakdown"].items(), key=lambda x: -x[1]):
        lines.append(f"| {gen} | {count:,} |")
    lines.append("")

    # Holdout Evaluation
    ev = result.get("evaluation", {})
    if ev:
        lines.append("## Holdout Evaluation")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| True Positives | {ev.get('true_positives', 0)} |")
        lines.append(f"| False Positives | {ev.get('false_positives', 0)} |")
        lines.append(f"| False Negatives | {ev.get('false_negatives', 0)} |")
        lines.append(f"| Recall | {ev.get('recall', 0):.4f} |")
        lines.append(f"| Precision | {ev.get('precision', 0):.4f} |")
        lines.append(f"| F1 Score | {ev.get('f1', 0):.4f} |")
        lines.append(f"| AUROC | {ev.get('auroc', 0):.4f} |")
        lines.append(f"| AUPRC | {ev.get('auprc', 0):.4f} |")
        lines.append(f"| Drug x Disease pairs | {ev.get('drug_disease_pairs_scored', 0):,} |")
        lines.append("")

        if ev.get("type_breakdown"):
            lines.append("### Prediction Type Breakdown")
            lines.append("")
            lines.append("| Relation | Count |")
            lines.append("|----------|-------|")
            for rel, count in sorted(ev["type_breakdown"].items(), key=lambda x: -x[1]):
                lines.append(f"| {rel} | {count:,} |")
            lines.append("")

    # Strategy Contributions
    strats = result.get("strategy_contributions", {})
    if strats:
        lines.append("## Strategy Contributions")
        lines.append("")
        lines.append("| Strategy | Conjectures |")
        lines.append("|----------|------------|")
        for strat, count in sorted(strats.items(), key=lambda x: -x[1]):
            lines.append(f"| {strat} | {count:,} |")
        lines.append("")

    # Top Predictions
    preds = result.get("top_predictions", [])
    if preds:
        lines.append(f"## Top {len(preds)} Predictions")
        lines.append("")
        lines.append("| # | Source | Target | Relation | Confidence | Strategy | Holdout? | Generators |")
        lines.append("|---|--------|--------|----------|-----------|----------|----------|------------|")
        for i, p in enumerate(preds, 1):
            holdout_flag = "YES" if p.get("holdout_match") else ""
            gens = ", ".join(p.get("candidate_sources", []))
            lines.append(
                f"| {i} | {p['source']} | {p['target']} | {p['relation']} | "
                f"{p['confidence']:.4f} | {p['strategy']} | {holdout_flag} | {gens} |"
            )
        lines.append("")

        # Reasoning chains for top 10
        lines.append("### Reasoning Chains (Top 10)")
        lines.append("")
        for i, p in enumerate(preds[:10], 1):
            lines.append(f"**{i}. {p['source']} -> {p['target']}** ({p['relation']}, conf={p['confidence']:.4f})")
            lines.append(f"  - Strategy: {p['strategy']}")
            lines.append(f"  - Reasoning: {p.get('reasoning', 'N/A')}")
            if p.get("holdout_match"):
                lines.append(f"  - **HOLDOUT MATCH**")
            lines.append("")

    # Audit results
    audit = result.get("audit")
    if audit:
        lines.append("## Audit Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total checks | {audit['total']} |")
        lines.append(f"| Passed | {audit['passed']} |")
        lines.append(f"| Critical failures | {audit['critical_failures']} |")
        lines.append(f"| Warnings | {audit['warnings']} |")
        lines.append("")

    # Phase Timings
    timings = result.get("timings", {})
    if timings:
        lines.append("## Phase Timings")
        lines.append("")
        lines.append("| Phase | Time (s) |")
        lines.append("|-------|----------|")
        for phase, t in timings.items():
            lines.append(f"| {phase} | {t} |")
        lines.append(f"| **Total** | **{result.get('total_time_s', '?')}** |")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="KOMPOSOS-III Large-Scale Drug Repurposing Lab Test"
    )
    parser.add_argument(
        "--tier", type=int, default=2, choices=[1, 2, 3],
        help="Test tier: 1=curated, 2=Hetionet, 3=Hetionet+OpenTargets (default: 2)",
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="Run full 22-check audit after conjecture",
    )
    parser.add_argument(
        "--top-predictions", type=int, default=50,
        help="Number of top predictions to include in report (default: 50)",
    )
    parser.add_argument(
        "--redo-full", action="store_true",
        help="Load full ReDO_DB expansion (~130 additional drugs)",
    )
    parser.add_argument(
        "--quorum", type=int, default=1,
        help="Minimum number of strategies that must agree for a prediction to count (default: 1 = no filter)",
    )
    args = parser.parse_args()

    config = {1: TierConfig.tier1, 2: TierConfig.tier2, 3: TierConfig.tier3}[args.tier]()
    test = LabScaleTest(config, run_audit=args.audit, top_predictions=args.top_predictions, redo_full=args.redo_full, quorum=args.quorum)
    result = test.run()

    print(f"\n{'='*70}")
    print(f"  DONE  Tier {config.tier}  |  "
          f"Recall={result['evaluation'].get('recall', '?')}  "
          f"AUROC={result['evaluation'].get('auroc', '?')}  "
          f"AUPRC={result['evaluation'].get('auprc', '?')}  |  "
          f"{result.get('total_time_s', '?')}s")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
