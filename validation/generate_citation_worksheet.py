#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Generate a citation worksheet for uncited morphisms.

Outputs a printable list of edges that need PubMed citations,
grouped by type, with pre-built PubMed search URLs.

Usage:
    python validation/generate_citation_worksheet.py
    python validation/generate_citation_worksheet.py --type drug_protein
    python validation/generate_citation_worksheet.py --type protein_disease
    python validation/generate_citation_worksheet.py --csv citations_todo.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.store import KomposOSStore

DB_PATH = "data/drugs/tier1.db"

PROTEIN_TYPES = {
    "Receptor", "Signaling", "Transcription", "TumorSuppressor",
    "Apoptosis", "Oncogene", "DNARepair", "CellCycle", "Regulator",
    "Splicing", "Epigenetic", "Metabolic", "Structural", "Chaperone",
    "Transporter", "Ligand", "Enzyme", "Marker",
}

# Human-readable names for common gene symbols
GENE_ALIASES = {
    "EGFR": "EGFR epidermal growth factor receptor",
    "ERBB2": "ERBB2 HER2",
    "VEGFR2": "KDR VEGFR2",
    "MTOR": "mTOR mechanistic target of rapamycin",
    "BCR_ABL": "BCR-ABL fusion",
    "KRAS": "KRAS",
    "BRAF": "BRAF V600",
    "ALK": "ALK anaplastic lymphoma kinase",
    "MET": "MET hepatocyte growth factor receptor",
    "KIT": "KIT stem cell factor receptor",
    "PDGFRA": "PDGFRA platelet-derived growth factor receptor",
    "JAK2": "JAK2 Janus kinase",
    "CDK4": "CDK4 cyclin-dependent kinase 4",
    "CDK6": "CDK6 cyclin-dependent kinase 6",
    "BCL2": "BCL2 B-cell lymphoma 2",
    "BRCA1": "BRCA1",
    "BRCA2": "BRCA2",
    "TP53": "TP53 p53 tumor suppressor",
    "AMPK": "AMPK AMP-activated protein kinase",
    "MEK1": "MEK1 MAP2K1",
    "CRBN": "CRBN cereblon",
}

RELATION_VERBS = {
    "inhibits": "inhibitor",
    "activates": "activator",
    "indirect_inhibitor": "inhibitor",
    "modulates": "modulator",
    "pathway_modulator": "modulator",
    "associated_with": "role in",
    "driver_of": "driver",
    "treats": "treatment",
}


def pubmed_url(drug: str, target: str, relation: str, target_type: str) -> str:
    """Build a PubMed search URL for an edge."""
    target_search = GENE_ALIASES.get(target, target)
    verb = RELATION_VERBS.get(relation, relation)

    if target_type == "Disease":
        query = f"{drug} {target_search} {verb}"
    else:
        query = f"{drug} {target_search} {verb}"

    encoded = urllib.parse.quote_plus(query)
    return f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded}"


def main():
    parser = argparse.ArgumentParser(description="Generate citation worksheet.")
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument(
        "--type",
        choices=["drug_protein", "protein_disease", "all"],
        default="all",
    )
    parser.add_argument("--csv", default=None, help="Output CSV file path")
    args = parser.parse_args()

    store = KomposOSStore(args.db)
    objects = store.list_objects(limit=100000)
    morphisms = store.list_morphisms(limit=100000)
    type_by_name = {o.name: o.type_name for o in objects}

    drug_protein = []
    protein_disease = []

    for m in morphisms:
        st = type_by_name.get(m.source_name, "?")
        tt = type_by_name.get(m.target_name, "?")
        prov = getattr(m, "provenance", "unknown")
        if prov != "unknown":
            continue
        if st == "Drug" and tt in PROTEIN_TYPES:
            drug_protein.append(m)
        elif st in PROTEIN_TYPES and tt == "Disease":
            protein_disease.append(m)

    edges = []
    if args.type in ("drug_protein", "all"):
        for m in drug_protein:
            tt = type_by_name.get(m.target_name, "?")
            edges.append(("Drug->Protein", m, tt))
    if args.type in ("protein_disease", "all"):
        for m in protein_disease:
            tt = type_by_name.get(m.target_name, "?")
            edges.append(("Protein->Disease", m, tt))

    edges.sort(key=lambda x: (x[0], x[1].source_name, x[1].target_name))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "category", "source", "relation", "target", "target_type",
                "confidence", "pubmed_search_url", "pmid", "verified",
            ])
            for cat, m, tt in edges:
                url = pubmed_url(m.source_name, m.target_name, m.name, tt)
                writer.writerow([
                    cat, m.source_name, m.name, m.target_name, tt,
                    f"{m.confidence:.2f}", url, "", "",
                ])
        print(f"Wrote {len(edges)} rows to {args.csv}")
        return

    # Print worksheet
    current_cat = None
    count = 0
    for cat, m, tt in edges:
        if cat != current_cat:
            current_cat = cat
            print(f"\n{'=' * 80}")
            print(f"  {cat} EDGES NEEDING CITATION")
            print(f"{'=' * 80}\n")

        count += 1
        url = pubmed_url(m.source_name, m.target_name, m.name, tt)
        print(f"  {count:3d}. {m.source_name} --[{m.name}]--> {m.target_name} ({tt})")
        print(f"       confidence={m.confidence:.2f}")
        print(f"       PubMed: {url}")
        print(f"       PMID: _______________")
        print()

    print(f"{'=' * 80}")
    print(f"  Total edges needing citation: {len(edges)}")
    print(f"  Drug->Protein: {len(drug_protein)}")
    print(f"  Protein->Disease: {len(protein_disease)}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
