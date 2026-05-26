#!/usr/bin/env python3
"""
Categorical PubMed Edge Filter
===============================

Scores and filters 3,149 PubMed Protein->Disease edges using 5 layers
of mathematical infrastructure already present in the KOMPOSOS-IV repo:

  Layer 1: Drug Path Witness (HoTT path induction)
    - For each P->D edge, find drugs X where X->P and X->D both exist.
    - Each such drug is a "constructible path witness" (refl base case).
    - Edges with zero witnesses are "orphan paths" (JResult, not reducible).

  Layer 2: Left Kan Extension Agreement
    - Lan_K(F)(D) = colimit over all drugs treating D of their protein targets.
    - If protein P is in the Kan-predicted set for disease D, the edge agrees.
    - Confidence = weighted colimit over (drug_confidence * target_confidence).

  Layer 3: Mechanistic Reachability (Composition / Tier 1)
    - BFS from P through mechanistic edges (activates, inhibits, etc.)
    - Check if any reachable protein has a trusted connection to D.
    - Depth-limited to 3 hops (category composition depth).

  Layer 4: Protein Specificity (COG Energy / Novelty)
    - Proteins linking to ALL 20 diseases are likely text-matching artifacts.
    - Score = 1 - (n_diseases_for_P / total_diseases). MMP1 -> 0.0, BRAF -> 0.9.

  Layer 5: Gray Interchange Coherence
    - For each P->D edge, find other proteins Q also linked to D.
    - If P and Q share drug-mediated pathways, their parallel 2-cells are coherent.
    - If P has no mechanistic overlap with ANY other protein targeting D, it's
      an interchange failure (Gray swap cost = 1.0).

Combined score = weighted blend:
  drug_witness: 0.30, kan_agreement: 0.20, mech_reach: 0.20,
  specificity: 0.15, gray_coherence: 0.15

Output:
  - Confidence-adjusted edges for re-import
  - Statistics and examples at each confidence tier
  - JSON manifest of filtered edges

Author: KOMPOSOS-IV categorical filter pipeline
"""

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB_PATH = Path('data/drugs/tier1.db')

# Scoring weights
WEIGHTS = {
    'drug_witness':    0.30,
    'kan_agreement':   0.20,
    'mech_reach':      0.20,
    'specificity':     0.15,
    'gray_coherence':  0.15,
}

# Mechanistic edge types for BFS
MECHANISTIC_EDGES = {
    'inhibits', 'activates', 'targets', 'binds', 'modulates',
    'phosphorylates', 'activator', 'indirect_inhibitor',
    'regulates', 'regulated_by', 'ubiquitinates', 'sequesters',
    'cooperates', 'synergizes_with', 'interacts', 'enhances',
    'pathway_crosstalk', 'pathway_modulator', 'synthetic_lethal',
}

# Drug-to-target edge types
DRUG_TARGET_EDGES = {
    'inhibits', 'targets', 'binds', 'activates', 'modulates',
    'indirect_inhibitor', 'activator', 'pathway_modulator',
}

# Drug-to-disease edge types
DRUG_DISEASE_EDGES = {'treats', 'associated_with'}

# Non-protein-like types (everything else is a protein-like target)
NON_PROTEIN_TYPES = {'Drug', 'Disease', 'ExternalCompound'}


