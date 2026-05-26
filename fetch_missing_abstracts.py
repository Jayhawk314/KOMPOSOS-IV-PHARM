#!/usr/bin/env python3
import re
import requests
import time

# Read candidate PMIDs
with open('candidate_pmids.txt') as f:
    candidates = {}
    for line in f:
        if line.strip():
            rowid, protein, disease, pmid = line.strip().split('|')
            candidates[pmid] = (rowid, protein, disease)

# Read already fetched PMIDs
with open('abstracts_to_verify.txt', encoding='utf-8') as f:
    content = f.read()
    fetched = set(re.findall(r'PMID:(\d+)', content))

# Find missing
missing = set(candidates.keys()) - fetched
print(f"Need to fetch {len(missing)} missing abstracts...")

# Fetch abstract with retries
def get_abstract(pmid, retries=3):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {'db': 'pubmed', 'id': pmid, 'retmode': 'xml', 'email': 'research@komposos.org'}

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            xml = resp.text

            # Try to extract abstract
            if '<AbstractText>' in xml:
                start = xml.find('<AbstractText>')
                end = xml.find('</AbstractText>', start)
                if start != -1 and end != -1:
                    abstract = xml[start+14:end]
                    # Clean HTML tags
                    abstract = re.sub(r'<[^>]+>', '', abstract)
                    return abstract.strip()

            # No abstract found
            return None

        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)
            continue

    return None

# Fetch missing abstracts
with open('missing_abstracts.txt', 'w', encoding='utf-8') as out:
    for i, pmid in enumerate(sorted(missing), 1):
        rowid, protein, disease = candidates[pmid]
        print(f"[{i}/{len(missing)}] Fetching PMID:{pmid} for {protein}->{disease}")

        abstract = get_abstract(pmid)
        if abstract:
            out.write(f"ROWID:{rowid}|PROTEIN:{protein}|DISEASE:{disease}|PMID:{pmid}\n")
            out.write(f"{abstract}\n")
            out.write("---\n")
            print(f"  FETCHED ({len(abstract)} chars)")
        else:
            # Record failed fetch
            out.write(f"ROWID:{rowid}|PROTEIN:{protein}|DISEASE:{disease}|PMID:{pmid}\n")
            out.write(f"NO_ABSTRACT_AVAILABLE\n")
            out.write("---\n")
            print(f"  NO ABSTRACT AVAILABLE")

        time.sleep(0.4)  # Rate limit

print(f"\nWrote missing abstracts to missing_abstracts.txt")
