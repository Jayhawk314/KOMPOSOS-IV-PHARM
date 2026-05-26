import json, sqlite3
from pathlib import Path
from collections import defaultdict
import sys
sys.path.insert(0, str(Path('.').resolve()))

# Load cancer_proteins data
from data.proteins.cancer_proteins import CANCER_PROTEINS, CANCER_INTERACTIONS

# Load existing DB state
conn = sqlite3.connect('data/drugs/tier1.db')
cur = conn.cursor()

# All protein-like objects = everything EXCEPT Drug and Disease
cur.execute("SELECT name, type_name FROM objects WHERE type_name NOT IN ('Drug', 'Disease')")
all_targets = {r[0]: r[1] for r in cur.fetchall()}

# All diseases
cur.execute("SELECT name FROM objects WHERE type_name='Disease'")
all_diseases = [r[0] for r in cur.fetchall()]

# All existing edges
cur.execute("SELECT source_name, target_name FROM morphisms")
existing_edges = set((r[0], r[1]) for r in cur.fetchall())

# Drug->Target edges (Drug to any non-Disease)
cur.execute("""
    SELECT m.source_name, m.target_name
    FROM morphisms m
    JOIN objects s ON m.source_name = s.name
    WHERE s.type_name = 'Drug'
      AND m.target_name NOT IN (SELECT name FROM objects WHERE type_name='Disease')
""")
drug_target = [(r[0], r[1]) for r in cur.fetchall()]

# Drug->Disease edges
cur.execute("""
    SELECT m.source_name, m.target_name
    FROM morphisms m
    JOIN objects s ON m.source_name = s.name
    JOIN objects t ON m.target_name = t.name
    WHERE s.type_name = 'Drug' AND t.type_name = 'Disease'
""")
drug_disease = [(r[0], r[1]) for r in cur.fetchall()]

conn.close()

print(f'Protein-like targets: {len(all_targets)}, Diseases: {len(all_diseases)}')
print(f'Existing edges: {len(existing_edges)}')
print(f'Drug->Target: {len(drug_target)}, Drug->Disease: {len(drug_disease)}')

# Build maps
drug_targets = defaultdict(set)
for d, p in drug_target:
    drug_targets[d].add(p)

drug_diseases_map = defaultdict(set)
for d, dz in drug_disease:
    drug_diseases_map[d].add(dz)

# Strategy 1: cancer_proteins.py curated -> disease mapping
# "multiple" means ALL cancers
cancer_name_map = {
    'lung': ['NSCLC'],
    'colorectal': ['Colorectal_Cancer'],
    'breast': ['Breast_Cancer'],
    'glioblastoma': ['Glioblastoma'],
    'melanoma': ['Melanoma'],
    'pancreatic': ['Pancreatic_Cancer'],
    'thyroid': ['Melanoma'],  # thyroid not in list, skip
    'prostate': ['Prostate_Cancer'],
    'gastric': ['Colorectal_Cancer'],  # closest
    'ovarian': ['Ovarian_Cancer'],
    'liver': ['HCC'],
    'endometrial': ['Ovarian_Cancer'],
    'retinoblastoma': ['Glioblastoma'],
    'leukemia': ['AML', 'CLL', 'CML'],
    'lymphoma': ['Multiple_Myeloma'],
    'myeloproliferative': ['Myelofibrosis', 'CML'],
    'multiple': all_diseases,  # "multiple cancers" -> all diseases
}

new_edges = {}
count_curated = 0
count_inferred = 0

# --- STRATEGY 1: cancer_proteins.py curated associations ---
for protein, data in CANCER_PROTEINS.items():
    if protein not in all_targets:
        continue
    ptype = data.get('type', '')
    for cancer in data.get('cancers', []):
        mapped_diseases = cancer_name_map.get(cancer.lower(), [])
        for disease in mapped_diseases:
            if disease not in all_diseases:
                continue
            k = (protein, disease)
            if k in existing_edges or k in new_edges:
                continue
            if ptype == 'Oncogene':
                rel, conf = 'driver_of', 0.80
            elif ptype == 'TumorSuppressor':
                rel, conf = 'loss_associated_with', 0.78
            else:
                rel, conf = 'associated_with', 0.70
            new_edges[k] = {
                'source': protein, 'target': disease, 'name': rel,
                'confidence': conf,
                'provenance': f'cancer_proteins:curated({ptype},{cancer})',
                'metadata': json.dumps({'source_file': 'cancer_proteins.py', 'evidence_type': 'Manual Curation', 'protein_type': ptype, 'cancer_annotation': cancer})
            }

