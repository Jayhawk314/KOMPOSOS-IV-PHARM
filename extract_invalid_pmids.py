#!/usr/bin/env python3
"""Extract invalid PMIDs from final_verification_results.txt"""

with open("final_verification_results.txt", "r") as f:
    lines = f.readlines()

invalid_entries = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue

    parts = line.split("|")
    if len(parts) >= 5:
        rowid = parts[0]
        source = parts[1]
        target = parts[2]
        pmid = parts[3]
        decision = parts[4]

        if decision in ["NO", "PARTIAL"]:
            reason = parts[5] if len(parts) > 5 else ""
            invalid_entries.append({
                "rowid": rowid,
                "source": source,
                "target": target,
                "pmid": pmid,
                "decision": decision,
                "reason": reason
            })

print(f"Found {len(invalid_entries)} invalid PMID entries:\n")
for entry in invalid_entries:
    print(f"ROWID {entry['rowid']}: {entry['source']} -> {entry['target']}")
    print(f"  PMID: {entry['pmid']} ({entry['decision']})")
    print(f"  Reason: {entry['reason']}")
    print()

# Get unique PMIDs
invalid_pmids = set(e['pmid'] for e in invalid_entries)
print(f"\nUnique invalid PMIDs to remove: {len(invalid_pmids)}")
print(", ".join(sorted(invalid_pmids)))
