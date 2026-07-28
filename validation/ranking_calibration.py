#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Benchmark calibration helpers for ranking scores.

The ranking score is a prioritization score, not a probability.  This module
maps ranking scores to observed label rates in a named benchmark protocol so
the UI can display calibration separately from strategy signals.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VERSION = "2026-05-27"
DEFAULT_CALIBRATION_PATH = Path("reports/ranking_score_calibration_2026-05-27.json")
CALIBRATION_TARGET = "benchmark_label_rate"
CALIBRATION_WARNING = (
    "Benchmark label rate under open-world negatives; not a clinical probability "
    "and not a probability of drug efficacy."
)


def build_quantile_bins(
    scores: list[float],
    labels: list[int],
    *,
    n_bins: int = 10,
) -> list[dict[str, float | int]]:
    """Build score-ordered bins with empirical and monotone label rates."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")
    if not scores:
        raise ValueError("cannot calibrate an empty score list")
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")

    paired = sorted(zip(scores, labels), key=lambda row: row[0])
    n = len(paired)
    raw_bins: list[dict[str, float | int]] = []
    start = 0
    for i in range(n_bins):
        end = round((i + 1) * n / n_bins)
        end = max(end, start + 1)
        end = min(end, n)
        if start >= n:
            break
        chunk = paired[start:end]
        positives = sum(label for _, label in chunk)
        count = len(chunk)
        raw_bins.append(
            {
                "bin": len(raw_bins) + 1,
                "score_min": round(chunk[0][0], 6),
                "score_max": round(chunk[-1][0], 6),
                "n": count,
                "positives": positives,
                "mean_score": round(sum(score for score, _ in chunk) / count, 6),
                "empirical_label_rate": round(positives / count, 6),
            }
        )
        start = end

    # Pool-adjacent-violators algorithm.  This preserves monotonicity without
    # requiring sklearn and avoids presenting noisy bin rates as calibrated.
    blocks: list[dict[str, float | int]] = []
    for idx, bin_row in enumerate(raw_bins):
        block = {
            "start": idx,
            "end": idx,
            "n": int(bin_row["n"]),
            "positives": int(bin_row["positives"]),
        }
        blocks.append(block)
        while len(blocks) >= 2:
            left = blocks[-2]
            right = blocks[-1]
            left_rate = left["positives"] / left["n"]
            right_rate = right["positives"] / right["n"]
            if left_rate <= right_rate:
                break
            merged = {
                "start": left["start"],
                "end": right["end"],
                "n": left["n"] + right["n"],
                "positives": left["positives"] + right["positives"],
            }
            blocks[-2:] = [merged]

    monotone_rates = [0.0] * len(raw_bins)
    for block in blocks:
        rate = block["positives"] / block["n"]
        for idx in range(int(block["start"]), int(block["end"]) + 1):
            monotone_rates[idx] = rate

    calibrated_bins = []
    for bin_row, rate in zip(raw_bins, monotone_rates):
        calibrated = dict(bin_row)
        calibrated["monotonic_label_rate"] = round(rate, 6)
        calibrated_bins.append(calibrated)
    return calibrated_bins


def calibrate_score(score: float, calibration: dict[str, Any] | None) -> float | None:
    """Return benchmark label rate for a ranking score, if calibration exists."""
    if not calibration:
        return None
    bins = calibration.get("bins") or []
    if not bins:
        return None

    for bin_row in bins:
        if score <= float(bin_row["score_max"]):
            return float(bin_row["monotonic_label_rate"])
    return float(bins[-1]["monotonic_label_rate"])


def load_calibration(path: str | Path = DEFAULT_CALIBRATION_PATH) -> dict[str, Any] | None:
    """Load a calibration artifact if present."""
    path = Path(path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
