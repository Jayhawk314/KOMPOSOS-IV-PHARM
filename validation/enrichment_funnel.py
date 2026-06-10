# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-KOMPOSOS-IV-Commercial
# Copyright (c) 2024-2026 James Ray Hawkins

"""
Enrichment funnel — quantify how much the ranker accelerates a candidate search.

This answers a single practical question: if a scientist can only afford to
look at the top X% of drug-disease pairs, how many of the real hits do they
catch? Equivalently: how much of the haystack can they skip and still find
most of the needles?

Protocol (strict, `remove_direct_labels`): the direct Drug->Disease label is
removed from the graph before scoring, so the ranker cannot read the answer it
is being graded on. We then score every Drug x Disease pair, rank them, and
measure how many known positives (FDA `treats` indications) land in the top of
the list.

Two views of the same curve:
  * enrichment    — hit density in the top X% vs. screening blindly (random).
  * search saving — how little of the list you must screen to capture K% of hits.

Caveat carried in every report: enrichment is measured on *known* positives
(recovery). For genuinely novel pairs, top-of-list precision is lower (see the
Hetionet external check). The temporal holdout shows the lift does not fully
collapse on unseen approvals, but treat these numbers as "search acceleration on
the curated graph," not a novel-discovery hit rate.

Importable: `build_funnel()` returns a structured `EnrichmentFunnel` that the
Streamlit app and the README generator both consume. CLI mirrors the benchmark.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
)

DEFAULT_FRACTIONS: tuple[float, ...] = (0.05, 0.10, 0.20)
DEFAULT_CAPTURE_TARGETS: tuple[float, ...] = (0.50, 0.80, 1.00)


@dataclass
class FunnelRow:
    """One 'screen the top X%' slice of the ranked list."""
    fraction: float          # e.g. 0.05
    n_screened: int          # pairs in the top X%
    captured: int            # known positives caught in that slice
    capture_rate: float      # captured / total_positives
    enrichment: float        # hit density in slice / base rate (x vs random)


@dataclass
class CaptureTarget:
    """How far down the list you must screen to capture K% of positives."""
    target_rate: float       # e.g. 0.80
    n_screened: int          # pairs you must look at
    fraction_screened: float # n_screened / n_pairs
    skip_fraction: float     # 1 - fraction_screened (the search you avoid)


@dataclass
class EnrichmentFunnel:
    n_pairs: int
    n_positives: int
    base_rate: float
    rows: list[FunnelRow] = field(default_factory=list)
    capture_targets: list[CaptureTarget] = field(default_factory=list)
    protocol: str = "remove_direct_labels"

    def to_dict(self) -> dict:
        return asdict(self)


def score_all_pairs(db_path: str = DB_PATH) -> tuple[list[float], list[int]]:
    """
    Score every Drug x Disease pair under the strict protocol.

    Returns parallel lists (scores, labels) where label == 1 marks an
    FDA-approved `treats` indication. Positives are read from the full graph;
    scoring runs on the label-removed graph so the direct edge is invisible.
    """
    category, _ = load_full_typed_view(db_path, remove_direct_labels=True)
    base_category, _ = load_full_typed_view(db_path)
    _, _, positives = drug_disease_pairs(base_category)

    drugs, diseases, _ = drug_disease_pairs(category)
    strategies = make_strategies(category)

    scores: list[float] = []
    labels: list[int] = []
    for drug in drugs:
        for disease in diseases:
            score, _votes = score_pair(strategies, drug, disease, fail_on_error=True)
            scores.append(score)
            labels.append(1 if (drug, disease) in positives else 0)
    return scores, labels


def compute_funnel(
    scores: list[float],
    labels: list[int],
    *,
    fractions: tuple[float, ...] = DEFAULT_FRACTIONS,
    capture_targets: tuple[float, ...] = DEFAULT_CAPTURE_TARGETS,
    protocol: str = "remove_direct_labels",
) -> EnrichmentFunnel:
    """Build the enrichment funnel from parallel (scores, labels) lists."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels must be the same length")

    order = sorted(zip(scores, labels), key=lambda sl: sl[0], reverse=True)
    n_pairs = len(order)
    n_positives = sum(labels)
    if n_pairs == 0 or n_positives == 0:
        raise ValueError("need at least one pair and one positive to build a funnel")

    base_rate = n_positives / n_pairs

    rows: list[FunnelRow] = []
    for frac in fractions:
        k = max(1, int(n_pairs * frac))
        captured = sum(lbl for _s, lbl in order[:k])
        slice_density = captured / k
        rows.append(FunnelRow(
            fraction=frac,
            n_screened=k,
            captured=captured,
            capture_rate=captured / n_positives,
            enrichment=slice_density / base_rate,
        ))

    targets: list[CaptureTarget] = []
    for target in capture_targets:
        need = max(1, int(n_positives * target + 0.999))  # ceil(positives * target)
        cum = 0
        screened = n_pairs
        for i, (_s, lbl) in enumerate(order, start=1):
            cum += lbl
            if cum >= need:
                screened = i
                break
        targets.append(CaptureTarget(
            target_rate=target,
            n_screened=screened,
            fraction_screened=screened / n_pairs,
            skip_fraction=1 - screened / n_pairs,
        ))

    return EnrichmentFunnel(
        n_pairs=n_pairs,
        n_positives=n_positives,
        base_rate=base_rate,
        rows=rows,
        capture_targets=targets,
        protocol=protocol,
    )


