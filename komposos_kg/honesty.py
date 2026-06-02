"""
honesty_intent.py — portable honesty + intent core for COG / OPTIMUS pipelines.

COPY this file into any KOMPOSOS domain repo (sec, chem, pharm, gdelt) and
implement a `DomainAdapter`. The honesty/intent core is domain-agnostic; only
the adapter changes. No third-party dependencies. It will optionally delegate
to a repo's COG engine / OPTIMUS object if you pass one (duck-typed).

────────────────────────────────────────────────────────────────────────────
THE MATH, HONESTLY SCOPED
────────────────────────────────────────────────────────────────────────────
SINCERITY (output matches the actual reasoning) is modeled as an *identification*
between a stated explanation and the actual reasoning trace — the HoTT idea that
"sameness" is a witnessed path that can fail in STRUCTURED ways, not a bare
boolean. The structured failures are: a FABRICATED step (claimed but never run),
a HIDDEN step (run and causal but not disclosed = a hidden goal), and a DISTORTED
step (claimed justification ≠ actual). We compute the witness/obstruction
concretely. We do NOT run a proof assistant; full HoTT/STT proofs would need
Lean/Agda/cubical and are out of scope here.

INTENT is a CONSTRAINED optimization, not a weighted trade-off. Honesty is a HARD
CONSTRAINT — never a term with a price. Intent maximizes a domain utility *within*
the honest feasible set (lexicographic order), so honesty can never be bought off
by a high-utility lie. When the preferred action is infeasible, OPTIMUS searches
honest alternatives; if none are found within budget, the system ABSTAINS.

TRUTHFULNESS (reasoning matches the world) is a SEPARATE problem and the domain's
job, expressed via `domain_invariants` — not this module's.

────────────────────────────────────────────────────────────────────────────
LIMITS (read before trusting it)
────────────────────────────────────────────────────────────────────────────
• Sincerity is *proved* only when the trace you pass is genuinely the causal
  driver of the action AND is inspectable (symbolic). For black-box / neural
  reasoning there is no such trace, so use MEASURED mode (consistency /
  calibration / intervention probes): that BOUNDS insincerity, it does not
  guarantee honesty.
• This module does not make a system honest. It (a) detects insincerity given a
  faithful trace and (b) structures intent so honesty is not tradeable. Garbage
  trace in → garbage verdict out.
• The candidate space may be infinite; we bound it and abstain rather than
  pretend to search exhaustively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (Any, Callable, Dict, Iterable, List, Optional, Protocol,
                    runtime_checkable)


# ───────────────────────────── reasoning + statement ────────────────────────

@dataclass(frozen=True)
class ReasoningStep:
    """One step the system ACTUALLY performed."""
    id: str
    op: str                      # what was done
    justification: str = ""      # why
    causal: bool = True          # did this step actually drive the outcome?


@dataclass
class ReasoningTrace:
    """The actual derivation. In a symbolic system this is inspectable truth."""
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""


@dataclass(frozen=True)
class ClaimedStep:
    """One step the system CLAIMS (in its explanation) that it performed."""
    id: str
    op: str
    justification: str = ""


@dataclass
class Statement:
    """The stated explanation offered to the user."""
    claimed_steps: List[ClaimedStep] = field(default_factory=list)
    claimed_conclusion: str = ""


# ───────────────────────────── sincerity (the HoTT path) ────────────────────

class Obstruction(Enum):
    FABRICATED = "fabricated_step"        # claimed but never actually run
    HIDDEN = "hidden_causal_step"         # run + causal but not disclosed
    DISTORTED = "distorted_justification"  # claimed != actual reasoning
    CONCLUSION_MISMATCH = "conclusion_mismatch"


@dataclass
class SincerityResult:
    sincere: bool
    mode: str                              # "proved" | "measured"
    score: float                           # 1.0 if proved-sincere; else in [0,1]
    witness: Dict[str, str] = field(default_factory=dict)   # claimed_id -> actual_id
    obstructions: List[Dict[str, str]] = field(default_factory=list)

    def to_cog_verdict(self) -> str:
        """Speak COG's vocabulary. Insincere = HOLLOW (structurally impossible)."""
        return "AGREE" if self.sincere else "HOLLOW"


