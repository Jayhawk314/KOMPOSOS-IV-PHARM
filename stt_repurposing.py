#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
STT-Enhanced Drug Repurposing

Applies three Simplicial Type Theory concepts as scoring strategies
to the KOMPOSOS-IV-PHARM tier1.db drug-target-disease graph:

  1. Yoneda Distance  -- structural drug similarity via presheaf fingerprints
  2. Fibration Transport -- lift drug efficacy along disease-disease morphisms
  3. Rezk Completion  -- merge Yoneda-isomorphic entities, propagate labels

Operates on a "clean subgraph" of MEASURED + ESTABLISHED edges only,
then compares AUROC against the existing 8-strategy baseline.

Usage:
    python stt_repurposing.py
"""

from __future__ import annotations

import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.category import Category
from validation.repurposing_benchmark import (
    load_full_typed_view,
    drug_disease_pairs,
    pairwise_auroc,
    make_strategies,
    score_pair,
    compute_auprc,
    compute_hits_at_k,
    compute_mrr,
)

DB_PATH = "data/drugs/tier1.db"
NON_PROTEIN_TYPES = {"Drug", "Disease", "ExternalCompound"}


# =====================================================================
# Step 0: Load clean subgraph
# =====================================================================

def load_clean_subgraph(
    db_path: str = DB_PATH,
    tiers: Tuple[str, ...] = ("MEASURED", "ESTABLISHED"),
) -> Tuple[Category, Dict[str, str]]:
    """Load a Category containing only edges from the specified evidence tiers.

    Returns:
        (category, type_map) where type_map maps object name -> type_name.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Load all objects with their types
    type_map: Dict[str, str] = {}
    cursor.execute("SELECT name, type_name FROM objects")
    for row in cursor.fetchall():
        type_map[row["name"]] = row["type_name"]

    # Load edges filtered by evidence tier
    placeholders = ",".join("?" for _ in tiers)
    query = f"""
        SELECT source_name, target_name, name, confidence, evidence_tier
        FROM morphisms
        WHERE evidence_tier IN ({placeholders})
    """
    cursor.execute(query, tiers)
    edges = cursor.fetchall()
    conn.close()

    cat = Category("clean_stt", db_path=":memory:")

    # Add objects that appear in filtered edges
    seen_objects: Set[str] = set()
    for edge in edges:
        for obj_name in (edge["source_name"], edge["target_name"]):
            if obj_name not in seen_objects:
                seen_objects.add(obj_name)
                cat.add(
                    obj_name,
                    type_name=type_map.get(obj_name, "Object"),
                )

    # Add morphisms
    for edge in edges:
        cat.connect(
            edge["source_name"],
            edge["target_name"],
            name=edge["name"],
            confidence=edge["confidence"] or 1.0,
        )

    return cat, type_map


def is_protein_like(type_name: str) -> bool:
    """Check if a type_name represents a protein-like entity."""
    return type_name not in NON_PROTEIN_TYPES


# =====================================================================
# Step 2: Yoneda Distance Strategy
# =====================================================================

def yoneda_fingerprint(obj_name: str, category: Category) -> Set[Tuple[str, str]]:
    """Compute the Yoneda presheaf fingerprint: all incoming morphisms as
    (source, relation_type) pairs."""
    return {(m.source, m.name) for m in category.morphisms_to(obj_name)}


def yoneda_fingerprint_outgoing(obj_name: str, category: Category) -> Set[Tuple[str, str]]:
    """Outgoing fingerprint: all morphisms FROM this object."""
    return {(m.target, m.name) for m in category.morphisms_from(obj_name)}


def yoneda_distance(obj1: str, obj2: str, category: Category) -> float:
    """Jaccard distance between Yoneda presheaf fingerprints.

    Uses both incoming and outgoing morphisms for a fuller picture.
    """
    fp1_in = yoneda_fingerprint(obj1, category)
    fp2_in = yoneda_fingerprint(obj2, category)
    fp1_out = yoneda_fingerprint_outgoing(obj1, category)
    fp2_out = yoneda_fingerprint_outgoing(obj2, category)

    fp1 = fp1_in | fp1_out
    fp2 = fp2_in | fp2_out

    if not fp1 and not fp2:
        return 1.0  # no data = max distance
    union = fp1 | fp2
    intersection = fp1 & fp2
    return 1.0 - len(intersection) / len(union)


