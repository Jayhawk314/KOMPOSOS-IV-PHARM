# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Verdict Bilattice
=================

Maps the KOMPOSOS 2x2 verdict grid (AGREE/HOLLOW/ORPHAN/REJECT) onto
a Belnap bilattice with complex amplitudes and inner horn geometry.

INNER HORN GEOMETRY — THE PRECISE STATEMENT
---------------------------------------------
A HOLLOW verdict witnesses a failed inner horn fill.

In simplicial terms, the inner horn Λ²₁ is:

        1
       / \\
      /   \\
     0     2

    Two edges: 0→1 (source morphism) and 1→2 (target morphism).
    The horn exists. The composite 0→2 (the filler) is the question.

    HOLLOW:  CAT finds a filler (structurally composable).
             ZFC rejects it (logically unsound).
             → Horn present, valid filler ABSENT.
             → This is the precise definition of a vulnerability:
               the type system allows the composition,
               the logic does not.

    ORPHAN:  ZFC finds a filler (logically forced).
             CAT cannot construct it (structurally absent).
             → Filler exists in logic but has no geometric realization.
             → A ghost path: provably required but unreachable.

    AGREE:   Both validators confirm the filler.
             → Fully Kan: the inner horn fills validly.

    REJECT:  Neither validator finds a filler.
             → No composition claim is being made. Not an attack.
             → The horn itself was never asserted.

This connects directly to ∞-category (quasicategory) theory:
  The Kan condition requires every inner horn to have a filler.
  HOLLOW = the Kan condition fails at this morphism.
  A codebase with HOLLOW morphisms is not a quasicategory —
  it has compositional gaps an attacker can walk through.

WHY A BILATTICE, NOT A QUANTALE
---------------------------------
A quantale has one ordering and one multiplication.
The verdict grid has TWO independent orderings:

  t-order (truth):     how valid is the composition being claimed?
  k-order (knowledge): how much do the validators agree with each other?

These are orthogonal. Collapsing them (as a quantale would) destroys
the HOLLOW/ORPHAN distinction — they become the same element.
A bilattice carries both orderings simultaneously.

THE BILATTICE STRUCTURE
------------------------
Verdicts as (CAT_says, ZFC_says) pairs:

    AGREE  = (T, T)  →  both confirm    →  high truth, high knowledge
    HOLLOW = (T, F)  →  CAT yes, ZFC no →  mixed truth, low knowledge
    ORPHAN = (F, T)  →  CAT no, ZFC yes →  mixed truth, low knowledge
    REJECT = (F, F)  →  both deny       →  low truth, high knowledge

t-order (truth ordering):
    REJECT <_t HOLLOW, ORPHAN <_t AGREE
    HOLLOW and ORPHAN are INCOMPARABLE under t-order
    (Different validators dominant — collapsing them loses this)

    Diamond:
              AGREE
             /     \\
         HOLLOW   ORPHAN
             \\     /
              REJECT

k-order (knowledge/agreement ordering):
    HOLLOW, ORPHAN <_k AGREE, REJECT

    Diamond:
           AGREE     REJECT
            |   \\ /    |
            |    X     |
            |   / \\    |
           HOLLOW  ORPHAN

COMPLEX AMPLITUDE
-----------------
Preserves both validator signals independently:

    amplitude = cat_conf + zfc_conf * 1j

Phase encodes validator balance — not lost through composition:
    Phase → 0:    HOLLOW  (CAT strong, ZFC absent, structural risk)
    Phase → π/2:  ORPHAN  (ZFC strong, CAT absent, ghost path)
    Phase → π/4:  AGREE   (both strong, balanced, safe)
    |amplitude| → 0: REJECT (both weak, no claim)

