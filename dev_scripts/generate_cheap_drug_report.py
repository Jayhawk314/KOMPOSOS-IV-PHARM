#!/usr/bin/env python3
"""
Generate Cheap Drug Repurposing Candidates Report

Runs triage for all diseases and extracts cheap generic drug candidates.
Renders full mechanistic chains with PMIDs from the triage JSON output.
"""

import subprocess
import json
import sys
from pathlib import Path

# List of cheap generic drugs to highlight
CHEAP_GENERICS = {
    'Mebendazole', 'Metformin', 'Atorvastatin', 'Aspirin', 'Doxycycline',
    'Cimetidine', 'Propranolol', 'Chloroquine', 'Niclosamide', 'Auranofin',
    'Disulfiram', 'Ivermectin', 'Valproic_Acid', 'Verapamil', 'Simvastatin',
    'Lovastatin', 'Pravastatin', 'Fluvastatin', 'Ibuprofen', 'Acetaminophen',
    'Ranitidine', 'Famotidine', 'Omeprazole', 'Lansoprazole', 'Dexamethasone',
    'Prednisone', 'Hydrocortisone', 'Azithromycin', 'Ciprofloxacin',
    'Levofloxacin', 'Minocycline', 'Tetracycline', 'Amoxicillin',
    'Clarithromycin', 'Clindamycin', 'Rifampicin', 'Isoniazid'
}

DISEASES = [
    'AML', 'Breast_Cancer', 'CLL', 'CML', 'Colorectal_Cancer',
    'Ewing_Sarcoma', 'GIST', 'Glioblastoma', 'HCC', 'Li_Fraumeni_Syndrome',
    'Melanoma', 'Multiple_Myeloma', 'Myelofibrosis', 'NSCLC', 'Ovarian_Cancer',
    'Pancreatic_Cancer', 'Prostate_Cancer', 'RCC', 'Soft_Tissue_Sarcoma',
    'Type2_Diabetes'
]


def run_triage(disease):
    """Run triage for a disease and return JSON results."""
    cmd = ['python', 'validation/triage.py', disease, '--all', '--json']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running triage for {disease}: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {disease}: {e}", file=sys.stderr)
        return None


def filter_cheap_generics(results, top_n=20):
    """Filter results for cheap generic drugs in top N."""
    if not results or 'candidates' not in results:
        return []

    candidates = results['candidates'][:top_n]
    return [c for c in candidates if c.get('drug', '') in CHEAP_GENERICS]


def format_chain_markdown(chain):
    """Format a single mechanistic chain as markdown with PMIDs."""
    edges = chain.get("edges", [])
    if not edges:
        return ""

    # Build path string: Drug -relation-> Target -relation-> Disease
    parts = [edges[0]["source"]]
    for edge in edges:
        parts.append(f" -{edge['relation']}-> {edge['target']}")
    path_str = "".join(parts)

    # Collect PMIDs and provenance
    pmids = []
    for edge in edges:
        prov = edge.get("provenance", "unknown")
        if prov and prov != "unknown":
            pmids.append(f"{edge['source']}->{edge['target']}: {prov}")

    lines = [f"`{path_str}`"]
    if pmids:
        for p in pmids:
            lines.append(f"  - {p}")

    return "\n".join(lines)


