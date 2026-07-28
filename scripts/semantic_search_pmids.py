#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Semantic PMID search using Claude API for better queries.

For edges that still don't have PMIDs, use Claude to generate better search
queries (with synonyms, alternative names, etc.) and find relevant papers.
"""
import sqlite3
import os
import requests
import time

DB_PATH = "data/drugs/tier1.db"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NCBI_EMAIL = "research@komposos.org"

if not ANTHROPIC_API_KEY:
    print("ERROR: Set ANTHROPIC_API_KEY environment variable")
    exit(1)

def get_search_strategies(protein, disease):
    """Use Claude to generate better search queries."""
    disease_clean = disease.replace('_', ' ')

    prompt = f"""I'm searching PubMed for papers about {protein} and {disease_clean}.

Generate 3 different search strategies to find papers that discuss {protein}'s role in {disease_clean}:

1. Include common aliases/synonyms for {protein}
2. Include alternative names for {disease_clean}
3. Suggest specific biological mechanisms or pathways to search for

Format your response as JSON with this structure:
{{
  "queries": [
    "search query 1",
    "search query 2",
    "search query 3"
  ],
  "protein_aliases": ["alias1", "alias2"],
  "disease_aliases": ["alias1", "alias2"]
}}

Keep queries concise and PubMed-compatible."""

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        import json
        result = json.loads(data['content'][0]['text'])
        return result.get('queries', [])
    except Exception as e:
        print(f"  Error generating strategies: {e}")
        # Fallback to simple query
        return [f'("{protein}"[Title/Abstract]) AND ("{disease_clean}"[Title/Abstract])']

def search_pubmed(query, max_results=5):
    """Search PubMed with given query."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
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
        return data.get('esearchresult', {}).get('idlist', [])
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
        xml = resp.text
        if '<AbstractText>' in xml:
            start = xml.find('<AbstractText>')
            end = xml.find('</AbstractText>', start)
            if start != -1 and end != -1:
                abstract = xml[start+14:end]
                abstract = abstract.replace('<i>', '').replace('</i>', '')
                abstract = abstract.replace('<b>', '').replace('</b>', '')
                return abstract
        return ""
    except Exception as e:
        return ""

def semantic_verify(protein, disease, abstract):
    """Use Claude to verify the PMID is relevant."""
    disease_clean = disease.replace('_', ' ')

    prompt = f"""Does this abstract discuss {protein} in relation to {disease_clean}?

Answer ONLY "YES" if it discusses their relationship, or "NO" if not.

Abstract:
{abstract}

Answer:"""

    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        answer = data['content'][0]['text'].strip().upper()
        return 'YES' in answer
    except Exception:
        return False

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get edges without PMIDs
    cur.execute("""
        SELECT rowid, source_name, target_name
        FROM morphisms
        WHERE provenance IN ('literature (unverified)', 'PubMed co-mention (unverified)')
        AND source_name IN (
            SELECT DISTINCT m.target_name
            FROM morphisms m
            JOIN objects o ON m.source_name = o.name AND o.type_name = 'Drug'
        )
    """)

    # Also check target is a disease
    edges = []
    for rowid, src, tgt in cur.fetchall():
        cur.execute("SELECT type_name FROM objects WHERE name = ?", (tgt,))
        tgt_type = cur.fetchone()
        if tgt_type and tgt_type[0] == 'Disease':
            edges.append((rowid, src, tgt))

    print(f"Semantic search for {len(edges)} edges without PMIDs...")

    found = 0

    for i, (rowid, protein, disease) in enumerate(edges, 1):
        print(f"\n[{i}/{len(edges)}] {protein} -> {disease}")

        # Get search strategies from Claude
        queries = get_search_strategies(protein, disease)
        print(f"  Generated {len(queries)} search strategies")

        verified_pmid = None

        for query in queries:
            pmids = search_pubmed(query, max_results=3)
            if not pmids:
                continue

            for pmid in pmids:
                abstract = fetch_abstract(pmid)
                if not abstract:
                    continue

                if semantic_verify(protein, disease, abstract):
                    print(f"  FOUND: PMID:{pmid}")
                    verified_pmid = pmid
                    break

                time.sleep(0.5)

            if verified_pmid:
                break

            time.sleep(0.5)

        if verified_pmid:
            cur.execute("UPDATE morphisms SET provenance = ? WHERE rowid = ?",
                       (f"PMID:{verified_pmid}", rowid))
            conn.commit()
            found += 1
        else:
            print("  No verified PMID found")

        time.sleep(1)  # Rate limit

    conn.close()
    print(f"\n\nDone. Found PMIDs for {found}/{len(edges)} edges")

if __name__ == '__main__':
    main()