Z2 PARITY — FALLS OUT NATURALLY
---------------------------------
    AGREE, REJECT → parity 0 (validators agree, Kan condition met or irrelevant)
    HOLLOW, ORPHAN → parity 1 (validators disagree, Kan condition failed)

    Fermionic exclusion: HOLLOW ∘ HOLLOW → NULL_COLLAPSE
    Two failed inner horn fills composing = chain with zero valid support.
    This is the Mythos exploit chain pattern algebraically.

FOLDER
------
foundation/verdict_bilattice.py
(pure math — depends only on standard library)
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Verdict — the four elements of the bilattice
# ---------------------------------------------------------------------------

class Verdict(IntEnum):
    """
    Z2-graded verdict element.

    Encodes (CAT_result, ZFC_result) as a 2-bit integer:
      bit 1 = CAT says valid
      bit 0 = ZFC says valid

    Parity = CAT XOR ZFC = validator disagreement.

    Compatible with DeltaType names for drop-in use:
      from foundation.verdict_bilattice import Verdict as DeltaType
    """
    REJECT = 0b00  # CAT=F, ZFC=F — parity 0
    ORPHAN = 0b01  # CAT=F, ZFC=T — parity 1
    HOLLOW = 0b10  # CAT=T, ZFC=F — parity 1
    AGREE  = 0b11  # CAT=T, ZFC=T — parity 0

    @property
    def cat_says(self) -> bool:
        return bool(self.value & 0b10)

    @property
    def zfc_says(self) -> bool:
        return bool(self.value & 0b01)

    @property
    def parity(self) -> int:
        """Z2 parity: 1 iff validators disagree (Kan condition fails)."""
        return self.cat_says ^ self.zfc_says

    @property
    def is_odd(self) -> bool:
        """True for HOLLOW and ORPHAN — failed inner horn fills."""
        return bool(self.parity)

    @property
    def horn_status(self) -> str:
        """Geometric interpretation in terms of inner horn Λ²₁."""
        if self == Verdict.AGREE:
            return "FILLED — inner horn Λ²₁ has valid filler (fully Kan)"
        elif self == Verdict.HOLLOW:
            return "FAILED — horn present, ZFC rejects filler (vulnerability)"
        elif self == Verdict.ORPHAN:
            return "GHOST — filler logically forced but structurally absent"
        else:  # REJECT
            return "ABSENT — no composition claimed, horn not asserted"

    def __repr__(self) -> str:
        return f"Verdict.{self.name}"


# ---------------------------------------------------------------------------
# Bilattice orderings
# ---------------------------------------------------------------------------

# t-order truth matrix: t_leq[a][b] = True iff a ≤_t b
# REJECT <_t HOLLOW, ORPHAN <_t AGREE
# HOLLOW and ORPHAN are incomparable
_T_LEQ = {
    #          REJECT  ORPHAN  HOLLOW  AGREE
    Verdict.REJECT: {Verdict.REJECT: True,  Verdict.ORPHAN: True,  Verdict.HOLLOW: True,  Verdict.AGREE: True},
    Verdict.ORPHAN: {Verdict.REJECT: False, Verdict.ORPHAN: True,  Verdict.HOLLOW: False, Verdict.AGREE: True},
    Verdict.HOLLOW: {Verdict.REJECT: False, Verdict.ORPHAN: False, Verdict.HOLLOW: True,  Verdict.AGREE: True},
    Verdict.AGREE:  {Verdict.REJECT: False, Verdict.ORPHAN: False, Verdict.HOLLOW: False, Verdict.AGREE: True},
}

# k-order knowledge matrix: k_leq[a][b] = True iff a ≤_k b
# HOLLOW, ORPHAN <_k AGREE, REJECT
# AGREE and REJECT are incomparable; HOLLOW and ORPHAN are incomparable
_K_LEQ = {
    #          REJECT  ORPHAN  HOLLOW  AGREE
    Verdict.REJECT: {Verdict.REJECT: True,  Verdict.ORPHAN: False, Verdict.HOLLOW: False, Verdict.AGREE: False},
    Verdict.ORPHAN: {Verdict.REJECT: True,  Verdict.ORPHAN: True,  Verdict.HOLLOW: False, Verdict.AGREE: True},
    Verdict.HOLLOW: {Verdict.REJECT: True,  Verdict.ORPHAN: False, Verdict.HOLLOW: True,  Verdict.AGREE: True},
    Verdict.AGREE:  {Verdict.REJECT: False, Verdict.ORPHAN: False, Verdict.HOLLOW: False, Verdict.AGREE: True},
}


