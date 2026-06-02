#!/usr/bin/env python3
"""reaudit_207.py — genuine in-session re-adjudication of the discovery 207.

Background: adjudicate_discoveries.py claimed "in-session agent reading" but is a
keyword classifier (it stamps VERIFIED on any 'associat'/'overexpress'/'linked'
substring, including methods/aim sentences, glossary abbreviation lists, null
results, and spurious gene-name matches). Two defects in the 207:

  1. 76 were disease->disease edges (the gap generator treated diseases reached by
     a drug 'treats' edge as druggable targets) -> dropped, not mechanistic.
  2.  2 were drug->disease edges (leakage-prone) -> dropped.
  -> 129 protein->disease candidates remained for genuine reading.

This file records the AGENT's verdict after reading every one of the 129 proof
sentences. COOCCUR_REASONS holds the 32 rejected candidates (by edge_id) with the
reason. All other 129 candidates are VERIFIED. Output: data/DISCOVERY_REAUDIT.json.

No LLM tokens — the verdicts below ARE the in-session reading.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANDS = REPO / "data" / "_reaudit_candidates.json"     # 129 protein->disease
OUT = REPO / "data" / "DISCOVERY_REAUDIT.json"

# edge_id -> reason it FAILS genuine adjudication (everything else = VERIFIED)
COOCCUR_REASONS = {
    "associated_with:ABCB1->CML": "aim-only: 'study aimed to evaluate the association'; no finding asserted",
    "associated_with:ABCB1->GIST": "incidental: ABCB1 polymorphism vs imatinib plasma level; GIST is patient cohort",
    "associated_with:ABCB1->RCC": "aim + incidental: polymorphism vs sunitinib toxicity in RCC patients",
    "associated_with:ABL1->Ewing_Sarcoma": "incidental: ABL1 fusion is in the leukemias listed; Ewing carries EWS-FLI1",
    "associated_with:ALDH2->Colorectal_Cancer": "methods/aim: case-control 'to evaluate the associations'; no result in sentence",
    "associated_with:ALK->Breast_Cancer": "glossary: ALK and disease only in abbreviation list",
    "associated_with:ALK->HCC": "glossary: abbreviation list only",
    "associated_with:AMPK->HCC": "glossary: NASH/autophagy abbreviation list only",
    "associated_with:AMPK->Melanoma": "glossary: abbreviation list only",
    "associated_with:AMPK->NSCLC": "incidental: AMPK only as pathway-axis name; association is about macrophages",
    "associated_with:CD274->Pancreatic_Cancer": "glossary: CD274/PDL1 only in abbreviation list",
    "associated_with:COX2->HCC": "glossary: PTGS2/COX2 only in abbreviation list",
    "associated_with:CRBN->CML": "glossary: PROTAC review abbreviation list only",
    "associated_with:CRBN->NSCLC": "glossary: abbreviation list only",
    "associated_with:CTLA4->CLL": "spurious: 'CLL-1' is a gene (CLEC12A); disease in sentence is AML, not CLL",
    "associated_with:HDAC2->NSCLC": "uncertain: 'functions of HDAC2 ... in NSCLC remain unclear'",
    "associated_with:HIF1A->Breast_Cancer": "glossary: HIF1A and disease only in abbreviation list",
    "associated_with:HIF1A->CML": "glossary: abbreviation list only",
    "associated_with:HMGCR->Melanoma": "glossary: abbreviation list only",
    "associated_with:HMGCR->NSCLC": "glossary: abbreviation list only",
    "associated_with:HMGCR->RCC": "null result: 'no significant association ... and RCC risk'",
    "associated_with:HRH2->Breast_Cancer": "null result: 'did not find any significant associations ... not a risk factor'",
    "associated_with:MMP1->CLL": "spurious: 'B-cell CLL/lymphoma 2 (BCL2)' is a gene; MMP1 overexpressed in adenomas, not CLL",
    "associated_with:MMP1->Ovarian_Cancer": "null result: 'no associations were found between MMP1 rs1799750 ... and ovarian cancer'",
    "associated_with:MMP2->CML": "glossary: abbreviation list only",
    "associated_with:MMP7->RCC": "incidental: sentence is about COP1 in RCC; MMP7 is a downstream readout",
    "associated_with:PTGS2->HCC": "glossary: PTGS2/COX2 only in abbreviation list",
    "associated_with:TGFB1->HCC": "glossary: NASH abbreviation list only",
    "associated_with:TGFB1->NSCLC": "glossary: HNSCC autophagy abbreviation list only",
    "associated_with:TOP1->HCC": "aim-only: 'study aimed to investigate the prognostic significance'",
    "associated_with:TOP1->Ovarian_Cancer": "incidental: TOP1 inhibitor is the breast-cancer context; ovarian re platinum",
    "associated_with:TYMS->NSCLC": "aim/methods: meta-analysis 'to assess the association' of TYMS with drug outcome",
}


def main():
    cands = json.loads(CANDS.read_text(encoding="utf-8"))
    verdicts = []
    v_ct = c_ct = 0
    for cand in cands:
        eid = cand["edge_id"]
        if eid in COOCCUR_REASONS:
            verdict, reason = "COOCCUR", COOCCUR_REASONS[eid]
            c_ct += 1
        else:
            verdict, reason = "VERIFIED", "agent-read: directed protein->disease association asserted"
            v_ct += 1
        verdicts.append({**{k: cand[k] for k in
                            ("edge_id", "source", "target", "relation", "pmid",
                             "proof_sentence")},
                         "agent_verdict": verdict, "agent_reason": reason})
    out = {
        "relation": "associated_with",
        "input_protein_disease_candidates": len(cands),
        "agent_verified": v_ct,
        "agent_cooccur": c_ct,
        "note": ("Genuine in-session agent re-adjudication of the discovery-207 "
                 "protein->disease subset. Supersedes adjudicate_discoveries.py "
                 "(a keyword classifier). VERIFIED here = agent read the cited "
                 "sentence and confirmed a directed protein->disease association. "
                 "76 disease->disease and 2 drug->disease candidates were dropped "
                 "upstream as invalid."),
        "verdicts": verdicts,
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"protein->disease candidates : {len(cands)}")
    print(f"  agent VERIFIED            : {v_ct}")
    print(f"  agent COOCCUR (rejected)  : {c_ct}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
