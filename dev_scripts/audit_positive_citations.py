from validation.repurposing_benchmark import load_full_typed_view, drug_disease_pairs
from data.store import KomposOSStore

DB_PATH = "data/drugs/tier1.db"

store = KomposOSStore(DB_PATH)
category, _ = load_full_typed_view(DB_PATH, remove_direct_labels=True)
_, _, positives = drug_disease_pairs(load_full_typed_view(DB_PATH)[0])
all_morphisms = store.list_morphisms(limit=1000)

protein_types = {
    "Receptor", "Signaling", "Transcription", "TumorSuppressor",
    "Apoptosis", "Oncogene", "DNARepair", "CellCycle", "Regulator",
    "Splicing", "Epigenetic", "Metabolic", "Structural", "Chaperone",
    "Transporter", "Ligand", "Enzyme", "Marker", "Protein"
}

print(f"Checking citation coverage for {len(positives)} positive pairs\n")
print("="*80)

uncited_positives = []

for drug, disease in sorted(positives):
    paths = category.find_paths(drug, disease, max_length=4)

    # Find mechanistic paths
    mechanistic_paths = []
    for path in paths:
        if hasattr(path, 'morphism_ids') and len(path.morphism_ids) >= 2:
            first_mor = path.morphism_ids[0]
            if '->' in first_mor:
                intermediate = first_mor.split('->')[1].strip()
                obj = category.get(intermediate)
                if obj and obj.type_name in protein_types:
                    mechanistic_paths.append(path)

    # Check if any mechanistic path is fully cited
    has_fully_cited_path = False
    for path in mechanistic_paths:
        all_cited = True
        for mor_id in path.morphism_ids:
            # Get the morphism object
            # Morphism IDs are in format "name:source->target"
            if ':' in mor_id:
                parts = mor_id.split(':', 1)
                name = parts[0]
                endpoints = parts[1].split('->')
                if len(endpoints) == 2:
                    source = endpoints[0].strip()
                    target = endpoints[1].strip()

                    # Check provenance
                    found = False
                    has_pmid = False
                    for m in all_morphisms:
                        if (m.name == name and
                            m.source_name == source and
                            m.target_name == target):
                            found = True
                            if m.provenance and m.provenance != "unknown" and "PMID" in m.provenance:
                                has_pmid = True
                            break

                    if not has_pmid:
                        all_cited = False
                        break

        if all_cited:
            has_fully_cited_path = True
            break

    status = "[CITED]" if has_fully_cited_path else "[UNCITED]"
    print(f"{status} {drug:20} -> {disease:20}  (paths: {len(mechanistic_paths)})")

    if not has_fully_cited_path and mechanistic_paths:
        # Show the first mechanistic path
        path = mechanistic_paths[0]
        print(f"  First mechanistic path:")
        for mor_id in path.morphism_ids:
            # Check if this morphism has a PMID
            if ':' in mor_id:
                parts = mor_id.split(':', 1)
                name = parts[0]
                endpoints = parts[1].split('->')
                if len(endpoints) == 2:
                    source = endpoints[0].strip()
                    target = endpoints[1].strip()

                    prov = "unknown"
                    for m in all_morphisms:
                        if (m.name == name and
                            m.source_name == source and
                            m.target_name == target):
                            prov = m.provenance
                            break

                    pmid_marker = "" if "PMID" in prov else " [NO PMID]"
                    print(f"    {mor_id}{pmid_marker}")

        uncited_positives.append((drug, disease))

print()
print("="*80)
print(f"Positives with fully cited mechanistic paths: {len(positives) - len(uncited_positives)}/{len(positives)}")
if uncited_positives:
    print(f"\nPositives WITHOUT fully cited paths: {len(uncited_positives)}")
    for drug, disease in uncited_positives:
        print(f"  {drug} -> {disease}")
