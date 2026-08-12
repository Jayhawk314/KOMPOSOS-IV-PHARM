# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""KOMPOSOS Oracle specialization for AlphaFold structural coherence.

The general CategoricalOracle predicts a missing relation for one source/target
pair.  Structural coherence is a different Oracle task: enumerate observed
domain-alignment triangles, compose their SE(3) morphisms, and rank conflicts.

This module deliberately preserves ``QUARANTINE`` as a standing rather than
encoding missing evidence as a small confidence number.  It does not enter the
drug-repurposing strategy ensemble or alter its scores.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Sequence

from geometry.alphafold_coherence import (
    AuditConfig,
    AuditReport,
    Domain,
    Standing,
    StructuralCoherenceAuditor,
    StructureModel,
    audit_manifest as run_geometry_manifest,
)


class StructuralCheckKind(str, Enum):
    DOMAIN_ARRANGEMENT = "DOMAIN_ARRANGEMENT"
    COMPOSITION_HORN = "COMPOSITION_HORN"


@dataclass(frozen=True)
class StructuralOracleCheck:
    """One receipt-bearing Oracle check, whether passed, failed or quarantined."""

    check_id: str
    kind: StructuralCheckKind
    standing: Standing
    source_model: str
    target_model: str
    via_model: Optional[str]
    domains: tuple[str, ...]
    review_priority: Optional[float]
    reasoning: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "kind": self.kind.value,
            "standing": self.standing.value,
            "source_model": self.source_model,
            "target_model": self.target_model,
            "via_model": self.via_model,
            "domains": list(self.domains),
            "review_priority": self.review_priority,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class StructuralOracleResult:
    family_id: str
    standing: Standing
    checks: tuple[StructuralOracleCheck, ...]
    ranked_findings: tuple[StructuralOracleCheck, ...]
    counts: dict[str, int]
    receipts: dict[str, Optional[str]]
    audit_report: AuditReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "oracle": "KOMPOSOS_STRUCTURAL_COHERENCE",
            "family_id": self.family_id,
            "standing": self.standing.value,
            "counts": self.counts,
            "receipts": self.receipts,
            "ranked_findings": [finding.to_dict() for finding in self.ranked_findings],
            "checks": [check.to_dict() for check in self.checks],
            "audit_report": self.audit_report.to_dict(),
        }


