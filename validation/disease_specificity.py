# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-KOMPOSOS-IV-Commercial
# Copyright (c) 2024-2026 James Ray Hawkins

"""
Disease-specificity ranking — demote pan-cancer hub drugs.

The raw repurposing score rewards "drug reaches a disease-linked protein via a
path". Promiscuous multi-kinase inhibitors (Imatinib, Sunitinib, ...) hit hub
proteins on many cancer pathways, so they float to the top of *most* diseases:
measured here, Imatinib lands in 17/20 disease top-5 lists. That is partly real
pan-cancer biology and partly a promiscuity/degree bias — either way, a drug
that tops every list carries little disease-specific information.

This module re-ranks candidates by how much a drug prefers THIS disease over its
own average across all diseases:

    lift(drug, disease) = raw_score(drug, disease) - mean_over_diseases(drug)

A hub drug has a high mean, so its lift is small; a drug that spikes for one
disease gets a high lift. We also report `hub_count` (how many diseases' top-K
the drug appears in) for transparency, so the hubs are demoted *visibly*, not
silently dropped.

This is a presentation/triage lens, NOT a change to the scoring model or to any
AUROC. The raw score is still shown alongside the lift.

Importable: `build_score_matrix()` (cached by the UI) then `specificity_ranking()`.
CLI mirrors the other validation tools.
"""

from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from statistics import mean

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
)

DEFAULT_TOP_K = 5  # "appears in a disease's top-K" defines a hub


@dataclass
class SpecRow:
    """One drug's standing for a disease under the specificity lens."""
    drug: str
    raw_score: float       # the model's raw score for (drug, disease)
    drug_mean: float       # that drug's mean raw score across all diseases
    lift: float            # raw_score - drug_mean (the disease-specific signal)
    hub_count: int         # number of diseases where drug is in the top-K
    is_positive: bool      # is this an approved `treats` indication?


@dataclass
class ScoreMatrix:
    """Full Drug x Disease score matrix plus per-drug summaries."""
    drugs: list[str]
    diseases: list[str]
    top_k: int
    scores: dict[tuple[str, str], float] = field(default_factory=dict)
    positives: set[tuple[str, str]] = field(default_factory=set)
    drug_mean: dict[str, float] = field(default_factory=dict)
    hub_count: dict[str, int] = field(default_factory=dict)


def build_score_matrix(db_path: str = DB_PATH, top_k: int = DEFAULT_TOP_K) -> ScoreMatrix:
    """
    Score every Drug x Disease pair once and summarise per-drug behaviour.

    Uses the full typed graph (the as-loaded view), matching what the triage UI
    shows. Heavy (~all-pairs scoring) — callers should cache the result.
    """
    buf = io.StringIO()
    with redirect_stdout(buf):  # silence bridge/loader chatter
        category, _ = load_full_typed_view(db_path)
        drugs, diseases, positives = drug_disease_pairs(category)
        strategies = make_strategies(category)
        scores: dict[tuple[str, str], float] = {}
        for drug in drugs:
            for disease in diseases:
                s, _votes = score_pair(strategies, drug, disease, fail_on_error=True)
                scores[(drug, disease)] = s

    drug_mean = {
        drug: mean(scores[(drug, dis)] for dis in diseases)
        for drug in drugs
    }
    # hub_count: in how many diseases' top-K (by raw score) does this drug appear
    hub_count: dict[str, int] = {drug: 0 for drug in drugs}
    for dis in diseases:
        ranked = sorted(drugs, key=lambda d: scores[(d, dis)], reverse=True)
        for d in ranked[:top_k]:
            hub_count[d] += 1

    return ScoreMatrix(
        drugs=drugs,
        diseases=diseases,
        top_k=top_k,
        scores=scores,
        positives=positives,
        drug_mean=drug_mean,
        hub_count=hub_count,
    )


