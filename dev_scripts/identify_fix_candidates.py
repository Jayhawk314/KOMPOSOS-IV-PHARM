#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
identify_fix_candidates.py — Identifies HOLLOW claims and prepares them for fixing.
"""

import json

def main():
    try:
        with open("data/PMID_AUDIT_REPORT.json") as f:
            audit = json.load(f)
        with open("data/action_verified_provenance.json") as f:
            provenance = json.load(f)
    except FileNotFoundError:
        print("Required data files not found.")
        return

    # Map provenance by edge_id for easy lookup
    prov_map = {p.get('edge_id', f"{p['relation']}:{p['source']}->{p['target']}"): p for p in provenance}
    
    # Filter for HOLLOW and REJECT
    fix_candidates = []
    for item in audit['detailed']:
        if item['verdict'] in ['HOLLOW', 'REJECT']:
            edge_id = item['edge_id']
            if edge_id in prov_map:
                entry = prov_map[edge_id]
                fix_candidates.append({
                    "edge_id": edge_id,
                    "source": entry['source'],
                    "target": entry['target'],
                    "relation": entry['relation'],
                    "pmid": entry['pmid'],
                    "reason": item['reason'],
                    "verdict": item['verdict'],
                    "proof_sentence": entry['proof_sentence']
                })

    print(f"Identified {len(fix_candidates)} candidates for replacement/verification.")
    
    # Save as a side project file
    with open("data/explored_fix_candidates.json", "w") as f:
        json.dump(fix_candidates, f, indent=2)
    
    print("Saved candidates to data/explored_fix_candidates.json")

    # Sample a few to show
    print("\nTop 5 Candidates for Fixing:")
    for c in fix_candidates[:5]:
        print(f"- {c['edge_id']} (PMID:{c['pmid']})")
        print(f"  Reason: {c['reason']}")

if __name__ == "__main__":
    main()
