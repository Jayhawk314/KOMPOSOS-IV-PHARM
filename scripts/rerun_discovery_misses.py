#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""rerun_discovery_misses.py — second-pass grounding for discovery misses.

The first discovery pass (discover_morphisms.py) left two buckets unrescued:
  - quarantined (HOLLOW): a co-occurrence sentence + PMID, but no signed-relation
    keyword sentence was found.
  - ungrounded: no abstract sentence mentioned both entities at all.

Root cause for most misses: the disease nodes are ABBREVIATIONS (HCC, RCC, AML,
CML, NSCLC, GIST, ...). PubMed and the sentence matcher were querying the literal
token, but abstracts spell the disease out ("hepatocellular carcinoma"). This
second pass expands each disease to its synonyms in BOTH the PubMed query and the
sentence matcher, and searches deeper.

The matched synonym is what is handed to the gate (so the gate's own term check
sees the text that is actually in the sentence); the canonical abbreviation is
what gets recorded in edge_id. tier1.db is NOT touched — output is a worklist.

No LLM tokens — NCBI eutils only.

Usage:
    python scripts/rerun_discovery_misses.py --limit 0      # all misses
    python scripts/rerun_discovery_misses.py --only quarantined --limit 50
"""
from __future__ import annotations

import argparse, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from discover_morphisms import (fetch_abstract, _get, ESEARCH, TOOL, EMAIL)
from komposos_kg.pharm_gate import build_pharm_memory
from komposos_kg.pharm_verifier import (RELATION_KEYWORDS, VERDICT_TO_TIER,
                                        _term_present, _polarity_conflict)

REPO = Path(__file__).resolve().parents[1]
IN = REPO / "data" / "DISCOVERED_MORPHISMS.json"
OUT = REPO / "data" / "DISCOVERY_RERUN.json"

# canonical disease node -> search/match synonyms (first entry is canonical text)
DISEASE_SYNONYMS = {
    "AML": ["acute myeloid leukemia", "acute myeloid leukaemia", "AML"],
    "CLL": ["chronic lymphocytic leukemia", "chronic lymphocytic leukaemia", "CLL"],
    "CML": ["chronic myeloid leukemia", "chronic myelogenous leukemia", "CML"],
    "NSCLC": ["non-small cell lung cancer", "non small cell lung cancer",
              "non-small-cell lung carcinoma", "NSCLC"],
    "HCC": ["hepatocellular carcinoma", "liver cancer", "HCC"],
    "RCC": ["renal cell carcinoma", "renal cell cancer", "kidney cancer", "RCC"],
    "GIST": ["gastrointestinal stromal tumor", "gastrointestinal stromal tumour", "GIST"],
    "Breast_Cancer": ["breast cancer", "breast carcinoma"],
    "Colorectal_Cancer": ["colorectal cancer", "colorectal carcinoma", "colon cancer"],
    "Ovarian_Cancer": ["ovarian cancer", "ovarian carcinoma"],
    "Pancreatic_Cancer": ["pancreatic cancer", "pancreatic carcinoma",
                          "pancreatic ductal adenocarcinoma"],
    "Prostate_Cancer": ["prostate cancer", "prostate carcinoma"],
    "Glioblastoma": ["glioblastoma", "glioblastoma multiforme", "GBM"],
    "Multiple_Myeloma": ["multiple myeloma"],
    "Myelofibrosis": ["myelofibrosis", "primary myelofibrosis"],
    "Soft_Tissue_Sarcoma": ["soft tissue sarcoma", "soft-tissue sarcoma"],
    "Ewing_Sarcoma": ["Ewing sarcoma", "Ewing's sarcoma", "Ewing tumor"],
    "Li_Fraumeni_Syndrome": ["Li-Fraumeni syndrome", "Li Fraumeni syndrome",
                             "Li-Fraumeni"],
    "Type2_Diabetes": ["type 2 diabetes", "type II diabetes",
                       "type 2 diabetes mellitus", "T2DM"],
    "Melanoma": ["melanoma", "malignant melanoma"],
}


def syns_for(node: str):
    return DISEASE_SYNONYMS.get(node, [node.replace("_", " ")])


def search_pubmed_syn(src: str, tgt_node: str, k: int):
    syn = syns_for(tgt_node)
    or_block = " OR ".join(f'"{s}"[Title/Abstract]' for s in syn)
    q = f'("{src}"[Title/Abstract]) AND ({or_block})'
    r = _get(ESEARCH, {"db": "pubmed", "term": q, "retmax": k, "retmode": "json",
                       "sort": "relevance", "tool": TOOL, "email": EMAIL})
    return r.json().get("esearchresult", {}).get("idlist", [])


def best_proof_syn(abstract: str, src: str, tgt_node: str, relation: str):
    """Return (sentence, matched_synonym, has_keyword). Target matches if ANY
    synonym is present; matched_synonym is the text actually in the sentence."""
    s_name = src.replace("_", " ")
    keywords = RELATION_KEYWORDS.get(relation, [])
    syn = syns_for(tgt_node)
    fallback = None
    for sent in re.split(r"(?<=[.!?])\s+", abstract):
        if not _term_present(s_name, sent):
            continue
        matched = next((s for s in syn if _term_present(s, sent)), None)
        if not matched:
            continue
        if _polarity_conflict(sent.lower(), relation):
            continue
        if any(kw in sent.lower() for kw in keywords):
            return sent.strip(), matched, True
        if fallback is None:
            fallback = (sent.strip(), matched)
    if fallback:
        return fallback[0], fallback[1], False
    return None, None, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["quarantined", "ungrounded", "both"],
                    default="both")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--per-pmid", type=int, default=5)
    ap.add_argument("--retmax", type=int, default=8)
    args = ap.parse_args()

    data = json.loads(IN.read_text(encoding="utf-8"))
    misses = []
    if args.only in ("quarantined", "both"):
        misses += [{**m, "_from": "quarantined"} for m in data["quarantined"]]
    if args.only in ("ungrounded", "both"):
        misses += [{**m, "_from": "ungrounded"} for m in data["ungrounded"]]

    # drop invalid candidates: source must be a biological entity, not a disease
    # or drug (the original gap generator emitted disease->disease / drug->disease).
    import sqlite3
    cur = sqlite3.connect(REPO / "data" / "drugs" / "tier1.db").cursor()
    types = {n: t for n, t in cur.execute("SELECT name, type_name FROM objects")}

    def valid_src(o):
        t = types.get(o, "") or ""
        return not ("isease" in t or "ancer" in t.lower() or "rug" in t)
    before = len(misses)
    misses = [m for m in misses if valid_src(m["source"])]
    print(f"dropped {before - len(misses)} disease/drug-source candidates")
    if args.limit:
        misses = misses[:args.limit]
    print(f"re-probing {len(misses)} misses "
          f"(per-pmid={args.per_pmid}, retmax={args.retmax})")

    mem = build_pharm_memory(use_cog=True, use_optimus=False, domain="discovery")
    print(f"gate backend: {mem._verify.__class__.__name__}\n")

    rescued, still_quarantined, still_ungrounded = [], [], []
    for i, m in enumerate(misses):
        src, rel, tgt = m["source"], m["relation"], m["target"]
        pmids = search_pubmed_syn(src, tgt, k=args.retmax); time.sleep(0.35)
        proof = matched = pmid_used = None; has_kw = False
        for pmid in pmids[:args.per_pmid]:
            ab = fetch_abstract(pmid); time.sleep(0.35)
            sent, syn, kw = best_proof_syn(ab, src, tgt, rel)
            if sent and (kw or proof is None):
                proof, matched, pmid_used, has_kw = sent, syn, pmid, kw
                if kw:
                    break
        if not proof:
            still_ungrounded.append({"source": src, "relation": rel, "target": tgt,
                                     "reason": "no synonym co-occurrence found"})
            print(f"[{i+1}/{len(misses)}] {src}->{tgt}: STILL UNGROUNDED")
            continue

        # hand the matched synonym (real sentence text) to the gate
        res = mem.remember(src, rel, matched, source=f"PMID:{pmid_used}", evidence=proof)
        rec = {"edge_id": f"{rel}:{src}->{tgt}", "source": src, "relation": rel,
               "target": tgt, "matched_synonym": matched, "pmid": pmid_used,
               "verdict": res.verdict, "tier": VERDICT_TO_TIER.get(res.verdict, "?"),
               "reason": res.reason, "proof_sentence": proof,
               "from_bucket": m["_from"]}
        if res.verdict == "AGREE":
            rescued.append(rec)
        else:
            still_quarantined.append(rec)
        print(f"[{i+1}/{len(misses)}] {src}->{tgt}: {res.verdict} "
              f"({rec['tier']}) via '{matched}' PMID:{pmid_used}")

    out = {"relation": data["relation"], "reprobed": len(misses),
           "per_pmid": args.per_pmid, "retmax": args.retmax,
           "counts": {"rescued_relation_screened": len(rescued),
                      "still_quarantined": len(still_quarantined),
                      "still_ungrounded": len(still_ungrounded)},
           "note": ("RESCUED = newly grounded RELATION-SCREENED via synonym "
                    "expansion; a CANDIDATE for adjudication, NOT verified. "
                    "tier1.db unchanged."),
           "rescued": rescued, "still_quarantined": still_quarantined,
           "still_ungrounded": still_ungrounded}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n{'='*60}\nRERUN COMPLETE")
    print(f"  RESCUED (RELATION-SCREENED) : {len(rescued)}")
    print(f"  still quarantined           : {len(still_quarantined)}")
    print(f"  still ungrounded            : {len(still_ungrounded)}")
    print(f"  -> {OUT}  (tier1.db NOT modified)")


if __name__ == "__main__":
    main()
