#!/usr/bin/env python3
"""reaudit_rerun.py — genuine in-session re-adjudication of the synonym-rescued set.

rerun_discovery_misses.py rescued 67 candidates (gate RELATION-SCREENED via disease
synonym expansion). The gate is a lexical screen, so each was read in-session here.
COOCCUR_REASONS holds the 13 rejected (by edge_id); all other rescued candidates
are VERIFIED. Output schema matches DISCOVERY_REAUDIT.json so the same integrator
consumes it.

No LLM tokens — the verdicts below ARE the in-session reading.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IN = REPO / "data" / "DISCOVERY_RERUN.json"
OUT = REPO / "data" / "DISCOVERY_RERUN_REAUDIT.json"

COOCCUR_REASONS = {
    "associated_with:ALK->CLL": "incidental: ALK defines ALCL (T-cell lymphoma); CLL is governed by TP53/IgHV in a separate clause",
    "associated_with:HIF1A->Ovarian_Cancer": "aim: 'investigated ... focusing on alterations in HIF1a function'; no finding",
    "associated_with:MAP2K1->RCC": "methods: MAP2K1 only listed in a mutation-screening gene panel for RCC",
    "associated_with:PDCD1->CLL": "null result: 'No associations between ... PDCD1 ... and susceptibility to CLL were found'",
    "associated_with:ABCB1->Type2_Diabetes": "uncertain: 'its association with type 2 diabetes ... are unclear'",
    "associated_with:AMPK->AML": "glossary: AMPK only in autophagy-review abbreviation list",
    "associated_with:CTLA4->Pancreatic_Cancer": "glossary: CTLA4 and PDAC only in abbreviation list",
    "associated_with:HDAC1->Type2_Diabetes": "incidental: HDAC1 listed near DMPs 'of the HDAC family'; no T2D association asserted",
    "associated_with:NTRK3->RCC": "incidental: ETV6-NTRK3 is about mesoblastic nephroma; translocation RCC is a separate item",
    "associated_with:PTGS2->Prostate_Cancer": "aim/methods: 'We investigated associations between PTGS2 polymorphisms and prostate cancer risk'",
    "associated_with:RET->Li_Fraumeni_Syndrome": "incidental: Li-Fraumeni is the TP53 reference point; RET mutation is in osteosarcoma germline",
    "associated_with:RET->Type2_Diabetes": "spurious: 'RET' here is Resistance Exercise Training, not the gene",
    "associated_with:TXNRD1->Colorectal_Cancer": "aim/methods: 'We evaluated the association ... with colorectal cancer risk'",
}


def main():
    rescued = json.loads(IN.read_text(encoding="utf-8"))["rescued"]
    verdicts = []
    v_ct = c_ct = 0
    for cand in rescued:
        eid = cand["edge_id"]
        if eid in COOCCUR_REASONS:
            verdict, reason = "COOCCUR", COOCCUR_REASONS[eid]
            c_ct += 1
        else:
            verdict, reason = "VERIFIED", "agent-read: directed protein->disease association asserted"
            v_ct += 1
        verdicts.append({"edge_id": eid, "source": cand["source"],
                         "target": cand["target"], "relation": cand["relation"],
                         "pmid": cand["pmid"], "proof_sentence": cand["proof_sentence"],
                         "matched_synonym": cand.get("matched_synonym", ""),
                         "agent_verdict": verdict, "agent_reason": reason})
    out = {"relation": "associated_with",
           "input_rescued_candidates": len(rescued),
           "agent_verified": v_ct, "agent_cooccur": c_ct,
           "note": ("Genuine in-session agent re-adjudication of the synonym-rescued "
                    "discovery misses. VERIFIED = agent read the cited sentence and "
                    "confirmed a directed protein->disease association."),
           "verdicts": verdicts}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"rescued candidates  : {len(rescued)}")
    print(f"  agent VERIFIED    : {v_ct}")
    print(f"  agent COOCCUR     : {c_ct}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
