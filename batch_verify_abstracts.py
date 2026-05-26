#!/usr/bin/env python3
"""
Batch process abstracts for manual verification.
Outputs a structured file ready for LLM review.
"""

with open('all_abstracts_verification.txt', encoding='utf-8') as f:
    content = f.read()

# Split by separator
entries = content.split('---\n')

verified_count = 0
no_abstract_count = 0

with open('abstracts_for_verification.txt', 'w', encoding='utf-8') as out:
    for entry in entries:
        if not entry.strip():
            continue

        lines = entry.strip().split('\n')
        if not lines:
            continue

        # First line is metadata
        metadata = lines[0]
        if not metadata.startswith('ROWID:'):
            continue

        # Rest is abstract
        abstract = '\n'.join(lines[1:]) if len(lines) > 1 else ""

        if 'NO_ABSTRACT' in abstract:
            no_abstract_count += 1
            continue

        if len(abstract) < 50:  # Skip very short entries
            continue

        # Extract source and target from metadata
        parts = metadata.split('|')
        if len(parts) >= 4:
            rowid = parts[0].replace('ROWID:', '')
            source = parts[1].replace('SOURCE:', '')
            target = parts[2].replace('TARGET:', '')
            pmid = parts[3].replace('PMID:', '')

            out.write(f"=== {rowid} | {source} -> {target} | PMID:{pmid} ===\n")
            out.write(f"{abstract[:500]}...\n" if len(abstract) > 500 else f"{abstract}\n")
            out.write(f"VERIFY: Does this abstract discuss {source} IN RELATION to {target}? [YES/NO/PARTIAL]\n")
            out.write("\n")
            verified_count += 1

print(f"Processed {verified_count} abstracts with text")
print(f"Skipped {no_abstract_count} with no abstract")
print(f"Output: abstracts_for_verification.txt")
