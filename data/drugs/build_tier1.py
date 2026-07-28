# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Reproducible build script for tier1.db.

Rebuilds the drug-target-disease knowledge graph from tier1_manifest.json.
Run from repo root:

    python data/drugs/build_tier1.py

This creates a fresh tier1.db from the manifest. The manifest is the
canonical, version-controlled source of truth for the graph.

To update the graph:
1. Edit tier1_manifest.json (add objects, morphisms, PMIDs).
2. Run this script to rebuild.
3. Run the benchmark to verify metrics.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(SCRIPT_DIR, "tier1_manifest.json")
DB_PATH = os.path.join(SCRIPT_DIR, "tier1.db")


def build(manifest_path: str = MANIFEST, db_path: str = DB_PATH, force: bool = False):
    if os.path.exists(db_path) and not force:
        print(f"ERROR: {db_path} already exists. Use --force to overwrite.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables matching existing schema
    c.execute("""
        CREATE TABLE objects (
            name TEXT PRIMARY KEY,
            type_name TEXT NOT NULL DEFAULT 'Object',
            metadata TEXT NOT NULL DEFAULT '{}',
            embedding BLOB,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            provenance TEXT NOT NULL DEFAULT 'unknown'
        )
    """)

    c.execute("""
        CREATE TABLE morphisms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_name TEXT NOT NULL,
            target_name TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            confidence REAL NOT NULL DEFAULT 1.0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            provenance TEXT NOT NULL DEFAULT 'unknown'
        )
    """)

    c.execute("""
        CREATE TABLE paths (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL DEFAULT '',
            morphism_ids TEXT NOT NULL,
            source_name TEXT NOT NULL,
            target_name TEXT NOT NULL,
            length INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '{}',
            confidence REAL NOT NULL DEFAULT 1.0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            provenance TEXT NOT NULL DEFAULT 'computed',
            FOREIGN KEY (source_name) REFERENCES objects(name),
            FOREIGN KEY (target_name) REFERENCES objects(name)
        )
    """)

    c.execute("""
        CREATE TABLE equivalence_classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            object_names TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE higher_morphisms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_morphism_id TEXT NOT NULL,
            target_morphism_id TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insert objects
    for obj in manifest["objects"]:
        c.execute(
            "INSERT INTO objects (name, type_name, provenance, created_at, updated_at) VALUES (?,?,?,?,?)",
            (obj["name"], obj["type"], obj.get("provenance", "unknown"), now, now),
        )

    # Insert morphisms
    for m in manifest["morphisms"]:
        mid = f"{m['edge_type']}:{m['source']}->{m['target']}"
        c.execute(
            "INSERT INTO morphisms (id, name, source_name, target_name, confidence, provenance, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (mid, m["edge_type"], m["source"], m["target"], m.get("confidence", 1.0), m.get("provenance", "unknown"), now, now),
        )

    conn.commit()

    # Verify
    c.execute("SELECT COUNT(*) FROM objects")
    obj_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM morphisms")
    morph_count = c.fetchone()[0]

    print(f"Built {db_path}")
    print(f"  Objects: {obj_count} (expected {manifest['object_count']})")
    print(f"  Morphisms: {morph_count} (expected {manifest['morphism_count']})")

    if obj_count != manifest["object_count"] or morph_count != manifest["morphism_count"]:
        print("WARNING: counts do not match manifest!")
        sys.exit(1)

    conn.close()
    print("OK")


if __name__ == "__main__":
    force = "--force" in sys.argv
    build(force=force)
