#!/usr/bin/env python3
import sqlite3
import requests
import time

DB_PATH = "data/drugs/tier1.db"

def search_pubmed(protein, disease):
    """Search PubMed with semantic queries."""
    disease_clean = disease.replace('_', ' ')

    # Try multiple query strategies
    queries = [
        f'("{protein}"[Title/Abstract]) AND ("{disease_clean}"[Title/Abstract]) AND (role OR pathogenesis OR mechanism)',
        f'("{protein}"[Title/Abstract]) AND ("{disease_clean}"[MeSH Terms])',
        f'("{protein}" AND "{disease_clean}" AND therapy)',
    ]

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    for query in queries:
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': 5,
            'retmode': 'json',
            'sort': 'relevance',
            'email': 'research@komposos.org'
        }

        try:
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            if pmids:
                return pmids[:3]  # Top 3
            time.sleep(0.4)
        except:
            continue

    return []

# Connect to database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get druggable proteins (proteins targeted by drugs)
cur.execute("""
    SELECT DISTINCT m.target_name
    FROM morphisms m
    JOIN objects o ON m.source_name = o.name
    WHERE o.type_name = 'Drug'
""")
druggable = {r[0] for r in cur.fetchall()}
print(f"Found {len(druggable)} druggable proteins")

# Get protein->disease edges without PMIDs for druggable proteins
cur.execute("""
    SELECT m.rowid, m.source_name, m.target_name
    FROM morphisms m
    JOIN objects src ON m.source_name = src.name
    JOIN objects tgt ON m.target_name = tgt.name
    WHERE src.type_name = 'Protein'
    AND tgt.type_name = 'Disease'
    AND (m.provenance IS NULL OR m.provenance NOT LIKE '%PMID:%')
""")

edges = []
for rowid, protein, disease in cur.fetchall():
    if protein in druggable:
        edges.append((rowid, protein, disease))

print(f"Found {len(edges)} druggable protein->disease edges without PMIDs")
print(f"Starting semantic search...")

# Search and save candidates
candidates_found = 0
with open('druggable_candidates.txt', 'w') as f:
    for i, (rowid, protein, disease) in enumerate(edges, 1):
        print(f"[{i}/{len(edges)}] {protein} -> {disease}", flush=True)

        pmids = search_pubmed(protein, disease)
        if pmids:
            print(f"  Found {len(pmids)} candidates: {', '.join(pmids)}")
            for pmid in pmids:
                f.write(f"{rowid}|{protein}|{disease}|{pmid}\n")
                candidates_found += 1
        else:
            print(f"  No candidates")

        time.sleep(0.5)  # Rate limit

conn.close()
print(f"\nDone! Found {candidates_found} candidate PMIDs for {len([e for e in edges if search_pubmed(e[1], e[2])])} edges")
print(f"Saved to druggable_candidates.txt")