class StructuralCoherenceOracle:
    """Turn measured structural coherence checks into ranked Oracle findings."""

    name = "structural_coherence_oracle"

    def __init__(self, config: Optional[AuditConfig] = None):
        self.config = config or AuditConfig()
        self.auditor = StructuralCoherenceAuditor(self.config)

    def audit_family(
        self,
        family_id: str,
        models: Sequence[StructureModel],
        domains: Sequence[Domain],
        reference_model: Optional[str] = None,
    ) -> StructuralOracleResult:
        report = self.auditor.audit(
            family_id=family_id,
            models=models,
            domains=domains,
            reference_model=reference_model,
        )
        return self.from_audit(report)

    def from_audit(self, report: AuditReport) -> StructuralOracleResult:
        serialized = report.to_dict()
        checks: list[StructuralOracleCheck] = []
        for index, (raw, measured) in enumerate(
            zip(serialized["domain_arrangements"], report.domain_arrangements), start=1
        ):
            priority = self._domain_priority(raw, report.config)
            checks.append(StructuralOracleCheck(
                check_id=f"domain-arrangement-{index:04d}",
                kind=StructuralCheckKind.DOMAIN_ARRANGEMENT,
                standing=measured.standing,
                source_model=measured.source_model,
                target_model=measured.target_model,
                via_model=None,
                domains=(measured.anchor_domain, measured.mobile_domain),
                review_priority=priority,
                reasoning=self._domain_reasoning(raw),
                evidence=raw,
            ))
        for index, (raw, measured) in enumerate(
            zip(serialized["composition_checks"], report.composition_checks), start=1
        ):
            priority = self._composition_priority(raw, report.config)
            checks.append(StructuralOracleCheck(
                check_id=f"composition-horn-{index:04d}",
                kind=StructuralCheckKind.COMPOSITION_HORN,
                standing=measured.standing,
                source_model=measured.source_model,
                target_model=measured.target_model,
                via_model=measured.via_model,
                domains=(measured.domain_id,),
                review_priority=priority,
                reasoning=self._composition_reasoning(raw),
                evidence=raw,
            ))
        findings = tuple(sorted(
            (check for check in checks if check.standing != Standing.CONSISTENT),
            key=self._rank_key,
        ))
        counts = {
            standing.value: sum(check.standing == standing for check in checks)
            for standing in Standing
        }
        receipts = {
            model["model_id"]: model.get("source_path") for model in serialized["models"]
        }
        return StructuralOracleResult(
            family_id=report.family_id,
            standing=report.standing,
            checks=tuple(checks),
            ranked_findings=findings,
            counts=counts,
            receipts=receipts,
            audit_report=report,
        )

    @staticmethod
    def _domain_priority(raw: dict[str, Any], config: AuditConfig) -> Optional[float]:
        if raw["standing"] == Standing.QUARANTINE.value:
            return None
        ratios = []
        if raw["excess_arrangement_rmsd"] is not None:
            ratios.append(raw["excess_arrangement_rmsd"] / config.arrangement_rmsd_threshold)
        if raw["rotation_disagreement_deg"] is not None:
            ratios.append(
                raw["rotation_disagreement_deg"] / config.arrangement_rotation_threshold_deg
            )
        return float(max(ratios, default=0.0))

    @staticmethod
    def _composition_priority(raw: dict[str, Any], config: AuditConfig) -> Optional[float]:
        if raw["standing"] == Standing.QUARANTINE.value:
            return None
        ratios = []
        if raw["filler_rmsd"] is not None:
            ratios.append(raw["filler_rmsd"] / config.composition_rmsd_threshold)
        if raw["rotation_disagreement_deg"] is not None:
            ratios.append(
                raw["rotation_disagreement_deg"] / config.composition_rotation_threshold_deg
            )
        return float(max(ratios, default=0.0))

    @staticmethod
    def _domain_reasoning(raw: dict[str, Any]) -> str:
        if raw["standing"] == Standing.QUARANTINE.value:
            return "Domain-arrangement check quarantined: " + "; ".join(raw["reasons"])
        summary = (
            f"Aligning on {raw['anchor_domain']} places {raw['mobile_domain']} with "
            f"excess RMSD {raw['excess_arrangement_rmsd']:.3f} A and rotation "
            f"disagreement {raw['rotation_disagreement_deg']:.3f} degrees."
        )
        if raw["standing"] == Standing.INCONSISTENT.value:
            return summary + " The relative domain pose exceeds a configured review threshold."
        return summary + " The relative domain pose passes current thresholds."

    @staticmethod
    def _composition_reasoning(raw: dict[str, Any]) -> str:
        if raw["standing"] == Standing.QUARANTINE.value:
            return "Composition-horn check quarantined: " + "; ".join(raw["reasons"])
        summary = (
            f"The composed {raw['source_model']} -> {raw['via_model']} -> "
            f"{raw['target_model']} morphism differs from the direct morphism by "
            f"{raw['filler_rmsd']:.3f} A and "
            f"{raw['rotation_disagreement_deg']:.3f} degrees."
        )
        if raw["standing"] == Standing.INCONSISTENT.value:
            return summary + " The observed triangle fails current coherence thresholds."
        return summary + " The observed triangle commutes within current thresholds."

    @staticmethod
    def _rank_key(check: StructuralOracleCheck) -> tuple[int, float, str]:
        # Assessable conflicts precede quarantines. Quarantines carry no invented
        # numeric priority and are ordered deterministically by receipt ID.
        if check.standing == Standing.INCONSISTENT:
            return (0, -(check.review_priority or 0.0), check.check_id)
        return (1, 0.0, check.check_id)


def audit_manifest(path: str | Path) -> StructuralOracleResult:
    report = run_geometry_manifest(path)
    return StructuralCoherenceOracle(report.config).from_audit(report)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the KOMPOSOS structural-coherence Oracle on an AlphaFold family"
    )
    parser.add_argument("manifest", type=Path, help="structural audit manifest")
    parser.add_argument("--output", type=Path, help="write Oracle JSON here")
    args = parser.parse_args(argv)
    result = audit_manifest(args.manifest)
    rendered = json.dumps(result.to_dict(), indent=2, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
