#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Import high-confidence protein-protein interactions from STRING database.

STRING provides confidence scores for protein-protein interactions based on:
- Experimental evidence (wet lab experiments)
- Database curation (curated pathway databases)
- Text mining (co-mentions in literature)
- Co-expression (gene expression patterns)
- Genomic context (gene neighborhood, gene fusion)
- Homology (orthologs in other species)

All edges have combined scores (0-1000) and evidence breakdowns.

Usage:
    python import_string.py \\
        --manifest data/drugs/tier1_manifest.json \\
        --output tier1_manifest_with_string.json \\
        --min-score 700 \\
        --limit 5000
"""

import json
import sys
import argparse
import requests
import gzip
from typing import List, Dict, Any, Set
from pathlib import Path
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# STRING API endpoint (free, no auth required)
STRING_API = "https://string-db.org/api"
STRING_BULK = "https://stringdb-downloads.org/download/protein.links.v12.0/9606.protein.links.v12.0.txt.gz"


class STRINGImporter:
    """Import protein-protein interactions from STRING database."""

    def __init__(self, min_score: int = 700, max_results: int = 5000, species: int = 9606):
        """
        Initialize importer.

        Args:
            min_score: Minimum combined score (0-1000). STRING recommends ≥400 for medium confidence, ≥700 for high.
            max_results: Maximum PPIs to import.
            species: NCBI taxonomy ID (9606 = Homo sapiens).
        """
        self.min_score = min_score
        self.max_results = max_results
        self.species = species
        self.imported_count = 0
        self.skipped_count = 0

    def get_existing_proteins(self, manifest: Dict[str, Any]) -> Set[str]:
        """
        Get set of protein names already in manifest.

        We only import PPIs for proteins we already have (from tier1.db or OpenTargets).
        """
        return {
            obj["name"]
            for obj in manifest.get("objects", [])
            if obj.get("type") in ["Protein", "Receptor", "Oncogene", "TumorSuppressor",
                                    "Apoptosis", "CellCycle", "DNARepair", "Signaling",
                                    "Transcription", "Metabolic", "Structural", "Chaperone",
                                    "Epigenetic", "Regulator", "Splicing"]
        }

    def download_string_bulk(self) -> List[Dict[str, Any]]:
        """
        Download STRING bulk file for human PPIs.

        Returns:
            List of {"protein1": name, "protein2": name, "score": int, ...}
        """
        logger.info(f"Downloading STRING bulk data for species {self.species}...")
        logger.info(f"URL: {STRING_BULK}")
        logger.info("This may take a few minutes (~200MB compressed, ~1GB uncompressed)...")

        try:
            response = requests.get(STRING_BULK, timeout=300, stream=True)
            response.raise_for_status()

            # Decompress gzip
            logger.info("Decompressing...")
            content = gzip.decompress(response.content).decode('utf-8')

            # Parse TSV
            logger.info("Parsing interactions...")
            interactions = []
            lines = content.strip().split('\n')

            for i, line in enumerate(lines):
                if i == 0:
                    continue  # Skip header

                if len(interactions) >= self.max_results:
                    logger.info(f"Reached max_results limit ({self.max_results})")
                    break

                parts = line.strip().split()
                if len(parts) < 3:
                    continue

                protein1 = parts[0].split('.')[1]  # Remove species prefix (9606.ENSP... -> ENSP...)
                protein2 = parts[1].split('.')[1]
                score = int(parts[2])

                if score < self.min_score:
                    self.skipped_count += 1
                    continue

                interactions.append({
                    "protein1": protein1,
                    "protein2": protein2,
                    "score": score,
                    "evidence_id": f"string:{protein1}:{protein2}",
                })
                self.imported_count += 1

            logger.info(f"Imported {self.imported_count} interactions (skipped {self.skipped_count})")
            return interactions

        except Exception as e:
            logger.error(f"Failed to download STRING bulk data: {e}")
            return []

    def map_ensembl_to_gene(self, ensembl_id: str) -> str:
        """
        Map ENSP ID to gene symbol using STRING API.

        STRING uses ENSP IDs, but we want gene symbols for tier1.db.

        Args:
            ensembl_id: ENSP00000... identifier

        Returns:
            Gene symbol (e.g., "BRAF") or original ENSP ID if mapping fails
        """
        try:
            url = f"{STRING_API}/tsv/get_string_ids"
            params = {
                "identifiers": ensembl_id,
                "species": self.species,
                "limit": 1,
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            if len(lines) > 1:  # Skip header
                parts = lines[1].split('\t')
                if len(parts) >= 2:
                    return parts[1]  # preferredName (gene symbol)

        except Exception as e:
            logger.warning(f"Failed to map {ensembl_id}: {e}")

        return ensembl_id  # Fallback to ENSP ID

    def filter_by_existing_proteins(
        self,
        interactions: List[Dict[str, Any]],
        existing_proteins: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Keep only interactions where BOTH proteins are in existing_proteins.

        This ensures we only add PPIs for proteins we already have in the graph.
        """
        filtered = []

        logger.info("Mapping ENSP IDs to gene symbols...")
        ensp_to_gene = {}  # Cache mappings

        for interaction in interactions:
            p1_ensp = interaction["protein1"]
            p2_ensp = interaction["protein2"]

            # Map to gene symbols
            if p1_ensp not in ensp_to_gene:
                ensp_to_gene[p1_ensp] = self.map_ensembl_to_gene(p1_ensp)
            if p2_ensp not in ensp_to_gene:
                ensp_to_gene[p2_ensp] = self.map_ensembl_to_gene(p2_ensp)

            p1_gene = ensp_to_gene[p1_ensp]
            p2_gene = ensp_to_gene[p2_ensp]

            # Check if both are in existing proteins
            if p1_gene in existing_proteins and p2_gene in existing_proteins:
                interaction["protein1"] = p1_gene
                interaction["protein2"] = p2_gene
                filtered.append(interaction)

        logger.info(f"Filtered to {len(filtered)} interactions (both proteins in graph)")
        return filtered

    def map_to_morphism(self, interaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert STRING PPI to morphisms.

        PPIs are undirected, so we create TWO morphisms: A→B and B→A.

        Args:
            interaction: {"protein1": ..., "protein2": ..., "score": ...}

        Returns:
            List of 2 morphisms (bidirectional)
        """
        # Normalize score to [0, 1]
        confidence = interaction["score"] / 1000.0

        morphisms = []

        # A → B
        morphisms.append({
            "source": interaction["protein1"],
            "target": interaction["protein2"],
            "name": "interacts_with",
            "confidence": round(confidence, 3),
            "provenance": interaction["evidence_id"],
            "metadata": {
                "source": "STRING",
                "score": interaction["score"],
                "direction": "forward"
            }
        })

        # B → A (symmetric)
        morphisms.append({
            "source": interaction["protein2"],
            "target": interaction["protein1"],
            "name": "interacts_with",
            "confidence": round(confidence, 3),
            "provenance": interaction["evidence_id"],
            "metadata": {
                "source": "STRING",
                "score": interaction["score"],
                "direction": "reverse"
            }
        })

        return morphisms

    def load_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """Load existing tier1_manifest.json."""
        with open(manifest_path, 'r') as f:
            return json.load(f)

    def save_manifest(self, manifest: Dict[str, Any], output_path: str):
        """Save updated manifest."""
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Saved to {output_path}")

    def add_morphisms(self, manifest: Dict[str, Any], interactions: List[Dict[str, Any]]):
        """Add PPI morphisms to manifest."""
        existing_pairs = {
            (m["source"], m["target"], m["name"])
            for m in manifest.get("morphisms", [])
        }

        new_morphisms = []
        for interaction in interactions:
            morphisms = self.map_to_morphism(interaction)
            for morphism in morphisms:
                key = (morphism["source"], morphism["target"], morphism["name"])
                if key not in existing_pairs:
                    new_morphisms.append(morphism)
                    existing_pairs.add(key)

        manifest["morphisms"].extend(new_morphisms)
        logger.info(f"Added {len(new_morphisms)} new morphisms ({len(interactions)} PPIs × 2)")

    def run(self, manifest_path: str, output_path: str):
        """Run full import pipeline."""
        logger.info("=" * 80)
        logger.info("STRING Import Pipeline")
        logger.info("=" * 80)

        # 1. Load manifest & get existing proteins
        logger.info(f"\nStep 1: Load existing manifest from {manifest_path}")
        manifest = self.load_manifest(manifest_path)
        existing_proteins = self.get_existing_proteins(manifest)
        logger.info(f"Found {len(existing_proteins)} existing proteins in manifest")

        # 2. Download STRING bulk data
        logger.info(f"\nStep 2: Download STRING PPIs (min_score={self.min_score})")
        interactions = self.download_string_bulk()

        if not interactions:
            logger.error("No interactions retrieved. Check download and thresholds.")
            return

        # 3. Filter by existing proteins
        logger.info("\nStep 3: Filter PPIs to existing proteins only")
        filtered = self.filter_by_existing_proteins(interactions, existing_proteins)

        if not filtered:
            logger.warning("No PPIs found for existing proteins. May need to run OpenTargets import first.")
            return

        # 4. Add morphisms
        logger.info("\nStep 4: Add PPI morphisms (bidirectional)")
        original_morphisms = len(manifest.get("morphisms", []))
        self.add_morphisms(manifest, filtered)

        # 5. Update version
        logger.info("\nStep 5: Update manifest version")
        manifest["version"] = "2026-06-01-string"
        manifest["sources"] = manifest.get("sources", []) + ["string_v12"]

        # 6. Save
        logger.info(f"\nStep 6: Save to {output_path}")
        self.save_manifest(manifest, output_path)

        # Summary
        final_morphisms = len(manifest.get("morphisms", []))
        logger.info("\n" + "=" * 80)
        logger.info("Summary")
        logger.info("=" * 80)
        logger.info(f"Morphisms: {original_morphisms} → {final_morphisms} (+{final_morphisms - original_morphisms})")
        logger.info(f"PPIs imported: {len(filtered)} (bidirectional = {len(filtered)*2} morphisms)")
        logger.info(f"\nNext steps:")
        logger.info(f"1. Review new morphisms in {output_path}")
        logger.info(f"2. python data/drugs/build_tier1.py --manifest {output_path}")
        logger.info(f"3. python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci")


def main():
    parser = argparse.ArgumentParser(
        description="Import protein-protein interactions from STRING"
    )
    parser.add_argument(
        "--manifest",
        default="data/drugs/tier1_manifest.json",
        help="Path to existing tier1_manifest.json"
    )
    parser.add_argument(
        "--output",
        default="data/drugs/tier1_manifest_string.json",
        help="Path to save updated manifest"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=700,
        help="Minimum combined score (0-1000). Default: 700 (high confidence)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum PPIs to import. Default: 5000"
    )
    parser.add_argument(
        "--species",
        type=int,
        default=9606,
        help="NCBI taxonomy ID. Default: 9606 (Homo sapiens)"
    )

    args = parser.parse_args()

    # Validate paths
    if not Path(args.manifest).exists():
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)

    # Run import
    importer = STRINGImporter(
        min_score=args.min_score,
        max_results=args.limit,
        species=args.species
    )
    importer.run(args.manifest, args.output)


if __name__ == "__main__":
    main()
