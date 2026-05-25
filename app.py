#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
KOMPOSOS-IV-PHARM Streamlit Web Frontend.

Wraps the triage CLI into an interactive web app for drug repurposing demos.

Usage:
    pip install streamlit
    streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
    score_pair_detailed,
)
from validation.trace_prediction import _build_provenance_index, trace_pair
from validation.triage import (
    _label_for_pair,
    _provenance_fraction,
    format_markdown,
    self_check,
    triage_disease,
    triage_drug,
)


# ── Cache heavy loads ────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading knowledge graph...")
def load_graph():
    category, _ = load_full_typed_view(DB_PATH)
    drugs, diseases, positives = drug_disease_pairs(category)
    strategies = make_strategies(category)
    provenance_index = _build_provenance_index(DB_PATH)
    n_objects = len(category.objects())
    n_morphisms = len(category.morphisms())
    check_recovered, check_total = self_check(
        category, drugs, diseases, positives
    )
    # Edge quality tiers by confidence
    high_conf = 0
    med_conf = 0
    low_conf = 0
    for mor in category.morphisms():
        c = mor.confidence if mor.confidence else 0.0
        if c >= 0.70:
            high_conf += 1
        elif c >= 0.40:
            med_conf += 1
        else:
            low_conf += 1
    return {
        "category": category,
        "drugs": drugs,
        "diseases": diseases,
        "positives": positives,
        "strategies": strategies,
        "provenance_index": provenance_index,
        "n_objects": n_objects,
        "n_morphisms": n_morphisms,
        "n_positives": len(positives),
        "check_recovered": check_recovered,
        "check_total": check_total,
        "high_conf": high_conf,
        "med_conf": med_conf,
        "low_conf": low_conf,
    }


# ── Page config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="KOMPOSOS-IV-PHARM",
    page_icon="\u2695",
    layout="wide",
)


# ── Sidebar ──────────────────────────────────────────────────────────

st.sidebar.title("KOMPOSOS-IV-PHARM")
st.sidebar.caption("Categorical Drug Repurposing")

mode = st.sidebar.radio(
    "Mode",
    ["Disease-first", "Drug-first", "Pair detail", "How Scoring Works", "About"],
)

g = load_graph()

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Graph**: {g['n_objects']} objects, {g['n_morphisms']} morphisms\n\n"
    f"**Positives**: {g['n_positives']} FDA-approved\n\n"
    f"**Self-check**: {g['check_recovered']}/{g['check_total']} recoverable"
)
st.sidebar.markdown(
    f"**Edge quality**: High: {g['high_conf']} | "
    f"Med: {g['med_conf']} | Low: {g['low_conf']}"
)
st.sidebar.caption("High >= 0.70 | Med 0.40-0.69 | Low < 0.40")


# ── Helpers ──────────────────────────────────────────────────────────

def _top_trace(chains: list) -> str:
    """Extract the top compositional trace as a short string."""
    if not chains:
        return "-"
    edges = chains[0].get("edges", [])
    if not edges:
        return "-"
    parts = [edges[0]["source"]]
    for edge in edges:
        parts.append(edge["target"])
    return " \u2192 ".join(parts)


