from data.store import KomposOSStore
from collections import defaultdict

store = KomposOSStore('data/drugs/tier1.db')
objs = store.list_objects(limit=1000)
morphs = store.list_morphisms(limit=1000)

drugs = {o.name for o in objs if o.type_name == 'Drug'}
diseases = {o.name for o in objs if o.type_name == 'Disease'}
proteins = {o.name for o in objs if o.type_name == 'Protein'}

# Get positive labels
positive_labels = [
    (m.source_name, m.target_name)
    for m in morphs
    if m.source_name in drugs and m.target_name in diseases
]

print(f"Checking mechanistic paths for {len(positive_labels)} positive labels\n")

# Build adjacency
drug_to_protein = defaultdict(list)
protein_to_disease = defaultdict(list)

for m in morphs:
    if m.source_name in drugs and m.target_name in proteins:
        drug_to_protein[m.source_name].append((m.target_name, m.name))
    if m.source_name in proteins and m.target_name in diseases:
        protein_to_disease[m.source_name].append((m.target_name, m.name))

# Check each positive for mechanistic paths
for drug, disease in positive_labels:
    paths = []
    if drug in drug_to_protein:
        for protein, edge1 in drug_to_protein[drug]:
            if protein in protein_to_disease:
                for target_disease, edge2 in protein_to_disease[protein]:
                    if target_disease == disease:
                        paths.append((drug, edge1, protein, edge2, disease))

    print(f"{drug} -> {disease}: {len(paths)} paths")
    if len(paths) == 0:
        print("  WARNING: NO MECHANISTIC PATHS")
    else:
        for path in paths[:3]:  # Show up to 3 paths
            print(f"  {path[0]} --{path[1]}--> {path[2]} --{path[3]}--> {path[4]}")

print("\n" + "="*70)
positives_with_paths = sum(1 for drug, disease in positive_labels
                           if any(protein in protein_to_disease and
                                  disease in [d for d, _ in protein_to_disease[protein]]
                                  for protein, _ in drug_to_protein[drug]))
print(f"Positives with mechanistic paths: {positives_with_paths}/{len(positive_labels)}")
