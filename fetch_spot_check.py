#!/usr/bin/env python3
import requests
import time
import re

def get_abstract(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {'db': 'pubmed', 'id': pmid, 'retmode': 'xml', 'email': 'research@komposos.org'}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        xml = resp.text
        if '<AbstractText>' in xml:
            start = xml.find('<AbstractText>')
            end = xml.find('</AbstractText>', start)
            if start != -1 and end != -1:
                abstract = xml[start+14:end]
                abstract = re.sub(r'<[^>]+>', '', abstract)
                return abstract.strip()
    except:
        pass
    return None

with open('spot_check_sample.txt') as f:
    lines = [l.strip() for l in f if '|' in l]

with open('spot_check_abstracts.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines, 1):
        rowid, src, tgt, pmid = line.split('|')
        print(f"[{i}/{len(lines)}] Fetching PMID:{pmid} for {src}->{tgt}")

        abstract = get_abstract(pmid)
        if abstract:
            out.write(f"ROWID:{rowid}|SOURCE:{src}|TARGET:{tgt}|PMID:{pmid}\n")
            out.write(f"{abstract}\n")
            out.write("---\n")
            print(f"  FETCHED")
        else:
            out.write(f"ROWID:{rowid}|SOURCE:{src}|TARGET:{tgt}|PMID:{pmid}\n")
            out.write(f"NO_ABSTRACT\n")
            out.write("---\n")
            print(f"  NO ABSTRACT")

        time.sleep(0.4)

print(f"\nWrote to spot_check_abstracts.txt")
