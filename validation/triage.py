#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Candidate Triage CLI for KOMPOSOS-IV-PHARM drug repurposing.

Turns scored drug-disease pairs into actionable candidate reports
a scientist can read and audit.

Usage:
    # Disease-first: rank all drugs for a disease
    python validation/triage.py Melanoma

    # Drug-first: rank all diseases for a drug
    python validation/triage.py --drug Metformin

    # Specific pair: detailed report
    python validation/triage.py Melanoma --drug Vemurafenib

    # Output formats
    python validation/triage.py Melanoma --json
    python validation/triage.py Melanoma --markdown

    # Options
    python validation/triage.py Melanoma --top 10
    python validation/triage.py Melanoma --all
    python validation/triage.py Melanoma --db path.db
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair_detailed,
)
from validation.ranking_calibration import (
    DEFAULT_CALIBRATION_PATH,
    calibrate_score,
    load_calibration,
)
from validation.trace_prediction import _build_provenance_index, trace_pair


RANKING_CALIBRATION = load_calibration(DEFAULT_CALIBRATION_PATH)


# ── ESMC protein classification ─────────────────────────────────────

def _load_esmc_embedder():
    """Load ESMC embedder with graceful fallback.

    Suppresses loading messages for clean triage output. Returns None
    if the esm package is not installed or sequences are unavailable.
    """
    try:
        from data.bio_embeddings import BiologicalEmbeddingsEngine
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            embedder = BiologicalEmbeddingsEngine(device='cpu')
        if embedder.is_available:
            return embedder
    except Exception:
        pass
    return None


def _esmc_classify(entry, positives, category, embedder):
    """Classify a drug-disease prediction using ESMC protein similarity.

    Compares the drug's target proteins against proteins targeted by
    approved treatments for the same disease.

    Returns dict with:
        classification: Family Extrapolation / Cross-Family Related / Cross-Family Novel
        max_similarity: highest ESMC cosine similarity found
        interpretation: human-readable explanation
        drug_target, reference_target, reference_drug: best matching pair
    """
    drug = entry["drug"]
    disease = entry["disease"]

    # Extract drug's DIRECT target proteins (first hop in each chain).
    # Using only first-hop targets avoids false matches from downstream
    # intermediates (e.g. Imatinib->KRAS->BRAF would incorrectly match
    # BRAF inhibitors if we used all intermediates).
    drug_proteins = set()
    for chain in entry.get("chains", []):
        edges = chain.get("edges", [])
        if edges:
            first_target = edges[0].get("target")
            if first_target and first_target != disease:
                drug_proteins.add(first_target)

    if not drug_proteins:
        return None

    # Build type index for filtering
    obj_types = {obj.name: obj.type_name for obj in category.objects()}

    # Find approved drugs for this disease (excluding the drug being evaluated)
    approved_drugs = {d for d, dis in positives if dis == disease and d != drug}

    if not approved_drugs:
        return {
            "classification": "No Reference",
            "max_similarity": 0.0,
            "interpretation": "no approved treatments for this disease to compare against",
        }

    # Find approved drugs' target proteins via direct morphisms
    ref_proteins = {}  # protein_name -> reference_drug
    for ad in approved_drugs:
        for m in category.morphisms_from(ad):
            tgt_type = obj_types.get(m.target)
            if tgt_type and tgt_type not in ('Drug', 'Disease'):
                ref_proteins[m.target] = ad

    if not ref_proteins:
        return {
            "classification": "No Reference Targets",
            "max_similarity": 0.0,
            "interpretation": "approved treatments have no mapped protein targets",
        }

    # Compute max ESMC similarity between drug targets and reference targets
    max_sim = 0.0
    best = None
    for dp in drug_proteins:
        for rp, ref_drug in ref_proteins.items():
            try:
                sim = embedder.similarity(dp, rp)
                if sim > max_sim:
                    max_sim = sim
                    best = (dp, rp, ref_drug, sim)
            except (ValueError, RuntimeError):
                continue

    # ESMC-300M thresholds (calibrated from observed distribution):
    # Same-family pairs: 0.95+ (KRAS-NRAS 0.99, BRAF-RAF1 0.99, EGFR-ERBB2 0.95)
    # Cross-family large proteins: 0.80-0.95 (TP53-BRAF 0.93, EGFR-BRAF 0.93)
    # Structurally diverse: <0.80 (KRAS-MTOR 0.42, KRAS-EGFR 0.68)
    if max_sim >= 0.95:
        classification = "Family Extrapolation"
        interpretation = (
            f"{drug} targets {best[0]} (ESMC sim {max_sim:.2f} to "
            f"{best[1]}, target of {best[2]})"
        )
    elif max_sim >= 0.80:
        classification = "Cross-Family Related"
        interpretation = (
            f"{drug}'s targets are structurally related to known treatment targets "
            f"(best: {best[0]} vs {best[1]}, sim {max_sim:.2f})"
        )
    else:
        classification = "Cross-Family Novel"
        interpretation = (
            f"{drug}'s targets are structurally distinct from known treatments"
            + (f" (best: {best[0]} vs {best[1]}, sim {max_sim:.2f})" if best else "")
        )

    result = {
        "classification": classification,
        "max_similarity": round(max_sim, 3),
        "interpretation": interpretation,
    }
    if best:
        result["drug_target"] = best[0]
        result["reference_target"] = best[1]
        result["reference_drug"] = best[2]

    return result


