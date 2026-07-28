#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""validate_gate.py — measure the automated PharmCitationVerifier gate against
the in-session agent adjudication (data/relation_extraction_verdicts.json).

Gate verdict -> predicted class:   AGREE -> VERIFIED ; HOLLOW/REJECT -> COOCCUR
Ground truth: adjudicated verdict  VERIFIED | COOCCUR

Reports a confusion matrix + precision/recall/F1 for the "VERIFIED" class, so we
know how close a pure-lexical write gate gets to human-style adjudication.
No LLM tokens.
"""
import json
from komposos_kg import Edge
from komposos_kg.pharm_verifier import PharmCitationVerifier


def main():
    proofs = {e["edge_id"]: e for e in
              json.load(open("data/action_verified_provenance.json", encoding="utf-8"))}
    truth = {v["edge_id"]: v for v in
             json.load(open("data/relation_extraction_verdicts.json", encoding="utf-8"))["verdicts"]}

    verifier = PharmCitationVerifier()
    tp = fp = tn = fn = 0
    disagreements = []

    eids = [e for e in truth if e in proofs]
    for eid in eids:
        p = proofs[eid]; t = truth[eid]
        edge = Edge(subject=p["source"], relation=p["relation"], object=p["target"],
                    source=f"PMID:{p['pmid']}", evidence=p["proof_sentence"])
        verdict, reason = verifier(edge, [])
        gate_verified = (verdict == "AGREE")
        adj_verified = (t["verdict"] == "VERIFIED")

        if gate_verified and adj_verified:   tp += 1
        elif gate_verified and not adj_verified: fp += 1
        elif not gate_verified and not adj_verified: tn += 1
        else: fn += 1

        if gate_verified != adj_verified:
            disagreements.append({"edge_id": eid, "relation": p["relation"],
                                  "gate": verdict, "reason": reason,
                                  "adjudicated": t["verdict"], "note": t.get("note", "")})

    n = tp + fp + tn + fn
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    acc  = (tp + tn) / n if n else 0.0

    print("=" * 64)
    print("AUTOMATED GATE vs AGENT ADJUDICATION  (n=%d)" % n)
    print("=" * 64)
    print("Confusion (gate predicts VERIFIED):")
    print(f"                 adj=VERIFIED   adj=COOCCUR")
    print(f"  gate=VERIFIED      {tp:>5}        {fp:>5}   (TP / FP)")
    print(f"  gate=COOCCUR       {fn:>5}        {tn:>5}   (FN / TN)")
    print()
    print(f"  Accuracy : {acc:.3f}")
    print(f"  Precision: {prec:.3f}   (of edges the gate calls VERIFIED, how many adj VERIFIED)")
    print(f"  Recall   : {rec:.3f}   (of adj-VERIFIED edges, how many the gate catches)")
    print(f"  F1       : {f1:.3f}")
    print()
    print(f"  FALSE POSITIVES (gate says VERIFIED, adjudication says COOCCUR): {fp}")
    print(f"    -> these would WRONGLY get a RELATION-VERIFIED tag if auto-trusted")
    print(f"  FALSE NEGATIVES (gate says COOCCUR, adjudication says VERIFIED): {fn}")
    print(f"    -> real relations the lexical screen misses (often missing vocabulary)")

    json.dump(disagreements, open("data/GATE_DISAGREEMENTS.json", "w"), indent=2)
    print(f"\n  {len(disagreements)} disagreements -> data/GATE_DISAGREEMENTS.json")

    # FN by relation (where vocabulary is weakest)
    from collections import Counter
    fn_rel = Counter(d["relation"] for d in disagreements if d["gate"] != "AGREE")
    fp_rel = Counter(d["relation"] for d in disagreements if d["gate"] == "AGREE")
    print("\n  False-negative relations (gate too strict):", dict(fn_rel.most_common(6)))
    print("  False-positive relations (gate too loose): ", dict(fp_rel.most_common(6)))


if __name__ == "__main__":
    main()
