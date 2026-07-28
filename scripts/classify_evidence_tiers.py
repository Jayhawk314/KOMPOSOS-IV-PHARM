#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Classify all morphisms in tier1.db into evidence tiers.

Adds evidence_tier column and classifies based on provenance source.
"""

import sqlite3
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.evidence_tiers import classify_tier_from_provenance, EvidenceTier

DB_PATH = "data/drugs/tier1.db"


def add_evidence_tier_column():
    """Add evidence_tier column to morphisms table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(morphisms)")
    columns = [col[1] for col in cursor.fetchall()]

    if "evidence_tier" not in columns:
        print("Adding evidence_tier column to morphisms table...")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN evidence_tier TEXT DEFAULT 'HYPOTHESIS'")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN quantitative_value REAL")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN value_unit TEXT")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN sample_size INTEGER")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN confidence_lower REAL")
        cursor.execute("ALTER TABLE morphisms ADD COLUMN confidence_upper REAL")
        conn.commit()
        print("[OK] Columns added")
    else:
        print("[OK] evidence_tier column already exists")

    conn.close()


def classify_all_edges():
    """Classify all morphisms into evidence tiers."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all morphisms
    cursor.execute("SELECT id, provenance, metadata, confidence FROM morphisms")
    all_morphisms = cursor.fetchall()

    print(f"\nClassifying {len(all_morphisms)} morphisms...")

    tier_counts = {tier: 0 for tier in EvidenceTier}

    for morph_id, provenance, metadata_str, confidence in all_morphisms:
        # Parse metadata
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except:
            metadata = {}

        # Classify tier
        tier = classify_tier_from_provenance(provenance, metadata, confidence)
        tier_counts[tier] += 1

        # Update database
        cursor.execute(
            "UPDATE morphisms SET evidence_tier = ? WHERE id = ?",
            (tier.value, morph_id)
        )

    conn.commit()

    # Print summary
    print("\n" + "="*60)
    print("EVIDENCE TIER CLASSIFICATION COMPLETE")
    print("="*60)

    total = sum(tier_counts.values())
    for tier in EvidenceTier:
        count = tier_counts[tier]
        pct = 100 * count / total if total > 0 else 0
        print(f"  {tier.value:15s}: {count:4d} ({pct:5.1f}%)")

    print(f"\n  TOTAL: {total}")

    conn.close()


def main():
    print("="*60)
    print("EVIDENCE TIER CLASSIFICATION")
    print("="*60)

    # Step 1: Add columns
    add_evidence_tier_column()

    # Step 2: Classify all edges
    classify_all_edges()

    print("\n[OK] Evidence tier classification complete!")
    print("\nNext steps:")
    print("  1. Update UI to display tiers (app.py)")
    print("  2. Extract quantitative data (Phase 2)")
    print("  3. Expand data sources (Phase 3)")


if __name__ == "__main__":
    main()
