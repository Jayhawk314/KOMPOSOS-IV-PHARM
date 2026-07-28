#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Semantic verification of PMIDs using Claude API.

For each PMID added by keyword search, use Claude to verify the abstract
actually discusses the protein-disease relationship (not just co-mentions both).
"""
import sqlite3
import os
import requests
import time

DB_PATH = "data/drugs/tier1.db"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("ERROR: Set ANTHROPIC_API_KEY environment variable")
    print("Get your key from: https://console.anthropic.com/settings/keys")
    exit(1)

def fetch_abstract(pmid):
    """Fetch abstract for a PMID."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    fetch_url = f"{base_url}efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'email': 'research@komposos.org'
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
        print(f"  Fetch failed for PMID:{pmid}: {e}")
        return ""

def semantic_verify(protein, disease, abstract):
    """Use Claude API to verify the relationship is actually discussed."""
    disease_clean = disease.replace('_', ' ')

    prompt = f"""Does this abstract discuss {protein} in relation to {disease_clean}?

I need you to verify if this paper actually discusses the relationship between {protein} and {disease_clean}, not just mentions both terms separately.

Abstract:
{abstract}

Answer with ONLY "YES" if the abstract discusses how {protein} is involved in, related to, or plays a role in {disease_clean}.
Answer with ONLY "NO" if the abstract merely mentions both terms without connecting them, or if one/both are not actually discussed.

Answer (YES or NO):"""

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
    except Exception as e:
        print(f"  API error: {e}")
        return False  # Conservative: if we can't verify, mark as unverified

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get all edges with PMIDs added by keyword search (conf < 0.90)
    cur.execute("""
        SELECT rowid, source_name, target_name, provenance, confidence
        FROM morphisms
        WHERE provenance LIKE 'PMID:%' AND confidence < 0.90
    """)
    edges = cur.fetchall()

    print(f"Semantically verifying {len(edges)} PMIDs...")

    verified = 0
    removed = 0

    for i, (rowid, protein, disease, prov, conf) in enumerate(edges, 1):
        pmid = prov.replace('PMID:', '').strip()
        print(f"\n[{i}/{len(edges)}] {protein} -> {disease} (PMID:{pmid})")

        # Fetch abstract
        abstract = fetch_abstract(pmid)
        if not abstract:
            print("  No abstract - removing")
            cur.execute("UPDATE morphisms SET provenance = 'literature (unverified)' WHERE rowid = ?", (rowid,))
            removed += 1
            time.sleep(0.35)
            continue

        # Semantic verification with Claude
        is_valid = semantic_verify(protein, disease, abstract)

        if is_valid:
            print("  VERIFIED - relationship discussed")
            verified += 1
        else:
            print("  REMOVED - only co-mention, no relationship")
            cur.execute("UPDATE morphisms SET provenance = 'literature (unverified)' WHERE rowid = ?", (rowid,))
            removed += 1

        conn.commit()
        time.sleep(0.5)  # Rate limit for both PubMed and Claude API

    conn.close()
    print(f"\n\nDone.")
    print(f"  Verified: {verified}")
    print(f"  Removed: {removed}")
    print(f"  Total checked: {len(edges)}")

if __name__ == '__main__':
    main()