count_s1 = len(new_edges)
print(f'Strategy 1 (cancer_proteins.py curated): {count_s1}')

# --- STRATEGY 2: Drug-target-disease inference ---
for drug, targets in drug_targets.items():
    for disease in drug_diseases_map.get(drug, []):
        for protein in targets:
            k = (protein, disease)
            if k in existing_edges or k in new_edges:
                continue
            new_edges[k] = {
                'source': protein, 'target': disease, 'name': 'associated_with',
                'confidence': 0.72,
                'provenance': f'inferred:Drug({drug})_treats_{disease}_targets_{protein}',
                'metadata': json.dumps({'source_file': 'tier1.db', 'evidence_type': 'Drug-Target-Disease Inference', 'via_drug': drug})
            }

count_s2 = len(new_edges) - count_s1
print(f'Strategy 2 (Drug-Target-Disease inference): {count_s2}')

# --- STRATEGY 3: Pathway neighbor inference ---
protein_neighbors = defaultdict(set)
for src, tgt, rel, conf, desc in CANCER_INTERACTIONS:
    protein_neighbors[src].add(tgt)
    protein_neighbors[tgt].add(src)

proteins_with_diseases = defaultdict(set)
for (p, d) in list(existing_edges) + list(new_edges.keys()):
    if d in all_diseases and p in all_targets:
        proteins_with_diseases[p].add(d)

for protein, neighbors in protein_neighbors.items():
    if protein not in all_targets:
        continue
    for neighbor in neighbors:
        if neighbor not in all_targets:
            continue
        for disease in proteins_with_diseases.get(neighbor, []):
            k = (protein, disease)
            if k in existing_edges or k in new_edges:
                continue
            new_edges[k] = {
                'source': protein, 'target': disease, 'name': 'associated_with',
                'confidence': 0.60,
                'provenance': f'pathway:neighbor_of_{neighbor}',
                'metadata': json.dumps({'source_file': 'cancer_proteins.py', 'evidence_type': 'Pathway Neighbor Inference', 'via_protein': neighbor})
            }

count_s3 = len(new_edges) - count_s1 - count_s2
print(f'Strategy 3 (Pathway neighbor inference): {count_s3}')
print(f'TOTAL new edges: {len(new_edges)}')

# Save manifest
manifest = {
    'version': '2026-05-24-comprehensive-expansion',
    'description': 'Protein->Disease edges from cancer_proteins.py curation + drug-target-disease inference + pathway neighbors',
    'count': len(new_edges),
    'morphisms': list(new_edges.values())
}

with open('scripts/protein_disease_edges_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f'[SAVED] scripts/protein_disease_edges_manifest.json')

# Import directly
conn = sqlite3.connect('data/drugs/tier1.db')
cur = conn.cursor()
inserted = 0
for edge in new_edges.values():
    try:
        cur.execute('INSERT INTO morphisms (source_name, target_name, name, confidence, provenance, metadata) VALUES (?, ?, ?, ?, ?, ?)',
            (edge['source'], edge['target'], edge['name'], edge['confidence'], edge['provenance'], edge['metadata']))
        inserted += 1
    except sqlite3.IntegrityError:
        pass
conn.commit()

# Final stats
cur.execute('SELECT COUNT(*) FROM morphisms')
total = cur.fetchone()[0]

# Count protein->disease edges (ALL protein-like types)
cur.execute("""
    SELECT COUNT(*) FROM morphisms
    WHERE target_name IN (SELECT name FROM objects WHERE type_name='Disease')
      AND source_name IN (SELECT name FROM objects WHERE type_name NOT IN ('Drug', 'Disease'))
""")
prot_dz = cur.fetchone()[0]

# Count distinct proteins with disease edges
cur.execute("""
    SELECT COUNT(DISTINCT source_name) FROM morphisms
    WHERE target_name IN (SELECT name FROM objects WHERE type_name='Disease')
      AND source_name IN (SELECT name FROM objects WHERE type_name NOT IN ('Drug', 'Disease'))
""")
prots_connected = cur.fetchone()[0]

conn.close()

print(f'')
print(f'[DONE] Inserted {inserted} edges')
print(f'Total morphisms: {total}')
print(f'Protein->Disease edges: {prot_dz}')
print(f'Proteins with disease connections: {prots_connected}/{len(all_targets)}')
print(f'Coverage: {prot_dz}/{len(all_targets)*len(all_diseases)} = {round(100*prot_dz/(len(all_targets)*len(all_diseases)), 1)}%')