# ── Data helpers ──────────────────────────────────────────────────────

def _label_for_pair(pair: tuple[str, str], positives: set[tuple[str, str]]) -> str:
    """Return APPROVED or NOT_APPROVED for a drug-disease pair.

    APPROVED = one of the 44 FDA-approved oncology indications in tier1.db.
    NOT_APPROVED = not in our 44 FDA-approved indications. This does NOT mean
    the combination is novel or unstudied -- it may already be in clinical
    trials, published literature, or off-label use. The label only reflects
    what is in our curated database.
    """
    return "APPROVED" if pair in positives else "NOT_APPROVED"


def _provenance_fraction(chains: list[dict]) -> tuple[int, int]:
    """Count (cited, total) edges across all chains."""
    cited = 0
    total = 0
    for chain in chains:
        for edge in chain.get("edges", []):
            total += 1
            prov = edge.get("provenance", "unknown")
            if prov and prov != "unknown":
                cited += 1
    return cited, total


def _benchmark_label_rate(score: float) -> float | None:
    """Benchmark-calibrated FDA-label rate for a ranking score."""
    return calibrate_score(score, RANKING_CALIBRATION)


def self_check(category, drugs, diseases, positives) -> tuple[int, int]:
    """Count how many approved indications have at least one mechanistic path."""
    recoverable = 0
    for drug, disease in sorted(positives):
        paths = category.find_paths(drug, disease, max_length=4)
        # Need at least one multi-hop path (not just the direct label edge)
        multi_hop = [p for p in paths if len(p.morphism_ids) >= 2]
        if multi_hop:
            recoverable += 1
    return recoverable, len(positives)


# ── Triage functions ─────────────────────────────────────────────────

