#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Directed-relation extractor: decide whether a sentence really asserts
`subject --relation--> object`, for relations where DIRECTION is the claim.

STATUS: EXPERIMENTAL - DOES NOT YET BEAT THE LEXICAL GATE. DO NOT SHIP.
=======================================================================
Tuned on 13 adjudicated AML candidates, where it reached 4/4 precision. On a
HELD-OUT Glioblastoma set (`data/DRIVER_OF_HELDOUT_GBM.json`) it scored:

    directed  precision 3/9  = 0.33   recall 3/5 = 0.60
    lexical   precision 5/15 = 0.33   recall 5/5 = 1.00

Same precision, worse recall. The AML result was overfitting to 13 examples.
Held-out failure modes the guards below do NOT catch:

    PGR    a METHODS sentence with no claim; 'oncogene' appears in a gene name
           -> the LCA scope is far too permissive on long sentences
    NR3C2  "miR-1204 promoted ... through targeting NR3C2" -> NR3C2 is the
           SUPPRESSED target; direction inverted
    VDR    "MED12 ... serves as an oncogene by targeting the VDR/... axis"
           -> wrong subject
    HRH1   "Integrative analysis ... predicts" -> computational prediction
    INSR   "We determined whether ..."          -> interrogative, not a finding
    ACE    a paper TITLE naming a topic         -> not a result

And two false NEGATIVES from over-strict hedging, where "might"/"potential"
attach to a different clause than the assertion (HMGCR, PIK3CD).

Use `--extractor directed` for experiments only. Fixing this properly needs a
biomedical relation-extraction model or a much larger labeled set - not more
hand-written rules, which is what this module demonstrates.

Why this exists
---------------
`PharmCitationVerifier` checks that both entities and a relation keyword appear
in the same sentence. For `associated_with` that is close enough to the claim
itself (~0.82 adjudicated precision). For a directed relation like `driver_of`
it is not: the 2026-07-20 discovery run scored **4/13 = 0.31** adjudicated
precision, because the gate never checks that the keyword ATTACHES to the pair.

The six observed failure modes, each of which has a guard below:

    ESR1   "driver genes ... lower in malignancies not associated with
            estrogens, e.g. AML"          -> CONTRASTIVE (claim is inverted)
    TFPI   "methylation of TFPI-2 promoter" -> keyword 'promot' hit "promoter"
    ROCK2  "The cause ... is still unknown" -> NEGATED / unknown
    SCN5A  "...through promoting apoptosis" -> polarity: promoting CELL DEATH
                                               is a suppressor, not a driver
    KEAP1  "two oncogenes (NrasG12D and MLL-AF9)" -> keyword binds ANOTHER entity
    CD33   "targeting FLT3, IDH1, IDH2"          -> keyword binds ANOTHER entity

Verdicts
--------
    VERIFIED  predicate binds the pair, no negation/hedge/inversion
    HEDGED    asserted but author-hedged ("may", "possible"), or the parse could
              not bind the predicate and only proximity supports it
    REJECTED  negated, inverted, wrong entity, or lexical false positive

Design note: this NEVER mutates PharmCitationVerifier. Discovery for
`associated_with` keeps its calibrated behaviour; only directed relations route
here. spaCy is optional - without it the module degrades to guards + proximity
and returns HEDGED where it would otherwise have confirmed binding.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

# Relations whose whole content is direction. `associated_with` is deliberately
# absent: co-occurrence IS its claim, so it stays on the calibrated lexical gate.
DIRECTED_RELATIONS = {
    "driver_of", "inhibits", "activates", "indirect_inhibitor",
    "phosphorylates", "ubiquitinates", "sequesters",
}

# Morphology-aware keywords. The old vocabulary used bare substrings, so 'promot'
# matched "promoter" (a DNA element, not the verb). These require real word forms.
RELATION_PATTERNS = {
    "driver_of": [
        r"\bdriv(?:e|es|en|ing|er|ers)\b",
        r"\boncogen(?:e|es|ic)\b",
        r"\btumou?rigen(?:ic|esis)\b",
        r"\bcarcinogen(?:ic|esis)\b",
        r"\bpathogenesis\b",
        r"\bcaus(?:e|es|ed|ing|al|ative)\b",
        r"\bpromot(?:e|es|ed|ing|ion)\b",   # NOT "promoter"
        r"\bcontribut(?:e|es|ed|ing)\b",
    ],
    "inhibits": [
        r"\binhibit(?:s|ed|ing|ion|or|ors)?\b", r"\bantagoni(?:se|ze|st|sm)\w*\b",
        r"\bblock(?:s|ed|ing|ade)?\b", r"\bsuppress(?:es|ed|ing|ion)?\b",
        r"\bdownregulat\w+\b", r"\babrogat\w+\b", r"\bsilenc\w+\b",
    ],
    "activates": [
        r"\bactivat(?:e|es|ed|ing|ion)\b", r"\bagonist\b",
        r"\binduc(?:e|es|ed|ing|tion)\b", r"\bupregulat\w+\b",
        r"\bstimulat\w+\b", r"\bpotentiat\w+\b",
        r"\bpromot(?:e|es|ed|ing|ion)\b",
    ],
    "phosphorylates": [r"\bphosphorylat\w+\b"],
}
RELATION_PATTERNS["indirect_inhibitor"] = RELATION_PATTERNS["inhibits"]