def load_graph(db_path):
    """Load full graph structure from SQLite into memory."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Load objects with types
    cur.execute('SELECT name, type_name FROM objects')
    objects = {r[0]: r[1] for r in cur.fetchall()}

    # Load all morphisms
    cur.execute('''
        SELECT id, source_name, target_name, name, confidence, provenance
        FROM morphisms
    ''')
    morphisms = cur.fetchall()

    conn.close()
    return objects, morphisms


def build_indices(objects, morphisms):
    """Build lookup indices for efficient graph queries."""

    # Identify PubMed batch edges
    pubmed_edges = []
    trusted_edges = []

    for mid, src, tgt, name, conf, prov in morphisms:
        if (prov.startswith('PMID:') and name == 'associated_with'
                and abs(conf - 0.65) < 0.01):
            pubmed_edges.append((mid, src, tgt, name, conf, prov))
        else:
            trusted_edges.append((mid, src, tgt, name, conf, prov))

    # Helper: is this a protein-like type?
    def is_protein_like(name):
        typ = objects.get(name, '')
        return typ and typ not in NON_PROTEIN_TYPES

    # Drug -> Protein targets (from trusted edges only)
    # Uses protein-LIKE types (Oncogene, Receptor, Signaling, etc.)
    drug_targets = defaultdict(list)  # drug -> [(protein, confidence)]
    for mid, src, tgt, name, conf, prov in trusted_edges:
        if (objects.get(src) == 'Drug' and is_protein_like(tgt)
                and name in DRUG_TARGET_EDGES):
            drug_targets[src].append((tgt, conf))

    # Drug -> Disease indications (from trusted edges only)
    drug_diseases = defaultdict(list)  # drug -> [(disease, confidence)]
    for mid, src, tgt, name, conf, prov in trusted_edges:
        if (objects.get(src) == 'Drug' and objects.get(tgt) == 'Disease'
                and name in DRUG_DISEASE_EDGES):
            drug_diseases[src].append((tgt, conf))

    # Protein-like -> Disease (trusted only, for baseline)
    trusted_prot_disease = defaultdict(set)  # protein -> {diseases}
    for mid, src, tgt, name, conf, prov in trusted_edges:
        if is_protein_like(src) and objects.get(tgt) == 'Disease':
            trusted_prot_disease[src].add(tgt)

    # Mechanistic adjacency (for BFS) — trusted edges only
    mech_adj = defaultdict(set)  # node -> {neighbors}
    for mid, src, tgt, name, conf, prov in trusted_edges:
        if name in MECHANISTIC_EDGES:
            mech_adj[src].add(tgt)
            mech_adj[tgt].add(src)  # undirected for reachability

    # Disease -> set of proteins with trusted connections
    disease_proteins = defaultdict(set)
    for mid, src, tgt, name, conf, prov in trusted_edges:
        if is_protein_like(src) and objects.get(tgt) == 'Disease':
            disease_proteins[tgt].add(src)

    # PubMed protein -> diseases count (for specificity)
    pubmed_protein_diseases = defaultdict(set)
    for mid, src, tgt, name, conf, prov in pubmed_edges:
        pubmed_protein_diseases[src].add(tgt)

    # All diseases
    diseases = {name for name, typ in objects.items() if typ == 'Disease'}

    # All drugs
    drugs = {name for name, typ in objects.items() if typ == 'Drug'}

    return {
        'pubmed_edges': pubmed_edges,
        'trusted_edges': trusted_edges,
        'drug_targets': drug_targets,
        'drug_diseases': drug_diseases,
        'trusted_prot_disease': trusted_prot_disease,
        'mech_adj': mech_adj,
        'disease_proteins': disease_proteins,
        'pubmed_protein_diseases': pubmed_protein_diseases,
        'diseases': diseases,
        'drugs': drugs,
        'objects': objects,
    }


# =========================================================================
# Layer 1: Drug Path Witness (HoTT)
# =========================================================================

def score_drug_witness(protein, disease, idx):
    """
    HoTT path induction: find constructible witnesses.

    For P->D, find drugs X where:
      X --inhibits/targets--> P  AND  X --treats--> D
    (direct witness = refl base case)

    Also find 1-hop extended witnesses:
      X --inhibits--> Q --mech_adj--> P  AND  X --treats--> D
    (transported witness via mechanistic path composition)

    Returns (score, witnesses) where score in [0, 1].
    """
    witnesses = []
    extended_witnesses = []

    # Protein's mechanistic neighbors
    p_neighbors = idx['mech_adj'].get(protein, set())

    for drug in idx['drugs']:
        drug_prots = {p for p, _ in idx['drug_targets'].get(drug, [])}
        drug_dis = {d for d, _ in idx['drug_diseases'].get(drug, [])}

        if disease not in drug_dis:
            continue

        # Direct witness: Drug targets P AND treats D
        if protein in drug_prots:
            prot_conf = max(
                c for p, c in idx['drug_targets'][drug] if p == protein
            )
            dis_conf = max(
                c for d, c in idx['drug_diseases'][drug] if d == disease
            )
            witnesses.append((drug, min(prot_conf, dis_conf)))
        else:
            # Extended witness: Drug targets neighbor of P AND treats D
            shared = drug_prots & p_neighbors
            if shared:
                via = next(iter(shared))
                prot_conf = max(
                    c for p, c in idx['drug_targets'][drug] if p == via
                )
                dis_conf = max(
                    c for d, c in idx['drug_diseases'][drug] if d == disease
                )
                extended_witnesses.append(
                    (drug, min(prot_conf, dis_conf) * 0.6, via)
                )

    if not witnesses and not extended_witnesses:
        return 0.0, []

    # Direct witnesses score higher than extended
    if witnesses:
        n = len(witnesses)
        best_conf = max(c for _, c in witnesses)
        score = min(1.0, n * 0.5) * best_conf
    else:
        n = len(extended_witnesses)
        best_conf = max(c for _, c, _ in extended_witnesses)
        score = min(0.7, n * 0.3) * best_conf

    all_w = [(d, c) for d, c in witnesses] + \
            [(d, c) for d, c, _ in extended_witnesses]
    return score, all_w


# =========================================================================
# Layer 2: Left Kan Extension Agreement
# =========================================================================

def score_kan_agreement(protein, disease, idx):
    """
    Left Kan extension: Lan_K(F)(Disease) predicts proteins.

    F maps Drug -> {target proteins}
    K embeds Drug into the full graph
    Lan_K(F)(Disease) = colimit over drugs treating Disease of their targets

    Extended colimit: also includes mechanistic neighbors of direct targets
    (1-hop extension of the comma category).

    If protein P is in this extended colimit, the edge agrees.

    Returns (score, kan_predicted_proteins).
    """
    # Find all drugs that treat this disease
    treating_drugs = []
    for drug in idx['drugs']:
        for dis, conf in idx['drug_diseases'].get(drug, []):
            if dis == disease:
                treating_drugs.append((drug, conf))

    if not treating_drugs:
        return 0.0, []

    # Colimit: collect all protein targets of treating drugs
    # Weight by drug_confidence * target_confidence
    kan_proteins = {}  # protein -> total weight
    for drug, drug_conf in treating_drugs:
        for prot, prot_conf in idx['drug_targets'].get(drug, []):
            weight = drug_conf * prot_conf
            kan_proteins[prot] = kan_proteins.get(prot, 0.0) + weight

    if protein in kan_proteins:
        # Direct Kan agreement
        raw = kan_proteins[protein]
        score = min(1.0, raw)
        return score, list(kan_proteins.keys())

    # Extended colimit: include mechanistic neighbors of Kan-predicted proteins
    # This extends the comma category by one composition step
    extended_kan = {}
    for kan_prot, weight in kan_proteins.items():
        for neighbor in idx['mech_adj'].get(kan_prot, set()):
            ext_weight = weight * 0.5  # Decay for extension
            extended_kan[neighbor] = extended_kan.get(neighbor, 0.0) + ext_weight

    if protein in extended_kan:
        score = min(0.7, extended_kan[protein])
        return score, list(extended_kan.keys())

    # Check if protein is a mechanistic neighbor of an extended Kan protein
    neighbors = idx['mech_adj'].get(protein, set())
    kan_neighbors = neighbors & (set(kan_proteins.keys()) | set(extended_kan.keys()))
    if kan_neighbors:
        best_weight = max(
            kan_proteins.get(n, 0) + extended_kan.get(n, 0)
            for n in kan_neighbors
        )
        score = min(0.4, best_weight * 0.3)  # Weaker: 2-hop Kan agreement
        return score, list(kan_neighbors)

    return 0.0, list(kan_proteins.keys())


# =========================================================================
# Layer 3: Mechanistic Reachability (Composition / COG Tier 1)
# =========================================================================

def score_mech_reach(protein, disease, idx, max_depth=3):
    """
    BFS through mechanistic edges to find paths to disease-connected proteins.

    Two pathways:
    1. P -> ... -> Q where Q has trusted Protein->Disease to D
    2. P -> ... -> Drug X where X treats D (drug bridge path)

    If P can reach (within max_depth hops) either target, P->D is supported.

    Returns (score, depth, reaching_node).
    """
    # Disease-connected proteins (trusted)
    target_proteins = idx['disease_proteins'].get(disease, set())

    # Drugs treating this disease
    treating_drugs = set()
    for drug in idx['drugs']:
        for dis, _ in idx['drug_diseases'].get(drug, []):
            if dis == disease:
                treating_drugs.add(drug)

    if protein in target_proteins:
        # P already has a trusted connection to D
        return 1.0, 0, protein

    # BFS through mechanistic adjacency
    visited = {protein}
    frontier = {protein}

    for depth in range(1, max_depth + 1):
        next_frontier = set()
        for node in frontier:
            for neighbor in idx['mech_adj'].get(node, set()):
                if neighbor not in visited:
                    # Path 1: reached a protein with trusted P->D edge
                    if neighbor in target_proteins:
                        score = 1.0 / depth
                        return min(1.0, score), depth, neighbor
                    # Path 2: reached a drug that treats D (drug bridge)
                    if neighbor in treating_drugs:
                        score = 0.8 / depth  # Slightly lower for drug bridge
                        return min(0.8, score), depth, neighbor
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
        if not frontier:
            break

    return 0.0, -1, None


# =========================================================================
# Layer 4: Protein Specificity (COG Energy / Novelty)
# =========================================================================

def score_specificity(protein, idx):
    """
    Proteins linking to ALL diseases are likely text-matching artifacts.

    MMP1 -> 20 diseases = specificity 0.0 (noise)
    BRAF -> 2 diseases  = specificity 0.9 (signal)

    Score = 1 - (n_pubmed_diseases / total_diseases)
    """
    n_diseases = len(idx['pubmed_protein_diseases'].get(protein, set()))
    total = len(idx['diseases'])

    if total == 0:
        return 1.0

    specificity = 1.0 - (n_diseases / total)
    return max(0.0, specificity)


# =========================================================================
# Layer 5: Gray Interchange Coherence
# =========================================================================

def score_gray_coherence(protein, disease, idx):
    """
    Gray category interchange cost.

    For P->D, find other proteins Q also connected to D (trusted).
    If P and Q share drug-mediated pathways (common drugs, common
    mechanistic neighbors), the interchange between P->D and Q->D
    is coherent (low swap cost).

    If P has NO mechanistic overlap with any Q targeting D,
    the interchange fails (high swap cost = noise).

    Returns (score, overlap_count).
    """
    # Proteins with trusted connections to D
    trusted_q = idx['disease_proteins'].get(disease, set())

    if not trusted_q:
        return 0.3, 0  # No trusted baselines = unknown, moderate prior

    # Check mechanistic overlap between P and each Q
    p_neighbors = idx['mech_adj'].get(protein, set())
    p_drugs = set()
    for drug in idx['drugs']:
        for prot, _ in idx['drug_targets'].get(drug, []):
            if prot == protein:
                p_drugs.add(drug)

    overlap_count = 0
    for q in trusted_q:
        # Shared mechanistic neighbors
        q_neighbors = idx['mech_adj'].get(q, set())
        shared_mech = p_neighbors & q_neighbors

        # Shared drugs
        q_drugs = set()
        for drug in idx['drugs']:
            for prot, _ in idx['drug_targets'].get(drug, []):
                if prot == q:
                    q_drugs.add(drug)
        shared_drugs = p_drugs & q_drugs

        # Direct mechanistic edge P<->Q
        direct = protein in q_neighbors or q in p_neighbors

        if shared_mech or shared_drugs or direct:
            overlap_count += 1

    if overlap_count == 0:
        return 0.1, 0  # No interchange coherence = suspicious

    # Score: more overlaps = more coherent
    score = min(1.0, overlap_count * 0.3)
    return score, overlap_count


# =========================================================================
# Combined Scoring
# =========================================================================

def score_edge(protein, disease, idx):
    """Compute combined categorical score for one PubMed edge."""
    scores = {}
    details = {}

    # Layer 1: Drug Path Witness
    s1, witnesses = score_drug_witness(protein, disease, idx)
    scores['drug_witness'] = s1
    details['drug_witness'] = {
        'score': s1,
        'witnesses': [(d, round(c, 3)) for d, c in witnesses],
    }

    # Layer 2: Kan Extension
    s2, kan_prots = score_kan_agreement(protein, disease, idx)
    scores['kan_agreement'] = s2
    details['kan_agreement'] = {
        'score': s2,
        'in_kan_set': protein in kan_prots if kan_prots else False,
    }

    # Layer 3: Mechanistic Reachability
    s3, depth, via = score_mech_reach(protein, disease, idx)
    scores['mech_reach'] = s3
    details['mech_reach'] = {
        'score': s3,
        'depth': depth,
        'via_protein': via,
    }

    # Layer 4: Specificity
    s4 = score_specificity(protein, idx)
    scores['specificity'] = s4
    details['specificity'] = {
        'score': s4,
        'n_diseases': len(idx['pubmed_protein_diseases'].get(protein, set())),
    }

    # Layer 5: Gray Coherence
    s5, overlap = score_gray_coherence(protein, disease, idx)
    scores['gray_coherence'] = s5
    details['gray_coherence'] = {
        'score': s5,
        'overlap_count': overlap,
    }

    # Weighted combination
    combined = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)

    # Meta-Kan delta classification
    if combined >= 0.6:
        delta = 'AGREE'
    elif combined >= 0.3:
        if s1 > 0 or s3 > 0:
            delta = 'PARTIAL'  # Some mechanistic support but weak
        else:
            delta = 'HOLLOW'  # Structurally present but no logical support
    elif combined >= 0.1:
        delta = 'ORPHAN'  # Isolated, minimal support
    else:
        delta = 'REJECT'  # No support from any layer

    return {
        'combined': round(combined, 4),
        'delta': delta,
        'layer_scores': {k: round(v, 4) for k, v in scores.items()},
        'details': details,
    }


# =========================================================================
# Main Pipeline
# =========================================================================

def main():
    print("=" * 70)
    print("KOMPOSOS-IV Categorical PubMed Edge Filter")
    print("  Layers: HoTT + Kan + Composition + COG Energy + Gray Coherence")
    print("=" * 70)

    # Load graph
    print("\n[1/4] Loading graph from tier1.db...")
    objects, morphisms = load_graph(DB_PATH)
    print(f"  {len(objects)} objects, {len(morphisms)} morphisms")

    # Build indices
    print("[2/4] Building indices...")
    idx = build_indices(objects, morphisms)
    print(f"  PubMed edges to score: {len(idx['pubmed_edges'])}")
    print(f"  Trusted edges: {len(idx['trusted_edges'])}")
    print(f"  Drugs with targets: {len(idx['drug_targets'])}")
    print(f"  Drugs with diseases: {len(idx['drug_diseases'])}")
    print(f"  Diseases: {len(idx['diseases'])}")

    # Score all PubMed edges
    print("[3/4] Scoring edges (5 layers)...")
    results = []

    for i, (mid, src, tgt, name, conf, prov) in enumerate(idx['pubmed_edges']):
        result = score_edge(src, tgt, idx)
        result['edge_id'] = mid
        result['source'] = src
        result['target'] = tgt
        result['original_confidence'] = conf
        result['provenance'] = prov

        # Adjusted confidence: blend original with categorical score
        # Original PubMed confidence (0.65) adjusted by categorical evidence
        adjusted = 0.65 * result['combined'] + 0.35 * conf * (0.5 + 0.5 * result['combined'])
        result['adjusted_confidence'] = round(adjusted, 4)

        results.append(result)

        if (i + 1) % 500 == 0:
            print(f"  ... scored {i + 1}/{len(idx['pubmed_edges'])}")

    print(f"  Scored all {len(results)} edges")

    # Statistics
    print("\n[4/4] Results")
    print("=" * 70)

    # Delta distribution
    delta_counts = defaultdict(int)
    for r in results:
        delta_counts[r['delta']] += 1

    print("\nMeta-Kan Delta Classification:")
    for delta in ['AGREE', 'PARTIAL', 'HOLLOW', 'ORPHAN', 'REJECT']:
        n = delta_counts.get(delta, 0)
        pct = 100 * n / len(results) if results else 0
        bar = '#' * int(pct / 2)
        print(f"  {delta:8s}: {n:5d} ({pct:5.1f}%) {bar}")

    # Score distribution
    score_bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    print("\nCombined Score Distribution:")
    for i in range(len(score_bins) - 1):
        lo, hi = score_bins[i], score_bins[i + 1]
        n = sum(1 for r in results if lo <= r['combined'] < hi)
        pct = 100 * n / len(results) if results else 0
        bar = '#' * int(pct / 2)
        print(f"  [{lo:.1f}, {hi:.1f}): {n:5d} ({pct:5.1f}%) {bar}")

    # Layer-by-layer breakdown
    print("\nLayer Score Averages:")
    for layer in WEIGHTS:
        avg = sum(r['layer_scores'][layer] for r in results) / max(len(results), 1)
        print(f"  {layer:20s}: {avg:.3f}")

    # Top-scored edges (AGREE)
    agree = sorted([r for r in results if r['delta'] == 'AGREE'],
                   key=lambda r: -r['combined'])
    print(f"\nTop 10 AGREE edges (strongest categorical support):")
    for r in agree[:10]:
        witnesses = r['details']['drug_witness']['witnesses']
        w_str = ', '.join(d for d, _ in witnesses[:3]) if witnesses else 'none'
        print(f"  {r['source']:15s} -> {r['target']:25s}  "
              f"score={r['combined']:.3f}  "
              f"adj_conf={r['adjusted_confidence']:.3f}  "
              f"witnesses=[{w_str}]")

    # Bottom-scored edges (REJECT/ORPHAN)
    rejects = sorted([r for r in results if r['delta'] in ('REJECT', 'ORPHAN')],
                     key=lambda r: r['combined'])
    print(f"\nBottom 10 edges (weakest, likely noise):")
    for r in rejects[:10]:
        n_dis = r['details']['specificity']['n_diseases']
        print(f"  {r['source']:15s} -> {r['target']:25s}  "
              f"score={r['combined']:.3f}  "
              f"specificity={r['layer_scores']['specificity']:.2f} "
              f"({n_dis} diseases)")

    # HOLLOW edges (structurally present but logically unsupported)
    hollows = sorted([r for r in results if r['delta'] == 'HOLLOW'],
                     key=lambda r: -r['combined'])
    print(f"\nSample HOLLOW edges (10 of {delta_counts.get('HOLLOW', 0)}):")
    for r in hollows[:10]:
        print(f"  {r['source']:15s} -> {r['target']:25s}  "
              f"score={r['combined']:.3f}  "
              f"drug_w={r['layer_scores']['drug_witness']:.2f}  "
              f"kan={r['layer_scores']['kan_agreement']:.2f}  "
              f"mech={r['layer_scores']['mech_reach']:.2f}")

    # Confidence adjustment summary
    orig_avg = sum(r['original_confidence'] for r in results) / max(len(results), 1)
    adj_avg = sum(r['adjusted_confidence'] for r in results) / max(len(results), 1)
    print(f"\nConfidence Adjustment:")
    print(f"  Original mean:  {orig_avg:.4f}")
    print(f"  Adjusted mean:  {adj_avg:.4f}")
    print(f"  Range: [{min(r['adjusted_confidence'] for r in results):.4f}, "
          f"{max(r['adjusted_confidence'] for r in results):.4f}]")

    # Recommended action
    n_keep = sum(1 for r in results if r['adjusted_confidence'] >= 0.3)
    n_demote = sum(1 for r in results if 0.15 <= r['adjusted_confidence'] < 0.3)
    n_remove = sum(1 for r in results if r['adjusted_confidence'] < 0.15)
    print(f"\nRecommended Actions:")
    print(f"  KEEP   (conf >= 0.30): {n_keep:5d} edges")
    print(f"  DEMOTE (0.15 <= conf < 0.30): {n_demote:5d} edges")
    print(f"  REMOVE (conf < 0.15): {n_remove:5d} edges")

    # Save results
    output_path = Path('scripts/pubmed_edge_scores.json')
    save_results = []
    for r in results:
        save_results.append({
            'edge_id': r['edge_id'],
            'source': r['source'],
            'target': r['target'],
            'original_confidence': r['original_confidence'],
            'adjusted_confidence': r['adjusted_confidence'],
            'combined_score': r['combined'],
            'delta': r['delta'],
            'layer_scores': r['layer_scores'],
        })

    with open(output_path, 'w') as f:
        json.dump({
            'version': '2026-05-24-categorical-filter',
            'description': 'PubMed edge scores from 5-layer categorical filter',
            'layers': list(WEIGHTS.keys()),
            'weights': WEIGHTS,
            'total_scored': len(results),
            'delta_distribution': dict(delta_counts),
            'edges': save_results,
        }, f, indent=2)

    print(f"\nFull scores saved to: {output_path}")
    print(f"  ({len(save_results)} edges with layer-by-layer scores)")
    print("=" * 70)


if __name__ == '__main__':
    main()
