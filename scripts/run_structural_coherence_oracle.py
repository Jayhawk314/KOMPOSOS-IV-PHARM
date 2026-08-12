# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Side-effect-free CLI for the KOMPOSOS structural-coherence Oracle.

Usage:
    python scripts/run_structural_coherence_oracle.py manifest.json
    python scripts/run_structural_coherence_oracle.py manifest.json --output report.json

The legacy ``geometry`` and ``oracle`` package initializers eagerly import
unrelated experimental stacks. This runner loads only the structural kernel and
Oracle specialization. It can be removed once those packages use lazy imports.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _runtime():
    geometry_package = types.ModuleType("geometry")
    geometry_package.__path__ = [str(ROOT / "geometry")]
    sys.modules["geometry"] = geometry_package
    _load(
        "geometry.alphafold_coherence",
        ROOT / "geometry" / "alphafold_coherence.py",
    )
    return _load(
        "komposos_structural_coherence_oracle",
        ROOT / "oracle" / "structural_coherence.py",
    )


if __name__ == "__main__":
    raise SystemExit(_runtime().main())
