#!/usr/bin/env python3
"""Apply PubChem corrections to drug_properties.py."""

import json
import re

# Load corrections
with open("scripts/pubchem_corrections.json") as f:
    data = json.load(f)

corrections = data["corrections"]

# Read the file
with open("data/drugs/drug_properties.py") as f:
    content = f.read()

for drug, diffs in corrections.items():
    # Find the line for this drug
    # Pattern: "DrugName": {"mw": X, "logP": Y, "hbd": Z, "hba": W, ...}
    escaped = re.escape(f'"{drug}"')
    pattern = rf'({escaped}:\s*\{{"mw": )([\d.]+)(, "logP": )([-\d.]+)(, "hbd": )(\d+)(, "hba": )(\d+)(.*?"cid": )(\d+)'

    match = re.search(pattern, content)
    if not match:
        print(f"WARNING: Could not find {drug} in file!")
        continue

    old_line = match.group(0)

    mw = match.group(2)
    logP = match.group(4)
    hbd = match.group(6)
    hba = match.group(8)
    cid = match.group(10)

    new_mw = str(diffs["mw"]["new"]) if "mw" in diffs else mw
    new_logP = str(diffs["logP"]["new"]) if "logP" in diffs else logP
    new_hbd = str(diffs["hbd"]["new"]) if "hbd" in diffs else hbd
    new_hba = str(diffs["hba"]["new"]) if "hba" in diffs else hba
    new_cid = str(diffs["cid"]["new"]) if "cid" in diffs else cid

    new_line = (
        match.group(1) + new_mw +
        match.group(3) + new_logP +
        match.group(5) + new_hbd +
        match.group(7) + new_hba +
        match.group(9) + new_cid
    )

    content = content.replace(old_line, new_line)
    changed = []
    if "mw" in diffs: changed.append(f"mw {mw}->{new_mw}")
    if "logP" in diffs: changed.append(f"logP {logP}->{new_logP}")
    if "hbd" in diffs: changed.append(f"hbd {hbd}->{new_hbd}")
    if "hba" in diffs: changed.append(f"hba {hba}->{new_hba}")
    if "cid" in diffs: changed.append(f"cid {cid}->{new_cid}")
    print(f"  {drug}: {', '.join(changed)}")

# Update the docstring to reflect PubChem verification
old_doc = "Properties sourced from DrugBank, PubChem, and published literature."
new_doc = "Properties verified against PubChem PUG REST API (2026-05-13).\nOriginal values from DrugBank; 46/68 drugs corrected via PubChem CID lookup."
content = content.replace(old_doc, new_doc)

# Write back
with open("data/drugs/drug_properties.py", "w") as f:
    f.write(content)

print(f"\nApplied {len(corrections)} corrections to data/drugs/drug_properties.py")
