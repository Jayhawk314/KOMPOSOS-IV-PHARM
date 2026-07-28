#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Reading Agent: Verifies triplet scrape candidates by reading abstracts.
Extracts "Proof Sentences" where Source + Action + Target are linked.
"""

import requests
import time
import json
import re
import os
from typing import List, Dict, Tuple
from pathlib import Path

CANDIDATE_POOL = "data/full_triplet_candidate_pool.json"
OUTPUT_PATH = "data/action_verified_provenance.json"
PUBMED_FETCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Mapping categorical relations to proof keywords. Entries are stems matched at
# a word boundary (see _keyword_present), so "inhib" covers inhibits/inhibitor/
# inhibition/inhibiting, etc. Broadening the vocabulary reduces false negatives
# (the KEYWORD_LOST class) without weakening the polarity guard.
ACTION_KEYWORDS = {
    'inhibits': ["inhib", "antagon", "block", "suppress", "downregulat",
                 "abrogat", "deplet", "knockdown", "knockout"],
    'indirect_inhibitor': ["inhib", "suppress", "downregulat", "block"],
    'activates': ["activat", "agonist", "induc", "upregulat", "stimulat",
                  "potentiat", "enhanc", "promot"],
    'activator': ["activat", "agonist", "stimulat"],
    'enhances': ["enhanc", "promot", "potentiat", "activat"],
    'associated_with': ["associat", "linked", "implicat", "correlat",
                        "express", "elevated", "overexpress", "mutat"],
    'driver_of': ["driver", "drives", "caus", "induc", "promot", "mediat",
                  "oncogen", "tumorigen"],
    'phosphorylates': ["phosphorylat"],
    'ubiquitinates': ["ubiquitinat"],
    'binds': ["bind", "affinity", "complex", "interact"],
    'interacts': ["interact", "bind", "complex"],
    'sequesters': ["sequester", "bind", "complex"],
    'synergizes_with': ["synerg", "potentiat", "combinat", "cooperat"],
    'treats': ["treat", "therap", "clinical trial", "effica", "approv",
               "indicat", "commission", "respon", "remission", "first-line",
               "second-line", "adjuvant", "neoadjuvant"],
}

# Opposite-polarity cues per relation direction. If one of these appears in the
# same sentence as the (positive-sounding) action keyword, the sentence likely
# asserts the OPPOSITE of the edge (e.g. "Akt1 ... decreased" for an `activates`
# edge), so we flag it rather than accept it as proof.
POSITIVE_RELATIONS = {"activates", "activator", "enhances", "driver_of"}
NEGATIVE_RELATIONS = {"inhibits", "indirect_inhibitor"}
OPPOSITE_CUES = {
    # contradict an "activation/up" claim
    "positive": ["decreas", "reduc", "loss of", "abrogat", "suppress",
                 "downregulat", "blockade", "depletion", "inhibit"],
    # contradict an "inhibition/down" claim
    "negative": ["increas", "upregulat", "induct", "enhanc", "activat",
                 "promot", "potentiat"],
}


def _term_present(term: str, sentence: str) -> bool:
    """Match a node name in the ORIGINAL-CASE sentence.

    Whole-word, case-insensitive match is the common path. For all-caps gene
    symbols we additionally allow a mutation/variant suffix (BRAFV600E,
    JAK2V617F, PI3KCAH1047R) by matching the symbol followed by uppercase/digit
    characters -- but checked case-sensitively, so 'MET' does NOT match the
    lowercase 'met' buried inside 'metabolism' or 'meta-analysis'.
    """
    # Optional trailing 's' tolerates plurals ('breast cancers') while still
    # excluding 'MET' inside 'metabolism' (no word boundary after 'MET'/'METs').
    if re.search(r"\b" + re.escape(term) + r"s?\b", sentence, re.IGNORECASE):
        return True
    if term.isupper() and re.search(r"\b" + re.escape(term) + r"[A-Z0-9]", sentence):
        return True
    return False


def _keyword_present(keyword: str, sent_lower: str) -> bool:
    """Stem-style match for action keywords: word-start boundary with any
    suffix, so 'inhibitor' also matches 'inhibitors' and 'inhibits' matches
    'inhibiting', without matching mid-word."""
    return re.search(r"\b" + re.escape(keyword.lower()), sent_lower) is not None


def _polarity_conflict(sent_lower: str, relation: str, found_keyword: str) -> bool:
    """True if an opposite-polarity cue is present, signalling the sentence may
    assert the reverse of the edge's stated direction."""
    if relation in POSITIVE_RELATIONS:
        cues = OPPOSITE_CUES["positive"]
    elif relation in NEGATIVE_RELATIONS:
        cues = OPPOSITE_CUES["negative"]
    else:
        # associated_with / treats / phosphorylates etc. have no signed direction
        return False
    kw = (found_keyword or "").lower()
    for cue in cues:
        # don't let the cue list fight the matched keyword itself
        if cue in kw:
            continue
        if cue in sent_lower:
            return True
    return False


