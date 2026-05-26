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
    score_pair,
)
from validation.trace_prediction import _build_provenance_index, trace_pair


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
        score, votes = score_pair(strategies, drug, disease)
        trace = trace_pair(category, drug, disease, strategies, provenance_index)
        label = _label_for_pair((drug, disease), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results.append({
            "rank": 0,
            "drug": drug,
            "disease": disease,
            "score": score,
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
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
        score, votes = score_pair(strategies, drug, disease)
        trace = trace_pair(category, drug, disease, strategies, provenance_index)
        label = _label_for_pair((drug, disease), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results.append({
            "rank": 0,
            "drug": drug,
            "disease": disease,
            "score": score,
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
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
    lines.append(f"Score: {entry['score']:.3f}")

    if entry["votes"]:
        lines.append("Scoring evidence:")
        # Map technical names to user-friendly labels
        strategy_labels = {
            "kan_extension": "Drug Analogy",
            "type_heuristic": "Type Match",
            "structural_hole": "Network Closure",
            "composition": "Mechanistic Path",
            "yoneda_pattern": "Interaction Profile",
            "fibration_lift": "Structural Inference",
            "topos_logic": "Evidence Integration",
            "binding_evidence": "Binding Evidence",
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
                # Summarize ESM2 provenance instead of dumping 30+ similarity scores
                if prov and prov.startswith("ESM2:"):
                    esm_scores = [float(s.split("(")[1].rstrip(")"))
                                  for s in prov.split("; ") if "(" in s]
                    n = len(esm_scores)
                    avg = sum(esm_scores) / n if n else 0
                    prov_display = f"ESM2 protein similarity ({n} proteins, avg {avg:.2f})"
                elif prov and prov != "unknown":
                    prov_display = prov
                else:
                    prov_display = "uncited"
                prov_notes.append(f"     {prov_display} ({edge['source']}->{edge['target']})  confidence: {edge['confidence']:.2f}")
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
    lines.append("Labels: APPROVED = in our 44 FDA oncology indications; NOT_APPROVED = not in our list (may still be in trials/literature)")
    lines.append("")

    # Table header
    hdr = f"{'Rank':>4}  {'Drug' if results and 'disease' != query_label else 'Target':<20s}  {'Score':>5}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    # Detect if this is drug-first (results have varying diseases) or disease-first
    is_drug_first = len(set(r["disease"] for r in results)) > 1
    if is_drug_first:
        hdr = f"{'Rank':>4}  {'Disease':<20s}  {'Score':>5}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    else:
        hdr = f"{'Rank':>4}  {'Drug':<20s}  {'Score':>5}  {'Label':<10s}  {'Evidence':<10s}  {'Chains':>6}  Top Evidence Path"
    lines.append(hdr)
    lines.append(f"{'----':>4}  {'----':<20s}  {'-----':>5}  {'-----':<10s}  {'--------':<10s}  {'------':>6}  ----------------")

    detail_entries = []
    for entry in results:
        entity = entry["disease"] if is_drug_first else entry["drug"]
        top_path = _top_evidence_path(entry["chains"])
        evidence_type = "Mechanistic" if entry["n_chains"] > 0 else "Analogy"
        lines.append(
            f"{entry['rank']:>4}  {entity:<20s}  {entry['score']:.3f}  {entry['label']:<10s}  {evidence_type:<10s}  {entry['n_chains']:>6}  {top_path}"
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
            "score": round(entry["score"], 4),
            "label": entry["label"],
            "evidence": "Mechanistic" if entry["n_chains"] > 0 else "Analogy",
            "strategy_votes": {name: round(conf, 4) for name, conf in entry["votes"]},
            "n_chains": entry["n_chains"],
            "provenance": {
                "cited_edges": entry["cited_edges"],
                "total_edges": entry["total_edges"],
            },
            "chains": entry["chains"],
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
    lines.append(f"| Rank | {entity_col} | Score | Label | Chains | Cited | Top Evidence Path |")
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
            lines.append(f"**Score:** {entry['score']:.3f}")
            lines.append("")
            if entry["votes"]:
                lines.append("| Strategy | Score |")
                lines.append("|----------|-------|")
                for name, conf in entry["votes"]:
                    lines.append(f"| {name} | {conf:.2f} |")
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
                        prov_str = prov if prov != "unknown" else "uncited"
                        if prov_str.startswith("PMID:"):
                            pmid_id = prov_str.replace("PMID:", "")
                            prov_str = f"[{prov}](https://pubmed.ncbi.nlm.nih.gov/{pmid_id})"
                        lines.append(f"   - {edge['source']}->{edge['target']}: {prov_str} (confidence: {edge['confidence']:.2f})")
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
        score, votes = score_pair(strategies, args.drug, args.target)
        trace = trace_pair(category, args.drug, args.target, strategies, provenance_index)
        label = _label_for_pair((args.drug, args.target), positives)
        cited, total_edges = _provenance_fraction(trace["chains"])
        results = [{
            "rank": 1,
            "drug": args.drug,
            "disease": args.target,
            "score": score,
            "label": label,
            "votes": votes,
            "n_chains": trace["n_chains"],
            "chains": trace["chains"],
            "cited_edges": cited,
            "total_edges": total_edges,
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