def render_results_table(results):
    """Show ranked results as a streamlit table."""
    rows = []
    for r in results:
        rows.append({
            "Rank": r["rank"],
            "Drug": r["drug"],
            "Disease": r["disease"],
            "Score": round(r["score"], 3),
            "Label": r["label"],
            "Top Trace": _top_trace(r.get("chains", [])),
            "Paths": r["n_chains"],
            "Cited": f"{r['cited_edges']}/{r['total_edges']}"
            if r["total_edges"] > 0 else "-",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


# User-friendly strategy labels for pharma audience
STRATEGY_DISPLAY = {
    "kan_extension": {
        "label": "Drug Analogy",
        "hint": "Similar drugs treat similar diseases",
    },
    "type_heuristic": {
        "label": "Type Match",
        "hint": "Drug-protein-disease type compatibility",
    },
    "structural_hole": {
        "label": "Network Closure",
        "hint": "Fills missing link in drug-target-disease triangle",
    },
    "composition": {
        "label": "Mechanistic Path",
        "hint": "Drug targets a protein involved in this disease",
    },
    "yoneda_pattern": {
        "label": "Interaction Profile",
        "hint": "Drug has similar target profile to known treatments",
    },
    "fibration_lift": {
        "label": "Structural Inference",
        "hint": "Prediction lifted from related biological context",
    },
    "topos_logic": {
        "label": "Evidence Integration",
        "hint": "Partial evidence combined from multiple sources",
    },
    "binding_evidence": {
        "label": "Binding Evidence",
        "hint": "Experimental IC50 and molecular compatibility data",
    },
}


def _provenance_source_type(prov: str) -> str:
    """Derive a short source label from a provenance string."""
    if not prov or prov == "unknown":
        return "uncited"
    if prov == "PubMed co-mention (unverified)":
        return "co-mention (unverified)"
    p = prov.upper()
    if "CHEMBL" in p:
        return "ChEMBL"
    if "FDA" in p:
        return "FDA"
    if "KEGG" in p:
        return "KEGG"
    if "ABPP" in p:
        return "ABPP"
    if "ESM2" in p:
        return "ESM2"
    if "STRING" in p:
        return "STRING"
    if "DEPMAP" in p or "GTEX" in p:
        return "DepMap/GTEx"
    if "PMID:" in p:
        return "PubMed"
    if "ESTABLISHED" in p or "MECHANISM" in p:
        return "Curated"
    if "PPI" in p:
        return "PPI"
    return "Other"


def _confidence_color(conf: float) -> str:
    """Return a Streamlit color name for a confidence value."""
    if conf >= 0.70:
        return "green"
    if conf >= 0.40:
        return "orange"
    return "red"


def _strategy_label(name: str) -> str:
    """Get user-friendly display label for a strategy."""
    info = STRATEGY_DISPLAY.get(name)
    return info["label"] if info else name


def _strategy_hint(name: str) -> str:
    """Get short explanation for a strategy."""
    info = STRATEGY_DISPLAY.get(name)
    return info["hint"] if info else ""


def render_detail(entry):
    """Show detailed evidence for one candidate."""
    label_color = "green" if entry["label"] == "APPROVED" else "orange"
    st.markdown(
        f"### {entry['drug']} \u2192 {entry['disease']}  "
        f"&nbsp; :{label_color}[{entry['label']}]"
    )

    # ── Score breakdown ──────────────────────────────────────────────
    breakdown = entry.get("breakdown")
    if breakdown:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final Score", f"{entry['score']:.3f}")
        c2.metric("Base (mean votes)", f"{breakdown['base']:.3f}")
        c3.metric("Path Bonus", f"{breakdown['path_bonus']:.3f}")
        if breakdown["mechanistic_discount"]:
            c4.metric("Mech. Discount", "0.80x applied")
        else:
            c4.metric("Mech. Discount", "none")
        if breakdown["composition_count"] > 0:
            st.caption(
                f"Composition paths: {breakdown['composition_count']} | "
                f"Sum of path confidences: {breakdown['composition_weight']:.2f} | "
                f"Path bonus = min(0.25, 0.04 x {breakdown['composition_weight']:.2f}) = "
                f"{breakdown['path_bonus']:.3f}"
            )
    else:
        st.metric("Score", f"{entry['score']:.3f}")

    # ── Strategy votes ───────────────────────────────────────────────
    if entry["votes"]:
        st.markdown("**Scoring Evidence**")
        for name, conf in entry["votes"]:
            label = _strategy_label(name)
            hint = _strategy_hint(name)
            col1, col2 = st.columns([2, 1])
            col1.write(f"**{label}**")
            col2.metric("Score", f"{conf:.2f}")
            if hint:
                st.caption(hint)

    # ── Binding evidence ─────────────────────────────────────────────
    binding_vote = [c for n, c in entry["votes"] if n == "binding_evidence"]
    if binding_vote:
        st.markdown("**Binding Evidence**")
        try:
            from abpp_bridge import ABPPBridge
            from data.drugs.drug_properties import get_drug_likeness, is_antibody
            abpp = ABPPBridge()
            drug = entry["drug"]
            ic50_rows = []
            seen = set()
            for chain in entry.get("chains", []):
                for edge in chain.get("edges", []):
                    protein = edge.get("target", "")
                    if protein in seen:
                        continue
                    seen.add(protein)
                    result = abpp.check_abpp(drug, protein)
                    if result and result.validated and result.ic50_um is not None:
                        ic50_rows.append({
                            "Target": protein,
                            "IC50 (\u00b5M)": result.ic50_um,
                            "Inhibition": f"{result.percent_inhibition:.0f}%",
                            "Source": result.publication,
                        })
            if ic50_rows:
                st.dataframe(ic50_rows, use_container_width=True, hide_index=True)
            likeness = get_drug_likeness(drug)
            if likeness is not None:
                st.metric("Drug-Likeness (Lipinski)", f"{likeness:.2f}")
            if is_antibody(drug):
                st.info(f"{drug} is a monoclonal antibody (not a small molecule)")
        except Exception:
            pass

    # ── Path quality classification ──────────────────────────────────
    if entry["chains"]:
        high_chains = []
        mid_chains = []
        spec_chains = []
        for chain in entry["chains"]:
            min_conf = min(e["confidence"] for e in chain["edges"])
            if min_conf >= 0.70:
                high_chains.append(chain)
            elif min_conf >= 0.40:
                mid_chains.append(chain)
            else:
                spec_chains.append(chain)
        parts = []
        if high_chains:
            parts.append(f"{len(high_chains)} high-confidence")
        if mid_chains:
            parts.append(f"{len(mid_chains)} medium")
        if spec_chains:
            parts.append(f"{len(spec_chains)} speculative")
        st.markdown(
            f"**Compositional Trace** (Drug \u2192 Protein \u2192 Disease) "
            f"-- {len(entry['chains'])} chains ({', '.join(parts)})"
        )

        for i, chain in enumerate(entry["chains"], 1):
            parts_p = [chain["edges"][0]["source"]]
            for edge in chain["edges"]:
                parts_p.append(f"\u2192 {edge['target']}")
            path_str = " ".join(parts_p)

            with st.expander(f"Path {i}: {path_str}"):
                for edge in chain["edges"]:
                    conf = edge["confidence"]
                    prov = edge.get("provenance", "unknown")
                    src_type = _provenance_source_type(prov)
                    color = _confidence_color(conf)
                    if prov == "PubMed co-mention (unverified)":
                        prov_display = "co-mention (unverified)"
                    elif prov == "unknown":
                        prov_display = "uncited"
                    elif prov.startswith("PMID:"):
                        pmid_id = prov.split(",")[0].replace("PMID:", "").strip()
                        prov_display = f"[{prov}](https://pubmed.ncbi.nlm.nih.gov/{pmid_id})"
                    else:
                        prov_display = prov
                    st.markdown(
                        f"- **{edge['source']}** -{edge['relation']}-> "
                        f"**{edge['target']}** "
                        f"(:{color}[conf: {conf:.2f}], {src_type} | {prov_display})"
                    )

    cited = entry["cited_edges"]
    total = entry["total_edges"]
    if total > 0:
        st.progress(cited / total, text=f"Provenance: {cited}/{total} edges cited")


def generate_report(results: list[dict], query_label: str) -> str:
    """Generate downloadable markdown report from current results."""
    return format_markdown(
        results, query_label,
        g["n_objects"], g["n_morphisms"], g["n_positives"],
        g["check_recovered"], g["check_total"],
    )


# ── Disease-first ────────────────────────────────────────────────────

if mode == "Disease-first":
    st.title("Rank drugs for a disease")
    disease = st.selectbox("Select disease", g["diseases"])
    top_n = st.slider("Top N", 5, len(g["drugs"]), 20)

    if st.button("Run triage", type="primary"):
        with st.spinner("Scoring all drugs..."):
            results = triage_disease(
                g["category"], g["strategies"], disease, g["positives"],
                g["provenance_index"], top_n=top_n,
            )
        render_results_table(results)

        report_md = generate_report(results, f"Disease: {disease}")
        st.download_button(
            "Download Report",
            data=report_md,
            file_name=f"triage_{disease}.md",
            mime="text/markdown",
        )

        st.markdown("---")
        st.subheader("Candidate Details")
        not_approved = [r for r in results if r["label"] == "NOT_APPROVED"]
        for entry in not_approved[:5]:
            render_detail(entry)
            st.markdown("---")


# ── Drug-first ───────────────────────────────────────────────────────

elif mode == "Drug-first":
    st.title("Rank diseases for a drug")
    drug = st.selectbox("Select drug", g["drugs"])

    if st.button("Run triage", type="primary"):
        with st.spinner("Scoring all diseases..."):
            results = triage_drug(
                g["category"], g["strategies"], drug, g["positives"],
                g["provenance_index"], top_n=len(g["diseases"]), show_all=True,
            )
        render_results_table(results)

        report_md = generate_report(results, f"Drug: {drug}")
        st.download_button(
            "Download Report",
            data=report_md,
            file_name=f"triage_{drug}.md",
            mime="text/markdown",
        )

        st.markdown("---")
        st.subheader("Top Predictions")
        for entry in results[:5]:
            render_detail(entry)
            st.markdown("---")


# ── Pair detail ──────────────────────────────────────────────────────

elif mode == "Pair detail":
    st.title("Inspect a specific drug-disease pair")
    col1, col2 = st.columns(2)
    drug = col1.selectbox("Drug", g["drugs"])
    disease = col2.selectbox("Disease", g["diseases"])

    if st.button("Analyze pair", type="primary"):
        with st.spinner("Analyzing..."):
            detailed = score_pair_detailed(g["strategies"], drug, disease)
            trace = trace_pair(
                g["category"], drug, disease,
                g["strategies"], g["provenance_index"],
            )
            label = _label_for_pair((drug, disease), g["positives"])
            cited, total_edges = _provenance_fraction(trace["chains"])
            entry = {
                "rank": 1,
                "drug": drug,
                "disease": disease,
                "score": detailed["score"],
                "label": label,
                "votes": detailed["votes"],
                "n_chains": trace["n_chains"],
                "chains": trace["chains"],
                "cited_edges": cited,
                "total_edges": total_edges,
                "breakdown": detailed,
            }
        render_detail(entry)

        report_md = generate_report([entry], f"Pair: {drug} -> {disease}")
        st.download_button(
            "Download Report",
            data=report_md,
            file_name=f"report_{drug}_{disease}.md",
            mime="text/markdown",
        )


# ── How Scoring Works ────────────────────────────────────────────────

elif mode == "How Scoring Works":
    st.title("How Scoring Works")
    st.caption(
        "This page explains every number you see in triage reports. "
        "All formulas match the code in validation/repurposing_benchmark.py "
        "and oracle/binding_strategy.py."
    )

    # ── Section A: Edge Confidence ───────────────────────────────────
    with st.expander("Edge Confidence: Where the Numbers Come From", expanded=True):
        st.markdown("""
Each edge (morphism) in the knowledge graph has a **confidence** value between
0 and 1. This is NOT a probability -- it encodes how much evidence supports
the relationship.

| Confidence | Source Type | Meaning | Researcher Action |
|-----------|------------|---------|-------------------|
| 0.90 - 1.00 | FDA labels, ChEMBL measured | Drug-disease indication confirmed by regulatory body or direct assay | **Trust** -- follow the cited PMID |
| 0.70 - 0.89 | ChEMBL binding, KEGG pathways, curated interactions | Strong database evidence for this relationship | **Trust** -- standard literature-backed edge |
| 0.50 - 0.69 | ESM2 protein similarity, STRING PPI, established mechanisms | Computational or curated evidence, not direct measurement | **Investigate** -- check the cited paper |
| 0.40 - 0.54 | PubMed co-mention (PARTIAL/AGREE after categorical verification) | Co-mentioned in literature AND supported by at least one categorical layer | **Consider** -- has some mechanistic support |
| 0.35 | PubMed co-mention (ORPHAN after categorical verification) | Co-mentioned in literature but isolated -- no mechanistic support found | **Verify independently** -- may be text-mining noise |
| 0.20 | PubMed co-mention (REJECT after categorical verification) | Co-mentioned in literature but failed categorical verification | **Hypothesis only** -- treat as noise unless you have independent evidence |
""")

    # ── Section B: 5-Layer Categorical Verification ──────────────────
    with st.expander("The 5-Layer Categorical Verification"):
        st.markdown("""
When PubMed co-mention edges are added to the graph, each one passes through a
**5-layer categorical verification** pipeline. Each layer asks a different
mathematical question about whether the edge is consistent with the rest of the
graph.

| Layer | Name | Weight | What It Checks |
|-------|------|--------|----------------|
| 1 | Drug Path Witness | 0.30 | Does any known drug connect to both this protein AND a disease through the graph? |
| 2 | Kan Extension Agreement | 0.20 | Does the categorical Kan extension (colimit of drug targets) predict this protein for this disease? |
| 3 | Mechanistic Reachability | 0.20 | Can we reach a disease-connected node from this protein via known mechanistic edges (activates, inhibits) within 3 hops? |
| 4 | Protein Specificity | 0.15 | Is this protein specific to a few diseases (good) or linked to everything (likely text-mining artifact)? |
| 5 | Gray Interchange Coherence | 0.15 | Do other proteins targeting the same disease share drug-mediated or mechanistic pathways with this protein? |

**Combined score** = weighted sum of all 5 layers.

**Delta classification** from the combined score:
- **AGREE** (>= 0.6): Edge is well-supported. Confidence adjusted to 0.40-0.54.
- **PARTIAL** (>= 0.3 with mechanistic support): Some support. Confidence ~0.40.
- **HOLLOW** (>= 0.3 without mechanistic support): Structurally present but ungrounded.
- **ORPHAN** (>= 0.1): Isolated, minimal support. Confidence set to 0.35.
- **REJECT** (< 0.1): No support from any layer. Confidence set to 0.20.

**Confidence adjustment formula:**
""")
        st.code(
            "adjusted = 0.65 * combined + 0.35 * original * (0.5 + 0.5 * combined)",
            language="python",
        )
        st.caption(
            "This blends the categorical verification score with the original "
            "confidence, so a high-combined edge gets boosted and a low-combined "
            "edge gets penalized."
        )

    # ── Section C: Final Score Formula ───────────────────────────────
    with st.expander("The Final Score Formula"):
        st.markdown("""
When you run a triage query, each drug-disease pair is scored in 3 steps:

**Step 1: Base score** = mean of all strategy votes

Each of the 8 strategies independently scores the pair. The base score is
their simple average.

**Step 2: Path bonus** from compositional (mechanistic) paths

For every Drug -> Protein -> Disease path found, the composition strategy
reports the path confidence (minimum edge confidence along the path). The
path bonus rewards having many high-quality mechanistic paths:
""")
        st.code(
            "composition_weight = sum(path_confidence for each path)\n"
            "path_bonus = min(0.25, 0.04 * composition_weight)",
            language="python",
        )
        st.markdown("""
**Why confidence-weighted?** A single FDA-confirmed path (confidence 0.90)
contributes 0.036 to the bonus. A PubMed REJECT path (confidence 0.20)
contributes only 0.008 -- roughly 4.5x less. This prevents score inflation
from many weak co-mention paths.

The **cap at 0.25** prevents score saturation: even with many paths, the bonus
cannot dominate the base score.

**Step 3: Mechanistic discount**

If the pair has **zero** composition paths (no Drug -> Protein -> Disease chain),
the score is penalized:
""")
        st.code(
            "if no_composition_paths:\n"
            "    score *= 0.80  # 20% penalty",
            language="python",
        )
        st.markdown("""
This ensures analogy-only predictions (from Kan extensions, binding evidence)
rank below mechanistically-supported candidates at similar base scores.

**Final:**
""")
        st.code(
            "final = min(1.0, (base + path_bonus) * discount)",
            language="python",
        )

    # ── Section D: IC50 to Confidence ────────────────────────────────
    with st.expander("IC50 to Confidence Mapping"):
        st.markdown("""
When ABPP experimental data provides an IC50 value (half-maximal inhibitory
concentration), it is converted to a 0-1 score:
""")
        st.code(
            "score = 1.0 / (1.0 + IC50_um / 0.5)\n"
            "score = min(score, 0.98)  # cap",
            language="python",
        )
        st.markdown("""
| IC50 (uM) | Score | Interpretation |
|-----------|-------|----------------|
| 0.001 | 0.998 | Extremely potent binder |
| 0.01 | 0.980 | Very potent (cap applied) |
| 0.1 | 0.833 | Potent |
| 0.5 | 0.500 | Moderate |
| 1.0 | 0.333 | Weak |
| 10.0 | 0.048 | Very weak |

**Lower IC50 = drug binds the protein more tightly = higher confidence.**

The 0.5 uM reference point means an IC50 of 0.5 uM maps to exactly 0.50.
The 0.98 cap prevents any single IC50 from dominating the binding strategy.
""")

    # ── Section E: Binding Evidence Strategy Weights ─────────────────
    with st.expander("Binding Evidence Strategy Weights"):
        st.markdown("""
The **binding_evidence** strategy (1 of 8 strategies) scores each drug-protein
link by combining 7 components:

| Component | Weight | Data Source |
|-----------|--------|-------------|
| ABPP experimental IC50 | 0.30 | 65 curated IC50/engagement entries with PMIDs |
| Graph edge confidence | 0.20 | The morphism confidence from the knowledge graph |
| Boltz2 heuristic binding | 0.10 | Structure-based binding prediction (fallback mode) |
| Drug-likeness (Lipinski) | 0.10 | Molecular weight, logP, H-bond donors/acceptors |
| Drug-target compatibility | 0.10 | logP and H-bond matching between drug and protein pocket |
| Molecular bridge scores | 0.10 | Solubility, steric, and reactivity compatibility |
| Pfam domain matching | 0.10 | Domain-drug class associations (kinase inhibitor -> kinase domain) |

**Renormalization:** If a component has no data (e.g., no ABPP entry for this
drug-protein pair), its weight is redistributed proportionally among the
remaining components. The system never penalizes missing data -- it just uses
what it has.

**Per-target scoring:** For a Drug -> Disease pair, the strategy scores ALL
intermediate proteins (Drug -> Protein edges) and returns the **best** score
across all targets.
""")

    # ── Section F: How Researchers Should Use This ───────────────────
    with st.expander("How Researchers Should Use This"):
        st.markdown("""
**Interpreting scores:**

- **Score 0.90+** with high-confidence edges (0.70+): Strong candidate.
  Follow the cited PMIDs and check if there are clinical trials.

- **Score 0.70-0.89** with mixed-confidence edges: Worth investigating.
  Check how many strategies agreed (6/8 is stronger than 2/8).

- **Score 0.70+** with mostly low-confidence edges (0.20-0.35): Score may be
  inflated by many weak PubMed co-mention paths. Verify the mechanism
  independently before investing resources.

- **Score < 0.50**: Weak candidate. Only worth pursuing if you have
  independent experimental evidence.

**What to look for in a triage report:**

1. **Strategy agreement**: How many of the 8 strategies voted? More
   agreement = more robust prediction.
2. **Path quality**: Are the mechanistic chains built on high-confidence
   edges (ChEMBL, FDA) or speculative ones (PubMed co-mention)?
3. **IC50 data**: If the binding_evidence strategy voted AND there are
   ABPP IC50 values, those are experimental measurements -- the strongest
   evidence type in this system.
4. **Cited papers**: Every edge has a provenance string. Follow the PMIDs
   to the original papers.

**What this system does NOT do:**

- It does not replace clinical judgment
- It does not predict safety, toxicity, or pharmacokinetics
- It does not account for patient-specific factors
- AUROC of 0.94 on our 44-positive benchmark does not guarantee real-world
  performance
- The system bridges knowledge silos; it does not generate new knowledge
""")


# ── About ────────────────────────────────────────────────────────────

elif mode == "About":
    st.title("About KOMPOSOS-IV-PHARM")

    n_drugs = len(g["drugs"])
    n_diseases = len(g["diseases"])
    n_obj = g["n_objects"]
    n_mor = g["n_morphisms"]
    n_pos = g["n_positives"]

    st.markdown(f"""
KOMPOSOS-IV-PHARM is a **categorical AI runtime** for drug repurposing. It uses
category theory (Kan extensions, Yoneda lemma, topos logic, fibrations) to
predict which existing drugs might treat diseases they weren't originally
approved for.

### How It Works

1. **Knowledge Graph**: {n_drugs} drugs, {n_obj - n_drugs - n_diseases} proteins/compounds, \
{n_diseases} diseases, {n_mor} edges -- all with literature citations (PMIDs + ChEMBL IDs)
2. **8 Inference Strategies**: Each uses a different mathematical or molecular lens
   (composition, Kan extensions, Yoneda patterns, topos logic, structural holes,
   fibration lifts, type heuristics, binding evidence)
3. **Binding Evidence**: IC50/engagement data from ABPP experiments, Boltz2
   heuristic binding, drug-likeness (Lipinski), drug-target molecular compatibility
4. **Scoring**: Average strategy confidences + path bonus for mechanistic
   Drug->Protein->Disease chains (see "How Scoring Works" page for the full formula)
5. **Evidence**: Every prediction comes with traceable mechanistic paths,
   literature citations, and IC50 data where available
""")

    st.markdown("### Live Graph Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Objects", f"{n_obj:,}")
    c2.metric("Edges", f"{n_mor:,}")
    c3.metric("Positives", n_pos)
    c4.metric("Self-check", f"{g['check_recovered']}/{g['check_total']}")

    st.markdown("**Edge confidence distribution**")
    st.markdown(
        f"- High confidence (>= 0.70): **{g['high_conf']}** edges\n"
        f"- Medium confidence (0.40 - 0.69): **{g['med_conf']}** edges\n"
        f"- Low confidence (< 0.40): **{g['low_conf']}** edges"
    )

    st.markdown("""
### Validation (remove_direct_labels protocol, 44 positives, full_typed view)

| Metric | Value |
|--------|-------|
| AUROC | 0.940 |
| AUPRC | 0.431 |
| Positives | 44 FDA-approved oncology indications |
| Strategies | 8 (incl. binding evidence with IC50 data) |
| Strongest baseline (shortest-path) | AUROC 0.931 |
| Margin over baseline | +0.009 |
| ClinicalTrials.gov cross-check | 63% IN_TRIALS, 30% PRECLINICAL, 7% NOVEL |

*The `remove_direct_labels` protocol removes Drug->Disease edges before scoring,
so the system must predict via mechanistic paths only. This is the scientifically
honest protocol for claiming repurposing capability. LOOCV AUROC (0.974) is higher
but leaves other positives' direct edges in the graph.*

### Limitations

- **Research prototype**: Not a clinical decision support system
- **Oncology only**: 20 cancer types currently
- **Small graph**: {n_obj} objects vs 47k+ in published systems like Rephetio
- **Open-world negatives**: Unlabeled pairs are unknowns, not confirmed negatives
- **AUROC is sensitive to graph expansion**: Adding PubMed co-mention edges
  (low confidence) changes AUROC depending on protocol and quality tier filter
- **Modest margin**: The system's advantage over graph-topology baselines is
  modest; its value is in multi-strategy voting and evidence traceability

### Citation

Hawkins, J.R. (2026). KOMPOSOS-IV-PHARM: Categorical Drug Repurposing.
Apache 2.0 / Commercial dual license.
""")