def triage_disease(category, strategies, disease: str, positives,
                   provenance_index, top_n: Optional[int] = 10,
                   show_all: bool = False):
    """Score all drugs for one disease, return ranked list with evidence."""
    drugs = sorted(obj.name for obj in category.objects() if obj.type_name == "Drug")
    results = []
    for drug in drugs:
        breakdown = score_pair_detailed(strategies, drug, disease)
        score = breakdown["score"]
        votes = breakdown["votes"]
        trace = trace_pair(category, drug, disease, None, provenance_index)
        label = _label_for_pair((drug, disease), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results.append({
            "rank": 0,
            "drug": drug,
            "disease": disease,
            "score": score,
            "benchmark_label_rate": _benchmark_label_rate(score),
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
            "breakdown": breakdown,
        })
    results.sort(key=lambda r: -r["score"])
    for i, r in enumerate(results, 1):
        r["rank"] = i
    if not show_all and top_n:
        results = results[:top_n]
    return results


def triage_drug(category, strategies, drug: str, positives,
                provenance_index, top_n: Optional[int] = 10,
                show_all: bool = False):
    """Score all diseases for one drug, return ranked list with evidence."""
    diseases = sorted(obj.name for obj in category.objects() if obj.type_name == "Disease")
    results = []
    for disease in diseases:
        breakdown = score_pair_detailed(strategies, drug, disease)
        score = breakdown["score"]
        votes = breakdown["votes"]
        trace = trace_pair(category, drug, disease, None, provenance_index)
        label = _label_for_pair((drug, disease), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results.append({
            "rank": 0,
            "drug": drug,
            "disease": disease,
            "score": score,
            "benchmark_label_rate": _benchmark_label_rate(score),
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
            "breakdown": breakdown,
        })
    results.sort(key=lambda r: -r["score"])
    for i, r in enumerate(results, 1):
        r["rank"] = i
    if not show_all and top_n:
        results = results[:top_n]
    return results


# ── Formatting helpers ───────────────────────────────────────────────

def _top_evidence_path(chains: list[dict]) -> str:
    """Return a human-readable string for the best mechanistic chain."""
    if not chains:
        return "(no mechanistic path)"
    best = chains[0]
    parts = []
    for edge in best["edges"]:
        if not parts:
            parts.append(edge["source"])
        parts.append(f"-{edge['relation']}->")
        parts.append(edge["target"])
    return " ".join(parts) if parts else "(no mechanistic path)"


def _detail_block(entry: dict) -> str:
    """Render a detailed evidence block for one candidate."""
    lines = []
    drug = entry["drug"]
    disease = entry["disease"]
    label = entry["label"]
    lines.append(f"---- Detail: #{entry['rank']} {drug} -> {disease} ({label}) ----")
    lines.append("")
    lines.append(f"Ranking score: {entry['score']:.3f}")
    label_rate = entry.get("benchmark_label_rate")
    if label_rate is not None:
        lines.append(
            f"Benchmark label rate: {label_rate:.1%} "
            "(score-bin FDA-label rate, not clinical probability)"
        )
    breakdown = entry.get("breakdown")
    if breakdown:
        lines.append(
            "Score breakdown: "
            f"base={breakdown['base']:.3f}, "
            f"path_bonus={breakdown['path_bonus']:.3f}, "
            f"yoneda_bonus={breakdown.get('yoneda_bonus', 0.0):.3f}, "
            f"composition_paths={breakdown['composition_count']}"
        )

    if entry["votes"]:
        lines.append("Strategy signal scores:")
        # Map technical names to user-friendly labels
        strategy_labels = {
            "kan_extension": "Drug Analogy",
            "structural_hole": "Network Closure",
            "composition": "Mechanistic Path",
            "yoneda_pattern": "Interaction Profile",
            "fibration_lift": "Structural Inference",
            "topos_logic": "Evidence Integration",
            "binding_evidence": "Binding Evidence",
            "yoneda_distance": "Structural Similarity",
        }
        for name, conf in entry["votes"]:
            label = strategy_labels.get(name, name)
            lines.append(f"  {label:25s} {conf:.2f}")

    # Show binding evidence detail when binding_evidence strategy voted
    binding_vote = [c for n, c in entry["votes"] if n == "binding_evidence"]
    if binding_vote:
        lines.append("")
        lines.append("Binding evidence:")
        try:
            from abpp_bridge import ABPPBridge
            abpp = ABPPBridge()
            from data.drugs.drug_properties import get_drug_likeness, is_antibody
            # Collect unique drug-protein binding entries (deduplicated)
            seen_pairs = set()
            for chain in entry.get("chains", []):
                for edge in chain.get("edges", []):
                    protein = edge.get("target", "")
                    if (drug, protein) in seen_pairs:
                        continue
                    result = abpp.check_abpp(drug, protein)
                    if result and result.validated and result.ic50_um is not None:
                        seen_pairs.add((drug, protein))
                        lines.append(
                            f"  {drug}->{protein}: IC50={result.ic50_um:.3f} uM"
                            f"  ({result.percent_inhibition:.0f}% inh.)"
                            f"  [{result.publication}]"
                        )
            likeness = get_drug_likeness(drug)
            if likeness is not None:
                lines.append(f"  Drug-likeness (Lipinski): {likeness:.2f}")
            if is_antibody(drug):
                lines.append(f"  Note: {drug} is a monoclonal antibody (not small molecule)")
        except Exception:
            pass  # Binding display is best-effort

    # Show Yoneda structural similarity detail when the strategy voted
    yoneda_vote = [c for n, c in entry["votes"] if n == "yoneda_distance"]
    if yoneda_vote:
        sim_score = yoneda_vote[0]
        lines.append("")
        lines.append("Structural similarity (Yoneda distance on MEASURED+ESTABLISHED):")
        lines.append(f"  Similarity score: {sim_score:.3f} (distance {1.0 - sim_score:.3f})")
        lines.append(
            f"  Interpretation: {drug} shares {sim_score:.0%} of its high-quality "
            f"target profile with a drug FDA-approved for {disease}"
        )

    # Show ESMC protein family classification
    esmc = entry.get("esmc_classification")
    if esmc:
        lines.append("")
        lines.append(f"ESMC protein classification: {esmc['classification']}")
        lines.append(f"  Max protein similarity: {esmc['max_similarity']:.3f}")
        lines.append(f"  {esmc['interpretation']}")
        if esmc.get("drug_target"):
            lines.append(
                f"  Best match: {esmc['drug_target']} <-> {esmc['reference_target']} "
                f"(via {esmc['reference_drug']})"
            )

    if entry["chains"]:
        # Classify chains by quality
        high_chains = []  # all hops >= 0.70
        mid_chains = []   # min hop 0.40-0.69
        low_chains = []   # any hop < 0.40
        for chain in entry["chains"]:
            min_conf = min(e["confidence"] for e in chain["edges"])
            if min_conf >= 0.70:
                high_chains.append(chain)
            elif min_conf >= 0.40:
                mid_chains.append(chain)
            else:
                low_chains.append(chain)

        lines.append("")
        summary_parts = []
        if high_chains:
            summary_parts.append(f"{len(high_chains)} high-confidence")
        if mid_chains:
            summary_parts.append(f"{len(mid_chains)} medium")
        if low_chains:
            summary_parts.append(f"{len(low_chains)} speculative")
        lines.append(f"Evidence chains: {len(entry['chains'])} total ({', '.join(summary_parts)})")

        for i, chain in enumerate(entry["chains"], 1):
            lines.append(f"  {i}. ", )
            prov_notes = []
            for edge in chain["edges"]:
                prov = edge.get("provenance", "unknown")
                # Summarize protein similarity provenance instead of dumping 30+ scores
                if prov and (prov.startswith("ESM2:") or prov.startswith("ESMC:")
                             or prov.startswith("text_similarity:")):
                    sim_scores = [float(s.split("(")[1].rstrip(")"))
                                  for s in prov.split("; ") if "(" in s]
                    n = len(sim_scores)
                    avg = sum(sim_scores) / n if n else 0
                    if prov.startswith("ESMC:"):
                        prov_display = f"ESMC protein similarity ({n} proteins, avg {avg:.2f})"
                    elif prov.startswith("text_similarity:"):
                        prov_display = f"text similarity ({n} proteins, avg {avg:.2f})"
                    else:
                        prov_display = f"ESM2 protein similarity ({n} proteins, avg {avg:.2f})"
                elif prov and prov != "unknown":
                    prov_display = prov
                else:
                    prov_display = "uncited"
                # Add quantitative data if available
                quant_info = ""
                quant_val = edge.get("quantitative_value")
                quant_unit = edge.get("value_unit")
                if quant_val is not None and quant_unit:
                    if quant_unit == "ic50":
                        quant_info = f"  [IC50={quant_val:.3f} uM]"
                    elif quant_unit == "hazard_ratio":
                        quant_info = f"  [HR={quant_val:.2f}]"
                    elif quant_unit == "mutation_frequency":
                        quant_info = f"  [Mutation freq={quant_val*100:.1f}%]"
                    elif quant_unit == "response_rate":
                        quant_info = f"  [Response rate={quant_val*100:.1f}%]"

                source_type = edge.get("source_type", "unknown_or_internal")
                validation_status = edge.get("validation_status", "unclassified")
                prov_notes.append(
                    f"     {prov_display} ({edge['source']}->{edge['target']})"
                    f"{quant_info}  confidence: {edge['confidence']:.2f}"
                    f"  source_type={source_type} status={validation_status}"
                )
            lines[-1] += " -> ".join(
                [chain["edges"][0]["source"]]
                + [f"-{e['relation']}-> {e['target']}" for e in chain["edges"]]
            )
            for note in prov_notes:
                lines.append(note)

    cited = entry["cited_edges"]
    total = entry["total_edges"]
    if total > 0:
        lines.append(f"\nProvenance: {cited}/{total} chain edges cited")
    else:
        lines.append("\nProvenance: no chain edges")
    lines.append("")
    return "\n".join(lines)


# ── Terminal output ──────────────────────────────────────────────────

def format_terminal(results: list[dict], query_label: str,
                    n_objects: int, n_morphisms: int, n_positives: int,
                    check_recovered: int, check_total: int,
                    detail_novel_top: int = 5,
                    detail_all: bool = False) -> str:
    """Render the default terminal report."""
    lines = []
    lines.append(f"KOMPOSOS-IV-PHARM Candidate Triage: {query_label}")
    lines.append("=" * 60)
    lines.append(f"Graph: {n_objects} objects, {n_morphisms} morphisms, {n_positives} approved indications")
    lines.append(f"Self-check: {check_recovered}/{check_total} approved indications mechanistically recoverable")
    lines.append(f"Labels: APPROVED = in our {n_positives} FDA oncology indications; NOT_APPROVED = not in our list (may still be in trials/literature)")
    lines.append("")

    # Table header
    hdr = f"{'Rank':>4}  {'Drug' if results and 'disease' != query_label else 'Target':<20s}  {'RankScore':>9}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    # Detect if this is drug-first (results have varying diseases) or disease-first
    is_drug_first = len(set(r["disease"] for r in results)) > 1
    if is_drug_first:
        hdr = f"{'Rank':>4}  {'Disease':<20s}  {'RankScore':>9}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    else:
        hdr = f"{'Rank':>4}  {'Drug':<20s}  {'RankScore':>9}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    lines.append(hdr)
    lines.append(f"{'----':>4}  {'----':<20s}  {'---------':>9}  {'-----':<10s}  {'--------':<10s}  {'------':>6}  ----------------")

    detail_entries = []
    for entry in results:
        entity = entry["disease"] if is_drug_first else entry["drug"]
        top_path = _top_evidence_path(entry["chains"])
        evidence_type = "Mechanistic" if entry["n_chains"] > 0 else "Analogy"
        lines.append(
            f"{entry['rank']:>4}  {entity:<20s}  {entry['score']:>9.3f}  {entry['label']:<10s}  {evidence_type:<10s}  {entry['n_chains']:>6}  {top_path}"
        )
        if detail_all:
            detail_entries.append(entry)
        elif entry["label"] == "NOT_APPROVED" and len(detail_entries) < detail_novel_top:
            detail_entries.append(entry)

    # Auto-expand detail blocks
    if detail_entries:
        lines.append("")
        for entry in detail_entries:
            lines.append(_detail_block(entry))

    return "\n".join(lines)


# ── JSON output ──────────────────────────────────────────────────────

def format_json(results: list[dict], query_label: str,
                n_objects: int, n_morphisms: int, n_positives: int,
                check_recovered: int, check_total: int) -> str:
    """Render the full structured JSON report."""
    report = {
        "query": query_label,
        "graph": {
            "n_objects": n_objects,
            "n_morphisms": n_morphisms,
            "n_approved_indications": n_positives,
        },
        "self_check": {
            "recovered": check_recovered,
            "total": check_total,
        },
        "candidates": [],
    }
    for entry in results:
        candidate = {
            "rank": entry["rank"],
            "drug": entry["drug"],
            "disease": entry["disease"],
            "ranking_score": round(entry["score"], 4),
            "benchmark_label_rate": (
                round(entry["benchmark_label_rate"], 6)
                if entry.get("benchmark_label_rate") is not None
                else None
            ),
            "label": entry["label"],
            "evidence": "Mechanistic" if entry["n_chains"] > 0 else "Analogy",
            "strategy_votes": {name: round(conf, 4) for name, conf in entry["votes"]},
            "score_breakdown": entry.get("breakdown"),
            "n_chains": entry["n_chains"],
            "provenance": {
                "cited_edges": entry["cited_edges"],
                "total_edges": entry["total_edges"],
            },
            "chains": entry["chains"],
            "esmc_classification": entry.get("esmc_classification"),
        }
        report["candidates"].append(candidate)
    return json.dumps(report, indent=2, default=str)


# ── Markdown output ──────────────────────────────────────────────────

def format_markdown(results: list[dict], query_label: str,
                    n_objects: int, n_morphisms: int, n_positives: int,
                    check_recovered: int, check_total: int) -> str:
    """Render a partner-readable markdown report."""
    lines = []
    lines.append(f"# KOMPOSOS-IV-PHARM Candidate Triage: {query_label}")
    lines.append("")
    lines.append("## Graph Summary")
    lines.append("")
    lines.append(f"- **Objects:** {n_objects}")
    lines.append(f"- **Morphisms:** {n_morphisms}")
    lines.append(f"- **Approved indications:** {n_positives}")
    lines.append(f"- **Self-check:** {check_recovered}/{check_total} approved indications mechanistically recoverable")
    lines.append("")
    lines.append("## Ranked Candidates")
    lines.append("")

    is_drug_first = len(set(r["disease"] for r in results)) > 1
    entity_col = "Disease" if is_drug_first else "Drug"
    lines.append(f"| Rank | {entity_col} | Ranking Score | Label | Chains | Cited | Top Evidence Path |")
    lines.append("|------|" + "-" * (len(entity_col) + 2) + "|-------|-------|--------|-------|-------------------|")

    for entry in results:
        entity = entry["disease"] if is_drug_first else entry["drug"]
        top_path = _top_evidence_path(entry["chains"])
        cited_str = f"{entry['cited_edges']}/{entry['total_edges']}" if entry["total_edges"] > 0 else "-"
        lines.append(
            f"| {entry['rank']} | {entity} | {entry['score']:.3f} | {entry['label']} | {entry['n_chains']} | {cited_str} | {top_path} |"
        )

    # Detail sections for NOT_APPROVED candidates (repurposing hypotheses)
    not_approved = [e for e in results if e["label"] == "NOT_APPROVED" and e["score"] > 0]
    if not_approved:
        lines.append("")
        lines.append("## Repurposing Candidate Details")
        lines.append("")
        lines.append("*NOT_APPROVED means not in our 44 FDA-approved oncology indications.*")
        lines.append("*These candidates may already be in clinical trials or published literature.*")
        for entry in not_approved[:5]:
            lines.append("")
            lines.append(f"### #{entry['rank']} {entry['drug']} -> {entry['disease']}")
            lines.append("")
            lines.append(f"**Ranking score:** {entry['score']:.3f}")
            label_rate = entry.get("benchmark_label_rate")
            if label_rate is not None:
                lines.append(
                    f"**Benchmark label rate:** {label_rate:.1%} "
                    "(score-bin FDA-label rate, not clinical probability)"
                )
            breakdown = entry.get("breakdown")
            if breakdown:
                lines.append(
                    f"**Breakdown:** base={breakdown['base']:.3f}, "
                    f"path_bonus={breakdown['path_bonus']:.3f}, "
                    f"yoneda_bonus={breakdown.get('yoneda_bonus', 0.0):.3f}, "
                    f"composition_paths={breakdown['composition_count']}"
                )
            lines.append("")
            if entry["votes"]:
                lines.append("| Strategy | Score |")
                lines.append("|----------|-------|")
                for name, conf in entry["votes"]:
                    lines.append(f"| {name} | {conf:.2f} |")
                lines.append("")
            esmc = entry.get("esmc_classification")
            if esmc:
                lines.append(f"**ESMC Protein Classification:** {esmc['classification']}")
                lines.append(f"- Max protein similarity: {esmc['max_similarity']:.3f}")
                lines.append(f"- {esmc['interpretation']}")
                if esmc.get("drug_target"):
                    lines.append(
                        f"- Best match: {esmc['drug_target']} <-> "
                        f"{esmc['reference_target']} (via {esmc['reference_drug']})"
                    )
                lines.append("")
            if entry["chains"]:
                lines.append("**Evidence chains:**")
                lines.append("")
                for i, chain in enumerate(entry["chains"], 1):
                    path_parts = [chain["edges"][0]["source"]]
                    for e in chain["edges"]:
                        path_parts.append(f"-{e['relation']}->")
                        path_parts.append(e["target"])
                    lines.append(f"{i}. {' '.join(path_parts)}")
                    for edge in chain["edges"]:
                        prov = edge.get("provenance", "unknown")
                        if prov == "unknown":
                            prov_str = "uncited"
                        elif "PMID:" in prov:
                            # Extract all PMIDs using regex to handle "ABPP; PMID:1234" etc.
                            import re
                            pmid_matches = re.findall(r"PMID:?\s*(\d+)", prov)
                            if pmid_matches:
                                prov_str = prov
                                for p in pmid_matches:
                                    prov_str = prov_str.replace(f"PMID:{p}", f"[PMID:{p}](https://pubmed.ncbi.nlm.nih.gov/{p})")
                            else:
                                prov_str = prov
                        else:
                            prov_str = prov

                        # Format edge info with quantitative data if available
                        edge_info = f"   - {edge['source']}->{edge['target']}: {prov_str}"

                        # Add quantitative value if present
                        quant_val = edge.get("quantitative_value")
                        quant_unit = edge.get("value_unit")
                        if quant_val is not None and quant_unit:
                            if quant_unit == "ic50":
                                edge_info += f" | IC50={quant_val:.3f} uM"
                            elif quant_unit == "hazard_ratio":
                                edge_info += f" | HR={quant_val:.2f}"
                            elif quant_unit == "mutation_frequency":
                                edge_info += f" | Mutation freq={quant_val*100:.1f}%"
                            elif quant_unit == "response_rate":
                                edge_info += f" | Response rate={quant_val*100:.1f}%"

                        edge_info += f" (confidence: {edge['confidence']:.2f})"
                        edge_info += (
                            f" | source_type={edge.get('source_type', 'unknown_or_internal')}"
                            f" | status={edge.get('validation_status', 'unclassified')}"
                        )
                        lines.append(edge_info)
                lines.append("")
            cited = entry["cited_edges"]
            total = entry["total_edges"]
            if total > 0:
                lines.append(f"**Provenance:** {cited}/{total} chain edges cited")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="KOMPOSOS-IV-PHARM Candidate Triage CLI. "
        "Rank drugs for a disease, diseases for a drug, or inspect a specific pair."
    )
    parser.add_argument(
        "target", nargs="?", default=None,
        help="Disease name (default mode) or query target.",
    )
    parser.add_argument(
        "--drug", default=None,
        help="Drug name. If target is also given, show that specific pair. "
        "If target is omitted, rank all diseases for this drug.",
    )
    parser.add_argument("--top", type=int, default=10, help="Show top N candidates (default: 10).")
    parser.add_argument("--all", action="store_true", dest="show_all", help="Show all candidates.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON.")
    parser.add_argument("--markdown", action="store_true", dest="as_markdown", help="Output as Markdown.")
    parser.add_argument("--db", default=DB_PATH, help="Path to tier1 SQLite database.")
    args = parser.parse_args()

    if args.target is None and args.drug is None:
        parser.error("Provide a disease name or --drug <name>.")

    # Load graph
    category, _ = load_full_typed_view(args.db)
    drugs_list, diseases_list, positives = drug_disease_pairs(category)
    strategies = make_strategies(category)
    provenance_index = _build_provenance_index(args.db)

    # Load ESMC embedder for protein classification (graceful fallback)
    embedder = _load_esmc_embedder()

    n_objects = len(category.objects())
    n_morphisms = len(category.morphisms())
    n_positives = len(positives)

    # Validate inputs
    if args.target and args.drug is None:
        # Disease-first mode: target must be a disease
        if args.target not in diseases_list:
            print(f"Error: '{args.target}' not found in diseases.", file=sys.stderr)
            print(f"Available diseases: {', '.join(diseases_list)}", file=sys.stderr)
            return 1
    elif args.drug and args.target is None:
        # Drug-first mode
        if args.drug not in drugs_list:
            print(f"Error: '{args.drug}' not found in drugs.", file=sys.stderr)
            print(f"Available drugs: {', '.join(drugs_list)}", file=sys.stderr)
            return 1
    elif args.target and args.drug:
        # Specific pair mode
        if args.drug not in drugs_list:
            print(f"Error: '{args.drug}' not found in drugs.", file=sys.stderr)
            return 1
        if args.target not in diseases_list:
            print(f"Error: '{args.target}' not found in diseases.", file=sys.stderr)
            return 1

    # Self-check
    check_recovered, check_total = self_check(category, drugs_list, diseases_list, positives)

    # Route to correct triage mode
    if args.target and args.drug:
        # Specific pair: single-entry result with full detail
        breakdown = score_pair_detailed(strategies, args.drug, args.target)
        score = breakdown["score"]
        votes = breakdown["votes"]
        trace = trace_pair(category, args.drug, args.target, None, provenance_index)
        label = _label_for_pair((args.drug, args.target), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results = [{
            "rank": 1,
            "drug": args.drug,
            "disease": args.target,
            "score": score,
            "benchmark_label_rate": _benchmark_label_rate(score),
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
            "breakdown": breakdown,
        }]
        query_label = f"{args.drug} -> {args.target}"
    elif args.target:
        # Disease-first
        query_label = args.target
        results = triage_disease(
            category, strategies, args.target, positives, provenance_index,
            top_n=args.top, show_all=args.show_all,
        )
    else:
        # Drug-first
        query_label = f"--drug {args.drug}"
        results = triage_drug(
            category, strategies, args.drug, positives, provenance_index,
            top_n=args.top, show_all=args.show_all,
        )

    # Add ESMC protein family classification to displayed results
    if embedder is not None:
        for entry in results:
            entry["esmc_classification"] = _esmc_classify(
                entry, positives, category, embedder
            )

    # Render output
    if args.as_json:
        output = format_json(results, query_label, n_objects, n_morphisms,
                             n_positives, check_recovered, check_total)
    elif args.as_markdown:
        output = format_markdown(results, query_label, n_objects, n_morphisms,
                                 n_positives, check_recovered, check_total)
    else:
        # For specific pair, always show detail regardless of label
        is_pair = args.target and args.drug
        output = format_terminal(results, query_label, n_objects, n_morphisms,
                                 n_positives, check_recovered, check_total,
                                 detail_all=is_pair)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
