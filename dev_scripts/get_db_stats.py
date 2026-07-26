import sqlite3
import json
import re

conn = sqlite3.connect('data/drugs/tier1.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM objects')
obj_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM morphisms')
morph_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM morphisms WHERE provenance != 'unknown'")
prov_count = cursor.fetchone()[0]

# Extract PMIDs from provenance
cursor.execute("SELECT provenance FROM morphisms")
all_provenance = cursor.fetchall()

pmids = set()
for (prov,) in all_provenance:
    if prov and prov != 'unknown':
        # Extract PMIDs using regex
        found_pmids = re.findall(r'PMID:(\d+)', prov)
        pmids.update(found_pmids)

print(f'Objects: {obj_count}')
print(f'Morphisms: {morph_count}')
print(f'Morphisms with provenance: {prov_count}')
print(f'Unique PMIDs referenced: {len(pmids)}')

# Get type breakdown
cursor.execute("SELECT type, COUNT(*) FROM objects GROUP BY type")
type_counts = cursor.fetchall()
print('\nObject type breakdown:')
for type_name, count in sorted(type_counts):
    print(f'  {type_name}: {count}')

conn.close()
