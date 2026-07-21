#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Negative control for post-hoc PubMed grounding.

The question
------------
Discovery proposes a protein->disease edge FIRST, then searches PubMed for a
sentence supporting it. PubMed holds ~37M abstracts, so for almost any protein
and any common cancer some sentence mentioning both exists. That makes "we
searched and found support" nearly uninformative on its own.

The only way to know whether the grounding step carries information is to measure
its rate on pairs that are NOT the proposed ones.

Design: permutation control
---------------------------
Take the exact proteins probed in a real run, but pair each with a RANDOM
DIFFERENT disease. This holds constant:
  - how much each protein is written about (same proteins)
  - the disease vocabulary (same disease pool)
  - the query construction, gate, and abstract budget (same pipeline)
and destroys only the specific protein-disease PAIRING.

    If AGREE(real) ~= AGREE(scrambled): the grounding measures corpus density,
        not relationship. The citations are decoration.
    If AGREE(real) >> AGREE(scrambled): the graph is selecting pairs the
        literature genuinely supports, and post-hoc confirmation is legitimate.

Usage:
    python scripts/grounding_negative_control.py --against data/DISCOVERED_DRIVER_GBM.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discover_morphisms import (best_proof_sentence, fetch_abstract, graph_gaps,
                                search_pubmed)
from komposos_kg.pharm_gate import build_pharm_memory
from komposos_kg.pharm_verifier import VERDICT_TO_TIER


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="data/drugs/tier1.db")
    ap.add_argument("--against", required=True,
                    help="Real-run JSON whose probed proteins define the control set.")
    ap.add_argument("--relation", default="driver_of")
    ap.add_argument("--per-pmid", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260720)
    ap.add_argument("--out", default="data/GROUNDING_NEGATIVE_CONTROL.json")
    args = ap.parse_args()

    real = json.loads(Path(args.against).read_text())
    real_disease = None
    proteins = []
    for bucket in ("relation_screened", "quarantined", "ungrounded"):
        for rec in real.get(bucket, []):
            proteins.append(rec["source"])
            real_disease = real_disease or rec["target"]
    # Preserve probe order, drop duplicates.
    seen, ordered = set(), []
    for p in proteins:
        if p not in seen:
            seen.add(p); ordered.append(p)

    _, diseases = graph_gaps(args.db, args.relation)
    pool = sorted(d for d in diseases if d != real_disease)
    rng = random.Random(args.seed)

    real_agree = len(real.get("relation_screened", []))
    real_n = real.get("probed", len(ordered))
    print(f"real run:  {args.against}")
    print(f"  disease={real_disease}  probed={real_n}  AGREE={real_agree} "
          f"({100*real_agree/real_n:.1f}%)")
    print(f"control:   same {len(ordered)} proteins, each paired with a random other disease")
    print(f"  disease pool: {len(pool)}  seed={args.seed}\n")

    mem = build_pharm_memory(use_cog=True, use_optimus=False, domain="control")

    screened, quarantined, ungrounded = [], [], []
    for i, prot in enumerate(ordered, 1):
        disease = rng.choice(pool)
        pmids = search_pubmed(prot, disease, k=args.per_pmid, relation=args.relation)
        time.sleep(0.35)
        proof, pmid_used = None, None
        for pmid in pmids:
            ab = fetch_abstract(pmid); time.sleep(0.35)
            sent, kw = best_proof_sentence(ab, prot, disease, args.relation)
            if sent and (kw or proof is None):
                proof, pmid_used = sent, pmid
                if kw:
                    break
        if not proof:
            ungrounded.append({"source": prot, "target": disease})
            print(f"[{i}/{len(ordered)}] {prot}->{disease}: UNGROUNDED")
            continue

        res = mem.remember(prot, args.relation, disease,
                           source=f"PMID:{pmid_used}", evidence=proof)
        rec = {"source": prot, "relation": args.relation, "target": disease,
               "pmid": pmid_used, "verdict": res.verdict,
               "tier": VERDICT_TO_TIER.get(res.verdict, "?"),
               "reason": res.reason, "proof_sentence": proof}
        (screened if res.verdict == "AGREE" else quarantined).append(rec)
        print(f"[{i}/{len(ordered)}] {prot}->{disease}: {res.verdict}")

    n = len(ordered)
    ctrl_rate = 100 * len(screened) / n if n else 0.0
    real_rate = 100 * real_agree / real_n if real_n else 0.0
    out = {
        "design": "permutation control - same proteins, randomly reassigned diseases",
        "relation": args.relation,
        "seed": args.seed,
        "real_run": {"file": args.against, "disease": real_disease,
                     "probed": real_n, "agree": real_agree, "agree_pct": round(real_rate, 1)},
        "control_run": {"probed": n, "agree": len(screened),
                        "agree_pct": round(ctrl_rate, 1),
                        "quarantined": len(quarantined), "ungrounded": len(ungrounded)},
        "interpretation": (
            "If the two AGREE rates are comparable, post-hoc PubMed grounding is "
            "measuring corpus density rather than the proposed relationship."),
        "control_screened": screened,
        "control_quarantined": quarantined,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))

    print("\n" + "=" * 62)
    print("NEGATIVE CONTROL COMPLETE")
    print(f"  real       AGREE {real_agree}/{real_n}  ({real_rate:.1f}%)")
    print(f"  scrambled  AGREE {len(screened)}/{n}  ({ctrl_rate:.1f}%)")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
