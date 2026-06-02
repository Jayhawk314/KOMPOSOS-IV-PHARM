#!/usr/bin/env python3
"""discover_morphisms.py — grounded morphism discovery, built on the COG gate.

Discovery = propose a missing edge, find REAL literature for it, and let the
write gate decide. Nothing is auto-written to tier1.db; the output is a set of
candidate morphisms tiered by the gate, ready for adjudication.

Pipeline (no LLM tokens — NCBI eutils only):
    1. CANDIDATES: graph gaps. For every druggable target T (a protein that some
       drug acts on) and every disease D with no existing T->D edge, propose
       `T associated_with D`. Grounding such a link completes a
       drug -> T -> D mechanistic path (a repurposing rationale).
    2. GROUND: search PubMed for a sentence containing both T and D; prefer a
       sentence that also carries a signed relation keyword.
    3. GATE: run the candidate through build_pharm_memory().remember().
         AGREE  -> RELATION-SCREENED  (grounded; awaits adjudication)
         HOLLOW -> LEXICAL-COOCCURRENCE (co-occurrence only; quarantined)
         REJECT -> discarded (no sentence mentions both entities)
    4. EMIT: data/DISCOVERED_MORPHISMS.json. tier1.db is NOT touched.

The gate's AGREE is a lexical screen (~0.82 precision vs adjudication), so a
discovered RELATION-SCREENED edge is a CANDIDATE, never a verified fact.
"""
from __future__ import annotations

import argparse, json, re, sqlite3, time
import requests

from komposos_kg.pharm_gate import build_pharm_memory
from komposos_kg.pharm_verifier import (RELATION_KEYWORDS, VERDICT_TO_TIER,
                                        _term_present, _polarity_conflict)

EMAIL = "research@komposos.org"; TOOL = "KOMPOSOS-IV-PHARM"
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _get(url, params, tries=4):
    for a in range(tries):
        try:
            return requests.get(url, params=params, timeout=45)
        except Exception:
            if a == tries - 1:
                raise
            time.sleep(1.5 * (a + 1))


def graph_gaps(db_path: str, relation: str):
    """Yield (target, relation, disease) for druggable targets x diseases with
    no existing edge. Targets are proteins that some Drug acts on."""
    c = sqlite3.connect(db_path); cur = c.cursor()
    cur.execute("SELECT name, type_name FROM objects")
    objs = {n: t for n, t in cur.fetchall()}
    drugs = {n for n, t in objs.items() if t and "rug" in (t or "")}
    diseases = {n for n, t in objs.items()
                if t and ("isease" in t or "ancer" in t.lower())}
    cur.execute("SELECT source_name, target_name FROM morphisms")
    edges = cur.fetchall(); c.close()
    # A valid mechanistic target is a biological entity a drug acts on -- NOT a
    # disease (drug 'treats' disease) and NOT another drug. Including diseases as
    # targets produced spurious disease->disease gaps in the first run.
    targets = {t for s, t in edges
               if s in drugs and t in objs and t not in diseases and t not in drugs}
    existing = {(s, t) for s, t in edges}
    gaps = [(p, relation, d) for p in sorted(targets) for d in sorted(diseases)
            if (p, d) not in existing and (d, p) not in existing]
    return gaps, diseases


def search_pubmed(term_a: str, term_b: str, k: int = 6):
    q = f'("{term_a}"[Title/Abstract]) AND ("{term_b.replace("_", " ")}"[Title/Abstract])'
    r = _get(ESEARCH, {"db": "pubmed", "term": q, "retmax": k, "retmode": "json",
                       "sort": "relevance", "tool": TOOL, "email": EMAIL})
    return r.json().get("esearchresult", {}).get("idlist", [])


