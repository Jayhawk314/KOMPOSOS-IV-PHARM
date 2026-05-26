#!/usr/bin/env python3
import requests
import time
import re

# Fetch abstract
def get_abstract(pmid, retries=3):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {'db': 'pubmed', 'id': pmid, 'retmode': 'xml', 'email': 'research@komposos.org'}

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            xml = resp.text

            if '<AbstractText>' in xml:
                start = xml.find('<AbstractText>')
                end = xml.find('</AbstractText>', start)
                if start != -1 and end != -1:
                    abstract = xml[start+14:end]
                    # Clean HTML tags
                    abstract = re.sub(r'<[^>]+>', '', abstract)
                    return abstract.strip()
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            continue
    return None

# Read candidates
with open('druggable_candidates.txt') as f:
    lines = f.readlines()

print(f"Fetching abstracts for {len(lines)} candidates...")

with open('druggable_abstracts.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines, 1):
        rowid, protein, disease, pmid = line.strip().split('|')
        print(f"[{i}/{len(lines)}] Fetching PMID:{pmid} for {protein}->{disease}")

        abstract = get_abstract(pmid)
        if abstract:
            out.write(f"ROWID:{rowid}|PROTEIN:{protein}|DISEASE:{disease}|PMID:{pmid}\n")
            out.write(f"{abstract}\n")
            out.write("---\n")
            print(f"  FETCHED ({len(abstract)} chars)")
        else:
            out.write(f"ROWID:{rowid}|PROTEIN:{protein}|DISEASE:{disease}|PMID:{pmid}\n")
            out.write(f"NO_ABSTRACT_AVAILABLE\n")
            out.write("---\n")
            print(f"  NO ABSTRACT")

        time.sleep(0.4)

print(f"\nWrote abstracts to druggable_abstracts.txt")
