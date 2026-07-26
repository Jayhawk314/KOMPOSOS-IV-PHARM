from data.store import KomposOSStore
import json

store = KomposOSStore('data/drugs/tier1.db')
morphs = store.list_morphisms(limit=1000)

print(f"Total morphisms: {len(morphs)}")
print()

# Check different ways PMIDs might be stored
pmid_keys = ['PMID', 'pmid', 'pmids', 'PMIDs', 'pubmed', 'PubMed']
counts = {key: 0 for key in pmid_keys}

morphs_with_any_pmid = []

for m in morphs:
    if m.metadata:
        has_pmid = False
        for key in pmid_keys:
            if key in m.metadata and m.metadata[key]:
                counts[key] += 1
                has_pmid = True
        if has_pmid:
            morphs_with_any_pmid.append(m)

print("PMID key variants found:")
for key, count in counts.items():
    if count > 0:
        print(f"  {key}: {count}")

if counts['PMID'] > 0 or counts['pmid'] > 0:
    print()
    print("Sample morphisms with PMIDs:")
    for m in morphs_with_any_pmid[:10]:
        print(f"  {m.name}: {m.source_name} -> {m.target_name}")
        print(f"    metadata: {m.metadata}")

# Check provenance field
provenance_values = {}
for m in morphs:
    if m.provenance and m.provenance != "unknown":
        if m.provenance not in provenance_values:
            provenance_values[m.provenance] = []
        provenance_values[m.provenance].append(m)

print()
print(f"Morphisms with non-'unknown' provenance: {sum(len(v) for v in provenance_values.values())}")
if provenance_values:
    print("Provenance values:")
    for prov, morph_list in sorted(provenance_values.items()):
        print(f"  {prov}: {len(morph_list)} morphisms")
        # Show sample
        for m in morph_list[:2]:
            print(f"    {m.name}: {m.source_name} -> {m.target_name}")
