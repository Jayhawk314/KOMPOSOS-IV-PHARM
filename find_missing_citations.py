#!/usr/bin/env python3
"""Find the 17 morphisms with unknown provenance and search for citations"""

import sqlite3

DB_PATH = "data/drugs/tier1.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find morphisms with unknown provenance
cursor.execute("""
    SELECT id, name, source_name, target_name, confidence, metadata
    FROM morphisms
    WHERE provenance = 'unknown'
    ORDER BY source_name, target_name
""")

unknown_morphisms = cursor.fetchall()

print(f"Found {len(unknown_morphisms)} morphisms with unknown provenance:\n")
print("=" * 80)

for morph_id, name, source, target, conf, metadata in unknown_morphisms:
    print(f"\nID: {morph_id}")
    print(f"Edge: {source} --[{name}]--> {target}")
    print(f"Confidence: {conf}")
    print(f"Metadata: {metadata[:200] if metadata else 'None'}...")
    print("-" * 80)

conn.close()

print(f"\n\nThese edges need citations. Options:")
print("1. Search PubMed for valid citations")
print("2. Check ChEMBL/KEGG/other databases")
print("3. Remove if no evidence exists")
