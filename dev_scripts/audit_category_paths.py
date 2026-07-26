from validation.repurposing_benchmark import load_full_typed_view, drug_disease_pairs

DB_PATH = "data/drugs/tier1.db"

# Load with and without direct labels
category_with_labels, _ = load_full_typed_view(DB_PATH)
category_no_labels, _ = load_full_typed_view(DB_PATH, remove_direct_labels=True)

_, _, positives = drug_disease_pairs(category_with_labels)

protein_types = {
    "Receptor", "Signaling", "Transcription", "TumorSuppressor",
    "Apoptosis", "Oncogene", "DNARepair", "CellCycle", "Regulator",
    "Splicing", "Epigenetic", "Metabolic", "Structural", "Chaperone",
    "Transporter", "Ligand", "Enzyme", "Marker", "Protein"
}

print(f"Checking {len(positives)} positive pairs for mechanistic paths\n")

for drug, disease in sorted(positives)[:3]:  # Check first 3 in detail
    print(f"\n{drug} -> {disease}")
    print("="*60)

    # Find paths with the graph that has direct labels removed
    paths = category_no_labels.find_paths(drug, disease, max_length=4)
    print(f"Total paths found: {len(paths)}")

    protein_paths = []
    for i, path in enumerate(paths[:10]):  # Examine up to 10 paths
        if hasattr(path, 'morphism_ids') and len(path.morphism_ids) >= 2:
            print(f"\nPath {i+1}: {len(path.morphism_ids)} morphisms")
            for mor_id in path.morphism_ids:
                print(f"  {mor_id}")

            # Check if first intermediate is a protein
            first_mor = path.morphism_ids[0]
            if '->' in first_mor:
                intermediate = first_mor.split('->')[1].strip()
                obj = category_no_labels.get(intermediate)
                if obj:
                    print(f"  First intermediate: {intermediate} (type: {obj.type_name})")
                    if obj.type_name in protein_types:
                        protein_paths.append(path)
                        print("  [YES] This is a mechanistic path!")

    print(f"\nMechanistic paths: {len(protein_paths)}")

# Summary for all positives
print("\n" + "="*70)
print("SUMMARY FOR ALL POSITIVES")
print("="*70)

for drug, disease in sorted(positives):
    paths = category_no_labels.find_paths(drug, disease, max_length=4)
    has_protein_path = False
    protein_intermediates = []

    for path in paths:
        if hasattr(path, 'morphism_ids') and len(path.morphism_ids) >= 2:
            first_mor = path.morphism_ids[0]
            if '->' in first_mor:
                intermediate = first_mor.split('->')[1].strip()
                obj = category_no_labels.get(intermediate)
                if obj and obj.type_name in protein_types:
                    has_protein_path = True
                    if intermediate not in protein_intermediates:
                        protein_intermediates.append(intermediate)

    status = "[YES]" if has_protein_path else "[NO]"
    print(f"{status} {drug:20} -> {disease:20}  paths: {len(paths):3}  proteins: {len(protein_intermediates)}")
