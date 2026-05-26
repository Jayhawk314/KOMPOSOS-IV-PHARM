#!/usr/bin/env python3
import sqlite3
import requests
import time

DB_PATH = "data/drugs/tier1.db"

def search_pubmed(protein, disease):
    """Search PubMed with better query."""
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

# Main
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get druggable protein->disease edges without PMIDs
cur.execute("""
    SELECT DISTINCT m.target_name FROM morphisms m
    JOIN objects o ON m.source_name = o.name AND o.type_name = 'Drug'
""")
drugged = {r[0] for r in cur.fetchall()}

cur.execute("""
    SELECT rowid, source_name, target_name FROM morphisms
    WHERE provenance IN ('literature (unverified)', 'PubMed co-mention (unverified)')
""")

edges = []
for rowid, src, tgt in cur.fetchall():
    if src in drugged:
        cur.execute('SELECT type_name FROM objects WHERE name = ?', (tgt,))
        t = cur.fetchone()
        if t and t[0] == 'Disease':
            edges.append((rowid, src, tgt))

print(f"Searching for {len(edges)} edges...")

# Output candidate PMIDs for manual verification
with open('candidate_pmids.txt', 'w') as f:
    for i, (rowid, protein, disease) in enumerate(edges, 1):
        print(f"[{i}/{len(edges)}] {protein} -> {disease}")
        pmids = search_pubmed(protein, disease)
        if pmids:
            print(f"  Found {len(pmids)} candidates: {', '.join(pmids)}")
            for pmid in pmids:
                f.write(f"{rowid}|{protein}|{disease}|{pmid}\n")
        else:
            print(f"  No candidates")
        time.sleep(0.5)

conn.close()
print(f"\nWrote candidates to candidate_pmids.txt for verification")