def fetch_abstracts(pmids: List[str]) -> Dict[str, str]:
    """Fetch abstracts for a list of PMIDs."""
    if not pmids:
        return {}
    
    params = {
        'db': 'pubmed',
        'id': ",".join(pmids),
        'retmode': 'xml',
        'tool': 'KOMPOSOS-IV-PHARM',
        'email': 'komposos@example.com'
    }
    
    abstracts = {}
    try:
        response = requests.get(PUBMED_FETCH_API, params=params, timeout=30)
        if response.status_code == 200:
            content = response.text
            # Simple XML parsing using regex for speed in background tasks
            articles = re.findall(r'<PubmedArticle>.*?</PubmedArticle>', content, re.DOTALL)
            for article in articles:
                pmid_match = re.search(r'<PMID[^>]*>(\d+)</PMID>', article)
                # Capture ALL AbstractText sections. Structured abstracts split
                # into BACKGROUND/METHODS/RESULTS/CONCLUSIONS as separate nodes;
                # grabbing only the first one hides the RESULTS where the actual
                # mechanistic claim usually lives.
                abstract_sections = re.findall(
                    r'<AbstractText[^>]*>(.*?)</AbstractText>', article, re.DOTALL
                )
                if pmid_match and abstract_sections:
                    pmid = pmid_match.group(1)
                    # Clean up XML tags from each section and join with spaces
                    cleaned = [re.sub(r'<[^>]+>', '', sec) for sec in abstract_sections]
                    abstracts[pmid] = " ".join(cleaned)
    except Exception as e:
        print(f"  [ERROR] Fetch failed: {e}")
    
    return abstracts

def find_proof_sentence(abstract: str, source: str, target: str,
                        relation: str) -> Tuple[str, float, str]:
    """Search for a sentence containing Source, Target, and Action keywords.

    Returns (best_sentence, score, flag). `flag` is "" when the sentence is
    clean, otherwise a short reason ("polarity_conflict") so callers can reject
    proofs that likely assert the opposite of the edge.
    """
    # Standardize names for matching (keep original case; _term_present is
    # case-insensitive but uses case to validate gene-symbol mutation suffixes).
    s_name = source.replace("_", " ")
    t_name = target.replace("_", " ")
    keywords = ACTION_KEYWORDS.get(relation, [relation])

    # Split abstract into sentences
    sentences = re.split(r'(?<=[.!?])\s+', abstract)

    best_sentence = ""
    best_flag = ""
    max_score = 0.0

    for sentence in sentences:
        sent_lower = sentence.lower()

        # Check if BOTH source and target are in this sentence (word-boundary,
        # so 'MET' does not match 'meta-analysis').
        if _term_present(s_name, sentence) and _term_present(t_name, sentence):
            score = 0.5  # Base score for co-occurrence in same sentence

            # Check for action keyword (stem match, allows plural/verb forms)
            found_keyword = None
            for kw in keywords:
                if _keyword_present(kw, sent_lower):
                    score += 0.4
                    found_keyword = kw
                    break

            # Bonus for proximity (simple check)
            if found_keyword:
                s_idx = sent_lower.find(s_name.lower())
                t_idx = sent_lower.find(t_name.lower())
                k_idx = sent_lower.find(found_keyword.lower())
                dist = max(abs(s_idx - k_idx), abs(t_idx - k_idx))
                if dist < 50:
                    score += 0.1

            # Flag sentences whose polarity likely contradicts the edge.
            flag = ""
            if found_keyword and _polarity_conflict(sent_lower, relation, found_keyword):
                flag = "polarity_conflict"

            if score > max_score:
                max_score = score
                best_sentence = sentence.strip()
                best_flag = flag

    return best_sentence, max_score, best_flag

