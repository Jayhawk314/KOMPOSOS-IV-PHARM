#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
READ-ONLY re-audit of the already-injected "Action-Verified" provenance.

Re-scores each stored proof sentence in data/action_verified_provenance.json
with the stricter matcher (word-boundary symbol matching + relation-aware
polarity check) from verify_triplet_abstracts.py. Reports how many of the 626
proofs survive. Does NOT touch tier1.db, the manifest, or the network.

Categories:
- PASS                      : both terms word-boundary match, keyword present, no polarity conflict
- SUBSTRING_FALSE_POSITIVE  : source or target only matched as a substring (e.g. MET in 'meta-analysis')
- POLARITY_CONFLICT         : opposite-polarity cue present (sentence may assert the reverse)
- KEYWORD_LOST              : terms match but action keyword no longer matches at a word boundary
"""

import json
from collections import Counter
from pathlib import Path

from verify_triplet_abstracts import find_proof_sentence, _term_present

VERIFIED_DATA_PATH = "data/action_verified_provenance.json"
REPORT_PATH = "data/action_verified_audit.json"


def categorize(entry: dict) -> str:
    src = entry["source"]
    tgt = entry["target"]
    rel = entry["relation"]
    sent = entry.get("proof_sentence", "") or ""

    s_name = src.replace("_", " ")
    t_name = tgt.replace("_", " ")

    # 1. Did the node names actually whole-word match (vs. spurious substring)?
    if not (_term_present(s_name, sent) and _term_present(t_name, sent)):
        return "SUBSTRING_FALSE_POSITIVE"

    # 2. Re-score the saved sentence with the strict matcher.
    _, score, flag = find_proof_sentence(sent, src, tgt, rel)

    if flag == "polarity_conflict":
        return "POLARITY_CONFLICT"
    if score < 0.7:
        return "KEYWORD_LOST"
    return "PASS"


def main():
    if not Path(VERIFIED_DATA_PATH).exists():
        print(f"Error: {VERIFIED_DATA_PATH} not found")
        return

    with open(VERIFIED_DATA_PATH) as f:
        verified = json.load(f)

    counts = Counter()
    by_relation = {}
    examples = {}
    detailed = []

    for entry in verified:
        cat = categorize(entry)
        counts[cat] += 1
        by_relation.setdefault(entry["relation"], Counter())[cat] += 1
        if cat != "PASS" and len(examples.setdefault(cat, [])) < 5:
            examples[cat].append({
                "source": entry["source"],
                "target": entry["target"],
                "relation": entry["relation"],
                "pmid": entry["pmid"],
                "proof_sentence": (entry.get("proof_sentence", "") or "")[:240],
            })
        detailed.append({
            "edge_id": entry.get("edge_id"),
            "source": entry["source"],
            "target": entry["target"],
            "relation": entry["relation"],
            "pmid": entry["pmid"],
            "category": cat,
        })

    total = len(verified)
    passed = counts["PASS"]

    print("=" * 70)
    print("READ-ONLY RE-AUDIT OF ACTION-VERIFIED PROVENANCE")
    print("=" * 70)
    print(f"Total injected proofs: {total}")
    print(f"  PASS (survive strict check):  {passed}  ({passed/total:.1%})")
    for cat in ["SUBSTRING_FALSE_POSITIVE", "POLARITY_CONFLICT", "KEYWORD_LOST"]:
        n = counts.get(cat, 0)
        print(f"  {cat:<26} {n}  ({n/total:.1%})")
    print()
    print("By relation (fail rate):")
    for rel, c in sorted(by_relation.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        fails = tot - c.get("PASS", 0)
        print(f"  {rel:<20} {tot:>4} proofs, {fails:>4} fail ({fails/tot:.0%})")
    print()
    for cat, exs in examples.items():
        print(f"--- {cat} examples ---")
        for e in exs:
            print(f"  {e['source']} -{e['relation']}-> {e['target']} (PMID:{e['pmid']})")
            print(f"    \"{e['proof_sentence']}\"")
        print()

    report = {
        "total": total,
        "counts": dict(counts),
        "pass_rate": passed / total,
        "by_relation": {r: dict(c) for r, c in by_relation.items()},
        "examples": examples,
        "detailed": detailed,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Full per-edge report written to: {REPORT_PATH}")
    print("(No database, manifest, or network state was modified.)")


if __name__ == "__main__":
    main()
