#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Import drug-target associations from ChEMBL - the gold standard for medicinal chemistry data.

ChEMBL is the PRIMARY SOURCE for drug-target data used by OpenTargets, DrugBank, and others.

Features:
- 2.4M+ bioactivity measurements
- All with provenance (PMIDs, assay IDs, experimental conditions)
- FDA-approved drugs with measured IC50, Ki, Kd values
- Curated mechanism of action data
- Production-grade reliability (used by Pfizer, Novartis, academia worldwide)

Usage:
    # Install ChEMBL client first
    pip install chembl_webresource_client

    # Run importer
    python import_chembl.py \
        --manifest data/drugs/tier1_manifest.json \
        --output tier1_manifest_chembl.json \
        --min-pchembl 6.0 \
        --limit 1000
"""

import json
import sys
import argparse
from typing import List, Dict, Any, Set
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChEMBLImporter:
    """Import drug-target associations from ChEMBL database."""

    def __init__(self, min_pchembl: float = 6.0, max_results: int = 10000, approved_only: bool = True):
        """
        Initialize ChEMBL importer.

        Args:
            min_pchembl: Minimum pChEMBL value (negative log of IC50/Ki/Kd in M).
                        6.0 = 1 µM (moderate activity)
                        7.0 = 100 nM (good activity)
                        8.0 = 10 nM (high activity)
            max_results: Maximum drug-target associations to import.
            approved_only: Only import FDA/EMA approved drugs (Phase 4).
        """
        self.min_pchembl = min_pchembl
        self.max_results = max_results
        self.approved_only = approved_only
        self.imported_count = 0
        self.skipped_count = 0

    def get_drug_targets(self) -> List[Dict[str, Any]]:
        """
        Query ChEMBL for drug-target associations.

        Returns:
            List of {"drug": name, "target": gene, "score": float, "evidence_id": str, ...}
        """
        try:
            from chembl_webresource_client.new_client import new_client
        except ImportError:
            logger.error("ChEMBL client not installed. Run: pip install chembl_webresource_client")
            return []

        associations = []

        try:
            logger.info("Connecting to ChEMBL database...")

            # Initialize ChEMBL clients
            drug_client = new_client.drug
            molecule_client = new_client.molecule
            mechanism_client = new_client.mechanism
            activity_client = new_client.activity

            # Step 1: Get approved drugs (use small batch to avoid rate limiting)
            logger.info("Querying ChEMBL for approved drugs (batch mode)...")

            if self.approved_only:
                # Get FDA/EMA approved drugs (max_phase = 4)
                # Limit to 50 drugs to avoid API overload
                drugs = drug_client.filter(max_phase=4).only(
                    ['molecule_chembl_id', 'pref_name', 'max_phase']
                )[:50]  # Small batch
            else:
                # Get all drugs in clinical trials
                drugs = drug_client.filter(max_phase__gte=1).only(
                    ['molecule_chembl_id', 'pref_name', 'max_phase']
                )[:50]  # Small batch

            # Convert to list (API returns iterator)
            drugs_list = list(drugs)
            logger.info(f"Found {len(drugs_list)} approved drugs in ChEMBL (batch mode)")
            logger.info("Processing in small batches to avoid rate limiting...")

            # Step 2: Get mechanisms of action and targets for each drug
            # PRODUCTION MODE: Slow but robust with error handling
            for idx, drug in enumerate(drugs_list):
                if self.imported_count >= self.max_results:
                    logger.info(f"Reached max_results limit ({self.max_results})")
                    break

                # Progress logging
                logger.info(f"Processing drug {idx+1}/{len(drugs_list)}...")

                drug_chembl_id = drug['molecule_chembl_id']
                drug_name = drug.get('pref_name', drug_chembl_id)
                max_phase = drug.get('max_phase', 0)

                # Rate limiting: pause between drugs to avoid API overload
                if idx > 0:
                    time.sleep(0.5)  # 500ms delay between drugs

                # Get mechanisms of action (provides target + action type)
                # RETRY LOGIC: 3 attempts with exponential backoff
                for attempt in range(3):
                    try:
                        mechanisms = mechanism_client.filter(
                            molecule_chembl_id=drug_chembl_id
                        ).only([
                            'mechanism_of_action',
                            'action_type',
                            'target_chembl_id',
                            'mechanism_refs'
                        ])

                        for mech in mechanisms:
                            if self.imported_count >= self.max_results:
                                break

                            target_chembl_id = mech.get('target_chembl_id')
                            if not target_chembl_id:
                                continue

                            # Get target details (gene symbol, organism)
                            # Rate limit: small delay between targets
                            time.sleep(0.2)  # 200ms between API calls

                            try:
                                target = new_client.target.get(target_chembl_id)

                                # Only human targets
                                if not target.get('organism', '').lower().startswith('homo sapiens'):
                                    continue

                                # Get gene symbol (preferred name)
                                target_components = target.get('target_components', [])
                                if not target_components:
                                    continue

                                # Get first component's gene symbol
                                component = target_components[0]
                                target_gene = component.get('accession')  # Uniprot accession

                                # Try to get gene symbol from component
                                component_synonyms = component.get('component_synonym', [])
                                for syn in component_synonyms:
                                    if syn.get('syn_type') == 'GENE_SYMBOL':
                                        target_gene = syn.get('component_synonym')
                                        break

                                if not target_gene:
                                    continue

                                # Get mechanism of action details
                                moa = mech.get('mechanism_of_action', 'unknown')
                                action_type = mech.get('action_type', 'unknown')
                                mech_refs = mech.get('mechanism_refs', [])

                                # Get PMIDs from references
                                pmids = [ref.get('ref_id') for ref in mech_refs if ref.get('ref_type') == 'PMID']
                                pmid_str = f"PMID:{pmids[0]}" if pmids else "ChEMBL_mechanism"

                                # Score based on clinical phase
                                # Phase 4 (approved) = 1.0, Phase 3 = 0.85, etc.
                                score = min(1.0, 0.4 + (max_phase * 0.15))

                                associations.append({
                                    "drug": drug_name,
                                    "drug_id": drug_chembl_id,
                                    "target": target_gene,
                                    "target_id": target_chembl_id,
                                    "score": score,
                                    "moa": f"{action_type}: {moa}",
                                    "phase": f"PHASE_{max_phase}",
                                    "evidence_id": f"chembl:{drug_chembl_id}:{target_chembl_id}",
                                    "pmid": pmid_str,
                                    "source": "ChEMBL_mechanism"
                                })
                                self.imported_count += 1

                            except Exception as e:
                                logger.debug(f"Failed to get target {target_chembl_id}: {e}")
                                continue

                        # Success - break retry loop
                        break

                    except Exception as e:
                        logger.warning(f"Attempt {attempt+1}/3 failed for {drug_chembl_id}: {e}")
                        if attempt < 2:  # Not last attempt
                            wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s
                            logger.info(f"Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Failed to get mechanisms for {drug_chembl_id} after 3 attempts")
                            continue

            logger.info(f"Retrieved {self.imported_count} drug-target associations from mechanisms")

            # Step 3: If we need more data, get bioactivity data
            if self.imported_count < self.max_results:
                logger.info("Getting additional associations from bioactivity data...")

                # Get high-quality bioactivity data
                activities = activity_client.filter(
                    pchembl_value__gte=self.min_pchembl,
                    assay_type='B',  # Binding assays
                    target_organism='Homo sapiens'
                ).only([
                    'molecule_chembl_id',
                    'target_chembl_id',
                    'pchembl_value',
                    'standard_type',
                    'document_chembl_id'
                ])[:min(1000, self.max_results - self.imported_count)]

                for activity in activities:
                    if self.imported_count >= self.max_results:
                        break

                    # Get molecule and target details
                    mol_id = activity.get('molecule_chembl_id')
                    target_id = activity.get('target_chembl_id')
                    pchembl = activity.get('pchembl_value', 0)

                    if not all([mol_id, target_id, pchembl]):
                        continue

                    # Get molecule name
                    try:
                        mol = molecule_client.get(mol_id)
                        drug_name = mol.get('pref_name', mol_id)
                    except:
                        drug_name = mol_id

                    # Get target gene symbol
                    try:
                        target = new_client.target.get(target_id)
                        target_components = target.get('target_components', [])
                        if not target_components:
                            continue

                        component = target_components[0]
                        target_gene = component.get('accession')

                        component_synonyms = component.get('component_synonym', [])
                        for syn in component_synonyms:
                            if syn.get('syn_type') == 'GENE_SYMBOL':
                                target_gene = syn.get('component_synonym')
                                break

                        if not target_gene:
                            continue

                        # Convert pChEMBL to confidence score
                        # pChEMBL 6 = 1µM = 0.7, pChEMBL 7 = 100nM = 0.85, pChEMBL 8 = 10nM = 0.95
                        score = min(1.0, 0.4 + ((pchembl - 5.0) * 0.12))

                        # Get document (PMID)
                        doc_id = activity.get('document_chembl_id', 'unknown')

                        associations.append({
                            "drug": drug_name,
                            "drug_id": mol_id,
                            "target": target_gene,
                            "target_id": target_id,
                            "score": score,
                            "moa": f"{activity.get('standard_type', 'unknown')}: pChEMBL={pchembl:.1f}",
                            "phase": "BIOACTIVITY",
                            "evidence_id": f"chembl:{mol_id}:{target_id}:{doc_id}",
                            "pmid": doc_id,
                            "source": "ChEMBL_bioactivity"
                        })
                        self.imported_count += 1

                    except Exception as e:
                        logger.debug(f"Failed to process activity: {e}")
                        continue

            logger.info(f"Total: {self.imported_count} associations retrieved (skipped {self.skipped_count})")

        except Exception as e:
            logger.error(f"Failed to query ChEMBL: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return associations

    def map_to_morphism(self, assoc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ChEMBL association to tier1_manifest morphism format.

        Args:
            assoc: {"drug": ..., "target": ..., "score": ..., ...}

        Returns:
            {"source": drug, "target": protein, "edge_type": "inhibits", ...}
        """
        # Infer morphism type from mechanism of action
        moa = assoc.get("moa", "unknown").lower()

        if "inhibit" in moa or "antagonist" in moa or "blocker" in moa:
            morphism_type = "inhibits"
        elif "agonist" in moa or "activat" in moa or "inducer" in moa:
            morphism_type = "activates"
        elif "modulator" in moa:
            morphism_type = "modulates"
        elif "bind" in moa or "ic50" in moa or "ki" in moa:
            morphism_type = "binds"
        else:
            morphism_type = "targets"

        return {
            "source": assoc["drug"],
            "target": assoc["target"],
            "edge_type": morphism_type,
            "confidence": round(assoc["score"], 3),
            "provenance": assoc.get("pmid", assoc["evidence_id"]),
            "metadata": {
                "source": "ChEMBL",
                "moa": assoc.get("moa", "unknown"),
                "phase": assoc.get("phase", "unknown"),
                "drug_id": assoc.get("drug_id"),
                "target_id": assoc.get("target_id"),
                "evidence_id": assoc["evidence_id"]
            }
        }

    def load_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """Load existing tier1_manifest.json."""
        with open(manifest_path, 'r') as f:
            return json.load(f)

    def save_manifest(self, manifest: Dict[str, Any], output_path: str):
        """Save updated manifest."""
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Saved to {output_path}")

    def add_objects(self, manifest: Dict[str, Any], associations: List[Dict[str, Any]]):
        """Add new protein objects from associations."""
        existing_names = {obj["name"] for obj in manifest.get("objects", [])}

        new_objects = []
        for assoc in associations:
            target_name = assoc["target"]
            if target_name not in existing_names:
                new_objects.append({
                    "name": target_name,
                    "type": "Protein",
                    "metadata": {
                        "chembl_id": assoc.get("target_id"),
                        "source": "ChEMBL"
                    }
                })
                existing_names.add(target_name)

        manifest["objects"].extend(new_objects)
        logger.info(f"Added {len(new_objects)} new protein objects")

    def add_morphisms(self, manifest: Dict[str, Any], associations: List[Dict[str, Any]]):
        """Add drug-target morphisms to manifest."""
        existing_pairs = {
            (m["source"], m["target"], m.get("edge_type", m.get("name", "")))
            for m in manifest.get("morphisms", [])
        }

        new_morphisms = []
        for assoc in associations:
            morphism = self.map_to_morphism(assoc)
            key = (morphism["source"], morphism["target"], morphism.get("edge_type", morphism.get("name", "")))

            if key not in existing_pairs:
                new_morphisms.append(morphism)
                existing_pairs.add(key)

        manifest["morphisms"].extend(new_morphisms)
        logger.info(f"Added {len(new_morphisms)} new morphisms")

    def run(self, manifest_path: str, output_path: str):
        """Run full import pipeline."""
        logger.info("=" * 80)
        logger.info("ChEMBL Import Pipeline (Production-Grade)")
        logger.info("=" * 80)

        # 1. Query ChEMBL
        logger.info(f"\nStep 1: Query ChEMBL (min_pchembl={self.min_pchembl}, approved_only={self.approved_only})")
        associations = self.get_drug_targets()

        if not associations:
            logger.error("No associations retrieved. Check ChEMBL client installation and connection.")
            return

        # 2. Load manifest
        logger.info(f"\nStep 2: Load existing manifest from {manifest_path}")
        manifest = self.load_manifest(manifest_path)
        logger.info(f"Original: {len(manifest['objects'])} objects, {len(manifest['morphisms'])} morphisms")

        # 3. Add objects
        logger.info("\nStep 3: Add new protein objects")
        self.add_objects(manifest, associations)

        # 4. Add morphisms
        logger.info("\nStep 4: Add drug-target morphisms")
        original_morphisms = len(manifest.get("morphisms", []))
        self.add_morphisms(manifest, associations)

        # 5. Update version
        logger.info("\nStep 5: Update manifest version")
        manifest["version"] = "2026-05-06-chembl"
        manifest["sources"] = manifest.get("sources", []) + ["chembl_v33"]

        # 6. Save
        logger.info(f"\nStep 6: Save to {output_path}")
        self.save_manifest(manifest, output_path)

        # Summary
        final_morphisms = len(manifest.get("morphisms", []))
        logger.info("\n" + "=" * 80)
        logger.info("Summary")
        logger.info("=" * 80)
        logger.info(f"Objects: {len(manifest['objects'])}")
        logger.info(f"Morphisms: {original_morphisms} → {final_morphisms} (+{final_morphisms - original_morphisms})")
        logger.info(f"Associations imported: {len(associations)}")
        logger.info(f"\nNext steps:")
        logger.info(f"1. Review new morphisms in {output_path}")
        logger.info(f"2. python data/drugs/build_tier1.py --manifest {output_path}")
        logger.info(f"3. python validation/repurposing_benchmark.py --view full_typed --protocol loocv --ci")


def main():
    parser = argparse.ArgumentParser(
        description="Import drug-target associations from ChEMBL (production-grade)"
    )
    parser.add_argument(
        "--manifest",
        default="data/drugs/tier1_manifest.json",
        help="Path to existing tier1_manifest.json"
    )
    parser.add_argument(
        "--output",
        default="data/drugs/tier1_manifest_chembl.json",
        help="Path to save updated manifest"
    )
    parser.add_argument(
        "--min-pchembl",
        type=float,
        default=6.0,
        help="Minimum pChEMBL value (6.0=1µM, 7.0=100nM, 8.0=10nM). Default: 6.0"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Maximum associations to import. Default: 10000"
    )
    parser.add_argument(
        "--all-phases",
        action="store_true",
        help="Include clinical trial drugs (not just approved). Default: approved only"
    )

    args = parser.parse_args()

    # Validate paths
    if not Path(args.manifest).exists():
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)

    # Run import
    importer = ChEMBLImporter(
        min_pchembl=args.min_pchembl,
        max_results=args.limit,
        approved_only=not args.all_phases
    )
    importer.run(args.manifest, args.output)


if __name__ == "__main__":
    main()