def t_leq(a: Verdict, b: Verdict) -> bool:
    """a ≤_t b in the truth ordering."""
    return _T_LEQ[a][b]


def k_leq(a: Verdict, b: Verdict) -> bool:
    """a ≤_k b in the knowledge ordering."""
    return _K_LEQ[a][b]


def t_meet(a: Verdict, b: Verdict) -> Verdict:
    """
    t-meet (∧_t): greatest lower bound in truth ordering.
    Most pessimistic truth — what both validators agree is the minimum.
    """
    if t_leq(a, b):
        return a
    if t_leq(b, a):
        return b
    # Incomparable (HOLLOW, ORPHAN) → meet is REJECT (bottom of t-order)
    return Verdict.REJECT


def t_join(a: Verdict, b: Verdict) -> Verdict:
    """
    t-join (∨_t): least upper bound in truth ordering.
    Most optimistic truth — what either validator says is the maximum.
    """
    if t_leq(a, b):
        return b
    if t_leq(b, a):
        return a
    # Incomparable (HOLLOW, ORPHAN) → join is AGREE (top of t-order)
    return Verdict.AGREE


def k_meet(a: Verdict, b: Verdict) -> Verdict:
    """
    k-meet (⊓): greatest lower bound in knowledge ordering.
    Least informative — used when combining parallel uncertain paths.
    When two paths disagree on which validator to trust, knowledge drops.
    """
    if k_leq(a, b):
        return a
    if k_leq(b, a):
        return b
    # Incomparable cases:
    # AGREE ⊓ REJECT → HOLLOW or ORPHAN? We return HOLLOW (CAT-dominant)
    # HOLLOW ⊓ ORPHAN → minimum knowledge → HOLLOW (both are k-bottom)
    return Verdict.HOLLOW


def k_join(a: Verdict, b: Verdict) -> Verdict:
    """
    k-join (⊔): least upper bound in knowledge ordering.
    Most informative — used to fold parallel paths (take most informative).
    """
    if k_leq(a, b):
        return b
    if k_leq(b, a):
        return a
    # Incomparable: AGREE ⊔ REJECT or HOLLOW ⊔ ORPHAN
    return Verdict.AGREE


# ---------------------------------------------------------------------------
# BilatticeElement — verdict + complex amplitude
# ---------------------------------------------------------------------------

