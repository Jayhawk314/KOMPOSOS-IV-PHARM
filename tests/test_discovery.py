# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Tests for grounded morphism discovery (pure logic; no network)."""
from discover_morphisms import best_proof_sentence


ABSTRACT = (
    "Background. We studied resistance mechanisms in cancer. "
    "ABCB1 overexpression was strongly associated with multidrug resistance in colorectal cancer. "
    "ABCB1 and melanoma were both present in the cohort. "
    "ABCB1 markedly decreased apoptosis in the treated arm."
)


def test_prefers_keyword_bearing_sentence():
    sent, has_kw = best_proof_sentence(ABSTRACT, "ABCB1", "Colorectal_Cancer", "associated_with")
    assert has_kw is True
    assert "associated with multidrug resistance" in sent


def test_falls_back_to_cooccurrence_without_keyword():
    sent, has_kw = best_proof_sentence(ABSTRACT, "ABCB1", "melanoma", "associated_with")
    assert has_kw is False                       # co-occurrence sentence, no relation keyword
    assert sent is not None
    assert "melanoma" in sent


def test_returns_none_when_entity_absent():
    sent, has_kw = best_proof_sentence(ABSTRACT, "ABCB1", "Glioblastoma", "associated_with")
    assert sent is None                          # glioblastoma not in abstract


def test_polarity_conflict_sentence_skipped():
    # 'activates' asserted but the only co-mention says 'decreased' -> skip it
    sent, has_kw = best_proof_sentence(ABSTRACT, "ABCB1", "apoptosis", "activates")
    assert sent is None
