#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Injects Gold Standard (Action-Verified) PMIDs into the live database and manifest.
Appends an [ACTION-VERIFIED] tag to the provenance string.
"""

import sqlite3
import json
import os
from pathlib import Path

DB_PATH = "data/drugs/tier1.db"
MANIFEST_PATH = "data/drugs/tier1_manifest.json"
VERIFIED_DATA_PATH = "data/action_verified_provenance.json"

def main():
    print("="*70)
    print("INJECTING GOLD STANDARD PROVENANCE")
    print("="*70)

    if not os.path.exists(VERIFIED_DATA_PATH):
        print(f"Error: Verified data not found at {VERIFIED_DATA_PATH}")
        return

    with open(VERIFIED_DATA_PATH) as f:
        verified_edges = json.load(f)

    print(f"Loaded {len(verified_edges)} verified edges to inject.")

    # 1. Update Database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    db_updated = 0
    for edge in verified_edges:
        src = edge['source']
        tgt = edge['target']
        rel = edge['relation']
        pmid = edge['pmid']

        # Match on relation too: parallel edges between the same node pair can
        # carry different relations, and a proof verifies one specific relation.
        # Matching only (source, target) would stamp it onto all of them.
        cur.execute(
            "SELECT id, provenance FROM morphisms WHERE source_name = ? AND target_name = ? AND name = ?",
            (src, tgt, rel),
        )
        rows = cur.fetchall()
        
        for morph_id, current_prov in rows:
            # We want to replace any existing PMID with the new Gold Standard one, 
            # but keep things like "ChEMBL" or "ABPP" if they exist.
            
            base_prov = current_prov if current_prov and current_prov != "unknown" else ""
            
            # Remove old PMIDs and the verified tag if they exist (to avoid duplicates)
            if base_prov:
                parts = [p.strip() for p in base_prov.split(';')]
                clean_parts = [p for p in parts if not p.startswith('PMID:') and not p.startswith('[ACTION-VERIFIED]')]
                base_prov = "; ".join(clean_parts)
            
            # Construct new provenance
            new_prov = f"PMID:{pmid}; [ACTION-VERIFIED]"
            if base_prov:
                new_prov = f"{base_prov}; {new_prov}"
                
            cur.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (new_prov, morph_id))
            db_updated += 1

    conn.commit()
    conn.close()
    print(f"Updated {db_updated} edges in the live database.")

    # 2. Update Manifest
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
        
    manifest_updated = 0
    for edge in verified_edges:
        src = edge['source']
        tgt = edge['target']
        rel = edge['relation']
        pmid = edge['pmid']

        for m in manifest['morphisms']:
            if m['source'] == src and m['target'] == tgt and m.get('edge_type') == rel:
                base_prov = m.get('provenance', '')
                if base_prov == "unknown":
                    base_prov = ""
                    
                if base_prov:
                    parts = [p.strip() for p in base_prov.split(';')]
                    clean_parts = [p for p in parts if not p.startswith('PMID:') and not p.startswith('[ACTION-VERIFIED]')]
                    base_prov = "; ".join(clean_parts)
                    
                new_prov = f"PMID:{pmid}; [ACTION-VERIFIED]"
                if base_prov:
                    new_prov = f"{base_prov}; {new_prov}"
                    
                m['provenance'] = new_prov
                manifest_updated += 1

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Updated {manifest_updated} edges in the manifest.")
    print("="*70)
    print("INJECTION COMPLETE")

if __name__ == "__main__":
    main()
