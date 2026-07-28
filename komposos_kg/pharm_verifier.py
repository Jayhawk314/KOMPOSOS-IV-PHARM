# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""pharm_verifier.py — a CONTENT verifier for the KGMemory write gate.

This is the piece the stock `CogVerifier` skips. CogVerifier accepts any fact
that merely *has* a source/evidence string (it only annotates evidenced facts
with COG's structural verdict). It never reads the evidence. So a PMID-bearing
pharm edge passes the gate regardless of whether the cited sentence supports the
relation.

`PharmCitationVerifier` reads `edge.evidence` (the proof sentence) and judges
whether it asserts the **directed, signed** relation:

    REJECT  — no evidence, or the sentence does not mention BOTH entities
    HOLLOW  — both entities present, but no relation keyword / polarity conflict
              (this is co-occurrence only -> the project's LEXICAL-COOCCURRENCE tier)
    AGREE   — both entities + a relation-specific keyword + consistent polarity
              (relation-supported -> eligible for the RELATION-VERIFIED tier)

HONEST SCOPE (read before trusting):
    AGREE means the sentence LEXICALLY asserts the directed relation (entity +
    signed keyword + no polarity conflict). That is a strong SCREEN, not full
    semantic entailment. It is an UPPER BOUND on relation support. Agent/human
    adjudication remains the gold standard; this gate is what you run before
    adjudication, or as an automated quarantine so co-occurrence cites never get
    labeled "verified" by default. See `validate_gate.py` for how closely it
    matches the in-session adjudication on the existing 737 edges.

No LLM tokens. Pure lexical logic, mirroring the relation/polarity rules already
used across the repo's provenance pipeline.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Directed/signed keyword stems per relation. Presence of a stem (with both
# entities) is the lexical signal that the relation — not mere co-mention — is
# asserted.
RELATION_KEYWORDS = {
    "inhibits":          ["inhib", "antagon", "block", "suppress", "downregulat",
                          "abrogat", "potency", "ic50", "deplet", "silenc", "knockdown"],
    "indirect_inhibitor":["inhib", "block", "suppress", "downregulat", "reduc",
                          "indirect", "deplet", "attenuat"],
    "activates":         ["activat", "agonist", "induc", "upregulat", "stimulat",
                          "potentiat", "promot", "trigger"],
    "associated_with":   ["associat", "linked", "implicat", "correlat", "overexpress",
                          "mutation", "polymorphism", "prognostic", "biomarker"],
    "treats":            ["treat", "therap", "clinical trial", "effica", "approv",
                          "indicat", "respon", "survival"],
    "driver_of":         ["driver", "drives", "caus", "oncogen", "tumorigen",
                          "pathogenesis", "promot"],
    "binds":             ["bind", "affinity", "complex with", "engage", "dock",
                          "kd", "ki", "co-crystal"],
    "interacts":         ["interact", "binds", "complex", "physical", "co-immunoprecipitat"],
    "phosphorylates":    ["phosphorylat"],
    "synergizes_with":   ["synerg", "combin", "potentiat", "additive", "co-treat"],
}

# Polarity guards: a relation with a clear sign is contradicted by opposite cues
# in the same sentence (e.g. "activates" but the sentence says "decreased").
_POS_CUES = ["increas", "upregulat", "induct", "enhanc", "activat", "promot", "elevat"]
_NEG_CUES = ["decreas", "reduc", "loss of", "abrogat", "suppress", "downregulat",
             "blockade", "inhibit", "attenuat"]

_POLARITY = {
    "activates": _NEG_CUES,            # asserting activation, contradicted by negative cues
    "driver_of": _NEG_CUES,
    "inhibits": _POS_CUES,             # asserting inhibition, contradicted by positive cues
    "indirect_inhibitor": _POS_CUES,
}


def _term_present(term: str, sentence: str) -> bool:
    """Word-boundary match (with optional trailing 's'); gene symbols like MET
    won't match inside 'metabolism'."""
    return re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE) is not None


def _polarity_conflict(sent_lower: str, relation: str) -> bool:
    cues = _POLARITY.get(relation)
    if not cues:
        return False
    return any(c in sent_lower for c in cues)


class PharmCitationVerifier:
    """KGMemory verifier: callable (edge, existing) -> (verdict, reason).

    Reads the proof sentence in `edge.evidence` and judges directed/signed
    relation support. Stateless; does not consult the graph (pass it through
    `CompositeVerifier` if you also want COG's structural opinion).
    """

    def __call__(self, edge, existing: List = None) -> Tuple[str, str]:
        sent = (edge.evidence or "").strip()
        if not sent:
            return "REJECT", "no proof sentence"

        src = edge.subject.replace("_", " ")
        tgt = edge.object.replace("_", " ")
        rel = edge.relation

        if not (_term_present(src, sent) and _term_present(tgt, sent)):
            return "REJECT", f"sentence does not mention both entities ({src}, {tgt})"

        sent_lower = sent.lower()
        if _polarity_conflict(sent_lower, rel):
            return "HOLLOW", f"polarity conflict for '{rel}' (co-occurrence only)"

        keywords = RELATION_KEYWORDS.get(rel)
        if keywords is None:
            # relation we have no signed vocabulary for -> cannot assert direction
            return "HOLLOW", f"no relation vocabulary for '{rel}'; co-occurrence only"

        for kw in keywords:
            if kw in sent_lower:
                return "AGREE", f"relation-supported (keyword '{kw}')"

        return "HOLLOW", f"no '{rel}' keyword in sentence (co-occurrence only)"


# Verdict -> provenance tier tag.
# NOTE the deliberate gap: the gate's AGREE maps to RELATION-SCREENED, NOT the
# published RELATION-VERIFIED tier. The screen is ~0.82 precision vs adjudication
# (validate_gate.py), so it must not mint "VERIFIED" on its own — promotion to
# RELATION-VERIFIED requires in-session adjudication. This keeps the automated
# gate from repeating the co-occurrence-as-verified overclaim.
VERDICT_TO_TIER = {
    "AGREE": "RELATION-SCREENED",        # lexical relation support; awaits adjudication
    "HOLLOW": "LEXICAL-COOCCURRENCE",
    "REJECT": "UNCITED",
}
