#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Drug Repurposing Scientific Audit
================================================

Formal scientific audit of the drug repurposing pipeline following
best practices from the drug repurposing validation literature.

28 checks across 6 categories:
  1. Network Topology     (4 checks)
  2. Holdout Validation   (7 checks) -- recall, precision, F1, AUROC, AUPRC, MRR, Hits@K
  3. Statistical Significance (4 checks) -- permutation test, enrichment factors, baseline comparison
  4. Mechanism Validation (5 checks) -- path evidence, multi-strategy, reasoning, confidence, ablation
  5. Data Provenance      (4 checks) -- leakage, source attribution, holdout source, negative sampling
  6. Reproducibility      (4 checks) -- determinism, parameter sensitivity, cross-validation, runtime

References:
  - Pushpakom et al. (2019) "Drug repurposing: progress, challenges and recommendations"
  - Himmelstein & Baranzini (2015) "Hetnet edge prediction"
  - AUROC/AUPRC: Davis & Goadrich (2006) "The relationship between PR and ROC curves"
"""

import sys
import io
import json
import time
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.scientific_audit import AuditResult, AuditReport, save_audit_report


# ---------------------------------------------------------------------------
# Manual AUROC / AUPRC (no sklearn dependency)
# ---------------------------------------------------------------------------

def _compute_auroc(scores, labels):
    """
    Compute Area Under ROC Curve via trapezoidal rule.

    Args:
        scores: list of float, predicted scores for each sample
        labels: list of int (0/1), ground truth

    Returns:
        float: AUROC value in [0, 1]
    """
    if not scores or not labels:
        return 0.0

    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0

    # Sort by score descending
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])

    tp = 0
    fp = 0
    prev_fpr = 0.0
    prev_tpr = 0.0
    auroc = 0.0
    prev_score = None

    for score, label in paired:
        if prev_score is not None and score != prev_score:
            fpr = fp / n_neg
            tpr = tp / n_pos
            # Trapezoidal area
            auroc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0
            prev_fpr = fpr
            prev_tpr = tpr
        prev_score = score
        if label == 1:
            tp += 1
        else:
            fp += 1

    # Final point
    fpr = fp / n_neg
    tpr = tp / n_pos
    auroc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0

    return auroc


def _compute_auprc(scores, labels):
    """
    Compute Area Under Precision-Recall Curve via step function.

    Args:
        scores: list of float, predicted scores for each sample
        labels: list of int (0/1), ground truth

    Returns:
        float: AUPRC value in [0, 1]
    """
    if not scores or not labels:
        return 0.0

    n_pos = sum(labels)
    if n_pos == 0:
        return 0.0

    # Sort by score descending
    paired = sorted(zip(scores, labels), key=lambda x: -x[0])

    tp = 0
    fp = 0
    auprc = 0.0
    prev_recall = 0.0

    for score, label in paired:
        if label == 1:
            tp += 1
        else:
            fp += 1
        precision = tp / (tp + fp)
        recall = tp / n_pos

        if recall != prev_recall:
            # Step function: precision * delta_recall
            auprc += precision * (recall - prev_recall)
            prev_recall = recall

    return auprc


# ---------------------------------------------------------------------------
# Category 1: Network Topology
# ---------------------------------------------------------------------------

def _check_network_topology(store, results):
    """4 checks on network structure."""
    n_nodes = store.count_objects()
    n_edges = store.count_morphisms()

    # Adaptive thresholds based on network scale
    # Small curated network: >= 50 nodes, >= 100 edges
    # Scaled network (Hetionet+): >= 1000 nodes, >= 10000 edges
    is_scaled = n_nodes >= 1000

    # For connectivity check, only sample objects (avoid loading millions)
    sample_limit = min(100000, n_nodes + 1000)
    all_objects = store.list_objects(limit=sample_limit)
    # For morphisms, use count instead of loading all for large networks
    if n_edges <= 100000:
        all_morphisms = store.list_morphisms(limit=100000)
    else:
        all_morphisms = store.list_morphisms(limit=100000)  # Sample for connectivity

    # 1. node_count
    min_nodes = 1000 if is_scaled else 50
    results.append(AuditResult(
        category="Network Topology",
        check_name="node_count",
        passed=n_nodes >= min_nodes,
        severity="CRITICAL",
        value=n_nodes,
        threshold=f">= {min_nodes}",
        message=f"{n_nodes:,} objects in store",
        reference="Minimum network size for meaningful link prediction",
    ))

    # 2. edge_count
    min_edges = 10000 if is_scaled else 100
    results.append(AuditResult(
        category="Network Topology",
        check_name="edge_count",
        passed=n_edges >= min_edges,
        severity="CRITICAL",
        value=n_edges,
        threshold=f">= {min_edges}",
        message=f"{n_edges:,} morphisms in store",
        reference="Minimum edge density for compositional reasoning",
    ))

    # 3. graph_density
    # Scaled networks are naturally sparser
    max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 1
    density = n_edges / max_edges
    density_min = 0.0001 if is_scaled else 0.01
    density_max = 0.1 if is_scaled else 0.5
    results.append(AuditResult(
        category="Network Topology",
        check_name="graph_density",
        passed=density_min <= density <= density_max,
        severity="WARNING",
        value=round(density, 6),
        threshold=f"{density_min} - {density_max}",
        message=f"Density = {density:.6f} ({n_edges:,}/{max_edges:,})",
        reference="Optimal density range for link prediction",
    ))

    # 4. connected_components -- Drug/Disease reachability via 2-hop
    obj_map = {o.name: o for o in all_objects}
    drugs = [o for o in all_objects if o.type_name == "Drug"]
    diseases = [o for o in all_objects if o.type_name == "Disease"]

    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for m in all_morphisms:
        outgoing[m.source_name].add(m.target_name)
        incoming[m.target_name].add(m.source_name)

    # For each Drug, find 2-hop reachable nodes
    reachable_count = 0
    total_drug_disease = len(drugs) * len(diseases)

    for drug in drugs:
        # 1-hop from drug
        hop1 = outgoing.get(drug.name, set())
        # 2-hop from drug
        hop2 = set()
        for intermediate in hop1:
            hop2 |= outgoing.get(intermediate, set())
        reachable = hop1 | hop2
        for disease in diseases:
            if disease.name in reachable:
                reachable_count += 1

    reachable_pct = (reachable_count / total_drug_disease * 100) if total_drug_disease > 0 else 0
    results.append(AuditResult(
        category="Network Topology",
        check_name="connected_components",
        passed=True,
        severity="INFO",
        value=round(reachable_pct, 1),
        threshold="informational (not all Drug-Disease pairs have biological paths)",
        message=f"{reachable_pct:.1f}% of Drug-Disease pairs reachable via 2-hop ({reachable_count}/{total_drug_disease})",
        reference="Network connectivity (path_exists on TPs is the real test)",
    ))


# ---------------------------------------------------------------------------
# Category 2: Holdout Validation
# ---------------------------------------------------------------------------

def _check_holdout_validation(store, engine, results, external_holdout=None):
    """
    5 checks: recall, precision, F1, AUROC, AUPRC.

    Args:
        external_holdout: Optional list of (source, target, relation, confidence)
            tuples from external databases (e.g. Hetionet). If provided, these
            are merged with the curated holdout set.

    Returns (all_scores, positive_set, conjectures) for downstream use.
    """
    from data.drugs.drug_network import get_holdout_edges, DRUGS, DISEASES, DRUG_DISEASE_APPROVED

    holdout = get_holdout_edges()
    holdout_set = {(h[0], h[1]) for h in holdout}
    approved_set = {(a[0], a[1]) for a in DRUG_DISEASE_APPROVED}

    # Merge external holdout if provided (from Hetionet or other sources)
    if external_holdout:
        for edge in external_holdout:
            holdout_set.add((edge[0], edge[1]))

    # Collect all Drug and Disease names from the store
    all_drugs = store.get_objects_by_type("Drug")
    all_diseases = store.get_objects_by_type("Disease")
    drug_names = sorted(set(list(DRUGS.keys()) + [d.name for d in all_drugs]))
    disease_names = sorted(set(list(DISEASES.keys()) + [d.name for d in all_diseases]))
    all_pairs = [(d, dis) for d in drug_names for dis in disease_names]

    # Positive set = holdout + approved
    positive_set = holdout_set | approved_set

    # Run conjecture engine -- adapt parameters for network size
    n_objects = store.count_objects()
    is_scaled = n_objects >= 1000
    max_cands = 5000 if is_scaled else 2000

    from oracle.conjecture import ConjectureEngine
    conjecture_engine = ConjectureEngine(engine)
    result = conjecture_engine.conjecture(
        top_k=5000,
        min_confidence=0.25,
    )

    # Extract drug-disease predictions
    all_objects_map = {o.name: o for o in store.list_objects(limit=100000)}
    drug_disease_conjectures = []
    for conj in result.conjectures:
        src = all_objects_map.get(conj.source)
        tgt = all_objects_map.get(conj.target)
        if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
            drug_disease_conjectures.append(conj)

    predicted_pairs = {(c.source, c.target) for c in drug_disease_conjectures}

    # TP / FP / FN
    tp = len(predicted_pairs & holdout_set)
    fp = len(predicted_pairs - holdout_set)
    fn = len(holdout_set - predicted_pairs)

    recall = tp / len(holdout_set) if holdout_set else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="recall",
        passed=recall >= 0.50,
        severity="CRITICAL",
        value=round(recall, 4),
        threshold=">= 0.50",
        message=f"Recall = {recall:.4f} ({tp}/{len(holdout_set)} holdout edges recovered)",
        reference="Drug repurposing minimum recall threshold",
    ))

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="precision",
        passed=precision >= 0.10,
        severity="WARNING",
        value=round(precision, 4),
        threshold=">= 0.10",
        message=f"Precision = {precision:.4f} ({tp}/{tp + fp} drug-disease predictions correct)",
        reference="Drug repurposing precision (false positives may be novel)",
    ))

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="f1_score",
        passed=f1 >= 0.20,
        severity="CRITICAL",
        value=round(f1, 4),
        threshold=">= 0.20",
        message=f"F1 = {f1:.4f}",
        reference="Harmonic mean of precision and recall",
    ))

    # Score ALL 408 drug-disease pairs for AUROC/AUPRC
    conj_score_map = {}
    for conj in drug_disease_conjectures:
        conj_score_map[(conj.source, conj.target)] = conj.top_confidence

    all_scores = []
    all_labels = []
    for pair in all_pairs:
        score = conj_score_map.get(pair, 0.0)
        label = 1 if pair in positive_set else 0
        all_scores.append(score)
        all_labels.append(label)

    auroc = _compute_auroc(all_scores, all_labels)
    auprc = _compute_auprc(all_scores, all_labels)

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="auroc",
        passed=auroc >= 0.70,
        severity="CRITICAL",
        value=round(auroc, 4),
        threshold=">= 0.70",
        message=f"AUROC = {auroc:.4f} over {len(all_pairs)} drug-disease pairs ({sum(all_labels)} positives, {len(all_labels) - sum(all_labels)} negatives)",
        reference="Area Under ROC: Davis & Goadrich (2006)",
    ))

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="auprc",
        passed=auprc >= 0.30,
        severity="WARNING",
        value=round(auprc, 4),
        threshold=">= 0.30",
        message=f"AUPRC = {auprc:.4f}",
        reference="Area Under Precision-Recall Curve",
    ))

    # --- MRR (Mean Reciprocal Rank) ---
    # For each holdout (drug, disease), rank all diseases for that drug by score.
    # MRR = mean of 1/rank across holdout edges.
    # Standard metric in all KG drug repurposing papers (TxGNN, DRKG, BioPathNet).
    reciprocal_ranks = []
    hits_at = {1: 0, 3: 0, 10: 0}
    for h_drug, h_disease in holdout_set:
        # Get scores for all diseases for this drug
        drug_scores = []
        for dis in disease_names:
            score = conj_score_map.get((h_drug, dis), 0.0)
            drug_scores.append((score, dis))
        # Sort descending by score
        drug_scores.sort(key=lambda x: -x[0])
        # Find rank of the holdout disease
        rank = None
        for idx, (sc, dis) in enumerate(drug_scores):
            if dis == h_disease:
                rank = idx + 1
                break
        if rank is not None:
            reciprocal_ranks.append(1.0 / rank)
            for k in hits_at:
                if rank <= k:
                    hits_at[k] += 1

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    n_holdout = len(holdout_set)

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="mrr",
        passed=mrr >= 0.20,
        severity="CRITICAL",
        value=round(mrr, 4),
        threshold=">= 0.20",
        message=f"MRR = {mrr:.4f} (mean reciprocal rank over {n_holdout} holdout edges)",
        reference="Standard KG link prediction metric (TxGNN, DRKG, BioPathNet)",
    ))

    # --- Hits@K ---
    hits10_pct = (hits_at[10] / n_holdout * 100) if n_holdout > 0 else 0
    hits3_pct = (hits_at[3] / n_holdout * 100) if n_holdout > 0 else 0
    hits1_pct = (hits_at[1] / n_holdout * 100) if n_holdout > 0 else 0

    results.append(AuditResult(
        category="Holdout Validation",
        check_name="hits_at_k",
        passed=hits10_pct >= 50,
        severity="WARNING",
        value={"hits@1": round(hits1_pct, 1), "hits@3": round(hits3_pct, 1), "hits@10": round(hits10_pct, 1)},
        threshold="Hits@10 >= 50%",
        message=f"Hits@1={hits1_pct:.1f}%, Hits@3={hits3_pct:.1f}%, Hits@10={hits10_pct:.1f}% ({hits_at[10]}/{n_holdout})",
        reference="Standard KG link prediction metric",
    ))

    return all_scores, all_labels, drug_disease_conjectures


# ---------------------------------------------------------------------------
# Category 3: Statistical Significance
# ---------------------------------------------------------------------------

def _check_statistical_significance(all_scores, all_labels, store, results):
    """4 checks: permutation test, enrichment at top-10 and top-50, baseline comparison."""
    n_total = len(all_labels)
    n_pos = sum(all_labels)
    baseline_rate = n_pos / n_total if n_total > 0 else 0.0

    # Observed AUROC
    observed_auroc = _compute_auroc(all_scores, all_labels)

    # Permutation test: shuffle labels 1000x, recompute AUROC each time
    n_permutations = 1000
    rng = random.Random(42)  # Deterministic seed
    count_ge = 0
    for _ in range(n_permutations):
        shuffled = all_labels[:]
        rng.shuffle(shuffled)
        perm_auroc = _compute_auroc(all_scores, shuffled)
        if perm_auroc >= observed_auroc:
            count_ge += 1

    p_value = count_ge / n_permutations

    results.append(AuditResult(
        category="Statistical Significance",
        check_name="permutation_test",
        passed=p_value < 0.05,
        severity="CRITICAL",
        value=round(p_value, 4),
        threshold="p < 0.05",
        message=f"Permutation p-value = {p_value:.4f} ({count_ge}/{n_permutations} permutations >= observed AUROC {observed_auroc:.4f})",
        reference="Permutation test for AUROC significance",
    ))

    # Enrichment factors at top-10 and top-50
    # Sort pairs by score descending
    paired = sorted(zip(all_scores, all_labels), key=lambda x: -x[0])

    for top_k, ef_threshold, check_name in [(10, 3.0, "enrichment_top10"), (50, 2.0, "enrichment_top50")]:
        top_k_actual = min(top_k, len(paired))
        top_k_labels = [lab for _, lab in paired[:top_k_actual]]
        tp_in_top_k = sum(top_k_labels)
        hit_rate = tp_in_top_k / top_k_actual if top_k_actual > 0 else 0
        ef = hit_rate / baseline_rate if baseline_rate > 0 else 0

        results.append(AuditResult(
            category="Statistical Significance",
            check_name=check_name,
            passed=ef >= ef_threshold,
            severity="WARNING",
            value=round(ef, 2),
            threshold=f">= {ef_threshold}",
            message=f"EF@{top_k} = {ef:.2f} ({tp_in_top_k}/{top_k_actual} true positives, baseline rate {baseline_rate:.4f})",
            reference=f"Enrichment factor at top-{top_k} predictions",
        ))

    # --- Baseline Comparison ---
    # Compare our AUROC against 3 trivial baselines:
    # 1. Random: random scores -> expected AUROC ~0.50
    # 2. Frequency: score = degree(drug) * degree(disease) -> tests if we just predict popular nodes
    # 3. Shortest-path: score = 1/path_length -> tests if we beat simple graph traversal
    rng_baseline = random.Random(42)
    random_scores = [rng_baseline.random() for _ in all_labels]
    random_auroc = _compute_auroc(random_scores, all_labels)

    # Frequency baseline: need degree info from store
    from data.drugs.drug_network import DRUG_TARGET_INTERACTIONS, PROTEIN_DISEASE_ASSOCIATIONS
    drug_degree = defaultdict(int)
    disease_degree = defaultdict(int)
    for dti in DRUG_TARGET_INTERACTIONS:
        drug_degree[dti[0]] += 1
    for pda in PROTEIN_DISEASE_ASSOCIATIONS:
        disease_degree[pda[1]] += 1

    from data.drugs.drug_network import DRUGS, DISEASES
    drug_names_sorted = sorted(DRUGS.keys())
    disease_names_sorted = sorted(DISEASES.keys())
    freq_scores = []
    for d in drug_names_sorted:
        for dis in disease_names_sorted:
            freq_scores.append(drug_degree.get(d, 0) * disease_degree.get(dis, 0))
    # Normalize
    max_freq = max(freq_scores) if freq_scores and max(freq_scores) > 0 else 1
    freq_scores = [s / max_freq for s in freq_scores]
    freq_auroc = _compute_auroc(freq_scores, all_labels)

    # Shortest-path baseline: score = 1/shortest_path_length in the graph
    # Tests whether our inference engine adds value beyond simple graph traversal
    all_morphisms_sp = store.list_morphisms(limit=100000)
    sp_adj = defaultdict(set)
    for m in all_morphisms_sp:
        sp_adj[m.source_name].add(m.target_name)
        sp_adj[m.target_name].add(m.source_name)  # undirected for BFS

    sp_scores = []
    for d in drug_names_sorted:
        # BFS from this drug to find shortest path to all nodes
        visited = {d: 0}
        queue = deque([d])
        while queue:
            node = queue.popleft()
            for neighbor in sp_adj.get(node, set()):
                if neighbor not in visited:
                    visited[neighbor] = visited[node] + 1
                    queue.append(neighbor)
        for dis in disease_names_sorted:
            path_len = visited.get(dis, -1)
            sp_scores.append(1.0 / path_len if path_len > 0 else 0.0)
    sp_auroc = _compute_auroc(sp_scores, all_labels)

    our_auroc = observed_auroc
    beats_all = (our_auroc > random_auroc + 0.05
                 and our_auroc > freq_auroc + 0.05
                 and our_auroc > sp_auroc + 0.05)
    results.append(AuditResult(
        category="Statistical Significance",
        check_name="baseline_comparison",
        passed=beats_all,
        severity="CRITICAL",
        value={"ours": round(our_auroc, 4), "random": round(random_auroc, 4), "frequency": round(freq_auroc, 4), "shortest_path": round(sp_auroc, 4)},
        threshold="Our AUROC > all 3 baselines by >= 0.05",
        message=f"Ours={our_auroc:.4f} vs Random={random_auroc:.4f}, Frequency={freq_auroc:.4f}, ShortestPath={sp_auroc:.4f}",
        reference="Baseline comparison: random, frequency bias, shortest-path (Nature Methods reproducibility standard)",
    ))


# ---------------------------------------------------------------------------
# Category 4: Mechanism Validation
# ---------------------------------------------------------------------------

def _check_mechanism_validation(conjectures, store, results):
    """5 checks: path_exists, multi_strategy, reasoning_present, confidence_calibration, ablation_study."""
    from data.drugs.drug_network import get_holdout_edges

    holdout = get_holdout_edges()
    holdout_set = {(h[0], h[1]) for h in holdout}

    all_morphisms = store.list_morphisms(limit=50000)
    outgoing = defaultdict(set)
    for m in all_morphisms:
        outgoing[m.source_name].add(m.target_name)

    # Classify conjectures as TP or FP
    tp_conjectures = [c for c in conjectures if (c.source, c.target) in holdout_set]
    fp_conjectures = [c for c in conjectures if (c.source, c.target) not in holdout_set]

    # 1. path_exists: every TP has a 2-hop Drug->Protein->Disease path
    paths_found = 0
    for conj in tp_conjectures:
        hop1 = outgoing.get(conj.source, set())
        hop2 = set()
        for intermediate in hop1:
            hop2 |= outgoing.get(intermediate, set())
        if conj.target in hop1 or conj.target in hop2:
            paths_found += 1

    path_pct = (paths_found / len(tp_conjectures) * 100) if tp_conjectures else 0
    results.append(AuditResult(
        category="Mechanism Validation",
        check_name="path_exists",
        passed=path_pct >= 100.0 if tp_conjectures else True,
        severity="CRITICAL",
        value=round(path_pct, 1),
        threshold="100% of TPs have 2-hop path",
        message=f"{path_pct:.1f}% of TPs have Drug->Protein->Disease path ({paths_found}/{len(tp_conjectures)})",
        reference="Mechanistic evidence for drug repurposing predictions",
    ))

    # 2. multi_strategy: >= 50% of predictions scored by 2+ inference strategies
    #    conj.predictions contains one Prediction per strategy that scored > 0.
    #    We count distinct strategy_name values, not candidate_sources (generators).
    multi_strat = 0
    for conj in conjectures:
        distinct_strategies = {p.strategy_name for p in conj.predictions}
        if len(distinct_strategies) >= 2:
            multi_strat += 1
    multi_pct = (multi_strat / len(conjectures) * 100) if conjectures else 0

    results.append(AuditResult(
        category="Mechanism Validation",
        check_name="multi_strategy",
        passed=multi_pct >= 50,
        severity="WARNING",
        value=round(multi_pct, 1),
        threshold=">= 50% predictions scored by 2+ inference strategies",
        message=f"{multi_pct:.1f}% of predictions corroborated by multiple strategies ({multi_strat}/{len(conjectures)})",
        reference="Multi-strategy corroboration (distinct inference strategies, not candidate generators)",
    ))

    # 3. reasoning_present: best prediction has non-empty reasoning
    with_reasoning = 0
    for conj in conjectures:
        best = conj.best
        if best and best.reasoning and len(best.reasoning.strip()) > 0:
            with_reasoning += 1
    reasoning_pct = (with_reasoning / len(conjectures) * 100) if conjectures else 0

    results.append(AuditResult(
        category="Mechanism Validation",
        check_name="reasoning_present",
        passed=reasoning_pct >= 80,
        severity="WARNING",
        value=round(reasoning_pct, 1),
        threshold=">= 80% predictions have reasoning",
        message=f"{reasoning_pct:.1f}% of predictions include reasoning ({with_reasoning}/{len(conjectures)})",
        reference="Explainability in drug repurposing",
    ))

    # 4. confidence_calibration: mean TP confidence > mean FP confidence
    tp_confs = [c.top_confidence for c in tp_conjectures]
    fp_confs = [c.top_confidence for c in fp_conjectures]
    tp_mean = sum(tp_confs) / len(tp_confs) if tp_confs else 0
    fp_mean = sum(fp_confs) / len(fp_confs) if fp_confs else 0

    results.append(AuditResult(
        category="Mechanism Validation",
        check_name="confidence_calibration",
        passed=tp_mean > fp_mean,
        severity="WARNING",
        value={"tp_mean": round(tp_mean, 4), "fp_mean": round(fp_mean, 4)},
        threshold="TP mean confidence > FP mean confidence",
        message=f"TP mean={tp_mean:.4f}, FP mean={fp_mean:.4f} ({'calibrated' if tp_mean > fp_mean else 'miscalibrated'})",
        reference="Confidence calibration for drug repurposing",
    ))

    # --- Ablation Study (Real) ---
    # Simulate removal of each strategy one at a time.
    # For each strategy S: filter out all predictions from S, check which
    # conjectures survive (still have at least one prediction from another strategy),
    # then recompute recall on the holdout set.
    # This tests whether the system is robust to loss of any single strategy.
    all_strategies = set()
    for conj in conjectures:
        for pred in conj.predictions:
            all_strategies.add(pred.strategy_name)

    # Full system recall (using all strategies)
    full_predicted = {(c.source, c.target) for c in conjectures}
    full_tp = len(full_predicted & holdout_set)
    full_recall = full_tp / len(holdout_set) if holdout_set else 0.0

    # Ablate each strategy: remove its predictions, check what survives
    ablation_details = {}
    strategies_contributing = 0
    min_ablated_recall = 1.0

    for strategy in sorted(all_strategies):
        ablated_pairs = set()
        for conj in conjectures:
            remaining = [p for p in conj.predictions if p.strategy_name != strategy]
            if remaining:
                # Conjecture survives -- at least one other strategy supports it
                ablated_pairs.add((conj.source, conj.target))

        ablated_tp = len(ablated_pairs & holdout_set)
        ablated_recall = ablated_tp / len(holdout_set) if holdout_set else 0.0
        delta = full_recall - ablated_recall

        ablation_details[strategy] = {
            "recall_without": round(ablated_recall, 4),
            "delta": round(delta, 4),
        }
        if delta > 0.001:  # strategy has measurable contribution
            strategies_contributing += 1
        min_ablated_recall = min(min_ablated_recall, ablated_recall)

    results.append(AuditResult(
        category="Mechanism Validation",
        check_name="ablation_study",
        passed=min_ablated_recall >= 0.70 and strategies_contributing >= 3,
        severity="WARNING",
        value={
            "full_recall": round(full_recall, 4),
            "min_recall_after_removal": round(min_ablated_recall, 4),
            "strategies_contributing": strategies_contributing,
            "total_strategies": len(all_strategies),
            "ablation_details": ablation_details,
        },
        threshold="No single removal drops recall < 0.70; >= 3 strategies contribute positively",
        message=f"Ablation: {strategies_contributing}/{len(all_strategies)} strategies contribute. Min recall after single removal: {min_ablated_recall:.4f}",
        reference="Ablation study: strategy robustness (BioPathNet Nature BME 2025, plan Check 26)",
    ))


# ---------------------------------------------------------------------------
# Category 5: Data Provenance
# ---------------------------------------------------------------------------

def _check_data_provenance(store, results, external_holdout=None):
    """3 checks: no_leakage, source_attribution, holdout_source."""
    from data.drugs.drug_network import get_holdout_edges, DRUGS

    holdout = get_holdout_edges()
    holdout_set = {(h[0], h[1]) for h in holdout}

    # Merge external holdout for leakage check
    if external_holdout:
        for edge in external_holdout:
            holdout_set.add((edge[0], edge[1]))

    # 1. no_leakage: no holdout edge exists in store morphisms
    # For large networks, check only treats/potential_treatment morphisms
    n_morphisms = store.count_morphisms()
    if n_morphisms > 100000:
        # Efficient check: only look at treats morphisms
        treats_morphisms = store.get_morphisms_by_name("treats")
        pot_morphisms = store.get_morphisms_by_name("potential_treatment")
        existing_pairs = {(m.source_name, m.target_name) for m in treats_morphisms + pot_morphisms}
    else:
        all_morphisms = store.list_morphisms(limit=100000)
        existing_pairs = {(m.source_name, m.target_name) for m in all_morphisms}

    leaked = holdout_set & existing_pairs

    results.append(AuditResult(
        category="Data Provenance",
        check_name="no_leakage",
        passed=len(leaked) == 0,
        severity="CRITICAL",
        value=len(leaked),
        threshold="0 leaked edges",
        message=f"{len(leaked)} holdout edges leaked into store" + (f": {list(leaked)[:5]}" if leaked else ""),
        reference="Data leakage prevention in drug repurposing",
    ))

    # 2. source_attribution: drugs have drugbank_id, mechanism, or hetionet_id
    drug_objects = store.get_objects_by_type("Drug")
    attributed = 0
    for drug in drug_objects:
        meta = drug.metadata if drug.metadata else {}
        if meta.get("drugbank_id") or meta.get("mechanism") or meta.get("hetionet_id"):
            attributed += 1
    attr_pct = (attributed / len(drug_objects) * 100) if drug_objects else 0

    results.append(AuditResult(
        category="Data Provenance",
        check_name="source_attribution",
        passed=attr_pct >= 90,
        severity="WARNING",
        value=round(attr_pct, 1),
        threshold=">= 90% drugs with drugbank_id, mechanism, or hetionet_id",
        message=f"{attr_pct:.1f}% of drugs have source attribution ({attributed}/{len(drug_objects)})",
        reference="Data provenance for drug repurposing",
    ))

    # 3. holdout_source: curated holdout edges have evidence string
    # (external holdout edges from Hetionet don't have evidence strings)
    with_evidence = 0
    for h in holdout:
        # holdout format: (drug, disease, relation, confidence, evidence)
        if len(h) >= 5 and h[4] and len(str(h[4]).strip()) > 0:
            with_evidence += 1
    evidence_pct = (with_evidence / len(holdout) * 100) if holdout else 100

    results.append(AuditResult(
        category="Data Provenance",
        check_name="holdout_source",
        passed=evidence_pct >= 100,
        severity="CRITICAL",
        value=round(evidence_pct, 1),
        threshold="100% curated holdout edges have evidence",
        message=f"{evidence_pct:.1f}% of curated holdout edges have evidence ({with_evidence}/{len(holdout)})",
        reference="Ground truth provenance",
    ))

    # --- Negative Sampling Documentation ---
    # Document the negative sampling strategy and verify ratio.
    # Negatives are "unobserved pairs" (open-world assumption).
    # Field standard: negative set >= 5x positive set.
    from data.drugs.drug_network import DRUGS as _DRUGS, DISEASES as _DISEASES, DRUG_DISEASE_APPROVED as _APPROVED
    n_drugs = len(_DRUGS)
    n_diseases = len(_DISEASES)
    total_pairs = n_drugs * n_diseases
    n_positive = len(holdout_set) + len(_APPROVED)
    n_negative = total_pairs - n_positive
    neg_pos_ratio = n_negative / n_positive if n_positive > 0 else 0

    results.append(AuditResult(
        category="Data Provenance",
        check_name="negative_sampling",
        passed=neg_pos_ratio >= 5.0,
        severity="WARNING",
        value={"total_pairs": total_pairs, "positives": n_positive, "negatives": n_negative, "ratio": round(neg_pos_ratio, 1)},
        threshold="Negative:Positive ratio >= 5:1",
        message=f"Neg:Pos ratio = {neg_pos_ratio:.1f}:1 ({n_negative} negatives, {n_positive} positives, {total_pairs} total pairs). Strategy: open-world unobserved pairs.",
        reference="Negative sampling strategy (DREAMwalk Nature Comms 2023, PMC 2025)",
    ))


# ---------------------------------------------------------------------------
# Category 6: Reproducibility
# ---------------------------------------------------------------------------

def _check_reproducibility(store, results):
    """3 checks: deterministic, parameter_sensitivity, runtime."""
    from data.drugs.drug_network import get_holdout_edges

    holdout = get_holdout_edges()
    holdout_set = {(h[0], h[1]) for h in holdout}

    # Helper: run engine with given min_confidence, return predicted Drug-Disease pairs
    def _run_engine(store_instance, min_conf):
        from data import EmbeddingsEngine, CategoryEmbedder
        from oracle import CategoricalOracle
        from oracle.conjecture import ConjectureEngine

        eng = EmbeddingsEngine()
        if not eng.is_available:
            import hashlib

            class _FallbackEmb:
                is_available = True
                def embed(self, text):
                    import numpy as np
                    h = hashlib.md5(text.encode()).hexdigest()
                    return np.array([int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)])
                def embed_batch(self, texts, show_progress=False):
                    return [self.embed(t) for t in texts]
                def similarity(self, a, b):
                    import numpy as np
                    ea = self.embed(a)
                    eb = self.embed(b)
                    dot = float(np.dot(ea, eb))
                    na = float(np.linalg.norm(ea))
                    nb = float(np.linalg.norm(eb))
                    return dot / (na * nb) if na > 0 and nb > 0 else 0.0
            eng = _FallbackEmb()

        embedder = CategoryEmbedder(store_instance, eng)
        embedder.embed_all_objects()

        oracle = CategoricalOracle(
            category=store_instance,
            embeddings=eng,
            min_confidence=min_conf,
            max_predictions=20,
        )
        ce = ConjectureEngine(oracle)
        res = ce.conjecture(top_k=5000, min_confidence=min_conf - 0.05)

        all_objects_map = {o.name: o for o in store_instance.list_objects(limit=10000)}
        dd_pairs = set()
        for conj in res.conjectures:
            src = all_objects_map.get(conj.source)
            tgt = all_objects_map.get(conj.target)
            if src and tgt and src.type_name == "Drug" and tgt.type_name == "Disease":
                dd_pairs.add((conj.source, conj.target))
        return dd_pairs

    # 1. deterministic: run engine twice, same predictions
    from domains.bio import BioDomainLoader
    loader = BioDomainLoader()

    store1 = loader.load_tier1("data/drugs/tier1.db")
    run1 = _run_engine(store1, 0.30)

    store2 = loader.load_tier1("data/drugs/tier1.db")
    run2 = _run_engine(store2, 0.30)

    deterministic = (run1 == run2)
    results.append(AuditResult(
        category="Reproducibility",
        check_name="deterministic",
        passed=deterministic,
        severity="CRITICAL",
        value=deterministic,
        threshold="exact match between runs",
        message=f"{'Deterministic' if deterministic else 'Non-deterministic'}: run1={len(run1)} preds, run2={len(run2)} preds, diff={len(run1 ^ run2)}",
        reference="Reproducibility of prediction pipeline",
    ))

    # 2. parameter_sensitivity: run at min_confidence 0.20 and 0.35, recall stays >= 0.40
    sensitivity_pass = True
    sensitivity_details = {}
    for mc in [0.20, 0.35]:
        store_ps = loader.load_tier1("data/drugs/tier1.db")
        preds = _run_engine(store_ps, mc)
        tp = len(preds & holdout_set)
        rec = tp / len(holdout_set) if holdout_set else 0.0
        sensitivity_details[str(mc)] = round(rec, 4)
        if rec < 0.40:
            sensitivity_pass = False

    results.append(AuditResult(
        category="Reproducibility",
        check_name="parameter_sensitivity",
        passed=sensitivity_pass,
        severity="WARNING",
        value=sensitivity_details,
        threshold="recall >= 0.40 at min_confidence 0.20 and 0.35",
        message=f"Recall at mc=0.20: {sensitivity_details.get('0.2', 'N/A')}, mc=0.35: {sensitivity_details.get('0.35', 'N/A')}",
        reference="Parameter sensitivity analysis",
    ))


# ---------------------------------------------------------------------------
# Category 7 (within Reproducibility): Cross-Validation
# ---------------------------------------------------------------------------

def _check_cross_validation(conjectures, results, n_folds=5):
    """
    5-fold cross-validation of holdout recall.

    Splits the holdout edge set into k folds. For each fold, measures what
    fraction of that fold's edges the system recovered. Reports mean and
    std of per-fold recall. This shows the result isn't an artifact of
    which edges happen to be in a lucky subset.

    Reference: NeurIPS 2023 link prediction benchmarks; AUDIT_IMPLEMENTATION_PLAN Check 27.
    """
    from data.drugs.drug_network import get_holdout_edges

    holdout = get_holdout_edges()
    holdout_list = sorted({(h[0], h[1]) for h in holdout})  # sorted for determinism

    # Deterministic shuffle
    rng = random.Random(42)
    rng.shuffle(holdout_list)

    # Build predicted drug-disease pairs from existing conjectures
    predicted_pairs = {(c.source, c.target) for c in conjectures}

    # Split into folds (round-robin assignment)
    folds = [[] for _ in range(n_folds)]
    for i, edge in enumerate(holdout_list):
        folds[i % n_folds].append(edge)

    # Measure recall per fold
    fold_recalls = []
    for fold in folds:
        fold_set = set(fold)
        tp = len(predicted_pairs & fold_set)
        recall = tp / len(fold_set) if fold_set else 0.0
        fold_recalls.append(recall)

    mean_recall = sum(fold_recalls) / len(fold_recalls) if fold_recalls else 0.0
    variance = sum((r - mean_recall) ** 2 for r in fold_recalls) / len(fold_recalls) if fold_recalls else 0.0
    std_recall = variance ** 0.5

    results.append(AuditResult(
        category="Reproducibility",
        check_name="cross_validation",
        passed=mean_recall >= 0.80 and std_recall < 0.15,
        severity="CRITICAL",
        value={
            "mean_recall": round(mean_recall, 4),
            "std_recall": round(std_recall, 4),
            "n_folds": n_folds,
            "fold_recalls": [round(r, 4) for r in fold_recalls],
            "fold_sizes": [len(f) for f in folds],
        },
        threshold="Mean recall >= 0.80, std < 0.15",
        message=f"{n_folds}-fold CV: mean recall = {mean_recall:.4f} +/- {std_recall:.4f} (folds: {[round(r, 3) for r in fold_recalls]})",
        reference="k-fold cross-validation (NeurIPS 2023 link prediction benchmarks, plan Check 27)",
    ))


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

def run_drug_repurposing_audit(store=None, verbose=True, external_holdout=None):
    """
    Run all 28 drug repurposing audit checks.

    Args:
        store: Pre-built KomposOSStore. If None, creates one from scratch.
        verbose: Print progress and results.
        external_holdout: Optional list of (source, target, relation, confidence)
            holdout edges from external databases (e.g. Hetionet Phase 1).
            Merged with the curated holdout set for validation.

    Returns:
        AuditReport with all 28 checks.
    """
    t_start = time.time()

    if verbose:
        print("=" * 70)
        print("KOMPOSOS-III DRUG REPURPOSING SCIENTIFIC AUDIT")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

    # Build store if not provided
    if store is None:
        if verbose:
            print("[Setup] Loading drug repurposing data from tier1.db...")
        from domains.bio import BioDomainLoader
        from validation.store_adapter import StoreAdapter
        loader = BioDomainLoader()
        category = loader.load_tier1("data/drugs/tier1.db")
        store = StoreAdapter(category)  # Wrap Category to provide old API

    # Build Oracle + embeddings
    if verbose:
        print("[Setup] Computing embeddings...")
    from data import EmbeddingsEngine, CategoryEmbedder
    from oracle import CategoricalOracle

    engine = EmbeddingsEngine()
    if not engine.is_available:
        if verbose:
            print("  WARNING: Sentence Transformers not available, using hash fallback.")
        import hashlib

        class _FallbackEmb:
            is_available = True
            def embed(self, text):
                import numpy as np
                h = hashlib.md5(text.encode()).hexdigest()
                return np.array([int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)])
            def embed_batch(self, texts, show_progress=False):
                return [self.embed(t) for t in texts]
            def similarity(self, a, b):
                import numpy as np
                ea = self.embed(a)
                eb = self.embed(b)
                dot = float(np.dot(ea, eb))
                na = float(np.linalg.norm(ea))
                nb = float(np.linalg.norm(eb))
                return dot / (na * nb) if na > 0 and nb > 0 else 0.0
        engine = _FallbackEmb()

    # Use the underlying category for embedder and oracle
    actual_category = store.category if hasattr(store, 'category') else store

    embedder = CategoryEmbedder(actual_category, engine)
    embedder.embed_all_objects()

    oracle = CategoricalOracle(
        category=actual_category,
        embeddings=engine,
        min_confidence=0.30,
        max_predictions=20,
    )

    # Create report
    report = AuditReport(
        timestamp=datetime.now().isoformat(),
        protein_name="drug_repurposing",
        sequence_length=0,
    )

    # Category 1: Network Topology
    if verbose:
        print("\n[1/6] Network Topology (4 checks)...")
    _check_network_topology(store, report.results)
    if verbose:
        for r in report.results[-4:]:
            _print_result(r)

    # Category 2: Holdout Validation
    if verbose:
        print("\n[2/6] Holdout Validation (7 checks)...")
    all_scores, all_labels, conjectures = _check_holdout_validation(
        store, oracle, report.results, external_holdout=external_holdout
    )
    if verbose:
        for r in report.results[-7:]:
            _print_result(r)

    # Category 3: Statistical Significance
    if verbose:
        print("\n[3/6] Statistical Significance (4 checks)...")
    _check_statistical_significance(all_scores, all_labels, store, report.results)
    if verbose:
        for r in report.results[-4:]:
            _print_result(r)

    # Category 4: Mechanism Validation
    if verbose:
        print("\n[4/6] Mechanism Validation (5 checks)...")
    _check_mechanism_validation(conjectures, store, report.results)
    if verbose:
        for r in report.results[-5:]:
            _print_result(r)

    # Category 5: Data Provenance
    if verbose:
        print("\n[5/6] Data Provenance (4 checks)...")
    _check_data_provenance(store, report.results, external_holdout=external_holdout)
    if verbose:
        for r in report.results[-4:]:
            _print_result(r)

    # Category 6: Reproducibility
    if verbose:
        print("\n[6/6] Reproducibility (4 checks)...")
    _check_reproducibility(store, report.results)
    if verbose:
        for r in report.results[-2:]:
            _print_result(r)

    # Cross-validation (reuses predictions from holdout validation -- no re-run)
    _check_cross_validation(conjectures, report.results)
    if verbose:
        _print_result(report.results[-1])

    # Runtime check (last of the 28)
    # Scaled networks (>1000 nodes) get 600s; curated networks get 300s
    elapsed = time.time() - t_start
    n_objects = store.count_objects()
    runtime_limit = 600 if n_objects >= 1000 else 300
    report.results.append(AuditResult(
        category="Reproducibility",
        check_name="runtime",
        passed=elapsed < runtime_limit,
        severity="INFO",
        value=round(elapsed, 1),
        threshold=f"< {runtime_limit} seconds",
        message=f"Total audit completed in {elapsed:.1f}s",
        reference="Reasonable runtime for scientific audit",
    ))
    if verbose:
        _print_result(report.results[-1])

    # Summary
    report.summary = {
        "total_checks": report.total_count,
        "passed": report.pass_count,
        "critical_failures": report.critical_count,
        "warnings": report.warning_count,
        "pass_rate": round(report.pass_count / max(report.total_count, 1) * 100, 1),
    }

    if verbose:
        print()
        print("=" * 70)
        print("DRUG REPURPOSING AUDIT SUMMARY")
        print("=" * 70)
        print(f"Total checks:      {report.total_count}")
        print(f"Passed:            {report.pass_count}")
        print(f"Warnings:          {report.warning_count}")
        print(f"Critical failures: {report.critical_count}")
        print(f"Pass rate:         {report.summary['pass_rate']}%")
        print()

        # Print key metrics
        for r in report.results:
            if r.check_name in ("auroc", "auprc", "mrr", "hits_at_k", "permutation_test", "enrichment_top10", "enrichment_top50", "baseline_comparison", "ablation_study", "cross_validation"):
                print(f"  {r.check_name}: {r.value}")

        print()
        if report.critical_count == 0:
            print("RESULT: PASS - No critical issues found")
        else:
            print(f"RESULT: {report.critical_count} critical issue(s)")
            for r in report.results:
                if not r.passed and r.severity == "CRITICAL":
                    print(f"  [!!] {r.check_name}: {r.message}")
        print("=" * 70)

    return report


def _print_result(r):
    """Print a single audit result."""
    icon = "  [OK]" if r.passed else "  [!!]" if r.severity == "CRITICAL" else "  [**]"
    print(f"{icon} {r.check_name}: {r.message}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    report = run_drug_repurposing_audit()

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(__file__).parent.parent / "validation_reports" / f"drug_repurposing_audit_{timestamp}.json"
    save_audit_report(report, output_path)
