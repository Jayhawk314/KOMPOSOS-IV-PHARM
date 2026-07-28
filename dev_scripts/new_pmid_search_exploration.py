#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
new_pmid_search_exploration.py — Search for a replacement PMID for a known HOLLOW edge.
"""

import requests
import time
import re
from typing import List

# --- Search and Verify Logic ---

def search_pubmed(protein, disease, max_results=3):
    query = f'("{protein}"[Title/Abstract]) AND ("{disease.replace("_", " ")}"[Title/Abstract]) AND "associated"'
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance'
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp.json().get('esearchresult', {}).get('idlist', [])
    except:
        return []

def fetch_abstract(pmid: str) -> str:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {'db': 'pubmed', 'id': pmid, 'retmode': 'xml'}
    try:
        resp = requests.get(url, params=params, timeout=10)
        sections = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', resp.text, re.DOTALL)
        return " ".join([re.sub(r'<[^>]+>', '', s) for s in sections])
    except:
        return ""

def main():
    print("="*80)
    print("NEW PMID SEARCH EXPLORATION: BRCA2 -> Pancreatic_Cancer")
    print("="*80)

    protein = "BRCA2"
    disease = "Pancreatic_Cancer"
    
    print(f"Searching for grounded papers for {protein} and {disease}...")
    new_pmids = search_pubmed(protein, disease)
    
    if not new_pmids:
        print("No new candidates found.")
        return

    print(f"Found {len(new_pmids)} potential replacements. Verifying...\n")
    
    for pmid in new_pmids:
        print(f"Checking PMID:{pmid}...")
        abstract = fetch_abstract(pmid)
        if not abstract:
            print("  Failed to fetch abstract.")
            continue
            
        # Look for a sentence that asserts the relation
        sentences = re.split(r'(?<=[.!?])\s+', abstract)
        found = False
        for sent in sentences:
            sent_lower = sent.lower()
            if protein.lower() in sent_lower and disease.replace("_", " ").lower() in sent_lower:
                if "associated" in sent_lower or "linked" in sent_lower or "mutation" in sent_lower:
                    print(f"  [SUCCESS] Found grounded sentence!")
                    print(f"  PROOF: \"{sent.strip()[:150]}...\"")
                    found = True
                    break
        
        if found:
            print(f"\nPROPOSED FIX: Replace inaccurate PMID:41899580 with verified PMID:{pmid}")
            break
        else:
            print("  No grounded sentence found in this abstract.")

    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