def fetch_abstract(pmid: str) -> str:
    r = _get(EFETCH, {"db": "pubmed", "id": pmid, "retmode": "xml",
                      "tool": TOOL, "email": EMAIL})
    secs = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", r.text, re.DOTALL)
    title = re.findall(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", r.text, re.DOTALL)
    return " ".join(re.sub(r"<[^>]+>", "", s) for s in (title + secs))


def best_proof_sentence(abstract: str, src: str, tgt: str, relation: str):
    """Return (sentence, has_keyword). Prefer a sentence with both entities AND a
    signed keyword; fall back to any sentence with both entities (co-occurrence)."""
    s_name = src.replace("_", " "); t_name = tgt.replace("_", " ")
    keywords = RELATION_KEYWORDS.get(relation, [])
    fallback = None
    for sent in re.split(r"(?<=[.!?])\s+", abstract):
        if _term_present(s_name, sent) and _term_present(t_name, sent):
            if _polarity_conflict(sent.lower(), relation):
                continue
            if any(kw in sent.lower() for kw in keywords):
                return sent.strip(), True
            if fallback is None:
                fallback = sent.strip()
    return (fallback, False) if fallback else (None, False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/drugs/tier1.db")
    ap.add_argument("--relation", default="associated_with")
    ap.add_argument("--limit", type=int, default=25, help="max gaps to probe")
    ap.add_argument("--per-pmid", type=int, default=4, help="abstracts per gap")
    ap.add_argument("--out", default="data/DISCOVERED_MORPHISMS.json")
    args = ap.parse_args()

    gaps, diseases = graph_gaps(args.db, args.relation)
    print(f"Druggable-target x disease gaps: {len(gaps)}; probing {min(args.limit, len(gaps))}")

    mem = build_pharm_memory(use_cog=True, use_optimus=False, domain="discovery")
    backend = "REAL COG" if mem._verify.__class__.__name__ == "CogVerifier" else "content-only"
    print(f"gate backend: {backend}\n")

    screened, quarantined, ungrounded = [], [], []
    for i, (src, rel, tgt) in enumerate(gaps[:args.limit]):
        pmids = search_pubmed(src, tgt, k=args.per_pmid); time.sleep(0.35)
        proof, pmid_used, has_kw = None, None, False
        for pmid in pmids:
            ab = fetch_abstract(pmid); time.sleep(0.35)
            sent, kw = best_proof_sentence(ab, src, tgt, rel)
            if sent and (kw or proof is None):
                proof, pmid_used, has_kw = sent, pmid, kw
                if kw:
                    break
        if not proof:
            ungrounded.append({"source": src, "relation": rel, "target": tgt,
                               "reason": "no abstract mentions both entities"})
            print(f"[{i+1}/{args.limit}] {src}->{tgt}: UNGROUNDED")
            continue

        res = mem.remember(src, rel, tgt, source=f"PMID:{pmid_used}", evidence=proof)
        rec = {"edge_id": f"{rel}:{src}->{tgt}", "source": src, "relation": rel,
               "target": tgt, "pmid": pmid_used, "verdict": res.verdict,
               "tier": VERDICT_TO_TIER.get(res.verdict, "?"),
               "reason": res.reason, "proof_sentence": proof}
        if res.verdict == "AGREE":
            screened.append(rec)
        else:
            quarantined.append(rec)
        print(f"[{i+1}/{args.limit}] {src}->{tgt}: {res.verdict} ({rec['tier']}) PMID:{pmid_used}")

    out = {"relation": args.relation, "gaps_total": len(gaps),
           "probed": min(args.limit, len(gaps)),
           "counts": {"relation_screened": len(screened),
                      "quarantined_cooccurrence": len(quarantined),
                      "ungrounded": len(ungrounded)},
           "note": ("RELATION-SCREENED = grounded lexical screen (~0.82 precision); "
                    "a CANDIDATE for adjudication, NOT a verified fact. tier1.db unchanged."),
           "relation_screened": screened,
           "quarantined": quarantined,
           "ungrounded": ungrounded}
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"\n{'='*60}")
    print(f"DISCOVERY COMPLETE (gate-grounded)")
    print(f"  RELATION-SCREENED candidates : {len(screened)}")
    print(f"  quarantined (co-occurrence)  : {len(quarantined)}")
    print(f"  ungrounded (no literature)   : {len(ungrounded)}")
    print(f"  -> {args.out}  (tier1.db NOT modified)")


if __name__ == "__main__":
    main()
