#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Scrape PubMed PMIDs using (Object A + Relation + Object B) triplets.
This implements the "fitted" search idea to find higher-precision provenance.
"""

import requests
import time
import sqlite3
import json
import re
from typing import List, Dict, Tuple
from pathlib import Path

DB_PATH = "data/drugs/tier1.db"
PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Mapping categorical relations to literature synonyms
RELATION_SYNONYMS = {
    'inhibits': ["inhibits", "inhibitor", "antagonist", "blocker", "suppression", "downregulates"],
    'indirect_inhibitor': ["inhibits", "inhibitor", "suppression"],
    'activates': ["activates", "activator", "agonist", "promoter", "induction", "upregulates"],
    'activator': ["activates", "activator", "agonist"],
    'enhances': ["enhances", "promotes", "activates"],
    'associated_with': ["associated", "linked", "implicated", "correlation"],
    'driver_of': ["driver", "causes", "induces", "promotes"],
    'targets': ["targets", "binding", "inhibits"],
    'phosphorylates': ["phosphorylates", "phosphorylation"],
    'ubiquitinates': ["ubiquitinates", "ubiquitination"],
    'binds': ["binds", "binding", "affinity", "complex"],
    'regulated_by': ["regulated by", "controlled by"],
    'regulates': ["regulates", "controls", "modulates"],
    'modulates': ["modulates", "modulation", "affects"],
    'synergizes_with': ["synergizes", "synergy", "potentiation", "combination"],
    'cooperates': ["cooperates", "cooperation", "interaction"],
    'synthetic_lethal': ["synthetic lethal", "synthetic lethality"],
    'treats': ["treats", "treatment", "therapy", "clinical trial"]
}

def search_pubmed(query: str, max_results: int = 10) -> List[str]:
    """Search PubMed and return list of PMIDs."""
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
    except Exception as e:
        print(f"  [ERROR] Search failed: {e}")
    return []

def main():
    print("="*70)
    print("TRIPLET-BASED PUBMED SCRAPER (A + RELATION + B)")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Process ALL morphisms
    cur.execute("""
        SELECT source_name, target_name, name, id 
        FROM morphisms 
    """)
    edges = cur.fetchall()
    
    results = []
    found_total = 0
    output_path = "data/full_triplet_candidate_pool.json"
    partial_path = "data/full_triplet_candidate_pool_PARTIAL.json"
    
    print(f"Starting full triplet search for {len(edges)} edges...")
    print(f"Estimated time: {int(len(edges) * 0.4 / 60)} minutes")
    
    for i, (src, tgt, rel, mid) in enumerate(edges):
        if i > 0 and i % 50 == 0:
            print(f"  [PROGRESS] Processed {i}/{len(edges)} edges. Found {found_total} PMIDs so far.")
            # Periodic save in case of interruption
            with open(partial_path, 'w') as f:
                json.dump(results, f, indent=2)
                
        synonyms = RELATION_SYNONYMS.get(rel, [rel])
        syn_query = " OR ".join([f"{s}[Title/Abstract]" for s in synonyms])
        
        # Clean names for query
        src_q = src.replace("_", " ")
        tgt_q = tgt.replace("_", " ")
        
        query = f'({src_q}[Title/Abstract]) AND ({tgt_q}[Title/Abstract]) AND ({syn_query})'
        
        # print(f"[{i+1}/{len(edges)}] Searching: {src} -{rel}-> {tgt}")
        pmids = search_pubmed(query)
        
        if pmids:
            # print(f"  [+] Found {len(pmids)} PMIDs")
            found_total += len(pmids)
            results.append({
                "edge_id": mid,
                "source": src,
                "target": tgt,
                "relation": rel,
                "query": query,
                "pmids": pmids
            })
            
        time.sleep(0.35) # Rate limiting
    
    # Final save
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "="*70)
    print("SCRAPE COMPLETE")
    print(f"Total edges with new PMIDs found: {len(results)}")
    print(f"Total PMIDs collected: {found_total}")
    print(f"Results saved to: {output_path}")
    print("="*70)
    
    conn.close()

if __name__ == "__main__":
    main()
