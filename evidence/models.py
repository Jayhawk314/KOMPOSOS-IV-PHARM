from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PairEvidence:
    """All reviewed contextual evidence for one canonical drug-disease pair."""

    drug: str
    disease: str
    reviews: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    studies: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    outcomes: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    receipts: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    #: Measured PRISM viability adjudication. Read-only context; never a feature.
    prism: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def reviewed(self) -> bool:
        return bool(self.reviews)

    @property
    def active_studies(self) -> tuple[dict[str, Any], ...]:
        active = {
            "RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION",
            "ACTIVE_NOT_RECRUITING",
        }
        return tuple(
            study for study in self.studies
            if study.get("recruitment_status") in active
        )

    @property
    def unresolved_receipts(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            receipt for receipt in self.receipts
            if receipt.get("resolves") == 0
        )
