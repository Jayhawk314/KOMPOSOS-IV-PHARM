# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Load drug repurposing network into KOMPOSOS-IV Category.

Two loaders are available:

1. create_drug_store() -- Original curated network (~105 objects, ~203 morphisms)
   Uses manually curated data from data/drugs/drug_network.py.

2. load_scaled_drug_network() -- Scaled network from external databases
   Incrementally integrates up to 7 external data sources:
     Phase 1: Hetionet      (47K nodes, 2.25M edges)
     Phase 2: Open Targets  (confidence enrichment)
     Phase 3: ChEMBL        (quantitative bioactivity)
     Phase 4: DGIdb         (47-source drug-gene interactions)
     Phase 5: BioGRID       (2.9M protein-protein interactions)
     Phase 6: Reactome      (pathway-level reasoning)
     Phase 7: COSMIC        (cancer gene census)

Each phase is a toggle. The curated network is always loaded as the base.

KOMPOSOS-IV Update:
- Now uses Category instead of KomposOSStore
- Uses Object/Morphism from core.types instead of StoredObject/StoredMorphism
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.category import Category
from core.types import Object, Morphism
from data.proteins.cancer_proteins import get_protein_network
from data.proteins.aml_proteins import get_aml_network
from data.drugs.drug_network import get_drug_network, ADDITIONAL_PROTEINS


def _add_protein(category, name, data, domain="protein"):
    """Add a protein object to the Category (upsert)."""
    # In KOMPOSOS-IV, just add the object with type_name
    obj = category.add(name, type_name=data["type"])
    # Metadata is stored in the object but IV handles it differently
    # The important part is the object name and type


def _add_interactions(category, interactions, domain="protein"):
    """Add a list of (source, target, relation, confidence, evidence) tuples."""
    for source, target, relation, confidence, evidence in interactions:
        # In KOMPOSOS-IV, use connect() method
        category.connect(source, target, relation, confidence=confidence)


