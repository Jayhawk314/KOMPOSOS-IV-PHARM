#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Search PubMed for papers with quantitative data related to our drug-disease-protein network.

Strategies:
1. Drug + Disease + "IC50" OR "response rate" OR "hazard ratio"
2. Protein + Disease + "mutation frequency" OR "mutation rate"
3. Drug + Protein + "IC50" OR "Ki" OR "Kd"
4. Disease + "KRAS mutation" OR "BRAF mutation" etc.

Builds a list of PMIDs likely to contain quantitative data for our edges.
"""

import requests
import time
import sqlite3
import json
from typing import List, Set, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


def load_drugs_diseases_proteins(conn: sqlite3.Connection) -> Tuple[List[str], List[str], List[str]]:
    """Load all drugs, diseases, and proteins from database."""
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM objects WHERE type_name = 'Drug'")
    drugs = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM objects WHERE type_name = 'Disease'")
    diseases = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name FROM objects WHERE type_name = 'Protein'")
    proteins = [row[0] for row in cursor.fetchall()]

    return drugs, diseases, proteins


def search_pubmed(query: str, max_results: int = 100) -> List[str]:
    """
    Search PubMed and return list of PMIDs.

    Args:
        query: PubMed search query
        max_results: Maximum number of results to return

    Returns:
        List of PMIDs
    """
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'tool': 'KOMPOSOS-IV-PHARM',
        'email': 'komposos@example.com'
    }

    try:
        response = requests.get(PUBMED_SEARCH_API, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if 'esearchresult' in data and 'idlist' in data['esearchresult']:
                return data['esearchresult']['idlist']
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Search failed: {e}")

    return []


def build_drug_disease_queries(drugs: List[str], diseases: List[str]) -> List[Tuple[str, str, str]]:
    """
    Build PubMed queries for drug-disease pairs with quantitative data.

    Returns:
        List of (query_string, drug_name, disease_name) tuples
    """
    queries = []

    # Focus on high-value quantitative terms
    quantitative_terms = [
        "IC50[Title/Abstract]",
        "response rate[Title/Abstract]",
        "hazard ratio[Title/Abstract]",
        "overall response rate[Title/Abstract]",
        "ORR[Title/Abstract]",
        "progression-free survival[Title/Abstract]",
        "PFS[Title/Abstract]"
    ]

    # Sample high-priority drugs (kinase inhibitors, targeted therapies)
    priority_drugs = [
        "Imatinib", "Sorafenib", "Sunitinib", "Vemurafenib", "Dabrafenib",
        "Trametinib", "Erlotinib", "Gefitinib", "Osimertinib", "Crizotinib",
        "Ceritinib", "Alectinib", "Pazopanib", "Axitinib", "Cabozantinib",
        "Lenvatinib", "Regorafenib", "Lapatinib", "Afatinib", "Ruxolitinib"
    ]

    # Sample diseases
    priority_diseases = [
        "melanoma", "NSCLC", "RCC", "AML", "CML", "breast cancer",
        "colorectal cancer", "pancreatic cancer", "glioblastoma"
    ]

    for drug in drugs:
        if drug not in priority_drugs:
            continue

        for disease in diseases:
            disease_term = disease.replace("_", " ")

            if disease not in priority_diseases and disease_term.lower() not in [d.lower() for d in priority_diseases]:
                continue

            # Build query with quantitative terms
            quant_query = " OR ".join(quantitative_terms)
            query = f'({drug}[Title/Abstract]) AND ({disease_term}[Title/Abstract]) AND ({quant_query})'

            queries.append((query, drug, disease))

    return queries


def build_protein_mutation_queries(proteins: List[str], diseases: List[str]) -> List[Tuple[str, str, str]]:
    """
    Build PubMed queries for protein mutations in diseases.

    Returns:
        List of (query_string, protein_name, disease_name) tuples
    """
    queries = []

    # Focus on commonly mutated oncogenes/tumor suppressors
    priority_proteins = [
        "KRAS", "NRAS", "BRAF", "EGFR", "ALK", "ROS1", "MET", "RET",
        "TP53", "PIK3CA", "PTEN", "AKT1", "ERBB2", "KIT", "PDGFRA",
        "FLT3", "JAK2", "BRCA1", "BRCA2", "ATM", "STK11", "KEAP1"
    ]

    mutation_terms = [
        "mutation frequency[Title/Abstract]",
        "mutation rate[Title/Abstract]",
        "mutated in[Title/Abstract]",
        "% mutation[Title/Abstract]",
        "prevalence[Title/Abstract]"
    ]

    for protein in proteins:
        if protein not in priority_proteins:
            continue

        for disease in diseases:
            disease_term = disease.replace("_", " ")

            mut_query = " OR ".join(mutation_terms)
            query = f'({protein}[Title/Abstract]) AND ({disease_term}[Title/Abstract]) AND ({mut_query})'

            queries.append((query, protein, disease))

    return queries


def build_drug_target_queries(drugs: List[str], proteins: List[str]) -> List[Tuple[str, str, str]]:
    """
    Build PubMed queries for drug-target IC50/binding data.

    Returns:
        List of (query_string, drug_name, protein_name) tuples
    """
    queries = []

    binding_terms = [
        "IC50[Title/Abstract]",
        "Ki[Title/Abstract]",
        "Kd[Title/Abstract]",
        "binding affinity[Title/Abstract]",
        "inhibition[Title/Abstract]"
    ]

    # Sample from both lists
    for drug in drugs[:20]:  # First 20 drugs
        for protein in proteins[:50]:  # First 50 proteins
            bind_query = " OR ".join(binding_terms)
            query = f'({drug}[Title/Abstract]) AND ({protein}[Title/Abstract]) AND ({bind_query})'

            queries.append((query, drug, protein))

    return queries


def main():
    print("="*70)
    print("PUBMED QUANTITATIVE DATA SEARCH")
    print("="*70)
    print()

    conn = sqlite3.connect(DB_PATH)

    print("[1] Loading drugs, diseases, proteins from database...")
    drugs, diseases, proteins = load_drugs_diseases_proteins(conn)
    print(f"  Drugs: {len(drugs)}")
    print(f"  Diseases: {len(diseases)}")
    print(f"  Proteins: {len(proteins)}")
    print()

    # Build search queries
    print("[2] Building PubMed search queries...")

    drug_disease_queries = build_drug_disease_queries(drugs, diseases)
    protein_mutation_queries = build_protein_mutation_queries(proteins, diseases)
    drug_target_queries = build_drug_target_queries(drugs, proteins)

    print(f"  Drug-Disease queries: {len(drug_disease_queries)}")
    print(f"  Protein-Mutation queries: {len(protein_mutation_queries)}")
    print(f"  Drug-Target queries: {len(drug_target_queries)}")
    print()

    # Execute searches
    print("[3] Searching PubMed (rate-limited to 3 req/sec)...")
    print()

    all_pmids: Set[str] = set()
    pmid_metadata = {}

    # Drug-Disease searches
    print("Searching Drug-Disease pairs with quantitative data...")
    for i, (query, drug, disease) in enumerate(drug_disease_queries):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(drug_disease_queries)}")

        pmids = search_pubmed(query, max_results=20)

        for pmid in pmids:
            all_pmids.add(pmid)
            if pmid not in pmid_metadata:
                pmid_metadata[pmid] = []
            pmid_metadata[pmid].append({
                "type": "drug_disease",
                "drug": drug,
                "disease": disease,
                "expected_data": ["response_rate", "hazard_ratio", "ic50"]
            })

        # Rate limiting
        time.sleep(0.35)

    print()
    print("Searching Protein-Disease mutations...")
    for i, (query, protein, disease) in enumerate(protein_mutation_queries[:50]):  # Limit to 50 for now
        if i % 10 == 0:
            print(f"  Progress: {i}/50")

        pmids = search_pubmed(query, max_results=20)

        for pmid in pmids:
            all_pmids.add(pmid)
            if pmid not in pmid_metadata:
                pmid_metadata[pmid] = []
            pmid_metadata[pmid].append({
                "type": "protein_mutation",
                "protein": protein,
                "disease": disease,
                "expected_data": ["mutation_frequency"]
            })

        time.sleep(0.35)

    print()
    print("="*70)
    print("SEARCH COMPLETE")
    print("="*70)
    print(f"Total unique PMIDs found: {len(all_pmids)}")
    print()

    # Save results
    results = {
        "pmids": list(all_pmids),
        "metadata": pmid_metadata,
        "search_date": "2026-05-25",
        "total_queries": len(drug_disease_queries) + len(protein_mutation_queries),
        "queries_executed": len(drug_disease_queries) + min(50, len(protein_mutation_queries))
    }

    output_file = "data/pubmed_quantitative_search.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    # Statistics
    print("By search type:")
    type_counts = {}
    for pmid, metadata_list in pmid_metadata.items():
        for meta in metadata_list:
            search_type = meta["type"]
            type_counts[search_type] = type_counts.get(search_type, 0) + 1

    for search_type, count in type_counts.items():
        print(f"  {search_type}: {count} PMIDs")

    print()
    print("Next steps:")
    print("  1. Extract quantitative data from these PMIDs")
    print("  2. Validate extractions against abstracts")
    print("  3. Add to database with provenance")

    conn.close()


if __name__ == "__main__":
    main()
