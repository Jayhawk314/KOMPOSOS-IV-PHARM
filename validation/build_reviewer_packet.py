#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Build the 50-pair human evidence and label-completeness audit packet.

This is roadmap step 2, and it is the exercise that has to happen before any
precision claim about PHARM is defensible in either direction. It measures three
things at once that no module can measure:

  1. LABEL COMPLETENESS - how many apparent false positives are actually
     approved indications or active trials that the 44-label gold set never
     recorded. This is the blocker on Phase 0.5.
  2. CITATION-TO-ASSERTION PRECISION - whether the cited sentence actually
     supports the relation the edge claims.
  3. WORKFLOW VALUE - whether a domain reviewer can reject a candidate quickly
     from what is shown.

WHAT THIS IS NOT: a benchmark. No AUROC, AUPRC, or precision figure may be
derived from this packet. It deliberately runs on the `all` cohort because the
unlabelled approvals that codes A and B exist to catch live almost entirely among
the 679 materialized ChEMBL drugs, which the `core` cohort excludes. Scoring a
benchmark on `all` is forbidden (see HONEST_VALUE.md); using it as a discovery
surface, which is what a triage review is, is exactly its documented purpose.

Direct Drug->Disease labels are removed before scoring, so the ranking reflects
composed evidence rather than a memorised indication.

Pairs are SHUFFLED and rank is withheld from the reviewer. A ranked list invites
anchoring on position instead of on the evidence shown, which would contaminate
the codes. The rank mapping is written to the manifest, which is the answer key
and is not sent out.

Run:
    python -m validation.build_reviewer_packet
    python -m validation.build_reviewer_packet --per-disease 25 --seed 20260731
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.repurposing_benchmark import (
    DB_PATH,
    DEFAULT_EXCLUDE_PROVENANCE,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
)
from validation.trace_prediction import _build_provenance_index, trace_pair

DISEASES = ["NSCLC", "Melanoma"]
PMID_RE = re.compile(r"PMID[:\s]*(\d{6,9})", re.IGNORECASE)

CODES = {
    "A": "approved indication - this is an FDA-approved use and the label set missed it",
    "B": "in active clinical trial for this indication",
    "C": "published preclinical rationale exists",
    "D": "mechanistically plausible but I can find no documentation",
    "E": "wrong - or the cited evidence does not support the claimed relation",
}


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------