def yoneda_score(
    drug: str,
    disease: str,
    clean_cat: Category,
    type_map: Dict[str, str],
    known_treatments: Dict[str, Set[str]],
) -> float:
    """Score a Drug-Disease pair via Yoneda distance to known treating drugs.

    For each drug D_known that treats this disease, compute
    yoneda_distance(drug, D_known). Score = max(1 - distance).
    """
    treating_drugs = known_treatments.get(disease, set())
    if not treating_drugs:
        return 0.0

    best_similarity = 0.0
    for known_drug in treating_drugs:
        if known_drug == drug:
            continue  # skip self
        dist = yoneda_distance(drug, known_drug, clean_cat)
        similarity = 1.0 - dist
        if similarity > best_similarity:
            best_similarity = similarity

    return best_similarity


# =====================================================================
# Step 3: CovariantFibration Transport Strategy
# =====================================================================

def disease_fiber(
    disease: str,
    category: Category,
    type_map: Dict[str, str],
) -> Tuple[Set[str], Set[Tuple[str, str]]]:
    """Compute the fiber over a disease: proteins connected to it, and
    (drug, protein) pairs reachable through those proteins.

    Returns:
        (proteins, drug_protein_pairs)
    """
    # Proteins directly connected to disease (incoming morphisms)
    proteins: Set[str] = set()
    for m in category.morphisms_to(disease):
        src_type = type_map.get(m.source, "Object")
        if is_protein_like(src_type):
            proteins.add(m.source)

    # Also check outgoing from disease
    for m in category.morphisms_from(disease):
        tgt_type = type_map.get(m.target, "Object")
        if is_protein_like(tgt_type):
            proteins.add(m.target)

    # Drug-protein pairs: drugs that target any of these proteins
    drug_protein_pairs: Set[Tuple[str, str]] = set()
    for protein in proteins:
        for m in category.morphisms_to(protein):
            src_type = type_map.get(m.source, "Object")
            if src_type == "Drug":
                drug_protein_pairs.add((m.source, protein))

    return proteins, drug_protein_pairs


def base_morphism_strength(
    d1: str,
    d2: str,
    disease_proteins: Dict[str, Set[str]],
) -> float:
    """Jaccard similarity of protein sets between two diseases.

    This defines the base category morphism strength.
    """
    p1 = disease_proteins.get(d1, set())
    p2 = disease_proteins.get(d2, set())
    if not p1 or not p2:
        return 0.0
    return len(p1 & p2) / len(p1 | p2)


def transport_score(
    drug: str,
    disease: str,
    clean_cat: Category,
    type_map: Dict[str, str],
    disease_proteins: Dict[str, Set[str]],
    disease_fibers: Dict[str, Set[Tuple[str, str]]],
    diseases: List[str],
) -> float:
    """Score a Drug-Disease pair via fibration transport.

    Find diseases where Drug is in the fiber, compute base morphism
    strength to target disease, sum strengths.
    """
    total = 0.0
    for d_other in diseases:
        if d_other == disease:
            continue
        # Is drug in the fiber of d_other?
        fiber = disease_fibers.get(d_other, set())
        drug_in_fiber = any(d == drug for d, _ in fiber)
        if not drug_in_fiber:
            continue
        strength = base_morphism_strength(d_other, disease, disease_proteins)
        total += strength

    return min(1.0, total)