# Author hedging -> asserted but not committed.
HEDGE_CUES = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpossibl[ey]\b", r"\bpotential(?:ly)?\b",
    r"\bsuggest(?:s|ed|ing)?\b", r"\bappears? to\b", r"\bseems? to\b",
    r"\blikely\b", r"\bputative\b", r"\bpresumabl[ey]\b", r"\bhypothes\w+\b",
]

# Explicit non-assertion. "the cause is unknown" is not a causal claim.
NEGATION_CUES = [
    r"\bunknown\b", r"\bunclear\b", r"\bnot\s+(?:yet\s+)?(?:known|clear|established|determined)\b",
    r"\bremains?\s+(?:to\s+be|unclear|unknown|elusive)\b", r"\bno\s+evidence\b",
    r"\bfail(?:s|ed)?\s+to\b", r"\bdid\s+not\b", r"\bdoes\s+not\b", r"\bwas\s+not\b",
    r"\bwithout\s+(?:any\s+)?effect\b", r"\bnon-?significant\b",
]

# The claim is being denied or attributed elsewhere for contrast.
CONTRASTIVE_CUES = [
    r"\bnot\s+associated\b", r"\bin\s+contrast\b", r"\bunlike\b", r"\bwhereas\b",
    r"\brather\s+than\b", r"\blower\s+in\b", r"\bless\s+(?:relevant|common|frequent)\b",
    r"\bexcept\b", r"\bother\s+than\b", r"\bas\s+opposed\s+to\b",
]

# Objects whose PROMOTION means tumour SUPPRESSION. "promotes apoptosis" is the
# opposite of driving cancer, but every positive-polarity cue reads it as support.
ANTI_TUMOUR_OBJECTS = [
    r"\bapoptosis\b", r"\bcell\s+death\b", r"\bautophagic\s+death\b",
    r"\bdifferentiation\b", r"\bsenescence\b", r"\bferroptosis\b",
    r"\bpyroptosis\b", r"\bcell\s+cycle\s+arrest\b", r"\bgrowth\s+arrest\b",
    r"\bchemosensitivity\b", r"\bdrug\s+sensitivity\b",
]

# Enumerations that attribute the claim to NAMED OTHER entities:
#   "two oncogenes (NrasG12D and MLL-AF9)"
#   "mutant proteins (e.g., FLT3, IDH1, IDH2)"
# The predicate is real and the subject is elsewhere in the sentence, so a purely
# structural binding test accepts it. Semantically the drivers are the listed genes.
_ENUM_SPAN = re.compile(r"\(([^)]*)\)|(?:such as|including|e\.g\.,?|namely)([^.;]*)",
                        re.IGNORECASE)
# Gene/protein-symbol shape: TP53, MLL-AF9, NrasG12D, IDH1 - letters plus a digit.
_SYMBOL = re.compile(r"\b(?=[A-Za-z\-]*\d)[A-Za-z][A-Za-z0-9\-]{2,}\b")

_NLP = None
_SPACY_TRIED = False


def _attributed_elsewhere(sentence: str, subject: str) -> Optional[str]:
    """Return the offending list if the claim is attributed to other named entities."""
    subj = subject.replace("_", " ").lower()
    for match in _ENUM_SPAN.finditer(sentence):
        span = match.group(1) or match.group(2) or ""
        symbols = [s for s in _SYMBOL.findall(span)]
        # Two or more named symbols, none of them the subject -> the sentence is
        # crediting those entities, not this one.
        if len(symbols) >= 2 and not any(subj == s.lower() or subj in s.lower()
                                         for s in symbols):
            return ", ".join(symbols[:4])
    return None


def _nlp():
    """Lazily load spaCy. Returns None if unavailable - callers degrade gracefully."""
    global _NLP, _SPACY_TRIED
    if _SPACY_TRIED:
        return _NLP
    _SPACY_TRIED = True
    try:
        import spacy
        _NLP = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
    except Exception:
        _NLP = None
    return _NLP


@dataclass(frozen=True)
class ExtractionResult:
    verdict: str          # VERIFIED | HEDGED | REJECTED
    reason: str
    keyword: Optional[str] = None
    bound: bool = False   # True if a dependency path tied predicate to the pair

    @property
    def agrees(self) -> bool:
        return self.verdict == "VERIFIED"


def _find(patterns, text: str) -> Optional[str]:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def _term_present(term: str, sentence: str) -> bool:
    """Word-boundary match tolerant of underscores and plural forms."""
    t = re.escape(term.replace("_", " "))
    return re.search(rf"\b{t}s?\b", sentence, re.IGNORECASE) is not None


def _entity_tokens(doc, term: str):
    """Tokens whose text starts the entity mention (handles TFPI-2, BCL11A, AML)."""
    head = term.replace("_", " ").split()[0].lower()
    return [t for t in doc if t.text.lower() == head or t.text.lower().startswith(head)]