def _db_fingerprint(db_path: str) -> str:
    """SHA-256 of the graph database, so the packet is pinned to one graph."""
    h = hashlib.sha256()
    with open(db_path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def select_top_pairs(category, strategies, disease: str, n: int,
                     known_positives: set[tuple[str, str]],
                     n_controls: int):
    """Score every drug against one disease; return n pairs for review.

    A first pass took the top n outright, which put 17 already-labelled positives
    into a 50-pair packet. That wastes a third of the reviewer's budget on pairs
    whose code is knowably 'A' before they read anything, and it dilutes the
    measurement the packet exists for.

    So: keep a SMALL number of the highest-scoring known positives as a
    calibration control - if a reviewer codes a recovered FDA approval as E, that
    is a finding about the evidence presentation, not about the drug - and fill
    the remainder from the top UNLABELLED pairs, which is where the
    label-completeness question actually lives.
    """
    drugs = sorted(o.name for o in category.objects() if o.type_name == "Drug")
    scored = []
    for drug in drugs:
        score, votes = score_pair(strategies, drug, disease)
        if not votes:
            continue  # abstention: nothing to review
        scored.append({
            "drug": drug,
            "disease": disease,
            "score": round(score, 6),
            "is_known_positive": (drug, disease) in known_positives,
        })
    scored.sort(key=lambda r: -r["score"])

    controls = [r for r in scored if r["is_known_positive"]][:n_controls]
    unlabelled = [r for r in scored if not r["is_known_positive"]]
    selected = controls + unlabelled[: max(0, n - len(controls))]
    for row in selected:
        row["selected_as"] = "control" if row["is_known_positive"] else "unlabelled"
    return selected


def pmids_from_edge(edge: dict) -> list[str]:
    return sorted(set(PMID_RE.findall(edge.get("provenance") or "")))


def best_chains(trace: dict, k: int = 3) -> list[dict]:
    """The k strongest chains, preferring shortest (Drug->Protein->Disease)."""
    chains = [c for c in trace["chains"] if c["edges"]]
    chains.sort(key=lambda c: (len(c["edges"]), -c["path_confidence"]))
    seen, out = set(), []
    for chain in chains:
        sig = tuple((e["source"], e["relation"], e["target"]) for e in chain["edges"])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(chain)
        if len(out) == k:
            break
    return out


def missing_evidence_line(chains: list[dict]) -> str:
    """State plainly what this candidate does NOT have. Never leave it blank."""
    gaps = []
    all_edges = [e for c in chains for e in c["edges"]]
    if not all_edges:
        return "No composed mechanistic chain at all - this candidate is ranked on analogy only."
    terminal = [e for e in all_edges if e["target_type"] == "Disease"]
    if terminal and all(e["relation"] == "associated_with" for e in terminal):
        gaps.append(
            "every terminal Protein->Disease hop is `associated_with`, a co-occurrence "
            "relation, not a mechanistic claim"
        )
    if not any(pmids_from_edge(e) for e in terminal):
        gaps.append("no PMID on any terminal hop")
    if all(e["quantitative_value"] is None for e in all_edges):
        gaps.append("no quantitative value on any edge (the column is NULL graph-wide)")
    if not any(e["evidence_tier"] in ("MEASURED", "ESTABLISHED") for e in all_edges):
        gaps.append("no MEASURED or ESTABLISHED edge anywhere in the chain")
    return "; ".join(gaps) if gaps else "no structural gap detected by the automated check"


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def render_pair_block(item: dict) -> str:
    lines = [
        f"### {item['pair_id']}  —  {item['drug']}  ·  {item['disease']}",
        "",
    ]
    if not item["chains"]:
        lines += ["_No composed evidence chain to display._", ""]
    for i, chain in enumerate(item["chains"], 1):
        arrow = "".join(
            f"{e['source']} —{e['relation']}→ " for e in chain["edges"]
        ) + chain["edges"][-1]["target"]
        # Paths that reach the target by hopping through ANOTHER disease are weak
        # by construction. Say so rather than letting the arrow diagram imply
        # they are equivalent to a direct mechanistic route.
        via_disease = any(
            e["target_type"] == "Disease" and e is not chain["edges"][-1]
            for e in chain["edges"]
        )
        flag = "  ⚠ **routes through another disease — co-occurrence, not mechanism**" if via_disease else ""
        lines.append(f"**Path {i}** · `{arrow}`{flag}")
        lines.append("")
        lines.append("| edge | relation | tier | provenance | PMID | conf |")
        lines.append("|---|---|---|---|---|---|")
        for e in chain["edges"]:
            pmids = pmids_from_edge(e)
            pmid_cell = ", ".join(
                f"[{p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in pmids[:3]
            ) or "—"
            prov = (e["provenance"] or "unknown")[:44]
            lines.append(
                f"| {e['source']} → {e['target']} | `{e['relation']}` | "
                f"{e['evidence_tier']} | {prov} | {pmid_cell} | {e['confidence']:.2f} |"
            )
        lines.append("")
    lines += [
        f"**What this candidate does not have:** {item['missing']}",
        "",
        f"**Your code ({'/'.join(CODES)}):** `____`    **Why:** ",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def render_packet(items: list[dict], meta: dict) -> str:
    head = f"""# PHARM reviewer packet — {meta['n_pairs']} candidate pairs

Generated {meta['generated']}. Graph fingerprint `{meta['db_sha256'][:16]}…`,
{meta['n_morphisms']} scored morphisms, scorer `{meta['scorer']}`.

## What I am asking

I am **not** asking whether these are good drugs. I am asking whether the evidence
shown is what you would need to **reject them quickly**.

The pairs below are in random order. Rank is deliberately withheld — I do not want
position to influence your reading.

## Task 1 — code every pair (about 45 minutes)

Assign each pair exactly one code:

| code | meaning |
|---|---|
{chr(10).join(f'| **{k}** | {v} |' for k, v in CODES.items())}

Codes **A** and **B** matter most to me and are not a criticism of your time: they
tell me how much of what my system calls a false positive is really a gap in my
label set. I currently cannot tell those apart, which is why I will not make any
claim about this system's precision.

A one-line reason is more useful than a careful one. Write "obviously approved" or
"never seen this" and move on.

## Task 2 — blind citation check (about 20 minutes)

See `BLIND_CITATION_SUBSET.md`. Ten cited sentences, each with the relation it is
supposed to support. Answer yes / partially / no. Do that file **before** reading
the pairs below if you can, so the surrounding context does not colour it.

## Task 3 — the debrief question

> What would have to be on this page for you to spend an afternoon on the pairs
> you coded **D**?

---

"""
    return head + "\n".join(render_pair_block(i) for i in items)


def render_blind_subset(items: list[dict], rng: random.Random, k: int = 10) -> str:
    # Priority matters here. The terminal Protein->Disease hop is the least
    # verified layer in the graph and the one the grounding negative control
    # found carries no signal, so it is what a citation check should spend its
    # slots on. Drug->Protein (ChEMBL/FDA) is independently derived and is the
    # useful contrast. Disease->Disease co-occurrence edges are filler and a
    # first pass wasted 2 of 10 slots on them.
    def priority(edge: dict) -> int:
        if edge["target_type"] == "Disease" and edge["source"] not in DISEASES:
            src_is_disease = any(
                edge["source"] == d for d in ("NSCLC", "Melanoma")
            )
            return 2 if src_is_disease else 0   # 0 = Protein->Disease, best
        if edge["target_type"] == "Disease":
            return 2                            # Disease->Disease, filler
        return 1                                # Drug->Protein / Protein->Protein

    candidates = []
    for item in items:
        for chain in item["chains"]:
            for e in chain["edges"]:
                pmids = pmids_from_edge(e)
                if pmids:
                    candidates.append((priority(e), item["pair_id"], e, pmids[0]))
    rng.shuffle(candidates)
    candidates.sort(key=lambda c: c[0])   # stable: keeps the shuffle within a tier

    picked, seen_edges = [], set()
    for _prio, pair_id, e, pmid in candidates:
        sig = (e["source"], e["relation"], e["target"])
        if sig in seen_edges:
            continue
        seen_edges.add(sig)
        picked.append((pair_id, e, pmid))
        if len(picked) == k:
            break
    rng.shuffle(picked)   # do not hand the reviewer the priority ordering

    lines = [
        "# Blind citation check",
        "",
        "For each row: does the cited source actually support the stated relation?",
        "Answer **yes**, **partially**, or **no**. If the source is about a different",
        "gene or a different sense of an ambiguous symbol, that is a **no** — please",
        "say so, because symbol collisions are a known defect in this pipeline.",
        "",
        "Do this before reading the main packet if you can.",
        "",
        "| # | claimed relation | source | your answer | note |",
        "|---|---|---|---|---|",
    ]
    for i, (pair_id, e, pmid) in enumerate(picked, 1):
        claim = f"`{e['source']}` —{e['relation']}→ `{e['target']}`"
        link = f"[PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
        lines.append(f"| {i} | {claim} | {link} | | |")
    lines += [
        "",
        "_Provenance strings and evidence tiers are withheld here on purpose._",
        "",
    ]
    return "\n".join(lines), [
        {"n": i, "pair_id": p, "source": e["source"], "relation": e["relation"],
         "target": e["target"], "pmid": pmid, "evidence_tier": e["evidence_tier"],
         "provenance": e["provenance"]}
        for i, (p, e, pmid) in enumerate(picked, 1)
    ]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--per-disease", type=int, default=25)
    parser.add_argument(
        "--controls-per-disease", type=int, default=3,
        help="How many already-labelled positives to keep as a calibration "
             "control. The rest of each disease's slots go to unlabelled pairs, "
             "which is where the label-completeness question lives.",
    )
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--outdir", default="reports/reviewer_audit_2026-07-31")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # `all` cohort on purpose - see module docstring.
    category, _ = load_full_typed_view(
        args.db, remove_direct_labels=True, cohort="all",
        exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE,
    )
    labelled, _ = load_full_typed_view(
        args.db, cohort="all", exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE,
    )
    _, _, known_positives = drug_disease_pairs(labelled)
    strategies = make_strategies(category)
    prov_index = _build_provenance_index(args.db)

    items = []
    for disease in DISEASES:
        print(f"[packet] scoring {disease} ...", flush=True)
        for row in select_top_pairs(category, strategies, disease,
                                    args.per_disease, known_positives,
                                    args.controls_per_disease):
            trace = trace_pair(category, row["drug"], disease,
                               strategies=strategies, provenance_index=prov_index)
            chains = best_chains(trace, k=3)
            items.append({
                **row,
                "chains": chains,
                "missing": missing_evidence_line(chains),
                "n_chains_total": trace["n_chains"],
            })

    # rank within disease, then destroy the ordering for the reviewer
    for disease in DISEASES:
        group = [i for i in items if i["disease"] == disease]
        group.sort(key=lambda r: -r["score"])
        for rank, item in enumerate(group, 1):
            item["rank_in_disease"] = rank

    rng.shuffle(items)
    for n, item in enumerate(items, 1):
        item["pair_id"] = f"P{n:02d}"

    meta = {
        "generated": str(date.today()),
        "db_sha256": _db_fingerprint(args.db),
        "n_morphisms": len(category.morphisms()),
        "n_objects": len(category.objects()),
        "scorer": "repurposing_benchmark.score_pair",
        "cohort": "all",
        "protocol": "remove_direct_labels",
        "exclude_provenance": DEFAULT_EXCLUDE_PROVENANCE,
        "seed": args.seed,
        "diseases": DISEASES,
        "per_disease": args.per_disease,
        "controls_per_disease": args.controls_per_disease,
        "n_pairs": len(items),
        "n_controls": sum(1 for i in items if i["is_known_positive"]),
        "n_unlabelled": sum(1 for i in items if not i["is_known_positive"]),
        "not_a_benchmark": (
            "No AUROC/AUPRC/precision figure may be derived from this packet. "
            "It runs on the `all` cohort, which is a discovery surface only."
        ),
    }

    blind_md, blind_key = render_blind_subset(items, rng)

    (outdir / "REVIEWER_PACKET.md").write_text(render_packet(items, meta), encoding="utf-8")
    (outdir / "BLIND_CITATION_SUBSET.md").write_text(blind_md, encoding="utf-8")

    with open(outdir / "CODING_SHEET.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pair_id", "drug", "disease", "code_A_to_E", "reason"])
        for item in items:
            w.writerow([item["pair_id"], item["drug"], item["disease"], "", ""])

    with open(outdir / "BLIND_CITATION_SHEET.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "answer_yes_partially_no", "note"])
        for row in blind_key:
            w.writerow([row["n"], "", ""])

    # the answer key - NOT to be sent to the reviewer
    (outdir / "MANIFEST.json").write_text(json.dumps({
        "meta": meta,
        "codes": CODES,
        "pairs": [
            {k: v for k, v in item.items() if k != "chains"} for item in items
        ],
        "blind_citation_key": blind_key,
    }, indent=2), encoding="utf-8")

    known = sum(1 for i in items if i["is_known_positive"])
    print(f"\n[packet] wrote {len(items)} pairs to {outdir}")
    print(f"[packet] {known} of them are already-labelled positives "
          f"(expected to be coded A; they are the exercise's internal control)")
    print(f"[packet] blind citation subset: {len(blind_key)} sentences")
    print("[packet] MANIFEST.json is the answer key - do not send it to the reviewer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