def check_sincerity(trace: ReasoningTrace, statement: Statement) -> SincerityResult:
    """
    Build the identification between what was CLAIMED and what was DONE.

    Sincere iff the explanation functor is full & faithful on the causal trace:
      - no FABRICATED claim (every claimed step maps to an actual step)
      - no HIDDEN causal step (every causal actual step is disclosed)
      - no DISTORTED justification (matched steps agree)
      - conclusion matches
    This has teeth ONLY when `trace` is the real causal driver (symbolic mode).
    """
    actual_by_id = {s.id: s for s in trace.steps}
    obstructions: List[Dict[str, str]] = []
    witness: Dict[str, str] = {}

    # Fabricated / distorted: walk the claims.
    for c in statement.claimed_steps:
        a = actual_by_id.get(c.id)
        if a is None:
            # try op-match before declaring fabrication
            a = next((s for s in trace.steps if s.op == c.op
                      and s.id not in witness.values()), None)
        if a is None:
            obstructions.append({"kind": Obstruction.FABRICATED.value,
                                 "detail": f"claimed '{c.op}' ({c.id}) was never run"})
            continue
        witness[c.id] = a.id
        if c.justification and a.justification and c.justification != a.justification:
            obstructions.append({"kind": Obstruction.DISTORTED.value,
                                 "detail": f"step {a.id}: claimed '{c.justification}' "
                                           f"vs actual '{a.justification}'"})

    # Hidden: causal actual steps that were never disclosed.
    disclosed = set(witness.values())
    for s in trace.steps:
        if s.causal and s.id not in disclosed:
            obstructions.append({"kind": Obstruction.HIDDEN.value,
                                 "detail": f"causal step {s.id} ('{s.op}') not disclosed"})

    if (statement.claimed_conclusion and trace.conclusion
            and statement.claimed_conclusion != trace.conclusion):
        obstructions.append({"kind": Obstruction.CONCLUSION_MISMATCH.value,
                             "detail": f"claimed '{statement.claimed_conclusion}' "
                                       f"vs actual '{trace.conclusion}'"})

    sincere = not obstructions
    # proved-score is binary; a partial score is informative for triage/logging
    n_claims = max(1, len(statement.claimed_steps) + 1)  # +1 for conclusion
    score = 1.0 if sincere else max(0.0, 1.0 - len(obstructions) / n_claims)
    return SincerityResult(sincere=sincere, mode="proved", score=score,
                           witness=witness, obstructions=obstructions)


def measured_sincerity(probes: Dict[str, float], threshold: float = 0.7
                       ) -> SincerityResult:
    """
    Fallback for non-inspectable (neural) reasoning. `probes` are named scores
    in [0,1], e.g. {"paraphrase_consistency":.., "calibration":.., "faithfulness":..}.
    BOUNDS insincerity; does not prove honesty. Score is the weakest link.
    """
    if not probes:
        return SincerityResult(False, "measured", 0.0,
                               obstructions=[{"kind": "no_probe",
                                              "detail": "no measurement available"}])
    score = min(probes.values())
    sincere = score >= threshold
    obs = [] if sincere else [{"kind": "low_probe",
                               "detail": f"weakest probe {score:.2f} < {threshold}"}]
    return SincerityResult(sincere, "measured", score, obstructions=obs)


# ───────────────────────────── domain plug-in surface ───────────────────────

@runtime_checkable
class DomainAdapter(Protocol):
    """Implement ONE of these per repo. Everything above stays unchanged."""

    def candidate_actions(self, context: Any) -> Iterable[Any]:
        """Possibly-infinite, lazily generated candidate actions."""

    def planned_trace(self, candidate: Any, context: Any) -> ReasoningTrace:
        """The reasoning the candidate WOULD actually run (its causal trace)."""

    def planned_statement(self, candidate: Any, context: Any) -> Statement:
        """The explanation the candidate WOULD give to the user."""

    def domain_invariants(self, candidate: Any, context: Any) -> List[str]:
        """Truthfulness/safety violations (empty list = none). Domain's job."""

    def utility(self, candidate: Any, context: Any) -> float:
        """How good this candidate is at the INTENT, ignoring honesty."""


# ───────────────────────────── intent = constrained search ──────────────────

class DecisionKind(Enum):
    ACT = "act"
    ABSTAIN = "abstain"


@dataclass
class Decision:
    kind: DecisionKind
    candidate: Optional[Any]
    rationale: str
    # full audit trail — every candidate and why it was kept/dropped
    considered: List[Dict[str, Any]] = field(default_factory=list)


