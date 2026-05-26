import json, sqlite3
from pathlib import Path

# Load source data
depmap = json.load(open('data/proteins/depmap_essentiality.json'))
tcga = json.load(open('data/proteins/tcga_expression.json'))
gtex = json.load(open('data/proteins/gtex_expression.json'))

print(f'TCGA proteins: {len(tcga)}, DepMap proteins: {len(depmap)}, GTEx proteins: {len(gtex)}')

# Load existing edges  
conn = sqlite3.connect('data/drugs/tier1.db')
cur = conn.cursor()
cur.execute('SELECT source_name, target_name FROM morphisms')
existing = set((r[0], r[1]) for r in cur.fetchall())
conn.close()
print(f'Existing edges in tier1.db: {len(existing)}')

diseases = ['AML', 'NSCLC', 'Breast_Cancer', 'Colorectal_Cancer', 'Melanoma', 'Pancreatic_Cancer', 'Lymphoma', 'Ovarian_Cancer', 'Prostate_Cancer', 'Renal_Cell_Carcinoma', 'Glioblastoma', 'Thyroid_Cancer', 'Hepatocellular_Carcinoma', 'Gastric_Cancer', 'Head_Neck_Cancer', 'Multiple_Myeloma']

edges_tcga = 0
edges_depmap = 0
edges_gtex = 0
edges = {}

# TCGA
for prot, dz_expr in tcga.items():
    for dz, expr in dz_expr.items():
        if expr >= 6.0:
            k = (prot, dz)
            if k not in existing:
                conf = min(0.85, 0.60 + expr/10)
                edges[k] = {
                    'source': prot, 'target': dz, 'name': 'associated_with',
                    'confidence': round(conf, 3),
                    'provenance': f'TCGA:{dz}(expr={expr:.1f})',
                    'metadata': {'source_file': 'TCGA', 'evidence_type': 'Expression'}
                }
                edges_tcga += 1

# DepMap
for prot, ess in depmap.items():
    if ess >= 0.7:
        for dz in diseases:
            k = (prot, dz)
            if k not in existing and k not in edges:
                conf = min(0.75, 0.55 + ess*0.20)
                edges[k] = {
                    'source': prot, 'target': dz, 'name': 'associated_with',
                    'confidence': round(conf, 3),
                    'provenance': f'DepMap:essentiality({ess:.2f})',
                    'metadata': {'source_file': 'DepMap', 'evidence_type': 'Essentiality'}
                }
                edges_depmap += 1

# GTEx
tissue_map = {
    'Bone_Marrow': ['AML', 'Lymphoma', 'Multiple_Myeloma'],
    'Lung': ['NSCLC'],
    'Breast': ['Breast_Cancer'],
    'Colon': ['Colorectal_Cancer'],
    'Skin': ['Melanoma'],
    'Pancreas': ['Pancreatic_Cancer'],
    'Liver': ['Hepatocellular_Carcinoma'],
    'Prostate': ['Prostate_Cancer'],
    'Kidney': ['Renal_Cell_Carcinoma'],
    'Brain': ['Glioblastoma'],
}
for prot, tissues in gtex.items():
    for tissue, expr in tissues.items():
        if expr >= 5.0 and tissue in tissue_map:
            for dz in tissue_map[tissue]:
                k = (prot, dz)
                if k not in existing and k not in edges:
                    conf = 0.55 + min(0.15, expr/20)
                    edges[k] = {
                        'source': prot, 'target': dz, 'name': 'associated_with',
                        'confidence': round(conf, 3),
                        'provenance': f'GTEx:{tissue}(expr={expr:.1f})',
                        'metadata': {'source_file': 'GTEx', 'evidence_type': 'Normal Tissue Expression'}
                    }
                    edges_gtex += 1

print('')
print('New edges built:')
print('  TCGA:    ' + str(edges_tcga))
print('  DepMap:  ' + str(edges_depmap))
print('  GTEx:    ' + str(edges_gtex))
print('  Total:   ' + str(len(edges)))

# Save manifest
manifest = {
    'version': '2026-05-24-protein-disease-expansion',
    'source': 'DepMap, TCGA, GTEx',
    'description': 'Protein->Disease edges derived from existing data sources to complete mechanistic paths',
    'count': len(edges),
    'morphisms': list(edges.values())
}

Path('scripts').mkdir(exist_ok=True)
with open('scripts/protein_disease_edges_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print('')
print('[SUCCESS] Manifest saved: scripts/protein_disease_edges_manifest.json')
print('')
print('Expected impact:')
print('  Current Protein->Disease edges: ~1052')
print('  New edges:                      ' + str(len(edges)))
print('  After merge:                    ~' + str(1052 + len(edges)))
print('  Coverage of 7320 possible:      ' + str(round(100 * (1052 + len(edges)) / 7320, 1)) + '%')