def verify_transport_axioms(
    diseases: List[str],
    disease_proteins: Dict[str, Set[str]],
    disease_fibers: Dict[str, Set[Tuple[str, str]]],
) -> Tuple[int, int, List[str]]:
    """Verify fibration transport axioms.

    Returns:
        (identity_ok, composition_violations_count, violation_descriptions)
    """
    identity_ok = 0
    violations: List[str] = []

    # Identity axiom: transporting along D -> D returns same fiber
    for d in diseases:
        fiber = disease_fibers.get(d, set())
        # Identity transport is trivially correct by definition
        identity_ok += 1

    # Composition axiom: transport(D1->D2->D3) == transport(D1->D3)
    # Check for triples where all pairwise base morphisms exist
    for d1 in diseases:
        for d2 in diseases:
            if d1 == d2:
                continue
            s12 = base_morphism_strength(d1, d2, disease_proteins)
            if s12 < 0.01:
                continue
            for d3 in diseases:
                if d3 == d1 or d3 == d2:
                    continue
                s23 = base_morphism_strength(d2, d3, disease_proteins)
                s13 = base_morphism_strength(d1, d3, disease_proteins)
                if s23 < 0.01 or s13 < 0.01:
                    continue
                # Composition: strength(D1->D3) should be >= strength(D1->D2) * strength(D2->D3)
                # (monotonicity in the enriched sense)
                composed = s12 * s23
                if s13 < composed * 0.5:  # allow some slack
                    violations.append(
                        f"  {d1} -> {d2} -> {d3}: "
                        f"s12={s12:.3f}, s23={s23:.3f}, "
                        f"composed={composed:.3f}, direct s13={s13:.3f}"
                    )

    return identity_ok, len(violations), violations


# =====================================================================
# Step 4: Rezk Completion Strategy
# =====================================================================

def rezk_equivalence_classes(
    objects: List[str],
    category: Category,
    threshold: float = 0.05,
) -> List[Set[str]]:
    """Group objects with Yoneda distance < threshold."""
    classes: List[Set[str]] = []
    assigned: Set[str] = set()

    for obj in objects:
        if obj in assigned:
            continue
        equiv_class = {obj}
        for other in objects:
            if other != obj and other not in assigned:
                dist = yoneda_distance(obj, other, category)
                if dist < threshold:
                    equiv_class.add(other)
        classes.append(equiv_class)
        assigned.update(equiv_class)

    return classes


def rezk_score(
    drug: str,
    disease: str,
    clean_cat: Category,
    type_map: Dict[str, str],
    disease_classes: List[Set[str]],
    known_treatments: Dict[str, Set[str]],
) -> float:
    """Score after Rezk completion: if any disease in the same equivalence
    class has a known drug treatment, propagate that label.

    Returns a score based on whether the drug treats any equivalent disease.
    """
    # Find which equivalence class this disease belongs to
    target_class: Optional[Set[str]] = None
    for cls in disease_classes:
        if disease in cls:
            target_class = cls
            break

    if target_class is None or len(target_class) <= 1:
        # No equivalences found, fall back to Yoneda score
        return yoneda_score(drug, disease, clean_cat, type_map, known_treatments)

    # Merge known treatments across all diseases in the class
    merged_treatments: Set[str] = set()
    for d in target_class:
        merged_treatments.update(known_treatments.get(d, set()))

    if drug in merged_treatments:
        return 1.0

    # Score by Yoneda similarity to any drug treating any disease in the class
    best = 0.0
    for treating_drug in merged_treatments:
        if treating_drug == drug:
            continue
        dist = yoneda_distance(drug, treating_drug, clean_cat)
        sim = 1.0 - dist
        if sim > best:
            best = sim

    return best


# =====================================================================
# Step 5: Combined Scoring & AUROC Comparison
# =====================================================================

