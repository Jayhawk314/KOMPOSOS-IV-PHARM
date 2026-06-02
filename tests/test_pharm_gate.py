"""Regression tests for the komposos_kg pharm write gate + honesty wiring."""
from komposos_kg import Edge, KGMemory
from komposos_kg.pharm_verifier import PharmCitationVerifier, VERDICT_TO_TIER


def _edge(sub, rel, obj, evidence):
    return Edge(subject=sub, relation=rel, object=obj,
                source="PMID:1", evidence=evidence)


def test_content_agree_on_signed_relation():
    v = PharmCitationVerifier()
    verdict, _ = v(_edge("Vemurafenib", "inhibits", "BRAF",
                         "Vemurafenib potently inhibits BRAF V600E kinase activity."), [])
    assert verdict == "AGREE"


def test_content_hollow_on_cooccurrence_only():
    v = PharmCitationVerifier()
    verdict, reason = v(_edge("ERK1", "activates", "MYC",
                              "ERK1 and MYC were both detected in the tumor samples."), [])
    assert verdict == "HOLLOW"           # both present, no relation keyword
    assert "co-occurrence" in reason


def test_content_reject_when_entity_missing():
    v = PharmCitationVerifier()
    verdict, _ = v(_edge("Sorafenib", "inhibits", "BRAF",
                         "Sorafenib was administered to the patient cohort."), [])
    assert verdict == "REJECT"           # BRAF not mentioned


def test_polarity_conflict_quarantines():
    v = PharmCitationVerifier()
    # asserting activation but sentence says decreased -> conflict
    verdict, reason = v(_edge("DrugX", "activates", "TargetY",
                              "DrugX markedly decreased TargetY expression."), [])
    assert verdict == "HOLLOW"
    assert "polarity" in reason


def test_gate_never_mints_published_verified_tier():
    # the automated screen must map AGREE -> RELATION-SCREENED, not RELATION-VERIFIED
    assert VERDICT_TO_TIER["AGREE"] == "RELATION-SCREENED"
    assert VERDICT_TO_TIER["HOLLOW"] == "LEXICAL-COOCCURRENCE"


def test_memory_quarantines_hollow_from_recall():
    mem = KGMemory(verifier=PharmCitationVerifier())
    mem.remember("Vemurafenib", "inhibits", "BRAF",
                 source="PMID:1", evidence="Vemurafenib inhibits BRAF kinase.")
    mem.remember("ERK1", "activates", "MYC",
                 source="PMID:2", evidence="ERK1 and MYC co-occur in samples.")
    recalled = {e.id for e in mem.recall()}
    assert "Vemurafenib|inhibits|BRAF" in recalled
    assert "ERK1|activates|MYC" not in recalled        # HOLLOW quarantined


def test_honesty_flags_fabricated_citation():
    mem = KGMemory(verifier=PharmCitationVerifier())
    mem.remember("Vemurafenib", "inhibits", "BRAF",
                 source="PMID:1", evidence="Vemurafenib inhibits BRAF kinase.")
    mem.recall(agent="A")
    good = mem.explain_action("act", ["Vemurafenib|inhibits|BRAF"], agent="A")
    bad = mem.explain_action("act", ["Fake|treats|Nothing"], agent="A")
    assert good.sincere is True
    assert bad.sincere is False
    assert any(o["kind"] == "fabricated_step" for o in bad.obstructions)