def create_drug_store(db_path: str = "data/drugs/drug_repurposing.db",
                      include_proteins: bool = True,
                      include_redo_expansion: bool = True,
                      include_redo_full: bool = False,
                      include_noetik_expansion: bool = True):
    """
    Create a Category with the drug repurposing network.

    Args:
        db_path: Path to SQLite database file
        include_proteins: If True, also load cancer + AML protein networks
                         (needed for Drug->Protein->Disease chains)
        include_redo_expansion: If True, load 20 additional ReDO drugs
        include_redo_full: If True, load ~130 additional ReDO_DB drugs
        include_noetik_expansion: If True, load 30 Noetik-focused drugs (NSCLC/CRC, immunotherapy)

    Returns:
        Populated Category instance (KOMPOSOS-IV)
    """
    print(f"Creating drug repurposing Category at: {db_path}")

    category = Category(db_path)

    # Step 1: Load cancer proteins (core signaling targets)
    if include_proteins:
        proteins, protein_interactions = get_protein_network()
        print(f"Adding {len(proteins)} cancer proteins...")
        for name, data in proteins.items():
            _add_protein(store, name, data)

        print(f"Adding {len(protein_interactions)} cancer protein interactions...")
        _add_interactions(store, protein_interactions)

        # Step 1b: Load AML proteins (expands network significantly)
        aml_proteins, aml_interactions = get_aml_network()
        # Only add proteins not already in cancer network
        new_aml = {k: v for k, v in aml_proteins.items() if k not in proteins}
        print(f"Adding {len(new_aml)} AML-specific proteins...")
        for name, data in new_aml.items():
            _add_protein(store, name, data, domain="aml_protein")

        print(f"Adding {len(aml_interactions)} AML protein interactions...")
        _add_interactions(store, aml_interactions, domain="aml_protein")

    # Step 2: Load additional drug-target proteins (KIT, ALK, AMPK, etc.)
    print(f"Adding {len(ADDITIONAL_PROTEINS)} additional target proteins...")
    for name, data in ADDITIONAL_PROTEINS.items():
        _add_protein(store, name, data, domain="drug_target")

    # Step 3: Load drugs and diseases
    entities, interactions = get_drug_network()

    drugs = {k: v for k, v in entities.items() if v["type"] == "Drug"}
    diseases = {k: v for k, v in entities.items() if v["type"] == "Disease"}

    print(f"Adding {len(drugs)} drugs...")
    for name, data in drugs.items():
        obj = StoredObject(
            name=name,
            type_name="Drug",
            metadata={
                "brand": data.get("brand", ""),
                "drug_class": data.get("drug_class", ""),
                "mechanism": data.get("mechanism", ""),
                "fda_year": data.get("fda_year", 0),
                "drugbank_id": data.get("drugbank_id", ""),
                "domain": "drug",
            }
        )
        store.add_object(obj)

    print(f"Adding {len(diseases)} diseases...")
    for name, data in diseases.items():
        obj = StoredObject(
            name=name,
            type_name="Disease",
            metadata={
                "full_name": data.get("full_name", name),
                "prevalence": data.get("prevalence", "unknown"),
                "mesh_id": data.get("mesh_id", ""),
                "domain": "disease",
            }
        )
        store.add_object(obj)

    # Step 4: Load all drug/disease interactions
    print(f"Adding {len(interactions)} drug/disease interactions...")
    _add_interactions(store, interactions, domain="drug_repurposing")

    # Step 5: Load ReDO expansion drugs (Batch 1: 20 additional drugs)
    if include_redo_expansion:
        try:
            from data.drugs.redo_expansion import (
                REDO_DRUGS,
                REDO_DRUG_TARGET_INTERACTIONS,
                REDO_ADDITIONAL_PROTEINS,
                REDO_PROTEIN_DISEASE_ASSOCIATIONS,
            )

            # Add new proteins needed for ReDO drug targets
            print(f"Adding {len(REDO_ADDITIONAL_PROTEINS)} ReDO additional proteins...")
            for name, data in REDO_ADDITIONAL_PROTEINS.items():
                _add_protein(store, name, data, domain="redo_target")

            # Add ReDO drugs
            print(f"Adding {len(REDO_DRUGS)} ReDO drugs...")
            for name, data in REDO_DRUGS.items():
                obj = StoredObject(
                    name=name,
                    type_name="Drug",
                    metadata={
                        "brand": data.get("brand", ""),
                        "drug_class": data.get("drug_class", ""),
                        "mechanism": data.get("mechanism", ""),
                        "fda_year": data.get("fda_year", 0),
                        "drugbank_id": data.get("drugbank_id", ""),
                        "original_indication": data.get("original_indication", ""),
                        "domain": "redo_drug",
                    }
                )
                store.add_object(obj)

            # Add ReDO drug-target and protein-disease interactions
            redo_interactions = (
                REDO_DRUG_TARGET_INTERACTIONS +
                REDO_PROTEIN_DISEASE_ASSOCIATIONS
            )
            print(f"Adding {len(redo_interactions)} ReDO interactions...")
            _add_interactions(store, redo_interactions, domain="redo_expansion")

        except ImportError:
            pass  # ReDO expansion module not available

    # Step 6: Load ReDO Full expansion (~130 additional drugs)
    if include_redo_full:
        try:
            from data.drugs.redo_full_expansion import (
                REDO_FULL_DRUGS,
                REDO_FULL_DRUG_TARGET_INTERACTIONS,
                REDO_FULL_ADDITIONAL_PROTEINS,
                REDO_FULL_PROTEIN_DISEASE_ASSOCIATIONS,
            )

            # Add new proteins needed for ReDO Full drug targets
            print(f"Adding {len(REDO_FULL_ADDITIONAL_PROTEINS)} ReDO Full additional proteins...")
            for name, data in REDO_FULL_ADDITIONAL_PROTEINS.items():
                _add_protein(store, name, data, domain="redo_full_target")

            # Add ReDO Full drugs
            print(f"Adding {len(REDO_FULL_DRUGS)} ReDO Full drugs...")
            for name, data in REDO_FULL_DRUGS.items():
                obj = StoredObject(
                    name=name,
                    type_name="Drug",
                    metadata={
                        "brand": data.get("brand", ""),
                        "drug_class": data.get("drug_class", ""),
                        "mechanism": data.get("mechanism", ""),
                        "fda_year": data.get("fda_year", 0),
                        "drugbank_id": data.get("drugbank_id", ""),
                        "original_indication": data.get("original_indication", ""),
                        "domain": "redo_full_drug",
                    }
                )
                store.add_object(obj)

            # Add ReDO Full drug-target and protein-disease interactions
            redo_full_interactions = (
                REDO_FULL_DRUG_TARGET_INTERACTIONS +
                REDO_FULL_PROTEIN_DISEASE_ASSOCIATIONS
            )
            print(f"Adding {len(redo_full_interactions)} ReDO Full interactions...")
            _add_interactions(store, redo_full_interactions, domain="redo_full_expansion")

        except ImportError:
            pass  # ReDO Full expansion module not available

    # Step 7: Load Noetik expansion (NSCLC/CRC-focused cancer drugs + immunotherapy)
    if include_noetik_expansion:
        try:
            from data.drugs.noetik_expansion import get_noetik_expansion

            noetik_drugs, noetik_proteins, noetik_interactions = get_noetik_expansion()

            # Add Noetik proteins/targets
            print(f"Adding {len(noetik_proteins)} Noetik biomarker/target proteins...")
            for name, data in noetik_proteins.items():
                _add_protein(store, name, data, domain="noetik_target")

            # Add Noetik drugs
            print(f"Adding {len(noetik_drugs)} Noetik expansion drugs...")
            for name, data in noetik_drugs.items():
                obj = StoredObject(
                    name=name,
                    type_name="Drug",
                    metadata={
                        "brand": data.get("brand", ""),
                        "drug_class": data.get("drug_class", ""),
                        "mechanism": data.get("mechanism", ""),
                        "fda_year": data.get("fda_year", 0),
                        "drugbank_id": data.get("drugbank_id", ""),
                        "domain": "noetik_drug",
                    }
                )
                store.add_object(obj)

            # Add Noetik drug-target interactions
            print(f"Adding {len(noetik_interactions)} Noetik drug-target interactions...")
            _add_interactions(store, noetik_interactions, domain="noetik_expansion")

        except ImportError as e:
            print(f"Warning: Noetik expansion module not available: {e}")
            pass

    # Summary
    all_objects = store.list_objects(limit=10000)
    all_morphisms = store.list_morphisms(limit=10000)

    from collections import Counter
    obj_types = Counter(o.type_name for o in all_objects)
    mor_types = Counter(m.name for m in all_morphisms)

    print(f"\n[OK] Drug repurposing store created")
    print(f"  Total objects: {len(all_objects)}")
    for t, c in obj_types.most_common():
        print(f"    {t}: {c}")
    print(f"  Total morphisms: {len(all_morphisms)}")
    for t, c in mor_types.most_common(10):
        print(f"    {t}: {c}")

    return store


