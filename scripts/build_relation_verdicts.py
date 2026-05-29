#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Records in-session (agent-adjudicated, NO API) relation-extraction verdicts.

For each proof sentence in the adjudication batch, the agent judged whether the
sentence actually ASSERTS the directed, signed relation (Source acts on Target),
versus mere co-occurrence / co-listing / name-ambiguity. Decisions are encoded
below by index and written to data/relation_extraction_verdicts.json.

This is a model adjudication, explicitly NOT human expert curation. It upgrades
only the edges the agent could confirm from the sentence text.
"""

import json

INPUT = "data/_adjudication_input.json"
OUT = "data/relation_extraction_verdicts.json"

# SAMPLE indices judged COOCCUR (sentence does NOT assert the directed relation:
# co-listing, mutation/keyword panels, downstream effect, or gene-symbol ambiguity
# such as SRC matching "SRC-1"/"Src family", glucagon only inside receptor names).
SAMPLE_COOCCUR = {0, 1, 2, 4, 5, 9, 11, 12, 13, 16, 18, 21, 24, 25, 30, 37}

COOCCUR_NOTES = {
    0: "glucagon appears only inside receptor names; sentence is about retatrutide agonism",
    1: "ddPCR mutation panel co-listing BRAF/KRAS; no activation asserted",
    2: "CXCL12-CXCR4 listed among upregulated components; axis not asserted directionally",
    4: "PubMed keyword/polymorphism list; relation not asserted",
    5: "BAX not asserted; sentence about PRP fibroblast effects",
    9: "PDGFRA-melanoma not asserted; melanoma is a drug side-effect risk",
    11: "RB1 not asserted; sentence about CMA-IDH1-CCND1 cascade",
    12: "name ambiguity: 'SRC-1' (NCOA1) is not SRC",
    13: "BRCA2 merely tested in a case; weak co-mention",
    16: "RB1 not asserted; autophagy-in-AML review",
    18: "E2F1 not asserted in the CMA cascade sentence",
    21: "fluorouracil not linked to TOP2A; TOP2A tied to anthracyclines",
    24: "proof sentence is garbled/CJK-encoded; unverifiable",
    25: "BRCA1 appears inside 'BRCA1-associated RING domain' (BARD1)",
    30: "name ambiguity: BLK is Src-family but not SRC itself",
    37: "CHRM1 inhibition attributed to pirenzepine, not atropine, in this sentence",
}


def main():
    data = json.load(open(INPUT))
    verdicts = []

    for e in data["treats"]:
        verdicts.append({
            "edge_id": e["edge_id"], "source": e["source"], "target": e["target"],
            "relation": e["relation"], "pmid": e["pmid"],
            "verdict": "VERIFIED",
            "note": "drug->disease clinical use/efficacy asserted in sentence",
        })

    for i, e in enumerate(data["sample"]):
        if i in SAMPLE_COOCCUR:
            verdicts.append({
                "edge_id": e["edge_id"], "source": e["source"], "target": e["target"],
                "relation": e["relation"], "pmid": e["pmid"],
                "verdict": "COOCCUR",
                "note": COOCCUR_NOTES.get(i, "co-occurrence only; directed relation not asserted"),
            })
        else:
            verdicts.append({
                "edge_id": e["edge_id"], "source": e["source"], "target": e["target"],
                "relation": e["relation"], "pmid": e["pmid"],
                "verdict": "VERIFIED",
                "note": "directed, signed relation asserted in sentence",
            })

    verified = [v for v in verdicts if v["verdict"] == "VERIFIED"]
    cooccur = [v for v in verdicts if v["verdict"] == "COOCCUR"]

    # precision of the lexical+polarity screen, estimated on the random sample only
    sample_verdicts = verdicts[len(data["treats"]):]
    s_ok = sum(1 for v in sample_verdicts if v["verdict"] == "VERIFIED")

    report = {
        "method": "in-session agent adjudication (no API); model judgement, not human expert curation",
        "adjudicated_total": len(verdicts),
        "treats_verified": f"{len(data['treats'])}/{len(data['treats'])}",
        "verified": len(verified),
        "cooccur": len(cooccur),
        "random_sample_precision": round(s_ok / len(sample_verdicts), 3),
        "random_sample_n": len(sample_verdicts),
        "verdicts": verdicts,
    }
    json.dump(report, open(OUT, "w"), indent=2)

    print(f"Adjudicated: {len(verdicts)}  (treats {len(data['treats'])} + sample {len(sample_verdicts)})")
    print(f"  VERIFIED: {len(verified)}   COOCCUR: {len(cooccur)}")
    print(f"  Random-sample precision of lexical screen: {s_ok}/{len(sample_verdicts)} = {s_ok/len(sample_verdicts):.1%}")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
