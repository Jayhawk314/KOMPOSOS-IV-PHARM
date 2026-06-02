#!/usr/bin/env python3
"""
pmid_exploration.py — Exploratory side project to identify inaccurate PMIDs using komposos_kg.
"""

import json
import re
from typing import List, Tuple
from komposos_kg import build_memory, Edge, KGMemory

# --- 1. Stricter Verification Logic (adapted from scripts/verify_triplet_abstracts.py) ---

ACTION_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat", "abrogat"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat", "potentiat"],
    'associated_with': ["associat", "linked", "implicat", "correlat"],
    'treats': ["treat", "therap", "clinical trial", "effica", "approv"],
}

OPPOSITE_CUES = {
    "positive": ["decreas", "reduc", "loss of", "abrogat", "suppress", "downregulat", "blockade", "inhibit"],
    "negative": ["increas", "upregulat", "induct", "enhanc", "activat", "promot"],
}

def _term_present(term: str, sentence: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE) is not None

def _polarity_conflict(sent_lower: str, relation: str) -> bool:
    if relation == "activates":
        cues = OPPOSITE_CUES["positive"]
    elif relation == "inhibits":
        cues = OPPOSITE_CUES["negative"]
    else:
        return False
    for cue in cues:
        if cue in sent_lower:
            return True
    return False

class StrictCitationVerifier:
    """A komposos_kg verifier that checks for text grounding and polarity."""
    
    def __call__(self, edge: Edge, existing: List[Edge]) -> Tuple[str, str]:
        if not edge.evidence:
            return "HOLLOW", "no proof sentence provided for verification"
        
        sent = edge.evidence
        sent_lower = sent.lower()
        src = edge.subject.replace("_", " ")
        tgt = edge.object.replace("_", " ")
        rel = edge.relation
        
        # 1. Check entity presence (whole-word)
        if not (_term_present(src, sent) and _term_present(tgt, sent)):
            return "REJECT", f"one or more entities ({src}, {tgt}) not found in proof sentence (substring match only?)"
            
        # 2. Check for relation keyword
        keywords = ACTION_KEYWORDS.get(rel, [])
        found_kw = False
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw), sent_lower):
                found_kw = True
                break
        
        # 3. Check for polarity conflict
        if _polarity_conflict(sent_lower, rel):
            return "HOLLOW", f"polarity conflict detected: sentence may assert opposite of {rel}"
            
        if not found_kw:
            return "HOLLOW", f"no action keyword found for relation '{rel}' (co-occurrence only)"
            
        return "AGREE", "verified: entities present, relation keyword found, no polarity conflict"

# --- 2. Exploration Script ---

def main():
    print("="*80)
    print("KOMPOSOS-IV-PHARM: PMID EXPLORATION (using komposos_kg)")
    print("="*80)

    # Initialize memory with our strict verifier
    # We don't use real COG here to keep the exploration focused on citation grounding
    mem = KGMemory(verifier=StrictCitationVerifier())

    # Load a sample of candidate proofs
    PROVENANCE_PATH = "data/action_verified_provenance.json"
    try:
        with open(PROVENANCE_PATH) as f:
            candidates = json.load(f)
    except FileNotFoundError:
        print(f"Error: {PROVENANCE_PATH} not found.")
        return

    # Process first 30 candidates as a sample
    print(f"Auditing sample of {min(30, len(candidates))} candidates...\n")
    
    for entry in candidates[:30]:
        res = mem.remember(
            subject=entry['source'],
            relation=entry['relation'],
            object=entry['target'],
            source=f"PMID:{entry['pmid']}",
            evidence=entry['proof_sentence']
        )
        
        status = f"[{res.verdict}]"
        print(f"{status:<10} {entry['source']} -{entry['relation']}-> {entry['target']} (PMID:{entry['pmid']})")
        if res.verdict != "AGREE":
            print(f"           REASON: {res.reason}")
            # print(f"           TEXT:   \"{entry['proof_sentence'][:100]}...\"")

    # Demonstrate Honest Recall
    print("\n" + "-"*40)
    print("AGENT RECALL DEMONSTRATION")
    print("-"*40)
    
    # Agent A tries to recall "verified" facts for 'activates'
    print("Agent A recalling 'activates' relations (AGREE only)...")
    verified_facts = mem.recall(relation="activates", agent="AgentA")
    for f in verified_facts:
        print(f"  RECALLED: {f.id}")

    # Honest Explanation
    print("\nHonesty Gate Check:")
    
    # Case 1: Sincere explanation (using a recalled fact)
    if verified_facts:
        fact = verified_facts[0]
        action = f"Suggest targeting {fact.object} because {fact.subject} activates it"
        res = mem.explain_action(action, [fact.id], agent="AgentA")
        print(f"  Sincere citation of {fact.id}: {res.sincere}")
    
    # Case 2: Insincere explanation (citing a fact that was HOLLOW/REJECTED and thus not recalled)
    # Let's find a hollow one from our audit
    hollow_ids = [k for k, v in mem._edges.items() if v.verdict == "HOLLOW"]
    if hollow_ids:
        bad_id = hollow_ids[0]
        action = f"Suggest targeting based on {bad_id}"
        res = mem.explain_action(action, [bad_id], agent="AgentA")
        print(f"  Sincere citation of HOLLOW fact {bad_id}: {res.sincere}")
        if not res.sincere:
            print(f"           OBSTRUCTIONS: {[o['kind'] for o in res.obstructions]}")

    print("\nSummary:")
    total = len(mem._edges)
    agreed = len([e for e in mem._edges.values() if e.verdict == "AGREE"])
    hollow = len([e for e in mem._edges.values() if e.verdict == "HOLLOW"])
    rejected = len([e for e in mem._edges.values() if e.verdict == "REJECT"])
    
    print(f"  Total Audited: {total}")
    print(f"  AGREE:         {agreed}")
    print(f"  HOLLOW:        {hollow} (Inaccurate/Unverified)")
    print(f"  REJECT:        {rejected} (Entity match failed)")
    print("="*80)

if __name__ == "__main__":
    main()
