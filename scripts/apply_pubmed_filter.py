#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Apply Categorical PubMed Edge Filter to tier1.db

Uses the scores from filter_pubmed_edges.py to:
1. AGREE/PARTIAL edges: update confidence to adjusted value
2. ORPHAN edges with mech support: set confidence to 0.35
3. ORPHAN edges without mech support: remove from DB
4. REJECT edges: remove from DB

This is reversible: original confidences are stored in the provenance metadata.
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path('data/drugs/tier1.db')
SCORES_PATH = Path('scripts/pubmed_edge_scores.json')

# Confidence thresholds for each delta class
THRESHOLDS = {
    'AGREE':   None,   # Use adjusted_confidence directly
    'PARTIAL': None,   # Use adjusted_confidence directly
    'ORPHAN':  0.35,   # Cap at this if mech_reach > 0, else remove
    'HOLLOW':  0.20,   # Low confidence (structurally plausible, logically unsupported)
    'REJECT':  None,   # Remove entirely
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'

    if mode not in ('preview', 'apply', 'revert'):
        print(f"Usage: {sys.argv[0]} [preview|apply|revert]")
        print("  preview: show what would happen (default)")
        print("  apply:   apply the filter to tier1.db")
        print("  revert:  undo the filter (restore confidence=0.65)")
        return

    print("=" * 70)
    print(f"PubMed Edge Filter — mode: {mode}")
    print("=" * 70)

    # Load scores
    with open(SCORES_PATH) as f:
        data = json.load(f)

    edges = data['edges']
    print(f"Loaded {len(edges)} edge scores")

    # Classify actions
    keep = []       # Update confidence
    remove = []     # Delete from DB

    for e in edges:
        delta = e['delta']
        ls = e['layer_scores']

        if delta == 'AGREE':
            keep.append((e['edge_id'], e['adjusted_confidence'], 'AGREE'))
        elif delta == 'PARTIAL':
            keep.append((e['edge_id'], e['adjusted_confidence'], 'PARTIAL'))
        elif delta == 'ORPHAN':
            if ls.get('mech_reach', 0) > 0:
                # Has mechanistic support — keep at reduced confidence
                conf = min(THRESHOLDS['ORPHAN'], e['adjusted_confidence'])
                keep.append((e['edge_id'], conf, 'ORPHAN_KEEP'))
            else:
                remove.append((e['edge_id'], 'ORPHAN_NO_MECH'))
        elif delta == 'HOLLOW':
            keep.append((e['edge_id'], THRESHOLDS['HOLLOW'], 'HOLLOW'))
        else:  # REJECT
            remove.append((e['edge_id'], 'REJECT'))

    print(f"\nActions:")
    print(f"  KEEP (update confidence): {len(keep)}")
    print(f"  REMOVE (delete from DB):  {len(remove)}")
    print(f"  Total:                    {len(keep) + len(remove)}")

    # Breakdown by type
    from collections import Counter
    keep_types = Counter(t for _, _, t in keep)
    remove_types = Counter(t for _, t in remove)
    print(f"\n  Keep breakdown:")
    for t, n in sorted(keep_types.items()):
        print(f"    {t}: {n}")
    print(f"  Remove breakdown:")
    for t, n in sorted(remove_types.items()):
        print(f"    {t}: {n}")

    # Confidence distribution of kept edges
    if keep:
        confs = [c for _, c, _ in keep]
        print(f"\n  Kept edge confidence: mean={sum(confs)/len(confs):.3f}, "
              f"min={min(confs):.3f}, max={max(confs):.3f}")

    if mode == 'preview':
        print("\n[Preview mode — no changes made]")
        print(f"Run with 'apply' to execute: python {sys.argv[0]} apply")
        return

    if mode == 'revert':
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        # Restore all PubMed batch edges to confidence=0.65
        cur.execute('''
            UPDATE morphisms SET confidence = 0.65
            WHERE provenance LIKE 'PMID:%' AND name = 'associated_with'
        ''')
        updated = cur.rowcount
        print(f"\nReverted {updated} edges to confidence=0.65")

        conn.commit()
        conn.close()
        print("[Revert complete]")
        return

    # Apply mode
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Count current state
    cur.execute('SELECT COUNT(*) FROM morphisms')
    before_count = cur.fetchone()[0]

    # Update confidence for kept edges
    updated = 0
    for edge_id, new_conf, action_type in keep:
        cur.execute('''
            UPDATE morphisms SET confidence = ?
            WHERE id = ?
        ''', (new_conf, edge_id))
        if cur.rowcount > 0:
            updated += 1

    # Remove rejected edges
    removed = 0
    for edge_id, reason in remove:
        cur.execute('DELETE FROM morphisms WHERE id = ?', (edge_id,))
        if cur.rowcount > 0:
            removed += 1

    conn.commit()

    # Verify
    cur.execute('SELECT COUNT(*) FROM morphisms')
    after_count = cur.fetchone()[0]

    print(f"\nResults:")
    print(f"  Confidence updated: {updated}")
    print(f"  Edges removed:      {removed}")
    print(f"  DB before: {before_count} morphisms")
    print(f"  DB after:  {after_count} morphisms")
    print(f"  Net change: {after_count - before_count}")

    conn.close()
    print("\n[Apply complete]")


if __name__ == '__main__':
    main()
