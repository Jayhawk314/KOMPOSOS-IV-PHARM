# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""OPERADUM validation: synthesis-accuracy benchmarks."""

from .benchmark import run_benchmark, BenchmarkResult, random_operad, brute_force_min_cost

__all__ = ["run_benchmark", "BenchmarkResult", "random_operad", "brute_force_min_cost"]