def load_scaled_drug_network(
    store: Optional[Category] = None,
    db_path: str = ":memory:",
    use_hetionet: bool = True,
    use_opentargets: bool = True,
    use_chembl: bool = False,
    use_dgidb: bool = False,
    use_biogrid: bool = False,
    use_reactome: bool = False,
    use_cosmic: bool = False,
    holdout_fraction: float = 0.20,
    cache_dir: str = "data/cache",
    verbose: bool = True,
) -> Tuple[Category, list]:
    """
    Load a scaled drug repurposing network from external databases.

    Starts with the curated network from create_drug_store(), then
    incrementally integrates external databases based on toggle flags.

    Args:
        store: Pre-existing store to enrich. If None, creates fresh one.
        db_path: Database path (only used if store is None).
        use_hetionet: Phase 1 -- Hetionet biomedical network.
        use_opentargets: Phase 2 -- Open Targets confidence scores.
        use_chembl: Phase 3 -- ChEMBL bioactivity data.
        use_dgidb: Phase 4 -- DGIdb drug-gene interactions.
        use_biogrid: Phase 5 -- BioGRID protein-protein interactions.
        use_reactome: Phase 6 -- Reactome pathway data.
        use_cosmic: Phase 7 -- COSMIC cancer gene census.
        holdout_fraction: Fraction of treats edges to hold out (Hetionet).
        cache_dir: Directory for cached downloads.
        verbose: Print progress messages.

    Returns:
        (store, holdout_edges) tuple where holdout_edges is a list of
        (source, target, relation, confidence) tuples from Hetionet.
    """
    from data.external.cache import DataCache
    from data.external.id_mapper import IDMapper

    cache = DataCache(cache_dir)
    id_mapper = IDMapper()
    hetionet_holdout = []

    # Step 0: Load curated network as the base
    if store is None:
        if verbose:
            print("=" * 60)
            print("KOMPOSOS-III Scaled Drug Network Loader")
            print("=" * 60)
        store = create_drug_store(db_path=db_path, include_proteins=True)

    # Populate id_mapper with existing drug DrugBank IDs
    for obj in store.list_objects(limit=10000):
        if obj.type_name == "Drug":
            dbid = obj.metadata.get("drugbank_id", "")
            if dbid:
                id_mapper.add_drug_mapping(obj.name, drugbank_id=dbid)

    # Phase 1: Hetionet
    if use_hetionet:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 1: Hetionet Integration")
            print("=" * 60)
        try:
            from data.external.hetionet_loader import load_hetionet_to_store
            id_mapper, hetionet_holdout = load_hetionet_to_store(
                store=store,
                cache=cache,
                id_mapper=id_mapper,
                holdout_fraction=holdout_fraction,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: Hetionet integration failed: {e}")

    # Phase 2: Open Targets
    if use_opentargets:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 2: Open Targets Enrichment")
            print("=" * 60)
        try:
            from data.external.opentargets_loader import enrich_with_opentargets
            enrich_with_opentargets(
                store=store,
                id_mapper=id_mapper,
                cache=cache,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: Open Targets enrichment failed: {e}")

    # Phase 3: ChEMBL
    if use_chembl:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 3: ChEMBL Bioactivity Enrichment")
            print("=" * 60)
        try:
            from data.external.chembl_loader import enrich_with_chembl
            enrich_with_chembl(
                store=store,
                id_mapper=id_mapper,
                cache=cache,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: ChEMBL enrichment failed: {e}")

    # Phase 4: DGIdb
    if use_dgidb:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 4: DGIdb Drug-Gene Interactions")
            print("=" * 60)
        try:
            from data.external.dgidb_loader import enrich_with_dgidb
            enrich_with_dgidb(
                store=store,
                id_mapper=id_mapper,
                cache=cache,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: DGIdb enrichment failed: {e}")

    # Phase 5: BioGRID
    if use_biogrid:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 5: BioGRID PPI Expansion")
            print("=" * 60)
        try:
            from data.external.biogrid_loader import enrich_with_biogrid
            enrich_with_biogrid(
                store=store,
                cache=cache,
                id_mapper=id_mapper,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: BioGRID enrichment failed: {e}")

    # Phase 6: Reactome
    if use_reactome:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 6: Reactome Pathways")
            print("=" * 60)
        try:
            from data.external.reactome_loader import enrich_with_reactome
            enrich_with_reactome(
                store=store,
                cache=cache,
                id_mapper=id_mapper,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: Reactome enrichment failed: {e}")

    # Phase 7: COSMIC
    if use_cosmic:
        if verbose:
            print("\n" + "=" * 60)
            print("Phase 7: COSMIC Cancer Gene Census")
            print("=" * 60)
        try:
            from data.external.cosmic_loader import enrich_with_cosmic
            enrich_with_cosmic(
                store=store,
                cache=cache,
                id_mapper=id_mapper,
                verbose=verbose,
            )
        except Exception as e:
            if verbose:
                print(f"  WARNING: COSMIC enrichment failed: {e}")

    # Final summary
    if verbose:
        print("\n" + "=" * 60)
        print("Scaled Network Summary")
        print("=" * 60)

        n_obj = store.count_objects()
        n_mor = store.count_morphisms()
        print(f"  Total objects:   {n_obj:,}")
        print(f"  Total morphisms: {n_mor:,}")
        print(f"  Holdout edges:   {len(hetionet_holdout)}")
        print(f"  ID mapper:       {id_mapper.stats()}")

        # Type breakdown (sample)
        all_objects = store.list_objects(limit=100000)
        from collections import Counter
        type_counts = Counter(o.type_name for o in all_objects)
        print("  Object types:")
        for t, c in type_counts.most_common():
            print(f"    {t}: {c:,}")

    return store, hetionet_holdout


def load_hetionet_network(
    db_path: str = ":memory:",
    holdout_fraction: float = 0.20,
    cache_dir: str = "data/cache",
    verbose: bool = True,
) -> Tuple[Category, list]:
    """
    Convenience function: load curated network + Hetionet only.

    This is the recommended starting point for scaled drug repurposing.

    Returns:
        (store, holdout_edges) tuple.
    """
    return load_scaled_drug_network(
        db_path=db_path,
        use_hetionet=True,
        use_opentargets=False,
        use_chembl=False,
        use_dgidb=False,
        use_biogrid=False,
        use_reactome=False,
        use_cosmic=False,
        holdout_fraction=holdout_fraction,
        cache_dir=cache_dir,
        verbose=verbose,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KOMPOSOS-III Drug Network Loader")
    parser.add_argument("--scaled", action="store_true", help="Use scaled network (Hetionet + enrichment)")
    parser.add_argument("--hetionet", action="store_true", help="Include Hetionet (Phase 1)")
    parser.add_argument("--opentargets", action="store_true", help="Include Open Targets (Phase 2)")
    parser.add_argument("--chembl", action="store_true", help="Include ChEMBL (Phase 3)")
    parser.add_argument("--dgidb", action="store_true", help="Include DGIdb (Phase 4)")
    parser.add_argument("--biogrid", action="store_true", help="Include BioGRID (Phase 5)")
    parser.add_argument("--reactome", action="store_true", help="Include Reactome (Phase 6)")
    parser.add_argument("--cosmic", action="store_true", help="Include COSMIC (Phase 7)")
    parser.add_argument("--all-phases", action="store_true", help="Enable all phases")
    args = parser.parse_args()

    if args.scaled or args.hetionet or args.all_phases:
        store, holdout = load_scaled_drug_network(
            use_hetionet=args.hetionet or args.all_phases,
            use_opentargets=args.opentargets or args.all_phases,
            use_chembl=args.chembl or args.all_phases,
            use_dgidb=args.dgidb or args.all_phases,
            use_biogrid=args.biogrid or args.all_phases,
            use_reactome=args.reactome or args.all_phases,
            use_cosmic=args.cosmic or args.all_phases,
        )
        print(f"\nHoldout edges: {len(holdout)}")
    else:
        store = create_drug_store()

        print("\nSample drugs:")
        for obj in store.list_objects(limit=200):
            if obj.type_name == "Drug":
                print(f"  - {obj.name}: {obj.metadata.get('drug_class', 'N/A')}")

        print("\nSample drug-target interactions:")
        count = 0
        for mor in store.list_morphisms(limit=500):
            if mor.metadata.get("domain") == "drug_repurposing":
                print(f"  - {mor.source_name} --[{mor.name}]--> {mor.target_name} (conf={mor.confidence:.2f})")
                count += 1
                if count >= 20:
                    break
