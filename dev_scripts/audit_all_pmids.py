#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
audit_all_pmids.py — Comprehensive audit of all 737 action-verified claims.
"""

import json
import re
from typing import List, Tuple
from komposos_kg import Edge, KGMemory

# --- Stricter Verification Logic ---

ACTION_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat", "abrogat", "reduc", "potency", "ic50"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat", "potentiat", "promot", "ec50"],
    'associated_with': ["associat", "linked", "implicat", "correlat", "overexpress", "mutation", "polymorphism"],
    'treats': ["treat", "therap", "clinical trial", "effica", "approv", "indicat", "respon", "survival"],
    'driver_of': ["driver", "drives", "caus", "induc", "promot", "oncogen", "tumorigen"],
    'binds': ["bind", "affinity", "complex", "engage", "dock", "partner", "interact", "kd", "ki"],
    'interacts': ["interact", "bind", "complex", "partner", "physical"],
    'phosphorylates': ["phosphorylat", "kinase"],
}

OPPOSITE_CUES = {
    "positive": ["decreas", "reduc", "loss of", "abrogat", "suppress", "downregulat", "blockade", "inhibit"],
    "negative": ["increas", "upregulat", "induct", "enhanc", "activat", "promot"],
}

def _term_present(term: str, sentence: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE) is not None

def _polarity_conflict(sent_lower: str, relation: str) -> bool:
    if relation in ["activates", "driver_of", "activator"]:
        cues = OPPOSITE_CUES["positive"]
    elif relation in ["inhibits", "indirect_inhibitor"]:
        cues = OPPOSITE_CUES["negative"]
    else:
        return False
    for cue in cues:
        if cue in sent_lower:
            return True
    return False

class StrictCitationVerifier:
    def __call__(self, edge: Edge, existing: List[Edge]) -> Tuple[str, str]:
        if not edge.evidence:
            return "HOLLOW", "no proof sentence provided"
        
        sent = edge.evidence
        sent_lower = sent.lower()
        src = edge.subject.replace("_", " ")
        tgt = edge.object.replace("_", " ")
        rel = edge.relation
        
        if not (_term_present(src, sent) and _term_present(tgt, sent)):
            return "REJECT", f"entities ({src}, {tgt}) match failed (substring or missing)"
            
        keywords = ACTION_KEYWORDS.get(rel, [])
        found_kw = False
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw), sent_lower):
                found_kw = True
                break
        
        if _polarity_conflict(sent_lower, rel):
            return "HOLLOW", f"polarity conflict for '{rel}'"
            
        if not found_kw:
            return "HOLLOW", f"no keyword for '{rel}' (co-occurrence only)"
            
        return "AGREE", "verified"

def main():
    mem = KGMemory(verifier=StrictCitationVerifier())
    with open("data/action_verified_provenance.json") as f:
        candidates = json.load(f)

    results = []
    for entry in candidates:
        res = mem.remember(
            subject=entry['source'],
            relation=entry['relation'],
            object=entry['target'],
            source=f"PMID:{entry['pmid']}",
            evidence=entry['proof_sentence']
        )
        results.append({
            "edge_id": entry.get('edge_id', f"{entry['relation']}:{entry['source']}->{entry['target']}"),
            "pmid": entry['pmid'],
            "verdict": res.verdict,
            "reason": res.reason
        })

    # Summary Report
    agreed = [r for r in results if r['verdict'] == "AGREE"]
    hollow = [r for r in results if r['verdict'] == "HOLLOW"]
    rejected = [r for r in results if r['verdict'] == "REJECT"]

    print(f"Audit Complete:")
    print(f"  Total:    {len(results)}")
    print(f"  AGREE:    {len(agreed)} ({len(agreed)/len(results):.1%})")
    print(f"  HOLLOW:   {len(hollow)} ({len(hollow)/len(results):.1%})")
    print(f"  REJECT:   {len(rejected)} ({len(rejected)/len(results):.1%})")

    # Group HOLLOW by reason
    reasons = {}
    for r in hollow:
        reasons[r['reason']] = reasons.get(r['reason'], 0) + 1
    
    print("\nHOLLOW Reasons:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {count:>3} x {reason}")

    # Write detailed report
    with open("data/PMID_AUDIT_REPORT.json", "w") as f:
        json.dump({
            "summary": {
                "total": len(results),
                "agree": len(agreed),
                "hollow": len(hollow),
                "reject": len(rejected)
            },
            "detailed": results
        }, f, indent=2)

if __name__ == "__main__":
    main()
