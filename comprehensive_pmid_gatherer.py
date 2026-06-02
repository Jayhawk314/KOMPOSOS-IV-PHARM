#!/usr/bin/env python3
"""
comprehensive_pmid_gatherer.py — Gather relevant PMIDs for all edges that currently have them.
Follows the protocol: Audit -> Identify -> Search -> List.
"""

import json
import re
import requests
import time
from typing import List, Tuple

# --- Configuration ---
NCBI_EMAIL = "research@komposos.org"
NCBI_TOOL = "KOMPOSOS-IV-PHARM"
PROVENANCE_PATH = "data/action_verified_provenance.json"
AUDIT_REPORT_PATH = "data/PMID_AUDIT_REPORT.json"
OUTPUT_PATH = "data/GATHERED_PMID_LIST.json"

# High-Signal Scientific Keywords
ACTION_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat", "abrogat", "reduc", "potency", "ic50"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat", "potentiat", "promot", "ec50"],
    'associated_with': ["associat", "linked", "implicat", "correlat", "overexpress", "mutation", "polymorphism"],
    'treats': ["treat", "therap", "clinical trial", "effica", "approv", "indicat", "respon", "survival"],
    'driver_of': ["driver", "drives", "caus", "induc", "promot", "oncogen", "tumorigen"],
    'binds': ["bind", "affinity", "complex", "engage", "dock", "partner", "interact", "kd", "ki"],
    'interacts': ["interact", "bind", "complex", "partner", "physical"],
    'phosphorylates': ["phosphorylat", "kinase"],
}

# --- PubMed Tools ---

def search_pubmed(protein: str, disease: str, relation: str, max_results=5) -> List[str]:
    """Search for PMIDs that discuss the relationship."""
    rel_keywords = ACTION_KEYWORDS.get(relation, ["associated"])
    query = f'("{protein}"[Title/Abstract]) AND ("{disease.replace("_", " ")}"[Title/Abstract])'
    # Add first keyword to refine search
    if rel_keywords:
        query += f' AND "{rel_keywords[0]}"'
        
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
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'tool': NCBI_TOOL,
        'email': NCBI_EMAIL
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        sections = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', resp.text, re.DOTALL)
        return " ".join([re.sub(r'<[^>]+>', '', s) for s in sections])
    except:
        return ""

def _term_present(term: str, sentence: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE) is not None

def verify_abstract(abstract: str, src: str, tgt: str, rel: str) -> Tuple[str, bool]:
    """Check if any sentence in the abstract supports the relation."""
    s_name = src.replace("_", " ")
    t_name = tgt.replace("_", " ")
    keywords = ACTION_KEYWORDS.get(rel, [])
    
    sentences = re.split(r'(?<=[.!?])\s+', abstract)
    for sent in sentences:
        sent_lower = sent.lower()
        if _term_present(s_name, sent) and _term_present(t_name, sent):
            # Check for at least one keyword
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw), sent_lower):
                    return sent.strip(), True
    return "", False

# --- Main Logic ---

def main():
    print("="*80)
    print("COMPREHENSIVE PMID GATHERER: BUILDING THE VERIFIED LIST")
    print("="*80)

    try:
        with open(PROVENANCE_PATH) as f:
            provenance = json.load(f)
        with open(AUDIT_REPORT_PATH) as f:
            audit = json.load(f)
    except FileNotFoundError:
        print("Required audit/provenance files not found. Please run the audit scripts first.")
        return

    # Map audit results for quick lookup
    audit_map = {item['edge_id']: item for item in audit['detailed']}
    
    gathered_list = []
    
    # Process all edges in the provenance set.
    print(f"Processing all {len(provenance)} edges from the provenance set...")

    for i, entry in enumerate(provenance):
        edge_id = entry.get('edge_id', f"{entry['relation']}:{entry['source']}->{entry['target']}")
        audit_res = audit_map.get(edge_id, {"verdict": "UNKNOWN"})
        
        source = entry['source']
        target = entry['target']
        relation = entry['relation']
        current_pmid = entry['pmid']
        
        result = {
            "edge_id": edge_id,
            "source": source,
            "relation": relation,
            "target": target,
            "original_pmid": current_pmid,
            "gathered_pmid": current_pmid,
            "status": "KEEP",
            "proof_sentence": entry.get('proof_sentence', "")
        }

        if audit_res['verdict'] == "AGREE":
            print(f"[{i+1}/{len(provenance)}] KEEP: {edge_id}")
            result["status"] = "VERIFIED"
        else:
            print(f"[{i+1}/{len(provenance)}] FIXING: {edge_id} (Reason: {audit_res.get('reason', 'Unknown')})")
            
            # Attempt to find a better PMID
            new_pmids = search_pubmed(source, target, relation)
            time.sleep(0.35) # Rate limit
            
            found_fix = False
            for pmid in new_pmids:
                if pmid == current_pmid: continue # Already checked
                
                abstract = fetch_abstract(pmid)
                time.sleep(0.35)
                
                new_sentence, ok = verify_abstract(abstract, source, target, relation)
                if ok:
                    result["gathered_pmid"] = pmid
                    result["status"] = "PROPOSED_FIX"
                    result["proof_sentence"] = new_sentence
                    print(f"      FOUND replacement PMID:{pmid}")
                    found_fix = True
                    break
            
            if not found_fix:
                print(f"      NO grounded replacement found.")
                result["status"] = "NOT_FOUND"

        gathered_list.append(result)

    # Save the final list
    with open(OUTPUT_PATH, "w") as f:
        json.dump(gathered_list, f, indent=2)

    print("\n" + "="*80)
    print(f"GATHERING COMPLETE. Results saved to {OUTPUT_PATH}")
    
    # Final Tally
    stats = {"VERIFIED": 0, "PROPOSED_FIX": 0, "NOT_FOUND": 0}
    for r in gathered_list:
        stats[r['status']] += 1
    
    print(f"Summary:")
    print(f"  Verified (Kept):   {stats['VERIFIED']}")
    print(f"  Proposed Fixes:    {stats['PROPOSED_FIX']}")
    print(f"  Still Unverified:  {stats['NOT_FOUND']}")
    print("="*80)

if __name__ == "__main__":
    main()