def specificity_ranking(
    matrix: ScoreMatrix, disease: str, *, top_n: int = 10
) -> list[SpecRow]:
    """Rank drugs for `disease` by disease-specific lift (descending)."""
    if disease not in matrix.diseases:
        raise ValueError(f"unknown disease: {disease!r}")

    rows: list[SpecRow] = []
    for drug in matrix.drugs:
        raw = matrix.scores[(drug, disease)]
        dmean = matrix.drug_mean[drug]
        rows.append(SpecRow(
            drug=drug,
            raw_score=raw,
            drug_mean=dmean,
            lift=raw - dmean,
            hub_count=matrix.hub_count[drug],
            is_positive=(drug, disease) in matrix.positives,
        ))
    rows.sort(key=lambda r: r.lift, reverse=True)
    return rows[:top_n]


def hub_summary(matrix: ScoreMatrix, top_n: int = 10) -> list[tuple[str, int]]:
    """Drugs that appear in the most disease top-K lists (the hubs being demoted)."""
    return sorted(
        matrix.hub_count.items(), key=lambda kv: kv[1], reverse=True
    )[:top_n]


def format_terminal(matrix: ScoreMatrix, disease: str, top_n: int = 10) -> str:
    rows = specificity_ranking(matrix, disease, top_n=top_n)
    lines = []
    lines.append(f"Disease-specific candidates for: {disease}")
    lines.append("=" * 64)
    lines.append(
        "Ranked by LIFT = raw score - drug's mean across all diseases. "
        "Hubs (high mean / high hub-count) are demoted; raw score still shown."
    )
    lines.append("")
    lines.append(
        f"{'Drug':<22} {'lift':>7} {'raw':>6} {'drug avg':>9} "
        f"{'hub':>5} {'label':>6}"
    )
    lines.append(f"{'-'*22} {'-'*7} {'-'*6} {'-'*9} {'-'*5} {'-'*6}")
    for r in rows:
        label = "TREATS" if r.is_positive else "-"
        hub = f"{r.hub_count}/{len(matrix.diseases)}"
        lines.append(
            f"{r.drug:<22} {r.lift:>+7.3f} {r.raw_score:>6.3f} "
            f"{r.drug_mean:>9.3f} {hub:>5} {label:>6}"
        )
    lines.append("")
    lines.append("Pan-cancer hubs (demoted - appear in the most disease top-K lists):")
    for drug, c in hub_summary(matrix):
        lines.append(f"  {drug:<22} {c}/{len(matrix.diseases)}")
    return "\n".join(lines)


def format_markdown(matrix: ScoreMatrix, disease: str, top_n: int = 10) -> str:
    rows = specificity_ranking(matrix, disease, top_n=top_n)
    lines = []
    lines.append(f"### Disease-specific candidates: {disease}")
    lines.append("")
    lines.append("_Ranked by lift = raw score - the drug's mean score across all "
                 "diseases. Hubs are demoted; raw score shown for comparison._")
    lines.append("")
    lines.append("| Drug | Lift | Raw | Drug avg | Hub (top-K) | Label |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        label = "TREATS" if r.is_positive else "-"
        lines.append(
            f"| {r.drug} | {r.lift:+.3f} | {r.raw_score:.3f} | "
            f"{r.drug_mean:.3f} | {r.hub_count}/{len(matrix.diseases)} | {label} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Disease-specificity ranking (demote pan-cancer hub drugs)"
    )
    parser.add_argument("disease", help="disease name, e.g. Melanoma")
    parser.add_argument("--db", default=DB_PATH, help="path to tier1.db")
    parser.add_argument("--top", type=int, default=10, help="rows to show")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="hub top-K threshold")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    matrix = build_score_matrix(args.db, top_k=args.top_k)

    if args.json:
        rows = specificity_ranking(matrix, args.disease, top_n=args.top)
        print(json.dumps([asdict(r) for r in rows], indent=2))
    elif args.markdown:
        print(format_markdown(matrix, args.disease, top_n=args.top))
    else:
        print(format_terminal(matrix, args.disease, top_n=args.top))


if __name__ == "__main__":
    main()
