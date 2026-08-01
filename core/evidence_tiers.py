#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Evidence tier system for KOMPOSOS-IV-PHARM.

Distinguishes measured biological data from graph-inferred relationships.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class EvidenceTier(Enum):
    """Evidence quality tiers from highest to lowest."""
    MEASURED = "MEASURED"           # IC50, clinical outcomes, mutation frequencies
    ESTABLISHED = "ESTABLISHED"     # FDA approvals, KEGG canonical pathways
    INFERRED = "INFERRED"          # ESM2, STRING PPI, computed similarities
    HYPOTHESIS = "HYPOTHESIS"       # PubMed citations (AGREE/PARTIAL)
    SPECULATIVE = "SPECULATIVE"     # PubMed ORPHAN (isolated edges)
    NOISE = "NOISE"                # PubMed REJECT (contradictory)


@dataclass
class EvidenceAnnotation:
    """
    Structured evidence annotation for a morphism.

    Separates quantitative measurements from graph-derived confidence.
    """
    tier: EvidenceTier
    source: str                    # "ChEMBL IC50", "FDA approval", "PMID:12345"
    quantitative_value: Optional[float] = None  # IC50 in μM, mutation freq, etc.
    unit: Optional[str] = None     # "μM", "percentage", "hazard_ratio"
    sample_size: Optional[int] = None
    p_value: Optional[float] = None
    confidence_lower: Optional[float] = None  # CI lower bound
    confidence_upper: Optional[float] = None  # CI upper bound

    def display_string(self) -> str:
        """Human-readable evidence string for UI display."""
        if self.tier == EvidenceTier.MEASURED and self.quantitative_value is not None:
            value_str = f"{self.quantitative_value:.3g} {self.unit or ''}"
            if self.confidence_lower is not None and self.confidence_upper is not None:
                value_str += f" (95% CI: {self.confidence_lower:.3g}-{self.confidence_upper:.3g})"
            return f"{self.tier.value}: {self.source} = {value_str}"

        elif self.tier == EvidenceTier.HYPOTHESIS:
            return f"{self.tier.value}: {self.source} (not quantified - graph coherence only)"

        else:
            return f"{self.tier.value}: {self.source}"

    def to_dict(self) -> dict:
        """Serialize to dictionary for database storage."""
        return {
            "tier": self.tier.value,
            "source": self.source,
            "quantitative_value": self.quantitative_value,
            "unit": self.unit,
            "sample_size": self.sample_size,
            "p_value": self.p_value,
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceAnnotation":
        """Deserialize from dictionary."""
        return cls(
            tier=EvidenceTier(data["tier"]),
            source=data["source"],
            quantitative_value=data.get("quantitative_value"),
            unit=data.get("unit"),
            sample_size=data.get("sample_size"),
            p_value=data.get("p_value"),
            confidence_lower=data.get("confidence_lower"),
            confidence_upper=data.get("confidence_upper"),
        )


def classify_tier_from_provenance(provenance: str, metadata: dict, confidence: float) -> EvidenceTier:
    """
    Classify a morphism into an evidence tier based on its provenance.

    Args:
        provenance: Provenance string (e.g., "ChEMBL IC50", "PMID:12345")
        metadata: Morphism metadata dict (may contain categorical_delta)
        confidence: Edge confidence (0-1)

    Returns:
        EvidenceTier enum value
    """
    prov_upper = provenance.upper()

    # ------------------------------------------------------------------
    # CEILING FIRST.  The honesty pipeline stamps its own verdict onto the
    # provenance string, and that verdict must be able to CAP the tier --
    # otherwise the tag that says "this is our weakest evidence" is invisible
    # to the function deciding how strong the evidence is.
    #
    # This was a real defect, measured 2026-08-01: all 37 `driver_of`
    # Protein->Disease edges carried tier ESTABLISHED, while 10 of them had
    # provenance [LEXICAL-COOCCURRENCE] or "literature (unverified)". None of
    # those tags appeared in any keyword list below, so every one fell through
    # to the confidence fallback, and a hand-set confidence of 0.88 became
    # "ESTABLISHED". BRAF->Melanoma and VEGFR2->RCC were among them, and
    # VEGFR2->RCC sits underneath several published candidate leads.
    #
    # The biology in those edges is correct. The problem is that the label
    # claimed a grade of evidence the citation could not support, which breaks
    # the one promise this system makes: click the receipt and it holds up.
    # ------------------------------------------------------------------
    if "[EMBEDDING-INFERRED]" in prov_upper:
        return EvidenceTier.INFERRED
    if "[LEXICAL-COOCCURRENCE]" in prov_upper:
        # Word co-occurrence in an abstract. The permutation control
        # (data/GROUNDING_NEGATIVE_CONTROL.json) found this carries no
        # measurable signal about whether the relation is real.
        return EvidenceTier.SPECULATIVE
    if "[RELATION-SCREENED]" in prov_upper:
        # A lexical gate agreed a relation word was present. ~0.82 precision
        # against human adjudication -- a screen, not a verification.
        return EvidenceTier.HYPOTHESIS
    if "UNVERIFIED" in prov_upper:
        # Checked BEFORE [RELATION-VERIFIED] on purpose. Several edges carry
        # both, e.g. "literature (unverified); PMID:...; [RELATION-VERIFIED]".
        # Contradictory tags must resolve DOWNWARD, never upward.
        return EvidenceTier.HYPOTHESIS
    if "[RELATION-VERIFIED]" in prov_upper:
        # Survived the relation-extraction gate: the cited sentence was read and
        # judged to assert this relation, not merely to mention both endpoints.
        # That is a real quality signal and the distinction the whole honesty
        # layer is built on, so it can reach ESTABLISHED.
        #
        # It is NOT human adjudication. HONEST_VALUE.md records the gate at
        # roughly 0.82 precision against in-session adjudication, so treat this
        # as "an automated reader agreed", not "an expert signed it off".
        return EvidenceTier.ESTABLISHED

    # MEASURED: Direct experimental measurements
    if any(keyword in prov_upper for keyword in ["CHEMBL", "IC50", "KI", "KD", "ABPP"]):
        return EvidenceTier.MEASURED

    # ESTABLISHED: Regulatory/canonical databases
    if any(keyword in prov_upper for keyword in ["FDA", "KEGG PATHWAY", "NDA", "BLA"]):
        return EvidenceTier.ESTABLISHED

    # INFERRED: Computational/similarity-based
    if any(keyword in prov_upper for keyword in ["ESM2", "ESM-2", "STRING PPI", "SIMILARITY"]):
        return EvidenceTier.INFERRED

    # Check categorical verification metadata for PubMed edges
    categorical_delta = metadata.get("categorical_delta", "")

    if categorical_delta == "REJECT":
        return EvidenceTier.NOISE

    elif categorical_delta == "ORPHAN":
        return EvidenceTier.SPECULATIVE

    elif categorical_delta in ["AGREE", "PARTIAL"]:
        return EvidenceTier.HYPOTHESIS

    # ------------------------------------------------------------------
    # NO CONFIDENCE FALLBACK.
    #
    # This previously read:
    #     if confidence >= 0.70: return ESTABLISHED
    #     elif confidence >= 0.40: return INFERRED
    #     else: return HYPOTHESIS
    #
    # That made the tier a re-encoding of the confidence number rather than an
    # independent statement about evidence quality. Somebody set BRAF->Melanoma
    # to 0.95 because it is obviously true; the classifier read 0.95 and
    # stamped ESTABLISHED; and the UI then displayed two columns that looked
    # like corroborating signals while being the same signal twice.
    #
    # A tier that echoes confidence cannot contradict it, so it can never warn
    # anyone that a high-confidence edge rests on a weak citation -- which is
    # the only job it has.
    #
    # An edge whose provenance matches nothing recognised is UNCLASSIFIED
    # evidence, regardless of how confident someone was. Say so.
    # ------------------------------------------------------------------
    return EvidenceTier.HYPOTHESIS


def tier_priority(tier: EvidenceTier) -> int:
    """
    Get numeric priority for a tier (lower = higher priority).

    Used for sorting/ranking evidence.
    """
    priority_map = {
        EvidenceTier.MEASURED: 1,
        EvidenceTier.ESTABLISHED: 2,
        EvidenceTier.INFERRED: 3,
        EvidenceTier.HYPOTHESIS: 4,
        EvidenceTier.SPECULATIVE: 5,
        EvidenceTier.NOISE: 6,
    }
    return priority_map[tier]
