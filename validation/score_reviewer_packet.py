#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Turn a returned reviewer coding sheet into the two numbers the packet exists for.

    python -m validation.score_reviewer_packet reports/reviewer_audit_2026-07-31

Reads CODING_SHEET.csv and BLIND_CITATION_SHEET.csv once the reviewer has filled
them in, joins against MANIFEST.json, and reports:

  1. LABEL COMPLETENESS - what fraction of the unlabelled pairs the system
     surfaced are actually approved (A) or in trial (B). This is the number that
     decides whether "external precision is weak" was ever a real finding or an
     artefact of a 44-label gold set. It feeds Phase 0.5 directly.

  2. CITATION-TO-ASSERTION PRECISION - what fraction of cited sources actually
     support the relation the edge claims.

  3. CONTROL CALIBRATION - whether the already-labelled positives seeded into the
     packet were coded A. If a reviewer codes a recovered FDA approval as E, the
     finding is about the evidence presentation, not the drug.

WHAT THIS DOES NOT PRODUCE: an AUROC, an AUPRC, or a precision figure for the
ranker. The packet runs on the `all` cohort and is a discovery surface, not a
benchmark. Anyone quoting a ranking metric off this output has misread it.

A single reviewer's codes are one expert's opinion, not ground truth. Report n,
report who, and do not average two reviewers into a number without also
reporting where they disagreed - the disagreements are usually the finding.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

VALID_CODES = {"A", "B", "C", "D", "E"}
VALID_ANSWERS = {"yes", "partially", "no"}


def _read_codes(path: Path) -> dict[str, dict]:
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("code_A_to_E") or "").strip().upper()
            if not code:
                continue
            if code not in VALID_CODES:
                print(f"  ! {row['pair_id']}: unrecognised code {code!r}, skipped")
                continue
            out[row["pair_id"]] = {"code": code, "reason": (row.get("reason") or "").strip()}
    return out


def _read_blind(path: Path) -> dict[int, dict]:
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            ans = (row.get("answer_yes_partially_no") or "").strip().lower()
            if not ans:
                continue
            if ans not in VALID_ANSWERS:
                print(f"  ! blind row {row['n']}: unrecognised answer {ans!r}, skipped")
                continue
            out[int(row["n"])] = {"answer": ans, "note": (row.get("note") or "").strip()}
    return out


def _pct(num: int, den: int) -> str:
    return f"{num}/{den} ({100.0 * num / den:.0f}%)" if den else f"{num}/0 (n/a)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("packet_dir")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    d = Path(args.packet_dir)
    manifest = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
    pairs = {p["pair_id"]: p for p in manifest["pairs"]}
    blind_key = {r["n"]: r for r in manifest["blind_citation_key"]}

    codes = _read_codes(d / "CODING_SHEET.csv")
    blind = _read_blind(d / "BLIND_CITATION_SHEET.csv")

    if not codes:
        print("No codes filled in yet. The packet is an artifact until a reviewer")
        print("completes CODING_SHEET.csv - it is not a result.")
        return 1

    controls = {k: v for k, v in codes.items() if pairs[k]["is_known_positive"]}
    unlabelled = {k: v for k, v in codes.items() if not pairs[k]["is_known_positive"]}

    u = Counter(v["code"] for v in unlabelled.values())
    n_u = sum(u.values())
    missing_labels = u["A"] + u["B"]

    report = {
        "packet": str(d),
        "graph_sha256": manifest["meta"]["db_sha256"],
        "n_coded": len(codes),
        "n_unlabelled_coded": n_u,
        "unlabelled_code_counts": dict(u),
        "label_completeness_gap": missing_labels,
        "citation_precision": {},
        "controls": {},
    }

    print("=" * 72)
    print("  PHARM reviewer packet - results")
    print("=" * 72)
    print(f"packet   {d}")
    print(f"graph    {manifest['meta']['db_sha256'][:16]}...")
    print(f"coded    {len(codes)} of {manifest['meta']['n_pairs']} pairs\n")

    print("1. LABEL COMPLETENESS  (unlabelled pairs only)")
    print("-" * 72)
    for code in "ABCDE":
        print(f"  {code}  {u[code]:>3}   {manifest['codes'][code]}")
    print()
    print(f"  Apparent false positives that are really missing labels (A+B): "
          f"{_pct(missing_labels, n_u)}")
    if n_u:
        if missing_labels / n_u >= 0.20:
            print("  -> A substantial share of what this system calls a false positive is a")
            print("    gap in the gold set. No precision claim was ever defensible. Build")
            print("    the Phase 0.5 label set before quoting any precision number.")
        elif missing_labels / n_u <= 0.05:
            print("  -> The gold set is close to complete at the top of this list. A precision")
            print("    claim becomes defensible once the label set is formalised, and the")
            print("    E-rate below is then the real signal.")
        else:
            print("  -> Partial contamination. Enough to invalidate a precision claim, not")
            print("    enough to explain it away. Formalise the label set and re-measure.")
    print()

    print("2. CITATION-TO-ASSERTION PRECISION  (blind subset)")
    print("-" * 72)
    if blind:
        b = Counter(v["answer"] for v in blind.values())
        n_b = sum(b.values())
        print(f"  yes {b['yes']}   partially {b['partially']}   no {b['no']}   (n={n_b})")
        print(f"  strict precision (yes only):       {_pct(b['yes'], n_b)}")
        print(f"  lenient (yes + partially):         {_pct(b['yes'] + b['partially'], n_b)}")
        report["citation_precision"] = {
            "counts": dict(b), "n": n_b,
            "strict": b["yes"] / n_b if n_b else None,
            "lenient": (b["yes"] + b["partially"]) / n_b if n_b else None,
        }
        by_layer = Counter()
        for n, v in blind.items():
            key = blind_key.get(n, {})
            layer = "terminal_protein_disease" if key.get("relation") in (
                "associated_with", "driver_of") else "other"
            by_layer[(layer, v["answer"])] += 1
        print("\n  by layer:")
        for (layer, ans), c in sorted(by_layer.items()):
            print(f"    {layer:<26} {ans:<10} {c}")
        print("\n  Reminder: the grounding negative control found post-hoc PubMed support")
        print("  on the terminal hop carries no measurable signal (12.5% vs 7.5%, p=0.28).")
        print("  A high citation precision here does NOT rehabilitate that layer.")
    else:
        print("  not yet filled in")
    print()

    print("3. CONTROL CALIBRATION  (already-labelled positives seeded in)")
    print("-" * 72)
    if controls:
        c = Counter(v["code"] for v in controls.values())
        print(f"  coded A: {_pct(c['A'], len(controls))}")
        offenders = {k: v for k, v in controls.items() if v["code"] in ("D", "E")}
        for pid, v in offenders.items():
            p = pairs[pid]
            print(f"  ! {pid} {p['drug']} | {p['disease']} - approved, but coded "
                  f"{v['code']}: {v['reason'] or '(no reason given)'}")
        if offenders:
            print("  -> The evidence presentation failed on a known-correct answer.")
            print("    That is a finding about the packet, not about the drug.")
        report["controls"] = {"n": len(controls), "counts": dict(c),
                              "miscoded": list(offenders)}
    else:
        print("  no controls coded")
    print()

    print("NOT DERIVABLE FROM THIS OUTPUT: AUROC, AUPRC, or a precision figure for")
    print("the ranker. This packet ran on the `all` cohort as a discovery surface.")

    if args.json:
        print("\n" + json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