def main():
    print("="*70)
    print("READING AGENT: VERIFYING PROOF SENTENCES")
    print("="*70)

    if not os.path.exists(CANDIDATE_POOL):
        print(f"Error: Candidate pool not found at {CANDIDATE_POOL}")
        return

    with open(CANDIDATE_POOL) as f:
        pool = json.load(f)

    # Process the ENTIRE pool
    print(f"Loading pool: {len(pool)} edges found.")
    verified_results = []
    
    # Flatten PMIDs to fetch in batches
    pmid_to_edges = {}
    for entry in pool:
        top_pmids = entry['pmids'][:5]
        for pmid in top_pmids:
            if pmid not in pmid_to_edges:
                pmid_to_edges[pmid] = []
            pmid_to_edges[pmid].append(entry)

    all_pmids = list(pmid_to_edges.keys())
    print(f"Fetching abstracts for {len(all_pmids)} unique top PMIDs...")
    
    batch_size = 100 # Increased for efficiency
    all_abstracts = {}
    for i in range(0, len(all_pmids), batch_size):
        batch = all_pmids[i:i+batch_size]
        print(f"  [FETCH] Processing batch {i//batch_size + 1}/{len(all_pmids)//batch_size + 1}...")
        all_abstracts.update(fetch_abstracts(batch))
        time.sleep(0.5)

    print(f"Analyzing {len(all_abstracts)} abstracts for proof...")
    OUTPUT_FULL = "data/action_verified_provenance_FULL.json"

    for i, entry in enumerate(pool):
        if i > 0 and i % 100 == 0:
            print(f"  [ANALysis] Processed {i}/{len(pool)} edges. Found {len(verified_results)} gold proofs.")
            # Periodic save
            with open(OUTPUT_FULL + ".PARTIAL", 'w') as f:
                json.dump(verified_results, f, indent=2)
        src = entry['source']
        tgt = entry['target']
        rel = entry['relation']
        
        best_overall_sentence = ""
        best_overall_score = 0.0
        best_overall_flag = ""
        best_pmid = ""

        for pmid in entry['pmids'][:5]:
            if pmid in all_abstracts:
                sentence, score, flag = find_proof_sentence(all_abstracts[pmid], src, tgt, rel)
                if score > best_overall_score:
                    best_overall_score = score
                    best_overall_sentence = sentence
                    best_overall_flag = flag
                    best_pmid = pmid

        # Reject proofs whose polarity likely contradicts the stated edge.
        if best_overall_score >= 0.7 and best_overall_flag == "":
            print(f"  [GOLD] {src} -{rel}-> {tgt} | Score: {best_overall_score:.2f}")
            print(f"    Proof: \"{best_overall_sentence[:120]}...\"")
            verified_results.append({
                "edge_id": entry['edge_id'],
                "source": src,
                "target": tgt,
                "relation": rel,
                "pmid": best_pmid,
                "proof_sentence": best_overall_sentence,
                "confidence_score": best_overall_score
            })

    # Save findings
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(verified_results, f, indent=2)

    print("\n" + "="*70)
    print("READING COMPLETE")
    print(f"Found {len(verified_results)} Gold Standard Proofs in first 100 edges.")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("="*70)

if __name__ == "__main__":
    main()