def build_funnel(
    db_path: str = DB_PATH,
    *,
    fractions: tuple[float, ...] = DEFAULT_FRACTIONS,
    capture_targets: tuple[float, ...] = DEFAULT_CAPTURE_TARGETS,
) -> EnrichmentFunnel:
    """Score the graph and compute the funnel in one call (the UI entry point)."""
    scores, labels = score_all_pairs(db_path)
    return compute_funnel(
        scores, labels, fractions=fractions, capture_targets=capture_targets
    )


def format_terminal(f: EnrichmentFunnel) -> str:
    lines = []
    lines.append("KOMPOSOS-IV-PHARM Search Enrichment Funnel")
    lines.append("=" * 60)
    lines.append(
        f"Protocol: {f.protocol} (strict - direct label removed before scoring)"
    )
    lines.append(
        f"Search space: {f.n_pairs} drug-disease pairs | "
        f"{f.n_positives} known positives | base rate {f.base_rate * 100:.2f}%"
    )
    lines.append("")
    lines.append(f"{'Screen top':>11}  {'pairs':>6}  {'capture':>16}  {'enrichment':>10}")
    lines.append(f"{'-'*11}  {'-'*6}  {'-'*16}  {'-'*10}")
    for r in f.rows:
        cap = f"{r.captured}/{f.n_positives} ({r.capture_rate*100:.0f}%)"
        lines.append(
            f"{r.fraction*100:>9.0f}%  {r.n_screened:>6}  {cap:>16}  {r.enrichment:>8.1f}x"
        )
    lines.append("")
    for t in f.capture_targets:
        lines.append(
            f"Capture {t.target_rate*100:>3.0f}% of known hits: "
            f"screen {t.n_screened}/{f.n_pairs} pairs "
            f"({t.fraction_screened*100:.0f}%) -> skip {t.skip_fraction*100:.0f}% of the search"
        )
    lines.append("")
    lines.append(
        "Note: measured on KNOWN positives (recovery). Novel-pair precision is "
        "lower (Hetionet AUPRC check); treat as search acceleration on the "
        "curated graph, not a novel-discovery hit rate."
    )
    return "\n".join(lines)


def format_markdown(f: EnrichmentFunnel) -> str:
    lines = []
    lines.append(
        f"**Search space:** {f.n_pairs} drug-disease pairs | "
        f"{f.n_positives} known positives | base rate {f.base_rate*100:.2f}% "
        f"| protocol `{f.protocol}` (strict)"
    )
    lines.append("")
    lines.append("| Screen top | Pairs | Capture | Enrichment vs random |")
    lines.append("|---|---|---|---|")
    for r in f.rows:
        lines.append(
            f"| {r.fraction*100:.0f}% | {r.n_screened} | "
            f"{r.captured}/{f.n_positives} ({r.capture_rate*100:.0f}%) | "
            f"**{r.enrichment:.1f}x** |"
        )
    lines.append("")
    for t in f.capture_targets:
        lines.append(
            f"- Capture **{t.target_rate*100:.0f}%** of known hits by screening "
            f"**{t.fraction_screened*100:.0f}%** of the list "
            f"(skip {t.skip_fraction*100:.0f}%)."
        )
    lines.append("")
    lines.append(
        "_Measured on known positives (recovery). Novel-pair precision is lower; "
        "treat as search acceleration on the curated graph._"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search enrichment funnel for the repurposing ranker")
    parser.add_argument("--db", default=DB_PATH, help="path to tier1.db")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--markdown", action="store_true", help="emit Markdown (for README)")
    args = parser.parse_args()

    funnel = build_funnel(args.db)

    if args.json:
        print(json.dumps(funnel.to_dict(), indent=2))
    elif args.markdown:
        print(format_markdown(funnel))
    else:
        print(format_terminal(funnel))


if __name__ == "__main__":
    main()
