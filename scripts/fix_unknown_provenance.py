# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

import json, sqlite3, requests, time

conn = sqlite3.connect('data/drugs/tier1.db')
cur = conn.cursor()
cur.execute("SELECT rowid, source_name, target_name, name FROM morphisms WHERE provenance = 'unknown'")
unknowns = cur.fetchall()
conn.close()

print(f'Querying PubMed for {len(unknowns)} unknown-provenance edges...')
print(f'Estimated time: {len(unknowns) * 0.4 / 60:.0f} minutes')

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

results = []
found = 0
not_found = 0

for i, (rowid, src, tgt, rel) in enumerate(unknowns):
    if i % 50 == 0 and i > 0:
        print(f'  Progress: {i}/{len(unknowns)} (found: {found}, not found: {not_found})')

    # Query: "PROTEIN_A" AND "PROTEIN_B" AND (activates OR inhibits OR phosphorylates)
    query = f'"{src}" AND "{tgt}"'

    try:
        resp = requests.get(
            PUBMED_SEARCH,
            params={'db': 'pubmed', 'term': query, 'retmax': 2, 'retmode': 'json'},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            if pmids:
                prov = ', '.join(f'PMID:{p}' for p in pmids[:2])
                results.append({'rowid': rowid, 'src': src, 'tgt': tgt, 'rel': rel, 'provenance': prov})
                found += 1
            else:
                not_found += 1
        else:
            not_found += 1

        time.sleep(0.35)

    except Exception as e:
        not_found += 1

print(f'')
print(f'Results: {found} found, {not_found} not found')

# Save results
with open('scripts/unknown_edge_pmids.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'Saved: scripts/unknown_edge_pmids.json')

# Apply to DB
if results:
    conn = sqlite3.connect('data/drugs/tier1.db')
    cur = conn.cursor()
    for r in results:
        cur.execute('UPDATE morphisms SET provenance = ? WHERE rowid = ?', (r['provenance'], r['rowid']))
    conn.commit()
    conn.close()
    print(f'Updated {len(results)} edges in tier1.db with PMIDs')