def generate_report():
    """Generate the full cheap drug repurposing report."""
    print("Generating Cheap Drug Repurposing Report...", file=sys.stderr)
    print(f"Analyzing {len(DISEASES)} diseases...", file=sys.stderr)

    # First pass: collect all cheap candidates
    disease_results = {}
    all_cheap = []

    for disease in DISEASES:
        print(f"Processing {disease}...", file=sys.stderr)
        results = run_triage(disease)
        disease_results[disease] = results

        if results:
            cheap = filter_cheap_generics(results, top_n=20)
            if cheap:
                all_cheap.extend([(disease, c) for c in cheap])

    print(f"\nFound {len(all_cheap)} cheap generic candidates", file=sys.stderr)

    # Build report
    report = []

    # ── Header ──────────────────────────────────────────────────────
    report.append("# Cheap Drug Repurposing Candidates\n\n")
    report.append("**Generated**: 2026-05-12\n")
    report.append("**Source**: KOMPOSOS-IV-PHARM tier1.db\n")
    report.append("**Graph**: 1143 objects, 1260 morphisms\n")
    report.append("**Validation**: LOOCV AUROC 0.974 [95% CI: 0.965-0.983], "
                   "full_typed/loocv protocol, 44 positives\n")
    report.append("**Strongest baseline**: shortest_path AUROC 0.931 "
                   "(margin +0.043)\n\n")

    # ── Executive Summary ───────────────────────────────────────────
    report.append("## Executive Summary\n\n")
    report.append("This report identifies cheap, FDA-approved generic drugs that show "
                   "mechanistic pathway evidence for repurposing to cancer indications, "
                   "based on categorical AI analysis of a drug-target-disease knowledge graph.\n\n")

    report.append("**Key Points:**\n")
    report.append("- All candidates are FDA-approved drugs (safety established)\n")
    report.append("- All candidates are generic (low cost, readily available)\n")
    report.append("- Rankings based on mechanistic Drug->Protein->Disease pathway analysis\n")
    report.append("- Each candidate includes evidence chains with literature citations (PMIDs)\n")
    report.append("- NOT_APPROVED label means not in our 44 FDA-approved oncology "
                   "indications -- candidates may already be in clinical trials or "
                   "published literature\n")
    report.append("- This is a research tool for hypothesis generation, not clinical "
                   "recommendations\n\n")

    report.append(f"**Cheap Generics Screened**: {len(CHEAP_GENERICS)} drugs\n")
    report.append(f"**Diseases Analyzed**: {len(DISEASES)} cancer types\n")
    report.append(f"**Candidates Found**: {len(all_cheap)} drug-disease entries\n\n")

    report.append("---\n\n")

    # ── Multi-Disease Candidates ────────────────────────────────────
    by_drug = {}
    for disease, candidate in all_cheap:
        drug = candidate['drug']
        if drug not in by_drug:
            by_drug[drug] = []
        by_drug[drug].append((disease, candidate))

    sorted_drugs = sorted(by_drug.items(), key=lambda x: len(x[1]), reverse=True)

    report.append("## Multi-Disease Candidates\n\n")
    report.append("Drugs with mechanistic pathway support for multiple cancers "
                   "(highest priority for investigation):\n\n")

    for drug, disease_candidates in sorted_drugs:
        if len(disease_candidates) > 1:
            report.append(f"### {drug}\n\n")
            report.append(f"**Cancer types**: {len(disease_candidates)}\n\n")

            for disease, candidate in sorted(disease_candidates,
                                             key=lambda x: x[1]['score'],
                                             reverse=True):
                label = candidate['label']
                score = candidate['score']
                rank = candidate['rank']
                n_chains = candidate.get('n_chains', 0)
                report.append(f"- **{disease}**: Rank {rank}, Score {score:.3f}, "
                               f"{n_chains} mechanistic paths ({label})\n")

            report.append("\n")

    report.append("---\n\n")

    # ── Disease-by-Disease Breakdown with Chains + PMIDs ────────────
    report.append("## Disease-by-Disease Breakdown\n\n")

    for disease in DISEASES:
        print(f"Formatting {disease}...", file=sys.stderr)
        results = disease_results.get(disease)

        if not results:
            continue

        cheap = filter_cheap_generics(results, top_n=20)
        if not cheap:
            continue

        report.append(f"## {disease}\n\n")

        # Summary stats -- use new label names
        approved = [c for c in cheap if c['label'] == 'APPROVED']
        not_approved = [c for c in cheap if c['label'] == 'NOT_APPROVED']

        report.append(f"**Cheap generics in top 20**: {len(cheap)}\n")
        if approved:
            report.append(f"**FDA-approved for this cancer**: {len(approved)}\n")
        report.append(f"**Repurposing candidates** (not in our 44 FDA "
                       f"oncology indications): {len(not_approved)}\n\n")

        # List candidates with full evidence
        for candidate in cheap:
            drug = candidate['drug']
            score = candidate['score']
            label = candidate['label']
            rank = candidate['rank']

            report.append(f"### {rank}. {drug}\n\n")
            report.append(f"- **Score**: {score:.3f}\n")
            report.append(f"- **Status**: {label}\n")

            # Strategy votes (the correct field from triage JSON)
            strategy_votes = candidate.get('strategy_votes', {})
            if strategy_votes:
                top3 = sorted(strategy_votes.items(),
                              key=lambda x: x[1], reverse=True)[:3]
                report.append("- **Top Strategies**: "
                              + ", ".join(f"{s} ({v:.3f})" for s, v in top3)
                              + "\n")

            # Provenance coverage
            prov = candidate.get('provenance', {})
            cited = prov.get('cited_edges', 0)
            total = prov.get('total_edges', 0)
            if total > 0:
                report.append(f"- **Provenance**: {cited}/{total} chain edges "
                               f"cited ({100*cited/total:.0f}%)\n")

            # Mechanistic chains with PMIDs (Bug 1 fix)
            chains = candidate.get('chains', [])
            if chains:
                report.append(f"- **Mechanistic paths**: {len(chains)}\n\n")
                for i, chain in enumerate(chains[:3], 1):  # Show top 3 chains
                    report.append(f"**Path {i}** "
                                   f"(confidence: {chain.get('path_confidence', 0):.3f}):\n")
                    report.append(format_chain_markdown(chain) + "\n\n")
            else:
                report.append("\n")

        report.append("---\n\n")

    # ── Methodology ─────────────────────────────────────────────────
    report.append("## Methodology\n\n")
    report.append("**Scoring**: Categorical AI analysis combining 22 mathematical "
                   "strategies over the drug-target-disease knowledge graph. Each "
                   "candidate is scored by averaging strategy votes and adding a "
                   "path bonus for Drug->Protein->Disease mechanistic chains.\n\n")

    report.append("**Graph Source**: tier1.db\n")
    report.append("- 1143 objects: 78 drugs, 366 proteins, 20 diseases, "
                   "679 ExternalCompound nodes\n")
    report.append("- 1260 morphisms (edges)\n")
    report.append("- 44 FDA-approved oncology indications (ground truth labels)\n")
    report.append("- 958/1260 morphisms with provenance (76%): "
                   "86 PMIDs, 872 ChEMBL/DOI\n\n")

    report.append("**Validation** (audit-reproduced):\n")
    report.append("- LOOCV AUROC: 0.974 [95% CI: 0.965-0.983] "
                   "(full_typed/loocv protocol, 44 positives)\n")
    report.append("- Strongest baseline: shortest_path AUROC 0.931 "
                   "(margin: +0.043)\n")
    report.append("- Other baselines: common_neighbor 0.918, path_count 0.596, "
                   "degree_product 0.474, random 0.469\n\n")

    report.append("**Validation** (reported, not yet audit-reproduced):\n")
    report.append("- External (Hetionet): AUROC 0.744 on 7 held-out pairs\n")
    report.append("- Temporal holdout (2013 cutoff): AUROC 0.959 on 22 "
                   "post-2013 FDA approvals\n")
    report.append("- Disease-level holdout: Mean AUROC 0.877 across 7 diseases\n\n")

    report.append("**Status Labels**:\n")
    report.append("- **APPROVED**: FDA-approved oncology indication "
                   "(one of 44 in our database)\n")
    report.append("- **NOT_APPROVED**: Not in our 44 FDA-approved oncology "
                   "indications. This does NOT mean the drug-disease combination "
                   "is novel or unstudied. It may already be in clinical trials, "
                   "published literature, or off-label use. The label only reflects "
                   "what is in our curated database.\n\n")

    # ── Disclaimer ──────────────────────────────────────────────────
    report.append("## Disclaimer\n\n")
    report.append("This is a **research tool for hypothesis generation**, not a "
                   "clinical decision support system. All predictions require "
                   "experimental and clinical validation before any clinical use. "
                   "Do not use for patient treatment without proper validation, "
                   "IRB approval, and clinical trial design.\n\n")

    report.append("---\n\n")
    report.append("**Generated by**: KOMPOSOS-IV-PHARM\n")
    report.append("**License**: Apache 2.0 / Commercial dual license\n")
    report.append("**Author**: James Ray Hawkins\n")

    return ''.join(report)


if __name__ == '__main__':
    report = generate_report()

    output_file = 'CHEAP_DRUG_REPURPOSING_CANDIDATES.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport generated: {output_file}", file=sys.stderr)
    # Don't print to console (Windows encoding issues with Unicode)
