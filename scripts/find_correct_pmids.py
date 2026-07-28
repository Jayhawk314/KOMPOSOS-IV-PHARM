#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Find correct PMIDs for protein-disease edges.

For each protein-disease edge that sits in a drug->protein->disease path,
search PubMed for papers that actually discuss that relationship and verify
them by checking the abstract.
"""
import sqlite3
import time
import requests
from collections import defaultdict

DB_PATH = "data/drugs/tier1.db"
NCBI_EMAIL = "research@komposos.org"  # Required by NCBI API policy

def get_actionable_edges(conn):
    """Get protein->disease edges in drug paths that need PMIDs."""
    cur = conn.cursor()

    # Find proteins with drug connections
    cur.execute("""
        SELECT DISTINCT m1.target_name
        FROM morphisms m1
        JOIN objects o1 ON m1.source_name = o1.name AND o1.type_name = 'Drug'
    """)
    drugged_proteins = {row[0] for row in cur.fetchall()}

    # Find protein->disease edges without verified PMIDs
    cur.execute("""
        SELECT rowid, source_name, target_name, name, confidence, provenance
        FROM morphisms
        WHERE provenance IN ('literature (unverified)', 'PubMed co-mention (unverified)')
    """)

    actionable = []
    for rowid, src, tgt, rel, conf, prov in cur.fetchall():
        # Check if source is a druggable protein
        if src in drugged_proteins:
            # Check if target is a disease
            cur.execute("SELECT type_name FROM objects WHERE name = ?", (tgt,))
            tgt_type = cur.fetchone()
            if tgt_type and tgt_type[0] == 'Disease':
                actionable.append((rowid, src, tgt, rel, conf))

    return actionable

def search_pubmed(protein, disease, max_results=5):
    """Search PubMed for papers about this protein-disease relationship."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Build search query
    query = f'("{protein}"[Title/Abstract]) AND ("{disease.replace("_", " ")}"[Title/Abstract])'

    # Search
    search_url = f"{base_url}esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance',
        'email': NCBI_EMAIL
    }

    try:
        resp = requests.get(search_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])
        return pmids
    except Exception as e:
        print(f"  Search failed: {e}")
        return []

def fetch_abstract(pmid):
    """Fetch abstract for a PMID."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    fetch_url = f"{base_url}efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'email': NCBI_EMAIL
    }

    try:
        resp = requests.get(fetch_url, params=params, timeout=10)
        resp.raise_for_status()
        # Extract abstract text from XML (simple extraction)
        xml = resp.text
        if '<AbstractText>' in xml:
            start = xml.find('<AbstractText>')
            end = xml.find('</AbstractText>', start)
            if start != -1 and end != -1:
                abstract = xml[start+14:end]
                # Remove XML tags
                abstract = abstract.replace('<i>', '').replace('</i>', '')
                abstract = abstract.replace('<b>', '').replace('</b>', '')
                return abstract
        return ""
    except Exception as e:
        print(f"  Fetch failed for PMID:{pmid}: {e}")
        return ""

def verify_pmid(pmid, protein, disease):
    """Check if this PMID actually discusses the protein-disease relationship."""
    abstract = fetch_abstract(pmid)
    if not abstract:
        return False

    # Simple verification: both protein and disease mentioned in abstract
    disease_clean = disease.replace('_', ' ').lower()
    abstract_lower = abstract.lower()

    if protein.lower() in abstract_lower and disease_clean in abstract_lower:
        return True

    # Try common aliases
    aliases = {
        'NSCLC': ['non-small cell lung cancer', 'lung adenocarcinoma'],
        'RCC': ['renal cell carcinoma', 'kidney cancer'],
        'HCC': ['hepatocellular carcinoma', 'liver cancer'],
        'CML': ['chronic myeloid leukemia', 'chronic myelogenous leukemia'],
        'AML': ['acute myeloid leukemia', 'acute myelogenous leukemia'],
        'CLL': ['chronic lymphocytic leukemia'],
        'GIST': ['gastrointestinal stromal tumor'],
    }

    disease_variants = aliases.get(disease, [disease_clean])
    for variant in disease_variants:
        if variant in abstract_lower:
            return True

    return False

def main():
    conn = sqlite3.connect(DB_PATH)

    print("Finding actionable protein->disease edges...")
    edges = get_actionable_edges(conn)
    print(f"Found {len(edges)} edges to verify")

    fixed = 0
    for i, (rowid, protein, disease, rel, conf) in enumerate(edges, 1):
        print(f"\n[{i}/{len(edges)}] {protein} -> {disease}")

        # Search PubMed
        pmids = search_pubmed(protein, disease, max_results=3)
        if not pmids:
            print("  No papers found")
            time.sleep(0.35)  # Rate limit: 3 req/sec
            continue

        print(f"  Found {len(pmids)} candidate papers")

        # Verify each PMID
        verified_pmid = None
        for pmid in pmids:
            print(f"  Checking PMID:{pmid}...", end='')
            if verify_pmid(pmid, protein, disease):
                print(" VERIFIED")
                verified_pmid = pmid
                break
            else:
                print(" not relevant")
            time.sleep(0.35)

        if verified_pmid:
            # Update DB
            new_prov = f"PMID:{verified_pmid}"
            cur = conn.cursor()
            cur.execute("UPDATE morphisms SET provenance = ? WHERE rowid = ?", (new_prov, rowid))
            conn.commit()
            fixed += 1
            print(f"  ADDED PMID:{verified_pmid}")
        else:
            print("  No verified PMID found")

        time.sleep(0.35)  # Rate limit

    conn.close()
    print(f"\n\nDone. Fixed {fixed}/{len(edges)} edges with verified PMIDs")

if __name__ == '__main__':
    main()