@dataclass
class BilatticeElement:
    """
    An element of the KOMPOSOS verdict bilattice.

    verdict:   The categorical verdict (AGREE/HOLLOW/ORPHAN/REJECT)
    amplitude: Complex confidence — real=CAT, imag=ZFC

    The complex amplitude preserves both validator signals through
    composition without collapsing them to a scalar.

    Phase interpretation:
        Phase 0      → pure CAT signal (HOLLOW character)
        Phase π/2    → pure ZFC signal (ORPHAN character)
        Phase π/4    → balanced (AGREE character)
        |amplitude|  → overall confidence magnitude
    """
    verdict: Verdict
    amplitude: complex = 1.0 + 0.0j

    def __post_init__(self):
        # Clamp amplitude magnitude to [0, 1]
        mag = abs(self.amplitude)
        if mag > 1.0:
            self.amplitude = self.amplitude / mag

    @classmethod
    def from_confidences(
        cls,
        cat_conf: float,
        zfc_conf: float,
    ) -> BilatticeElement:
        """
        Build a BilatticeElement from raw validator confidences.

        Verdict is derived from which validators are above threshold (0.5).
        Amplitude encodes both signals in the complex plane.
        """
        cat_bool = cat_conf >= 0.5
        zfc_bool = zfc_conf >= 0.5

        if cat_bool and zfc_bool:
            verdict = Verdict.AGREE
        elif cat_bool and not zfc_bool:
            verdict = Verdict.HOLLOW
        elif not cat_bool and zfc_bool:
            verdict = Verdict.ORPHAN
        else:
            verdict = Verdict.REJECT

        amplitude = complex(cat_conf, zfc_conf)
        return cls(verdict=verdict, amplitude=amplitude)

    @property
    def cat_conf(self) -> float:
        """CAT confidence — real part of amplitude."""
        return self.amplitude.real

    @property
    def zfc_conf(self) -> float:
        """ZFC confidence — imaginary part of amplitude."""
        return self.amplitude.imag

    @property
    def magnitude(self) -> float:
        """Overall confidence — |amplitude|."""
        return abs(self.amplitude)

    @property
    def phase(self) -> float:
        """Phase angle in radians — validator balance."""
        return cmath.phase(self.amplitude)

    @property
    def parity(self) -> int:
        return self.verdict.parity

    @property
    def is_odd(self) -> bool:
        return self.verdict.is_odd

    @property
    def horn_status(self) -> str:
        return self.verdict.horn_status

    def t_meet(self, other: BilatticeElement) -> BilatticeElement:
        """Pessimistic truth combination. Use for AND-paths."""
        v = t_meet(self.verdict, other.verdict)
        amp = self.amplitude * other.amplitude  # both must be confident
        return BilatticeElement(verdict=v, amplitude=amp)

    def t_join(self, other: BilatticeElement) -> BilatticeElement:
        """Optimistic truth combination. Use for OR-paths."""
        v = t_join(self.verdict, other.verdict)
        # Take the amplitude from the more confident element
        amp = (
            self.amplitude if abs(self.amplitude) >= abs(other.amplitude)
            else other.amplitude
        )
        return BilatticeElement(verdict=v, amplitude=amp)

    def k_meet(self, other: BilatticeElement) -> BilatticeElement:
        """Least informative combination. Use to find worst-case knowledge."""
        v = k_meet(self.verdict, other.verdict)
        amp = complex(
            min(self.cat_conf, other.cat_conf),
            min(self.zfc_conf, other.zfc_conf),
        )
        return BilatticeElement(verdict=v, amplitude=amp)

    def k_join(self, other: BilatticeElement) -> BilatticeElement:
        """
        Most informative combination.

        This is the parallel path fold:
        Given two paths through the same source/target,
        take the most informative verdict and the maximum amplitude.
        Replaces the pairwise loop in check_chain_interference.
        """
        v = k_join(self.verdict, other.verdict)
        amp = complex(
            max(self.cat_conf, other.cat_conf),
            max(self.zfc_conf, other.zfc_conf),
        )
        return BilatticeElement(verdict=v, amplitude=amp)

    def compose(self, other: BilatticeElement) -> BilatticeElement:
        """
        Z2-graded composition with Fermionic exclusion.

        odd ∘ odd → NULL_COLLAPSE:
          Two failed inner horn fills composing = chain collapse.
          Catches HOLLOW∘HOLLOW and HOLLOW∘ORPHAN chains.

        Even compositions use t-meet (pessimistic truth through chain).
        """
        if self.parity == 1 and other.parity == 1:
            # Two failed Kan conditions composing: chain has no valid support
            return BilatticeElement(
                verdict=Verdict.REJECT,  # collapse to bottom of t-order
                amplitude=0.0 + 0.0j,   # zero amplitude = NULL_COLLAPSE
            )
        return self.t_meet(other)

    def __mul__(self, other: BilatticeElement) -> BilatticeElement:
        return self.compose(other)

    def is_null_collapse(self) -> bool:
        return abs(self.amplitude) < 1e-9

    def __repr__(self) -> str:
        return (
            f"BilatticeElement({self.verdict.name} | "
            f"amp={self.amplitude:.3f} | "
            f"mag={self.magnitude:.3f} | "
            f"phase={math.degrees(self.phase):.1f}°)"
        )


