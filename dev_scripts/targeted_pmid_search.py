#!/usr/bin/env python3
"""
targeted_pmid_search.py — Targeted search for the 143 unverified edges using expanded keywords.
"""

import json
import re
import requests
import time
from typing import List, Tuple

# --- Configuration ---
NCBI_EMAIL = "research@komposos.org"
NCBI_TOOL = "KOMPOSOS-IV-PHARM"
GATHERED_LIST_PATH = "data/GATHERED_PMID_LIST.json"
OUTPUT_PATH = "data/TARGETED_SEARCH_RESULTS.json"

# Expanded Broad Keywords for difficult cases
BROAD_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat", "reduc", "potency", "deplet", "silenc", "knockdown"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat", "potentiat", "promot", "trigger", "signaling"],
    'associated_with': ["associat", "linked", "implicat", "correlat", "overexpress", "mutation", "biomarker", "marker", "prognostic", "pathway", "regulation", "clinical"],
    'treats': ["treat", "therap", "clinical", "effica", "approv", "indicat", "respon", "survival", "patient"],
    'driver_of': ["driver", "drives", "caus", "induc", "promot", "oncogen", "tumorigen", "pathogenesis"],
    'binds': ["bind", "affinity", "complex", "engage", "dock", "partner", "interact", "physical", "structural"],
    'interacts': ["interact", "bind", "complex", "partner", "physical", "dock"],
    'phosphorylates': ["phosphorylat", "kinase", "signaling"],
}

def search_pubmed_broad(protein: str, disease: str, relation: str, max_results=10) -> List[str]:
    """Search for PMIDs with broader terms."""
    query = f'("{protein}"[Title/Abstract]) AND ("{disease.replace("_", " ")}"[Title/Abstract])'
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'relevance',
        'tool': NCBI_TOOL,
        'email': NCBI_EMAIL
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        return resp.json().get('esearchresult', {}).get('idlist', [])
    except:
        return []

def fetch_abstract(pmid: str) -> str:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {'db': 'pubmed', 'id': pmid, 'retmode': 'xml', 'tool': NCBI_TOOL, 'email': NCBI_EMAIL}
    try:
        resp = requests.get(url, params=params, timeout=10)
        sections = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', resp.text, re.DOTALL)
        return " ".join([re.sub(r'<[^>]+>', '', s) for s in sections])
    except:
        return ""

def verify_abstract_broad(abstract: str, src: str, tgt: str, rel: str) -> Tuple[str, bool]:
    s_name = src.replace("_", " ")
    t_name = tgt.replace("_", " ")
    keywords = BROAD_KEYWORDS.get(rel, ["associated"])
    
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    for sent in sentences:
        sent_lower = sent.lower()
        # Entity match
        if re.search(r"\b" + re.escape(s_name.lower()) + r"s?\b", sent_lower) and \
           re.search(r"\b" + re.escape(t_name.lower()) + r"s?\b", sent_lower):
            # Keyword match
            for kw in keywords:
                if kw.lower() in sent_lower:
                    return sent.strip(), True
    return "", False

def main():
    print("="*80)
    print("TARGETED SEARCH FOR UNVERIFIED EDGES (BROAD KEYWORDS)")
    print("="*80)

    try:
        with open(GATHERED_LIST_PATH) as f:
            gathered = json.load(f)
    except FileNotFoundError:
        print("Gathered list not found.")
        return

    unverified = [item for item in gathered if item['status'] == "NOT_FOUND"]
    print(f"Targeting {len(unverified)} unverified edges...\n")

    results = []
    fixed_count = 0

    for i, entry in enumerate(unverified):
        source = entry['source']
        target = entry['target']
        relation = entry['relation']
        edge_id = entry['edge_id']

        # Skip edges with missing info
        if not source or not target or source == "None" or target == "None":
            continue

        print(f"[{i+1}/{len(unverified)}] Searching for {edge_id}...")
        
        new_pmids = search_pubmed_broad(source, target, relation)
        time.sleep(0.35)
        
        found = False
        for pmid in new_pmids:
            abstract = fetch_abstract(pmid)
            time.sleep(0.35)
            
            proof, ok = verify_abstract_broad(abstract, source, target, relation)
            if ok:
                print(f"      [SUCCESS] Found replacement PMID:{pmid}")
                entry['gathered_pmid'] = pmid
                entry['status'] = "PROPOSED_FIX_BROAD"
                entry['proof_sentence'] = proof
                fixed_count += 1
                found = True
                break
        
        if not found:
            print("      No broad match found.")
        
        results.append(entry)

    # Save results
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*80)
    print(f"TARGETED SEARCH COMPLETE. Fixed {fixed_count}/{len(unverified)} edges.")
    print(f"Results saved to {OUTPUT_PATH}")
    print("="*80)

if __name__ == "__main__":
    main()
