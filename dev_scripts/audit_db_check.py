from data.store import KomposOSStore
from collections import Counter

store = KomposOSStore('data/drugs/tier1.db')
objs = store.list_objects(limit=1000)
morphs = store.list_morphisms(limit=1000)

drugs = [o for o in objs if o.type_name == 'Drug']
diseases = [o for o in objs if o.type_name == 'Disease']

print(f"Total objects: {len(objs)}")
print(f"Total morphisms: {len(morphs)}")
print(f"Drugs: {len(drugs)}")
print(f"Diseases: {len(diseases)}")
print()

# Check for Drug->Disease edges
drug_names = {d.name for d in drugs}
disease_names = {d.name for d in diseases}

drug_disease_edges = [
    m for m in morphs
    if m.source_name in drug_names and m.target_name in disease_names
]

print(f"Drug->Disease edges: {len(drug_disease_edges)}")
print("\nDrug->Disease edge types:")
edge_types = Counter(m.name for m in drug_disease_edges)
for edge_type, count in edge_types.most_common():
    print(f"  {edge_type}: {count}")

print("\nAll Drug->Disease edges:")
for m in drug_disease_edges:
    pmid = m.metadata.get('PMID', 'no PMID')
    print(f"  {m.name}: {m.source_name} -> {m.target_name} (PMID: {pmid})")

# Check for PMIDs
morphs_with_pmid = [m for m in morphs if m.metadata.get('PMID')]
print(f"\nMorphisms with PMID: {len(morphs_with_pmid)}/{len(morphs)}")

# Check unreferenced objects
all_referenced = set()
for m in morphs:
    all_referenced.add(m.source_name)
    all_referenced.add(m.target_name)

unreferenced = [o.name for o in objs if o.name not in all_referenced]
print(f"\nUnreferenced objects: {len(unreferenced)}")
if unreferenced:
    print("  " + ", ".join(unreferenced))

# Check for missing endpoints
all_morphism_endpoints = set()
for m in morphs:
    all_morphism_endpoints.add(m.source_name)
    all_morphism_endpoints.add(m.target_name)

obj_names = {o.name for o in objs}
missing_endpoints = all_morphism_endpoints - obj_names

print(f"\nMissing endpoint objects: {len(missing_endpoints)}")
if missing_endpoints:
    print("  " + ", ".join(sorted(missing_endpoints)))