# ---------------------------------------------------------------------------
# Parallel path fold — replaces pairwise loop in chain interference
# ---------------------------------------------------------------------------

def fold_parallel_paths(
    elements: Iterable[BilatticeElement],
) -> BilatticeElement:
    """
    Fold a set of parallel paths through the same source/target
    into a single most-informative BilatticeElement.

    Uses k-join (supremum in knowledge ordering):
    - Takes the most informative verdict across all parallel paths
    - Takes max(cat_conf), max(zfc_conf) independently
    - Preserves the HOLLOW/ORPHAN distinction (does not collapse them)

    This replaces the pairwise odd-probe loop in check_chain_interference
    for the case of parallel (not sequential) attack paths.

    Example:
        paths = [
            BilatticeElement.from_confidences(0.8, 0.2),  # HOLLOW
            BilatticeElement.from_confidences(0.7, 0.3),  # HOLLOW
            BilatticeElement.from_confidences(0.6, 0.6),  # AGREE
        ]
        worst = fold_parallel_paths(paths)
        # Returns AGREE element — most informative across parallel paths
    """
    elements = list(elements)
    if not elements:
        return BilatticeElement(Verdict.REJECT, 0.0 + 0.0j)

    result = elements[0]
    for elem in elements[1:]:
        result = result.k_join(elem)
    return result


def fold_sequential_chain(
    elements: Iterable[BilatticeElement],
) -> BilatticeElement:
    """
    Fold a sequential chain of morphisms using Z2-graded composition.

    Detects NULL_COLLAPSE when two consecutive odd elements compose.
    Aborts fold at first collapse (returns the collapse element).

    Example:
        chain = [
            BilatticeElement.from_confidences(0.8, 0.2),  # HOLLOW
            BilatticeElement.from_confidences(0.9, 0.1),  # HOLLOW
            BilatticeElement.from_confidences(0.7, 0.8),  # AGREE
        ]
        result = fold_sequential_chain(chain)
        # Returns NULL_COLLAPSE — HOLLOW∘HOLLOW detected
        # (third element never reached)
    """
    elements = list(elements)
    if not elements:
        return BilatticeElement(Verdict.REJECT, 0.0 + 0.0j)

    result = elements[0]
    for elem in elements[1:]:
        result = result.compose(elem)
        if result.is_null_collapse():
            return result  # early exit on collapse
    return result


# ---------------------------------------------------------------------------
# Kan defect — how far is this element from being fully Kan?
# ---------------------------------------------------------------------------

def kan_defect(elem: BilatticeElement) -> float:
    """
    Measure how far a BilatticeElement is from satisfying the Kan condition.

    Kan condition = inner horn has a valid filler = AGREE verdict.

    Returns a scalar in [0, 1]:
        0.0 → fully Kan (AGREE, high amplitude)
        1.0 → maximally non-Kan (HOLLOW/ORPHAN, high amplitude)

    Formula:
        defect = parity × magnitude

    Rationale:
        Even elements (AGREE, REJECT) have parity 0 → defect 0
        Odd elements (HOLLOW, ORPHAN) have parity 1 → defect = magnitude
        High-confidence HOLLOW = high defect (confident bad path)
        Low-confidence HOLLOW = low defect (weak signal)
    """
    return elem.parity * elem.magnitude


def chain_kan_defect(elements: Iterable[BilatticeElement]) -> float:
    """
    Total Kan defect across a chain.

    Sum of individual defects — measures total compositional unsoundness.
    A chain with high total defect has many failed inner horn fills
    and is a candidate exploit path.
    """
    return sum(kan_defect(e) for e in elements)