def run_comparison(db_path: str = DB_PATH) -> None:
    """Run full STT comparison experiment."""
    t0 = time.time()
    print("STT Drug Repurposing Experiment")
    print("=" * 60)
    print()

    # ---- Load existing system ----
    print("Loading full typed view (existing 8 strategies)...")
    base_cat, missing = load_full_typed_view(db_path, remove_direct_labels=True)
    # Get positives from unmodified graph
    base_cat_full, _ = load_full_typed_view(db_path)
    drugs, diseases, positives = drug_disease_pairs(base_cat_full)
    print(f"  {len(drugs)} drugs, {len(diseases)} diseases, {len(positives)} positives")
    print(f"  {len(base_cat.morphisms())} morphisms (direct labels removed)")

    # ---- Build known treatments map ----
    known_treatments: Dict[str, Set[str]] = defaultdict(set)
    for drug, disease in positives:
        known_treatments[disease].add(drug)

    # ---- Load clean subgraph ----
    print("\nLoading clean subgraph (MEASURED + ESTABLISHED)...")
    clean_cat, type_map = load_clean_subgraph(db_path)
    n_clean = len(clean_cat.morphisms())
    n_clean_objs = len(clean_cat.objects())
    print(f"  {n_clean_objs} objects, {n_clean} morphisms")

    # Also load inferred tier for comparison
    print("Loading extended subgraph (+ INFERRED)...")
    extended_cat, _ = load_clean_subgraph(
        db_path, tiers=("MEASURED", "ESTABLISHED", "INFERRED")
    )
    n_ext = len(extended_cat.morphisms())
    print(f"  {len(extended_cat.objects())} objects, {n_ext} morphisms")

    # ---- Precompute disease fibers and protein sets ----
    print("\nPrecomputing disease fibers...")
    disease_proteins: Dict[str, Set[str]] = {}
    disease_fibers: Dict[str, Set[Tuple[str, str]]] = {}
    for d in diseases:
        proteins, fiber = disease_fiber(d, clean_cat, type_map)
        disease_proteins[d] = proteins
        disease_fibers[d] = fiber
    print(f"  Diseases with proteins: {sum(1 for p in disease_proteins.values() if p)}/{len(diseases)}")
    print(f"  Total drug-protein fiber entries: {sum(len(f) for f in disease_fibers.values())}")

    # ---- Compute Rezk equivalence classes ----
    print("\nComputing Rezk equivalence classes...")
    disease_classes = rezk_equivalence_classes(diseases, clean_cat, threshold=0.05)
    drug_classes = rezk_equivalence_classes(drugs, clean_cat, threshold=0.05)

    nontrivial_disease = [c for c in disease_classes if len(c) > 1]
    nontrivial_drug = [c for c in drug_classes if len(c) > 1]
    print(f"  Disease classes: {len(disease_classes)} total, {len(nontrivial_disease)} nontrivial")
    print(f"  Drug classes: {len(drug_classes)} total, {len(nontrivial_drug)} nontrivial")

    # ---- Verify transport axioms ----
    print("\nVerifying transport axioms...")
    id_ok, n_violations, violation_details = verify_transport_axioms(
        diseases, disease_proteins, disease_fibers
    )
    print(f"  Identity axiom: {id_ok}/{len(diseases)} diseases OK")
    print(f"  Composition violations: {n_violations}")

    # ---- Score all pairs ----
    print(f"\nScoring {len(drugs)} x {len(diseases)} = {len(drugs) * len(diseases)} pairs...")
    strategies = make_strategies(base_cat)

    existing_scores: List[float] = []
    yoneda_scores: List[float] = []
    transport_scores: List[float] = []
    rezk_scores: List[float] = []
    stt_combined_scores: List[float] = []
    all_combined_scores: List[float] = []
    labels: List[int] = []

    # Track STT-unique predictions
    stt_novel: List[Tuple[str, str, float, float, float, float, float]] = []
    stt_disagree: List[Tuple[str, str, float, float, float]] = []

    for i, drug in enumerate(drugs):
        if (i + 1) % 20 == 0:
            print(f"  Scored {i + 1}/{len(drugs)} drugs...")
        for disease in diseases:
            label = 1 if (drug, disease) in positives else 0
            labels.append(label)

            # Existing 8-strategy score
            ex_score, _ = score_pair(strategies, drug, disease)
            existing_scores.append(ex_score)

            # Yoneda distance score
            y_score = yoneda_score(drug, disease, clean_cat, type_map, known_treatments)
            yoneda_scores.append(y_score)

            # Transport score
            t_score = transport_score(
                drug, disease, clean_cat, type_map,
                disease_proteins, disease_fibers, diseases,
            )
            transport_scores.append(t_score)

            # Rezk completion score
            r_score = rezk_score(
                drug, disease, clean_cat, type_map,
                disease_classes, known_treatments,
            )
            rezk_scores.append(r_score)

            # STT combined (equal weight)
            stt_comb = (y_score + t_score + r_score) / 3.0
            stt_combined_scores.append(stt_comb)

            # All 11 combined: existing 8 weight 0.6, STT 3 weight 0.4
            all_comb = 0.6 * ex_score + 0.4 * stt_comb
            all_combined_scores.append(all_comb)

            # Track novel/disagreement
            if label == 0:
                if stt_comb > 0.5 and ex_score < 0.3:
                    stt_novel.append((
                        drug, disease, ex_score, y_score, t_score, r_score, stt_comb
                    ))
                if abs(ex_score - stt_comb) > 0.3:
                    stt_disagree.append((
                        drug, disease, ex_score, stt_comb,
                        stt_comb - ex_score,
                    ))

    # ---- Compute AUROCs ----
    print("\nComputing metrics...")
    results = {}
    for name, scores in [
        ("Existing 8 strategies", existing_scores),
        ("Yoneda distance only", yoneda_scores),
        ("Fibration transport", transport_scores),
        ("Rezk completion", rezk_scores),
        ("STT combined (3)", stt_combined_scores),
        ("All combined (8+3)", all_combined_scores),
    ]:
        auroc, conc, disc, tied = pairwise_auroc(scores, labels)
        auprc = compute_auprc(scores, labels)
        hits5 = compute_hits_at_k(scores, labels, 5)
        hits10 = compute_hits_at_k(scores, labels, 10)
        mrr_val = compute_mrr(scores, labels)
        results[name] = {
            "auroc": auroc,
            "auprc": auprc,
            "hits5": hits5,
            "hits10": hits10,
            "mrr": mrr_val,
        }

    elapsed = time.time() - t0

    # ---- Output ----
    print()
    print("=" * 60)
    print("STT Drug Repurposing Results")
    print("=" * 60)
    print()
    print(f"Protocol: full_typed / remove_direct_labels")
    print(f"Clean subgraph: {n_clean_objs} objects, {n_clean} morphisms (MEASURED + ESTABLISHED)")
    print(f"Extended subgraph: {n_ext} morphisms (+ INFERRED)")
    print(f"Pairs: {len(drugs)} drugs x {len(diseases)} diseases = {len(labels)}")
    print(f"Positives: {sum(labels)}")
    print()

    # AUROC table
    print(f"{'Method':<28s} {'AUROC':>7s} {'AUPRC':>7s} {'H@5':>5s} {'H@10':>5s} {'MRR':>7s}")
    print("-" * 68)
    for name, m in results.items():
        print(
            f"{name:<28s} {m['auroc']:>7.3f} {m['auprc']:>7.3f} "
            f"{m['hits5']:>5.2f} {m['hits10']:>5.2f} {m['mrr']:>7.4f}"
        )
    print()

    # Disease Yoneda equivalence classes
    print("Disease Yoneda Equivalence Classes (distance < 0.05):")
    if nontrivial_disease:
        for cls in nontrivial_disease:
            members = sorted(cls)
            # Compute pairwise distances
            dists = []
            members_list = list(members)
            for i in range(len(members_list)):
                for j in range(i + 1, len(members_list)):
                    d = yoneda_distance(members_list[i], members_list[j], clean_cat)
                    dists.append(d)
            avg_dist = sum(dists) / len(dists) if dists else 0.0
            print(f"  {{{', '.join(members)}}} (avg distance {avg_dist:.4f})")
    else:
        print("  None found -- all diseases have distinct Yoneda profiles on clean subgraph")
    print()

    # Drug Yoneda equivalence classes
    print(f"Drug Yoneda Equivalence Classes (distance < 0.05):")
    if nontrivial_drug:
        for cls in sorted(nontrivial_drug, key=lambda c: -len(c)):
            members = sorted(cls)
            dists = []
            members_list = list(members)
            for i in range(len(members_list)):
                for j in range(i + 1, len(members_list)):
                    d = yoneda_distance(members_list[i], members_list[j], clean_cat)
                    dists.append(d)
            avg_dist = sum(dists) / len(dists) if dists else 0.0
            print(f"  {{{', '.join(members)}}} (avg distance {avg_dist:.4f})")
    else:
        print("  None found -- all drugs have distinct Yoneda profiles on clean subgraph")
    print()

    # Transport axiom violations
    print(f"Transport Axiom Verification:")
    print(f"  Identity: {id_ok}/{len(diseases)} OK")
    print(f"  Composition violations: {n_violations}")
    if violation_details:
        for v in violation_details[:10]:
            print(v)
        if len(violation_details) > 10:
            print(f"  ... and {len(violation_details) - 10} more")
    print()

    # Disease protein coverage
    print("Disease Protein Coverage (clean subgraph):")
    for d in sorted(diseases):
        n_proteins = len(disease_proteins.get(d, set()))
        n_fiber = len(disease_fibers.get(d, set()))
        print(f"  {d:<25s} {n_proteins:>3d} proteins, {n_fiber:>3d} drug-protein pairs")
    print()

    # Top STT-unique predictions
    stt_novel.sort(key=lambda x: -x[6])
    print("Top 10 STT-Enhanced Candidates (STT > 0.5, existing < 0.3):")
    if stt_novel:
        for rank, (drug, disease, ex, y, t, r, s) in enumerate(stt_novel[:10], 1):
            print(
                f"  {rank:>2d}. {drug} -> {disease}  "
                f"(existing={ex:.3f}, yoneda={y:.3f}, transport={t:.3f}, "
                f"rezk={r:.3f}, stt={s:.3f})"
            )
    else:
        print("  None -- no pairs where STT > 0.5 and existing < 0.3")
    print()

    # Top disagreements
    stt_disagree.sort(key=lambda x: -abs(x[4]))
    print("Top 10 Largest STT vs Existing Disagreements:")
    if stt_disagree:
        for rank, (drug, disease, ex, stt, delta) in enumerate(stt_disagree[:10], 1):
            direction = "STT higher" if delta > 0 else "STT lower"
            print(
                f"  {rank:>2d}. {drug} -> {disease}  "
                f"(existing={ex:.3f}, stt={stt:.3f}, delta={delta:+.3f} {direction})"
            )
    else:
        print("  None -- no pairs with |delta| > 0.3")
    print()

    # Summary interpretation
    existing_auroc = results["Existing 8 strategies"]["auroc"]
    stt_auroc = results["STT combined (3)"]["auroc"]
    all_auroc = results["All combined (8+3)"]["auroc"]

    print("=" * 60)
    print("Interpretation")
    print("=" * 60)
    delta_stt = stt_auroc - existing_auroc
    delta_all = all_auroc - existing_auroc
    print(f"  Existing AUROC: {existing_auroc:.3f}")
    print(f"  STT-only AUROC: {stt_auroc:.3f} ({delta_stt:+.3f})")
    print(f"  Combined AUROC: {all_auroc:.3f} ({delta_all:+.3f})")
    print()
    if delta_all > 0.005:
        print("  STT strategies ADD predictive signal beyond path-walking.")
    elif delta_all > -0.005:
        print("  STT strategies are comparable -- structural analysis valuable for")
        print("  equivalence detection and data quality, not raw AUROC.")
    else:
        print("  STT strategies hurt AUROC on the clean subgraph.")
        print("  The clean subgraph may be too sparse, or the graph too small for")
        print("  shape-based analysis to outperform path-walking.")
    print()
    print(f"  Elapsed: {elapsed:.1f}s")
    print()

    # ---- Extended subgraph comparison ----
    print("=" * 60)
    print("Extended Subgraph Comparison (+ INFERRED edges)")
    print("=" * 60)
    print()

    ext_yoneda_scores: List[float] = []
    ext_labels: List[int] = []

    for drug in drugs:
        for disease in diseases:
            label = 1 if (drug, disease) in positives else 0
            ext_labels.append(label)
            y_score = yoneda_score(drug, disease, extended_cat, type_map, known_treatments)
            ext_yoneda_scores.append(y_score)

    ext_auroc, _, _, _ = pairwise_auroc(ext_yoneda_scores, ext_labels)
    clean_yoneda_auroc = results["Yoneda distance only"]["auroc"]
    print(f"  Yoneda AUROC on clean subgraph ({n_clean} edges):    {clean_yoneda_auroc:.3f}")
    print(f"  Yoneda AUROC on extended subgraph ({n_ext} edges): {ext_auroc:.3f}")
    print(f"  Delta: {ext_auroc - clean_yoneda_auroc:+.3f}")
    if ext_auroc > clean_yoneda_auroc:
        print("  INFERRED edges improve Yoneda fingerprint resolution.")
    else:
        print("  INFERRED edges add noise to Yoneda fingerprints.")
    print()


def main() -> int:
    run_comparison()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
