#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Reject candidates whose drug pushes the target the WRONG WAY.

THE BUG THIS FIXES
------------------
The graph records whether a drug `inhibits` or `activates` its target. Nothing
in the scoring path ever read that field. Composition asked only "is there a
path", so a drug that ACTIVATES a protein that DRIVES a cancer composed into a
candidate exactly like a drug that inhibits it.

The flaw was latent for as long as most drug->target edges happened to be
inhibitors. Adding ESR1 -> Breast_Cancer and AR -> Prostate_Cancer on 2026-08-01
made it visible, because those are the cases where the difference is stark:

  Estropipate   -activates-> ESR1 ... ESR1 drives Breast_Cancer      (an estrogen)
  Dienestrol    -activates-> ESR1 ... ESR1 drives Breast_Cancer      (an estrogen)
  Ethylestrenol -activates-> AR   ... AR drives Prostate_Cancer      (an androgen)
  Dromostanolone-activates-> AR   ... AR drives Prostate_Cancer      (an androgen)
  Avatrombopag  -activates-> MPL  ... MPL activation drives Myelofibrosis

Every one of those would be expected to WORSEN the disease. Fulvestrant and
bicalutamide -- the correct blockers -- sat in the same ranking with nothing to
distinguish them.

THE RULE
--------
If the terminal edge says the protein DRIVES the disease, the drug must push
that protein DOWN. Anything that pushes it up is rejected, not down-weighted:
this is a sign error, not a weak signal.

    driver_of  +  inhibits/indirect_inhibitor/binds/targets   ->  COHERENT
    driver_of  +  activates/activator/enhances                ->  REJECT
    driver_of  +  modulates/pathway_modulator                 ->  UNKNOWN sign
    associated_with terminal edge                             ->  NOT ASSESSED
                    (co-occurrence states no direction, so none can be checked)

WHAT THIS DOES NOT DO
---------------------
It does not touch the database or the scorer. It is a filter applied to
candidate lists, so the underlying ranking stays comparable to every published
number.

It also cannot catch a drug that inhibits the right protein in the wrong tissue
(EGFR inhibitors in glioblastoma pass this filter and still fail clinically).
Direction is necessary, not sufficient.

Run:
    python -m validation.direction_filter
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DOWN = {"inhibits", "indirect_inhibitor", "binds", "targets", "antagonizes"}
UP = {"activates", "activator", "enhances", "agonist"}
AMBIGUOUS = {"modulates", "pathway_modulator", "synergizes_with", "associated_with"}

COHERENT, REJECT, UNKNOWN, NOT_ASSESSED = (
    "COHERENT", "REJECT_WRONG_DIRECTION", "UNKNOWN_SIGN", "NOT_ASSESSED")


def direction_verdict(drug_relation: str, terminal_relation: str,
                      target_type: str = "") -> tuple[str, str]:
    """(verdict, human reason) for one Drug -rel-> Target -rel-> Disease chain.

    THE SIGN DEPENDS ON WHAT KIND OF PROTEIN IT IS, and a first version of this
    function got that wrong. `driver_of` means different things for the two:

      ONCOGENE / receptor / signalling : drives the cancer when ACTIVE, so a
                                         drug must push it DOWN.
      TUMOUR SUPPRESSOR               : drives the cancer when LOST, so
                                         restoring or activating it is the
                                         CORRECT move.

    "TP53 driver_of Soft_Tissue_Sarcoma" means TP53 LOSS drives the sarcoma.
    Cisplatin activating TP53 is therefore textbook chemotherapy, not an error.
    The first version rejected all 12 such rows, which would have thrown away
    correct chemistry alongside the genuine sign errors.
    """
    if terminal_relation == "associated_with":
        return NOT_ASSESSED, (
            "the terminal hop is co-occurrence, which asserts no direction, so "
            "no direction check is possible"
        )

    suppressor = target_type == "TumorSuppressor"
    wanted = UP if suppressor else DOWN
    wrong = DOWN if suppressor else UP
    kind = "tumour suppressor (driven by its LOSS)" if suppressor else \
           "driver when active"

    if drug_relation in wanted:
        return COHERENT, (
            f"target is a {kind}; drug `{drug_relation}` pushes it the right way"
        )
    if drug_relation in wrong:
        return REJECT, (
            f"target is a {kind}, and the drug `{drug_relation}` it. This would "
            "be expected to worsen the disease, not treat it."
        )
    if drug_relation in AMBIGUOUS:
        return UNKNOWN, f"`{drug_relation}` does not state a direction"
    return UNKNOWN, f"unrecognised relation `{drug_relation}`"


def load_edges(db: str):
    conn = sqlite3.connect(db)
    types = {n: t for n, t in conn.execute("SELECT name,type_name FROM objects")}
    drug_rel, term_rel = {}, {}
    for s, t, n, p in conn.execute(
            "SELECT source_name,target_name,name,provenance FROM morphisms"):
        if "ESMC" in (p or ""):
            continue
        if types.get(s) == "Drug" and types.get(t) not in ("Disease", None):
            drug_rel.setdefault((s, t), n)
        if types.get(s) not in ("Drug", "Disease", None) and types.get(t) == "Disease":
            term_rel.setdefault((s, t), n)
    conn.close()
    return types, drug_rel, term_rel


def check(drug: str, target: str, disease: str, drug_rel, term_rel, types=None):
    dr = drug_rel.get((drug, target))
    tr = term_rel.get((target, disease))
    if dr is None or tr is None:
        return NOT_ASSESSED, "edge not found in the graph"
    return direction_verdict(dr, tr, (types or {}).get(target, ""))


def main() -> int:
    from validation.repurposing_benchmark import DB_PATH, DEFAULT_EXCLUDE_PROVENANCE, load_full_typed_view
    from oracle.horns import inner_horns, best_fillers
    import collections

    types, drug_rel, term_rel = load_edges(DB_PATH)
    cat, _ = load_full_typed_view(DB_PATH, exclude_provenance=DEFAULT_EXCLUDE_PROVENANCE)
    unfilled = [h for h in best_fillers(inner_horns(cat, a_type="Drug", c_type="Disease")).values()
                if not h.filled_treats]

    counts = collections.Counter()
    rejected = []
    for h in unfilled:
        v, why = check(h.a, h.b, h.c, drug_rel, term_rel, types)
        counts[v] += 1
        if v == REJECT:
            rejected.append((h.a, h.b, h.c, drug_rel.get((h.a, h.b)), why))

    print("=" * 78)
    print("  DIRECTION CHECK over every unfilled-horn candidate")
    print("=" * 78)
    print(f"  candidates: {len(unfilled)}\n")
    for k in (COHERENT, REJECT, UNKNOWN, NOT_ASSESSED):
        print(f"  {k:<24}{counts[k]}")
    print(f"\n  REJECTED -- drug pushes a driver UP ({len(rejected)}):")
    for d, t, dis, rel, _ in sorted(rejected):
        print(f"    {d[:26]:<27}-{rel}-> {t:<9}-> {dis}")
    print("\n  These would be expected to worsen the disease. A candidate list")
    print("  that contains them must not be published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