def _is_honest_and_valid(candidate, context, adapter: DomainAdapter,
                         cog=None) -> SincerityResult:
    """Hard feasibility test for one candidate. Returns the sincerity result;
    domain-invariant breaches are folded in as a REJECT-style obstruction."""
    trace = adapter.planned_trace(candidate, context)
    stmt = adapter.planned_statement(candidate, context)
    res = check_sincerity(trace, stmt)

    invs = adapter.domain_invariants(candidate, context)
    if invs:
        res = SincerityResult(False, res.mode, min(res.score, 0.0), res.witness,
                              res.obstructions + [{"kind": "domain_invariant",
                                                   "detail": v} for v in invs])
    # Optional COG delegation: if the repo's engine says HOLLOW, it's infeasible.
    if cog is not None and hasattr(cog, "verify_morphism"):
        try:
            verdict = cog.verify_morphism(candidate)            # duck-typed
            if str(verdict).upper().find("HOLLOW") >= 0:
                res = SincerityResult(False, res.mode, 0.0, res.witness,
                                      res.obstructions + [{"kind": "cog_hollow",
                                                           "detail": str(verdict)}])
        except Exception:
            pass
    return res


def decide(context: Any, adapter: DomainAdapter, *, cog=None, optimus=None,
           max_candidates: int = 256) -> Decision:
    """
    Lexicographic intent optimization:
      1. FILTER candidates to the honest + valid feasible set (hard constraint).
      2. Among feasible, MAXIMIZE domain utility.
      3. If none feasible, ask OPTIMUS for honest alternatives.
      4. If still none, ABSTAIN (escalate) — never emit an infeasible action.

    Honesty is never scalarized against utility, so a high-utility lie can never win.
    """
    considered: List[Dict[str, Any]] = []
    feasible: List[Any] = []

    def evaluate(pool: Iterable[Any], source: str):
        for i, cand in enumerate(pool):
            if i >= max_candidates:
                considered.append({"candidate": "…", "note":
                                   f"hit budget {max_candidates}; remaining branches unsearched"})
                break
            res = _is_honest_and_valid(cand, context, adapter, cog=cog)
            considered.append({"candidate": repr(cand), "source": source,
                               "feasible": res.sincere,
                               "utility": adapter.utility(cand, context) if res.sincere else None,
                               "obstructions": res.obstructions})
            if res.sincere:
                feasible.append(cand)

    evaluate(adapter.candidate_actions(context), "domain")

    if not feasible and optimus is not None and hasattr(optimus, "alternatives"):
        try:
            evaluate(optimus.alternatives(context), "optimus")   # duck-typed
        except Exception:
            pass

    if not feasible:
        return Decision(DecisionKind.ABSTAIN, None,
                        "no honest, valid action within budget — escalate to a "
                        "human or a heavier reasoner", considered)

    best = max(feasible, key=lambda c: adapter.utility(c, context))
    return Decision(DecisionKind.ACT, best,
                    f"best of {len(feasible)} honest candidate(s) by utility "
                    f"{adapter.utility(best, context):.3f}", considered)


# ───────────────────────────── runnable self-test ───────────────────────────

if __name__ == "__main__":
    # Toy domain: pick a "reply". A high-utility reply LIES (hides a causal
    # step); an honest reply has lower utility. The constraint must reject the lie.
    @dataclass
    class Reply:
        name: str
        util: float
        hides_step: bool

    class ToyAdapter:
        def candidate_actions(self, ctx):
            return [Reply("persuasive_but_hides_motive", 0.95, True),
                    Reply("honest_but_plainer", 0.60, False)]

        def planned_trace(self, c: Reply, ctx):
            steps = [ReasoningStep("s1", "consult_data", "looked up facts"),
                     ReasoningStep("s2", "pursue_engagement_goal",
                                   "optimize for clicks", causal=True)]
            return ReasoningTrace(steps, conclusion="recommend X")

        def planned_statement(self, c: Reply, ctx):
            claims = [ClaimedStep("s1", "consult_data", "looked up facts")]
            if not c.hides_step:                       # honest reply discloses s2
                claims.append(ClaimedStep("s2", "pursue_engagement_goal",
                                          "optimize for clicks"))
            return Statement(claims, claimed_conclusion="recommend X")

        def domain_invariants(self, c, ctx):
            return []

        def utility(self, c: Reply, ctx):
            return c.util

    d = decide(context={}, adapter=ToyAdapter())
    print("DECISION:", d.kind.value, "->",
          d.candidate.name if d.candidate else None)
    print("RATIONALE:", d.rationale)
    for row in d.considered:
        print(f"  - {row['candidate']:<40} feasible={row['feasible']} "
              f"util={row['utility']} obstructions={[o['kind'] for o in row['obstructions']]}")
    assert d.candidate is not None and d.candidate.name == "honest_but_plainer", \
        "constraint failed: the high-utility lie should have been rejected"
    print("\nOK: the high-utility lie was rejected; honesty was a constraint, not a price.")