def _lca(a, b):
    """Lowest common ancestor of two tokens in the dependency tree."""
    chain = [a] + list(a.ancestors)
    ancestors_b = {t.i for t in ([b] + list(b.ancestors))}
    for t in chain:
        if t.i in ancestors_b:
            return t
    return None


def _binds_pair(sentence: str, subject: str, obj: str,
                keywords: list[str]) -> Tuple[Optional[bool], Optional[str]]:
    """
    Does any candidate predicate actually govern BOTH entities?

    Uses the lowest common ancestor of the entity pair as the clause boundary: if
    the predicate sits inside that subtree, it is talking about this pair. That
    admits nominalized predicates ("the role of ANGPT2 in the pathogenesis of AML")
    which a verb-only nsubj/dobj test wrongly discards, while still excluding a
    keyword parked in a parenthetical about OTHER entities ("oncogenes (NrasG12D
    and MLL-AF9)").

    Returns (bound, matched_keyword). bound is None when spaCy is unavailable or
    the tokens cannot be located; the caller then downgrades to HEDGED.
    """
    nlp = _nlp()
    if nlp is None:
        return None, None
    doc = nlp(sentence)
    subj_tokens = _entity_tokens(doc, subject)
    obj_tokens = _entity_tokens(doc, obj)
    if not (subj_tokens and obj_tokens):
        return None, None

    located_any = False
    for kw_text in keywords:
        kw_head = kw_text.split()[0].lower()
        stem = kw_head[:6]
        kw_tokens = [t for t in doc if t.text.lower().startswith(stem)]
        if not kw_tokens:
            continue
        located_any = True
        for kw in kw_tokens:
            for st in subj_tokens:
                for ot in obj_tokens:
                    anc = _lca(st, ot)
                    if anc is not None and kw.i in {t.i for t in anc.subtree}:
                        return True, kw_text
                    # Canonical "A drives B": subject governs predicate, object under it.
                    if kw.i in {t.i for t in st.ancestors} and ot.i in {t.i for t in kw.subtree}:
                        return True, kw_text
    return (False, None) if located_any else (None, None)


def extract(sentence: str, subject: str, obj: str, relation: str) -> ExtractionResult:
    """Judge whether `sentence` asserts subject --relation--> obj."""
    sent = (sentence or "").strip()
    if not sent:
        return ExtractionResult("REJECTED", "no proof sentence")

    if not (_term_present(subject, sent) and _term_present(obj, sent)):
        return ExtractionResult("REJECTED", f"sentence lacks both entities ({subject}, {obj})")

    low = sent.lower()

    contra = _find(CONTRASTIVE_CUES, low)
    if contra:
        return ExtractionResult("REJECTED", f"contrastive/inverted claim ('{contra}')")

    neg = _find(NEGATION_CUES, low)
    if neg:
        return ExtractionResult("REJECTED", f"negated or non-assertion ('{neg}')")

    patterns = RELATION_PATTERNS.get(relation)
    if patterns is None:
        return ExtractionResult("REJECTED", f"no directed vocabulary for '{relation}'")

    # Collect EVERY matching predicate, not just the first. A nominalization can
    # match ahead of the real verb ("pathogenesis" before "contributes"), and
    # binding must be allowed to succeed on any of them.
    matches = []
    for p in patterns:
        for m in re.finditer(p, sent, re.IGNORECASE):
            if m.group(0) not in matches:
                matches.append(m.group(0))
    if not matches:
        return ExtractionResult("REJECTED", f"no '{relation}' predicate in sentence")
    keyword = matches[0]

    # Polarity: promoting an anti-tumour process is the suppressor direction.
    if relation in ("driver_of", "activates"):
        anti = _find(ANTI_TUMOUR_OBJECTS, low)
        if anti and re.search(r"\bpromot|induc|activat|enhanc", low):
            return ExtractionResult(
                "REJECTED", f"polarity inversion: promotes anti-tumour process ('{anti}')",
                keyword=keyword,
            )

    attributed = _attributed_elsewhere(sent, subject)
    if attributed:
        return ExtractionResult(
            "REJECTED", f"claim attributed to other named entities ({attributed})",
            keyword=keyword,
        )

    bound, bound_kw = _binds_pair(sent, subject, obj, matches)
    if bound is False:
        return ExtractionResult(
            "REJECTED",
            f"predicate '{keyword}' does not bind {subject}->{obj} (attaches elsewhere)",
            keyword=keyword,
        )

    keyword = bound_kw or keyword

    hedge = _find(HEDGE_CUES, low)
    if hedge:
        return ExtractionResult("HEDGED", f"author-hedged ('{hedge}')", keyword=keyword,
                                bound=bool(bound))

    if bound is None:
        return ExtractionResult(
            "HEDGED", f"predicate '{keyword}' present but binding unverified (no parse)",
            keyword=keyword, bound=False,
        )

    return ExtractionResult("VERIFIED", f"predicate '{keyword}' binds {subject}->{obj}",
                            keyword=keyword, bound=True)
