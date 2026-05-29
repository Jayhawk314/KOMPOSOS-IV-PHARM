#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
READ-ONLY: count independent literature support per edge.

One proof sentence in one paper is not "established". This reports, per edge,
how many DISTINCT PMIDs the triplet search returned (data/full_triplet_candidate_pool.json),
which is a proxy for independent corroboration. Writes data/edge_support_counts.json.
No DB or network access.
"""

import json
from collections import Counter
from pathlib import Path

POOL = "data/full_triplet_candidate_pool.json"
OUT = "data/edge_support_counts.json"


def bucket(n: int) -> str:
    if n == 0:
        return "0"
    if n == 1:
        return "1 (single source)"
    if n <= 4:
        return "2-4"
    if n <= 9:
        return "5-9"
    return "10+ (search cap)"


def main():
    pool = json.load(open(POOL))
    per_edge = []
    dist = Counter()
    by_relation = {}
    for e in pool:
        n = len(set(e["pmids"]))
        per_edge.append({
            "source": e["source"], "target": e["target"],
            "relation": e["relation"], "distinct_pmids": n,
        })
        dist[bucket(n)] += 1
        by_relation.setdefault(e["relation"], []).append(n)

    total = len(pool)
    single = sum(1 for x in per_edge if x["distinct_pmids"] == 1)
    multi = sum(1 for x in per_edge if x["distinct_pmids"] >= 2)

    print("=" * 70)
    print("INDEPENDENT LITERATURE SUPPORT PER EDGE (candidate pool)")
    print("=" * 70)
    print(f"Edges with >=1 candidate PMID: {total}")
    print(f"  single-source (exactly 1 PMID): {single}  ({single/total:.1%})")
    print(f"  multi-source  (>=2 PMIDs):      {multi}  ({multi/total:.1%})")
    print()
    print("Distribution of distinct supporting PMIDs:")
    for b in ["1 (single source)", "2-4", "5-9", "10+ (search cap)"]:
        n = dist.get(b, 0)
        print(f"  {b:<20} {n:>5}  ({n/total:.1%})")
    print()
    print("Median distinct PMIDs by relation:")
    for rel, counts in sorted(by_relation.items(), key=lambda kv: -len(kv[1])):
        counts.sort()
        med = counts[len(counts) // 2]
        print(f"  {rel:<20} n={len(counts):>4}  median={med}")

    json.dump({
        "total_edges": total,
        "single_source": single,
        "multi_source": multi,
        "distribution": dict(dist),
        "per_edge": per_edge,
    }, open(OUT, "w"), indent=2)
    print(f"\nWritten: {OUT}  (read-only; no DB/network changes)")


if __name__ == "__main__":
    main()
