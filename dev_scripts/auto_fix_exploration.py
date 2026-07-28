#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
auto_fix_exploration.py — Attempt to find better proof sentences in full abstracts for HOLLOW claims.
"""

import json
import re
import requests
from typing import List, Tuple
from komposos_kg import Edge, KGMemory

# --- Stricter Verification Logic (Shared with audit) ---

ACTION_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat", "abrogat", "reduc"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat", "potentiat", "promot"],
    'associated_with': ["associat", "linked", "implicat", "correlat", "overexpress"],
    'treats': ["treat", "therap", "clinical trial", "effica", "approv", "indicat"],
}

def _term_present(term: str, sentence: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE) is not None

def fetch_abstract(pmid: str) -> str:
    """Fetch full abstract text from NCBI."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'tool': 'KOMPOSOS-IV-PHARM'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            content = response.text
            sections = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', content, re.DOTALL)
            cleaned = [re.sub(r'<[^>]+>', '', sec) for sec in sections]
            return " ".join(cleaned)
    except:
        pass
    return ""

def find_better_sentence(abstract: str, src: str, tgt: str, rel: str) -> Tuple[str, str]:
    """Search for a sentence in the abstract that satisfies the relation."""
    s_name = src.replace("_", " ")
    t_name = tgt.replace("_", " ")
    keywords = ACTION_KEYWORDS.get(rel, [])
    
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    for sent in sentences:
        sent_lower = sent.lower()
        if _term_present(s_name, sent) and _term_present(t_name, sent):
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw), sent_lower):
                    return sent.strip(), "AGREE"
    return "", "HOLLOW"

def main():
    print("="*80)
    print("AUTO-FIX EXPLORATION: RE-SCANNING FULL ABSTRACTS")
    print("="*80)

    try:
        with open("data/explored_fix_candidates.json") as f:
            candidates = json.load(f)
    except:
        print("Candidates file not found.")
        return

    # Select a small batch
    batch = candidates[:5]
    
    for c in batch:
        print(f"\nAUDITING: {c['edge_id']} (PMID:{c['pmid']})")
        print(f"  Current Reason: {c['reason']}")
        
        print("  Fetching full abstract...", end='', flush=True)
        abstract = fetch_abstract(c['pmid'])
        if not abstract:
            print(" FAILED.")
            continue
        print(" DONE.")
        
        print("  Scanning for better proof sentence...", end='', flush=True)
        new_sentence, verdict = find_better_sentence(abstract, c['source'], c['target'], c['relation'])
        
        if verdict == "AGREE":
            print(" SUCCESS!")
            print(f"  NEW PROOF: \"{new_sentence[:120]}...\"")
        else:
            print(" FAILED (Abstract does not assert relation).")
            print("  ACTION: Mark for replacement via new PubMed search.")

    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
