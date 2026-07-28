#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Fetch protein sequences from UniProt for all biological entities in tier1.db.

Cross-references against existing data/proteins/sequences/metadata.json and
fetches missing sequences from the UniProt REST API (human proteome only).

Some entities may not be individual genes (e.g., complexes, pathways) and
will be reported as unresolvable.
"""

import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = "data/drugs/tier1.db"
SEQUENCES_DIR = Path("data/proteins/sequences")
METADATA_FILE = SEQUENCES_DIR / "metadata.json"

# Rate limit: UniProt allows ~100 requests/second, but be polite
REQUEST_DELAY = 0.2  # seconds between requests


def load_existing_sequences() -> Dict[str, dict]:
    """Load existing protein sequences from metadata.json."""
    if not METADATA_FILE.exists():
        return {}

    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    return {p["gene_name"]: p for p in metadata.get("proteins", [])}


def load_tier1_biological_entities() -> List[str]:
    """Load all non-Drug, non-Disease object names from tier1.db."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, type_name FROM objects
        WHERE type_name NOT IN ('Drug', 'Disease')
        ORDER BY name
    """)

    entities = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()

    return entities


def fetch_uniprot_sequence(gene_name: str) -> Optional[dict]:
    """
    Fetch protein sequence from UniProt REST API.

    Args:
        gene_name: Gene symbol (e.g., "TP53")

    Returns:
        Dict with gene_name, uniprot_id, sequence, length, function, organism
        or None if not found.
    """
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        'query': f'gene_exact:{gene_name} AND organism_id:9606 AND reviewed:true',
        'format': 'json',
        'size': 1,
        'fields': 'accession,gene_names,sequence,protein_name,organism_name'
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if not results:
            # Try without reviewed filter
            params['query'] = f'gene_exact:{gene_name} AND organism_id:9606'
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])

        if not results:
            return None

        entry = results[0]
        sequence_data = entry.get('sequence', {})
        sequence = sequence_data.get('value', '')

        if not sequence:
            return None

        # Extract function description
        function_desc = ""
        comments = entry.get('comments', [])
        for comment in comments:
            if comment.get('commentType') == 'FUNCTION':
                texts = comment.get('texts', [])
                if texts:
                    function_desc = texts[0].get('value', '')[:200]
                    break

        return {
            "gene_name": gene_name,
            "uniprot_id": entry.get('primaryAccession', ''),
            "sequence": sequence,
            "length": len(sequence),
            "function": function_desc,
            "organism": "Homo sapiens",
            "reviewed": True
        }

    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Network error for {gene_name}: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"  [ERROR] Parse error for {gene_name}: {e}")
        return None


def main():
    print("=" * 70)
    print("FETCH PROTEIN SEQUENCES FROM UNIPROT")
    print("=" * 70)

    # Load existing
    print("\n[1] Loading existing sequences...")
    existing = load_existing_sequences()
    print(f"  Existing sequences: {len(existing)}")

    # Load tier1.db entities
    print("\n[2] Loading biological entities from tier1.db...")
    entities = load_tier1_biological_entities()
    print(f"  Biological entities: {len(entities)}")

    # Find missing
    missing = [(name, type_name) for name, type_name in entities
               if name not in existing]
    print(f"  Missing sequences: {len(missing)}")

    if not missing:
        print("\n  All entities already have sequences!")
        return

    # Fetch missing sequences
    print(f"\n[3] Fetching {len(missing)} sequences from UniProt...")
    fetched = []
    failed = []

    for i, (gene_name, type_name) in enumerate(missing, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(missing)}")

        result = fetch_uniprot_sequence(gene_name)

        if result:
            fetched.append(result)
            print(f"  [OK] {gene_name} ({result['uniprot_id']}, {result['length']}aa)")
        else:
            failed.append((gene_name, type_name))
            print(f"  [MISS] {gene_name} ({type_name})")

        time.sleep(REQUEST_DELAY)

    # Merge and save
    print(f"\n[4] Saving sequences...")
    all_proteins = list(existing.values()) + fetched

    SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {"proteins": all_proteins}
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Also write individual FASTA files for new proteins
    for protein in fetched:
        fasta_path = SEQUENCES_DIR / f"{protein['gene_name']}.fasta"
        with open(fasta_path, 'w') as f:
            f.write(f">{protein['gene_name']}|{protein['uniprot_id']}|{protein['organism']}\n")
            # Write sequence in 80-char lines
            seq = protein['sequence']
            for j in range(0, len(seq), 80):
                f.write(seq[j:j+80] + "\n")

    # Report
    print(f"\n{'=' * 70}")
    print("SEQUENCE FETCH COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Previously had: {len(existing)}")
    print(f"  Newly fetched:  {len(fetched)}")
    print(f"  Failed/missing: {len(failed)}")
    print(f"  Total now:      {len(all_proteins)}")

    if failed:
        print(f"\n  Unresolvable entities ({len(failed)}):")
        for name, type_name in failed:
            print(f"    {name} ({type_name})")

    print(f"\n  Saved to: {METADATA_FILE}")


if __name__ == "__main__":
    main()
