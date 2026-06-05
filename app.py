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

import re
import sqlite3
import sys
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parent
BUNDLED_OPERADUM_ROOT = APP_ROOT / "operadum"
SIBLING_OPERADUM_ROOT = APP_ROOT.parent / "operadum"

sys.path.insert(0, str(APP_ROOT))
# Prefer the self-contained stack bundled inside this KOMPOSOS checkout. Fall
# back to the standalone sibling copy used as the universal source/workbench.
if (BUNDLED_OPERADUM_ROOT / "pronoia").is_dir():
    OPERADUM_STACK_ROOT = BUNDLED_OPERADUM_ROOT
elif (SIBLING_OPERADUM_ROOT / "pronoia").is_dir():
    OPERADUM_STACK_ROOT = SIBLING_OPERADUM_ROOT
else:
    OPERADUM_STACK_ROOT = BUNDLED_OPERADUM_ROOT
sys.path.insert(0, str(OPERADUM_STACK_ROOT))

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
    make_strategies,
    score_pair,
    score_pair_detailed,
)
from validation.ranking_calibration import (
    DEFAULT_CALIBRATION_PATH,
    calibrate_score,
    load_calibration,
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

# OPERADUM decision layer is optional: if the vendored copy is missing or fails
# to import, the rest of the app still runs and the OPERADUM mode is hidden.
try:
    from operadum import DRUG_PORTFOLIO, EVIDENCE_FIRST, FASTEST_RECOVERY
    from operadum.integrations.komposos_drug_world import KompososDrugEvidenceClient
    from operadum.integrations.drug_batch_ranker import Candidate, rank_candidates

    OPERADUM_AVAILABLE = True
    OPERADUM_PROFILES = {
        "Portfolio (evidence + safety + developability)": DRUG_PORTFOLIO,
        "Evidence-first": EVIDENCE_FIRST,
        "Fastest next step": FASTEST_RECOVERY,
    }
except Exception as _operadum_exc:  # pragma: no cover - environment dependent
    OPERADUM_AVAILABLE = False
    OPERADUM_IMPORT_ERROR = str(_operadum_exc)


# PRONOIA prediction audit is optional and requires the bundled stack or the
# standalone sibling fallback. The app still runs if only KOMPOSOS is present.
try:
    from operadum.integrations.komposos_pharm_evidence import (
        KompososPharmEvidenceProvider,
        pharm_candidate,
    )
    from operadum.integrations.pronoia_pharm_loop import (
        PharmScoreConfig,
        rank_pharm_candidates_with_pronoia,
    )

    PRONOIA_AVAILABLE = True
except Exception as _pronoia_exc:  # pragma: no cover - environment dependent
    PRONOIA_AVAILABLE = False
    PRONOIA_IMPORT_ERROR = str(_pronoia_exc)


# ── Cache heavy loads ────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading knowledge graph...")
def load_graph():
    category, _ = load_full_typed_view(DB_PATH)
    drugs, diseases, positives = drug_disease_pairs(category)
    strategies = make_strategies(category)
    provenance_index = _build_provenance_index(DB_PATH)
    ranking_calibration = load_calibration(DEFAULT_CALIBRATION_PATH)
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

    pmids = set()
    provenance_rows = 0
    quantitative_edges = 0  # rows with a populated structured quantitative_value column
    tier_counts: dict[str, int] = {}
    # Data-source signatures scanned from provenance/metadata text (edges overlap).
    source_patterns = {
        "ChEMBL": r"ChEMBL",
        "PubMed": r"PMID|PubMed",
        "ESMC": r"ESM",
        "KEGG": r"KEGG",
        "FDA": r"\bFDA\b",
        "STRING": r"STRING|PPI",
        "ABPP": r"ABPP",
        "cBioPortal": r"cBioPortal|genomic",
    }
    source_counts = {name: 0 for name in source_patterns}
    compiled_sources = {n: re.compile(p, re.IGNORECASE) for n, p in source_patterns.items()}
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(morphisms)")
        morphism_columns = {row[1] for row in cursor.fetchall()}
        quant_expr = (
            "quantitative_value"
            if "quantitative_value" in morphism_columns
            else "NULL AS quantitative_value"
        )
        tier_expr = (
            "evidence_tier"
            if "evidence_tier" in morphism_columns
            else "NULL AS evidence_tier"
        )
        cursor.execute(
            f"SELECT provenance, metadata, {quant_expr}, {tier_expr} FROM morphisms"
        )
        for provenance, metadata, quantitative_value, evidence_tier in cursor.fetchall():
            text = f"{provenance or ''} {metadata or ''}"
            pmids.update(re.findall(r"PMID:?\s*(\d+)", text))
            if provenance and provenance != "unknown":
                provenance_rows += 1
            if quantitative_value is not None:
                quantitative_edges += 1
            if evidence_tier:
                tier_counts[evidence_tier] = tier_counts.get(evidence_tier, 0) + 1
            for name, pat in compiled_sources.items():
                if pat.search(text):
                    source_counts[name] += 1

    # Experimental potency values (IC50/engagement) are not stored on graph edges;
    # they live in the ABPP dataset and are injected by the binding strategy at
    # scoring time. Report that real, defensible count rather than the empty
    # structured column.
    abpp_measurements = 0
    abpp_path = Path(__file__).resolve().parent / "data" / "abpp_results.json"
    try:
        import json
        abpp_data = json.loads(abpp_path.read_text())
        records = abpp_data if isinstance(abpp_data, list) else abpp_data.get(
            "results", abpp_data
        )
        abpp_measurements = len(records)
    except Exception:
        abpp_measurements = 0

    return {
        "category": category,
        "drugs": drugs,
        "diseases": diseases,
        "positives": positives,
        "strategies": strategies,
        "strategy_names": [strategy.name for strategy in strategies],
        "provenance_index": provenance_index,
        "n_objects": n_objects,
        "n_morphisms": n_morphisms,
        "n_positives": len(positives),
        "check_recovered": check_recovered,
        "check_total": check_total,
        "high_conf": high_conf,
        "med_conf": med_conf,
        "low_conf": low_conf,
        "pmid_count": len(pmids),
        "provenance_rows": provenance_rows,
        "quantitative_edges": quantitative_edges,
        "abpp_measurements": abpp_measurements,
        "tier_counts": tier_counts,
        "source_counts": source_counts,
        "ranking_calibration": ranking_calibration,
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

_modes = ["Disease-first", "Drug-first", "Pair detail"]
if OPERADUM_AVAILABLE:
    _modes.append("Decision ranking (OPERADUM)")
if PRONOIA_AVAILABLE:
    _modes.append("Prediction audit (PRONOIA)")
_modes += ["How Scoring Works", "About"]

mode = st.sidebar.radio("Mode", _modes)
if PRONOIA_AVAILABLE:
    st.sidebar.caption(f"Audit stack: OPERADUM + PRONOIA from `{OPERADUM_STACK_ROOT}`")
elif OPERADUM_AVAILABLE:
    st.sidebar.caption(f"Decision stack: OPERADUM from `{OPERADUM_STACK_ROOT}`")

g = load_graph()

_tier_order = ["MEASURED", "ESTABLISHED", "INFERRED", "HYPOTHESIS"]
_tiers = g.get("tier_counts", {})
_tier_str = " · ".join(
    f"{t.title()} {_tiers[t]}" for t in _tier_order if _tiers.get(t)
) or "n/a"
_sources = g.get("source_counts", {})
_source_str = " · ".join(
    f"{name} {n}" for name, n in sorted(
        _sources.items(), key=lambda kv: kv[1], reverse=True
    ) if n
) or "n/a"

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Graph**: {g['n_objects']} objects, {g['n_morphisms']} edges\n\n"
    f"**Positives**: {g['n_positives']} FDA-approved drug-disease labels\n\n"
    f"**Self-check**: {g['check_recovered']}/{g['check_total']} recoverable\n\n"
    f"**Evidence tiers**: {_tier_str}\n\n"
    f"**Sources** (edges may cite several): {_source_str}\n\n"
    f"**Source fields**: {g['provenance_rows']}/{g['n_morphisms']} edges, "
    f"{g['pmid_count']} PMID IDs\n\n"
    f"**Quantitative evidence**: {g['abpp_measurements']} experimental ABPP "
    f"IC50/engagement measurements"
)
st.sidebar.caption(
    "Experimental potency values are integrated by the binding strategy from the "
    f"ABPP dataset, not stored on graph edges; the on-edge quantitative_value "
    f"column is {g['quantitative_edges']}/{g['n_morphisms']} populated "
    "(edge-level numeric extraction is an open task)."
)
st.sidebar.caption(
    f"Live strategy profile: {len(g['strategy_names'])} modules; "
    f"Yoneda {'active' if 'yoneda_distance' in g['strategy_names'] else 'inactive'}"
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


def _benchmark_label_rate(score: float) -> float | None:
    """Return benchmark-calibrated label rate for a ranking score."""
    return calibrate_score(score, g.get("ranking_calibration"))


def _target_from_result(result) -> str | None:
    """Pull the mechanistic target (the protein in a drug->protein->disease path).

    The top compositional chain's first hop ends at the intermediate node, which
    for a mechanistic path is the drug's target. Returns None when no such hop
    exists, in which case OPERADUM just uses fewer applicable actions.
    """
    chains = result.get("chains", [])
    if not chains:
        return None
    edges = chains[0].get("edges", [])
    if len(edges) >= 2:
        return edges[0].get("target")
    return None


if OPERADUM_AVAILABLE:

    @st.cache_resource(show_spinner=False)
    def operadum_client():
        """OPERADUM evidence client pointed at THIS PHARM checkout's data."""
        pharm_root = str(Path(__file__).resolve().parent)
        return KompososDrugEvidenceClient(pharm_root, use_komposos=True)

    def _ev(evidence, key):
        return f"{evidence[key].score:.2f}" if key in evidence else "-"

    def generate_operadum_report(slate, profile_name, require_evidence) -> str:
        """Markdown decision-record report for one OPERADUM ranking."""
        from datetime import date

        gate = ("evidence_strength >= 0.8 required for the next action"
                if require_evidence else "no evidence gate on the next action")
        out = [
            f"# OPERADUM Decision Ranking — {slate.disease}",
            "",
            f"- Date: {date.today().isoformat()}",
            f"- Profile: {profile_name} ({slate.monoid_name})",
            f"- Next-action gate: {gate}",
            f"- Candidates ranked: {len(slate.assessments)}",
            f"- Graph: {g['n_objects']} objects, {g['n_morphisms']} morphisms; "
            f"self-check {g['check_recovered']}/{g['check_total']} approved indications recoverable",
            "",
            "Lower decision score is better (negative is good). Scores are relative "
            "within this ranking only — do not compare across diseases or profiles.",
            "",
        ]
        if slate.winner is not None:
            w = slate.winner
            out += [
                f"## Recommendation: {w.candidate.drug}",
                "",
                f"- Target: {w.candidate.target or 'n/a'}",
                f"- Decision score: {w.score:+.3f}",
                f"- Best next action: {w.best_action_name or 'no feasible action'}",
                "",
            ]
        out += [
            "## Ranked candidates",
            "",
            "| Rank | Drug | Target | Decision Score | Next Action | Graph | Engagement | Binding | Drug-likeness |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for rank, a in enumerate(slate.assessments, start=1):
            ev = a.evidence
            out.append(
                f"| {rank} | {a.candidate.drug} | {a.candidate.target or '-'} | "
                f"{a.score:+.3f} | {a.best_action_name or 'no feasible action'} | "
                f"{_ev(ev, 'graph')} | {_ev(ev, 'engagement')} | "
                f"{_ev(ev, 'binding')} | {_ev(ev, 'druglike')} |"
            )
        out += ["", "## Evidence sources", ""]
        for a in slate.assessments:
            out.append(f"### {a.candidate.drug}")
            for name, res in a.evidence.items():
                out.append(f"- **{name}** {res.score:.3f} — {res.source}: {res.detail}")
            out.append("")
        out += [
            "## Honest limits",
            "",
            "- A prioritization aid on Track A — not clinical, prospective, or "
            "Track B. The risk figures are coarse priors, not validated safety "
            "predictions.",
            "- Structure binding uses OPERADUM's fallback unless Boltz is installed.",
            "- Decision scores are relative within this single ranking only.",
            "- The categorical fold is transparent and reproducible but is not "
            "independently validated as beating a hand-tuned scorecard.",
            "",
            "Generated by KOMPOSOS-IV-PHARM + OPERADUM decision layer.",
        ]
        return "\n".join(out)

    def render_operadum_detail(assessment):
        """Per-candidate evidence + next-action verdict for the details section."""
        a = assessment
        feasible = a.best_action is not None
        color = "green" if feasible else "orange"
        verdict = a.best_action_name or "no feasible action"
        st.markdown(
            f"### {a.candidate.drug} → {a.disease}  &nbsp; :{color}[{verdict}]"
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Decision Score", f"{a.score:+.2f}")
        c2.metric("Target", a.candidate.target or "—")
        if "confidence" in a.portfolio:
            c3.metric("Joint confidence", f"{a.portfolio['confidence']:.2f}")
        ev_rows = [
            {"Source": name, "Score": round(r.score, 3),
             "From": r.source, "Detail": r.detail}
            for name, r in a.evidence.items()
        ]
        if ev_rows:
            st.dataframe(ev_rows, use_container_width=True, hide_index=True)
        if not feasible:
            st.caption(
                "No next action clears the evidence gate — not currently backable "
                "without gathering more evidence first."
            )


if PRONOIA_AVAILABLE:

    @st.cache_resource(show_spinner=False)
    def pronoia_evidence_provider(remove_direct_labels: bool, quality_tier: str):
        """PRONOIA evidence provider pointed at THIS PHARM checkout."""
        category, _ = load_full_typed_view(
            str(APP_ROOT / DB_PATH),
            remove_direct_labels=remove_direct_labels,
            quality_tier=quality_tier,
        )
        return KompososPharmEvidenceProvider(
            komposos_path=str(APP_ROOT),
            quality_tier=quality_tier,
            include_benchmark_score=False,
            category=category,
        )

    def _collect_pmids(value) -> tuple[str, ...]:
        pmids = []

        def walk(obj):
            if isinstance(obj, dict):
                for pmid in obj.get("pmids", ()) or ():
                    pmids.append(str(pmid))
                for child in obj.values():
                    walk(child)
            elif isinstance(obj, (list, tuple)):
                for child in obj:
                    walk(child)
            elif isinstance(obj, str):
                pmids.extend(re.findall(r"PMID:?\s*(\d+)", obj))

        walk(value)
        seen = set()
        out = []
        for pmid in pmids:
            if pmid and pmid not in seen:
                seen.add(pmid)
                out.append(pmid)
        return tuple(out)

    def _pmid_links(pmids: tuple[str, ...]) -> str:
        if not pmids:
            return "-"
        return ", ".join(
            f"[PMID:{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid})"
            for pmid in pmids
        )

    def _top_pronoia_evidence(report):
        packet = report.evidence
        items = tuple(getattr(packet, "items", ()) or ())
        if not items:
            return None
        return sorted(items, key=lambda item: float(item.score or 0.0), reverse=True)[0]

    def _pronoia_label(report) -> str:
        drug = report.candidate.metadata.get("drug", report.candidate.name)
        disease = report.candidate.metadata.get("disease", report.candidate.target)
        return _label_for_pair((drug, disease), g["positives"])

    def _evidence_tiers(item) -> tuple[str, ...]:
        metadata = item.metadata or {}
        tiers = metadata.get("evidence_tiers") or ()
        if tiers:
            return tuple(str(t) for t in tiers)
        out = []
        for key in ("evidence_tier",):
            if metadata.get(key):
                out.append(str(metadata[key]))
        for key in ("first", "second"):
            child = metadata.get(key)
            if isinstance(child, dict) and child.get("evidence_tier"):
                out.append(str(child["evidence_tier"]))
        seen = set()
        return tuple(t for t in out if not (t in seen or seen.add(t)))

    def generate_pronoia_audit_report(slate, disease: str, settings: dict) -> str:
        """Markdown audit report for one PRONOIA PHARM ranking."""
        from datetime import date

        label_mode = (
            "direct Drug->Disease labels hidden"
            if settings["remove_direct_labels"] else
            "direct Drug->Disease labels visible"
        )
        out = [
            f"# PRONOIA Prediction Audit - {disease}",
            "",
            f"- Date: {date.today().isoformat()}",
            f"- KOMPOSOS checkout: `{APP_ROOT}`",
            f"- OPERADUM/PRONOIA stack: `{OPERADUM_STACK_ROOT}`",
            f"- Evidence protocol: {label_mode}",
            f"- Evidence quality tier: {settings['quality_tier']}",
            f"- Minimum grounding: {settings['min_grounding']:.2f}",
            f"- Candidates ranked: {len(slate.reports)}",
            "",
            "## Layer Roles",
            "",
            "- KOMPOSOS-IV-PHARM supplies the graph evidence, paths, PMIDs, FDA strings, evidence tiers, and local benchmark labels.",
            "- OPERADUM packages candidates and provides the decision/prioritization layer elsewhere in the UI.",
            "- PRONOIA scores the candidate as a prediction audit: structured mechanism/path strength plus grounding, with raw MDL retained for transparency.",
            "",
            "This is not a clinical recommendation. It is a reproducible audit trail for expert review.",
            "",
            "## Ranked Prediction Audit",
            "",
            "| Rank | Candidate | Local label | Decision | PRONOIA score | Grounding | Base strength | Raw MDL gain | Evidence | PMIDs |",
            "|---:|---|---|---|---:|---:|---:|---:|---|---|",
        ]
        for rank, report in enumerate(slate.reports, start=1):
            top = _top_pronoia_evidence(report)
            top_claim = top.claim if top is not None else "-"
            top_pmids = _collect_pmids(top.metadata if top is not None else {})
            out.append(
                f"| {rank} | {report.candidate.name} -> {report.candidate.target} | "
                f"{_pronoia_label(report)} | {report.decision} | "
                f"{report.score:.2f} | {report.metrics.get('grounding', 0.0):.3f} | "
                f"{report.metrics.get('pharm_base_strength', 0.0):.3f} | "
                f"{report.metrics.get('raw_mdl_gain_bits', 0.0):.1f} | "
                f"{top_claim} | {_pmid_links(top_pmids)} |"
            )
        out += ["", "## Per-Candidate Evidence", ""]
        for report in slate.reports:
            out += [
                f"### {report.candidate.name} -> {report.candidate.target}",
                "",
                f"- Decision: {report.decision}",
                f"- PRONOIA score: {report.score:.2f}",
                f"- Grounding: {report.metrics.get('grounding', 0.0):.3f}",
                f"- Base path/mechanism strength: {report.metrics.get('pharm_base_strength', 0.0):.3f}",
                f"- Raw MDL gain: {report.metrics.get('raw_mdl_gain_bits', 0.0):.1f} bits",
                "",
            ]
            packet = report.evidence
            for item in sorted(
                tuple(getattr(packet, "items", ()) or ()),
                key=lambda ev: float(ev.score or 0.0),
                reverse=True,
            )[:8]:
                pmids = _collect_pmids({"metadata": item.metadata, "provenance": item.provenance})
                tiers = _evidence_tiers(item)
                out.append(
                    f"- **{item.source}** score={float(item.score or 0.0):.3f}; "
                    f"tiers={', '.join(tiers) if tiers else '-'}; "
                    f"pmids={', '.join(pmids) if pmids else '-'}; {item.claim}"
                )
            out.append("")
        out += [
            "## Honest Limits",
            "",
            "- PRONOIA v2 is a mechanism/path audit score, not a clinical probability.",
            "- Raw MDL is retained for transparency but is not the primary PHARM ranker.",
            "- The contradiction/residual penalty is not yet wired into v2.",
            "- Local NOT_APPROVED labels are open-world: they may include missing labels, active trials, or off-label/unstudied cases.",
            "",
            "Generated by KOMPOSOS-IV-PHARM UI with the OPERADUM -> KOMPOSOS -> PRONOIA audit stack.",
        ]
        return "\n".join(out)

    def render_pronoia_detail(report):
        color = "green" if report.decision == "BACK" else "orange"
        st.markdown(
            f"### {report.candidate.name} -> {report.candidate.target} "
            f"&nbsp; :{color}[{report.decision}]"
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PRONOIA score", f"{report.score:.1f}")
        c2.metric("Grounding", f"{report.metrics.get('grounding', 0.0):.3f}")
        c3.metric("Base strength", f"{report.metrics.get('pharm_base_strength', 0.0):.3f}")
        c4.metric("Raw MDL gain", f"{report.metrics.get('raw_mdl_gain_bits', 0.0):.1f}")
        st.caption(report.explanation)

        packet = report.evidence
        rows = []
        for item in sorted(
            tuple(getattr(packet, "items", ()) or ()),
            key=lambda ev: float(ev.score or 0.0),
            reverse=True,
        ):
            pmids = _collect_pmids({"metadata": item.metadata, "provenance": item.provenance})
            tiers = _evidence_tiers(item)
            rows.append({
                "Source": item.source,
                "Score": round(float(item.score or 0.0), 3),
                "Evidence": item.claim,
                "Tiers": ", ".join(tiers) if tiers else "-",
                "PMIDs": ", ".join(pmids) if pmids else "-",
                "Provenance": item.provenance or "-",
            })
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)


def render_results_table(results):
    """Show ranked results as a streamlit table."""
    rows = []
    has_calibration = g.get("ranking_calibration") is not None
    for r in results:
        row = {
            "Rank": r["rank"],
            "Drug": r["drug"],
            "Disease": r["disease"],
            "Score": round(r["score"], 3),
            "Label": r["label"],
            "Top Trace": _top_trace(r.get("chains", [])),
            "Paths": r["n_chains"],
            "Cited": f"{r['cited_edges']}/{r['total_edges']}"
            if r["total_edges"] > 0 else "-",
        }
        if has_calibration:
            label_rate = _benchmark_label_rate(r["score"])
            row["Benchmark Label Rate"] = f"{label_rate:.1%}" if label_rate is not None else "-"
        rows.append(row)
    st.dataframe(rows, use_container_width=True, hide_index=True)


# User-friendly strategy labels for pharma audience
STRATEGY_DISPLAY = {
    "kan_extension": {
        "label": "Drug Analogy",
        "hint": "Similar drugs treat similar diseases",
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
    "yoneda_distance": {
        "label": "Structural Similarity",
        "hint": "Drug has similar target profile to known treatments on clean evidence subgraph (Yoneda presheaf distance)",
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


def _generate_strategy_explanation(strategy_name: str, drug: str, disease: str,
                                   confidence: float, entry: dict, graph_data: dict) -> str:
    """Generate case-specific explanation for why a strategy voted."""
    category = graph_data["category"]

    if strategy_name == "kan_extension":
        # Find similar drugs that treat this disease
        similar_drugs = []
        for obj in category.objects():
            if obj.type_name == "Drug" and obj.name != drug:
                # Check if this drug treats the disease
                for mor in category.morphisms():
                    if mor.source == obj.name and mor.target == disease and mor.name == "treats":
                        similar_drugs.append(obj.name)
                        break

        if similar_drugs:
            return (
                f"**Why this score?** Found {len(similar_drugs)} drugs that treat {disease}: "
                f"{', '.join(similar_drugs[:3])}{'...' if len(similar_drugs) > 3 else ''}. "
                f"The Kan extension computed structural similarity between {drug} and these drugs "
                f"based on shared protein targets. Higher similarity \u2192 higher confidence that "
                f"{drug} should also treat {disease}."
            )
        else:
            return f"**Low confidence reason:** No similar drugs found that treat {disease} to compare {drug} against."

    elif strategy_name == "composition":
        n_paths = entry.get("n_chains", 0)
        if n_paths > 0:
            high = sum(1 for c in entry.get("chains", []) if min(e["confidence"] for e in c["edges"]) >= 0.70)
            med = sum(1 for c in entry.get("chains", []) if 0.40 <= min(e["confidence"] for e in c["edges"]) < 0.70)
            low = n_paths - high - med

            return (
                f"**Mechanistic paths found:** {n_paths} total paths from {drug} through proteins to {disease}. "
                f"Quality breakdown: {high} high-confidence (both edges \u2265 0.70), {med} medium (0.40-0.69), "
                f"{low} speculative (< 0.40). Score = best path confidence."
            )
        else:
            return f"**No direct mechanistic path:** No Drug\u2192Protein\u2192Disease chain found. Other strategies may suggest this based on analogy."

    elif strategy_name == "binding_evidence":
        # Check for IC50 data
        has_ic50 = False
        try:
            from abpp_bridge import ABPPBridge
            abpp = ABPPBridge()
            for chain in entry.get("chains", []):
                for edge in chain.get("edges", []):
                    protein = edge.get("target", "")
                    result = abpp.check_abpp(drug, protein)
                    if result and result.validated and result.ic50_um is not None:
                        has_ic50 = True
                        break
        except:
            pass

        if has_ic50:
            return (
                f"**Experimental data available:** This score integrates IC50 binding measurements from ABPP experiments. "
                f"See the 'Binding Evidence' section below for IC50 values. Also includes drug-likeness (Lipinski rules) "
                f"and molecular compatibility with protein targets."
            )
        else:
            return (
                f"**Computational estimate:** No experimental IC50 data for {drug}. Score based on drug-likeness (Lipinski), "
                f"molecular compatibility (logP/H-bond matching), and graph edge confidence."
            )

    elif strategy_name == "structural_hole":
        return (
            f"**Network closure pattern:** This strategy identifies Drug-Protein-Disease triangles where two edges exist "
            f"but the third is missing. Score reflects how strongly the existing structure suggests {drug}\u2192{disease}."
        )

    elif strategy_name == "yoneda_pattern":
        return (
            f"**Interaction profile matching:** Compares {drug}'s protein interaction pattern to known treatments for {disease}. "
            f"Higher score = more similar interaction profiles. Based on the Yoneda lemma (objects determined by morphisms to/from them)."
        )

    elif strategy_name == "fibration_lift":
        return (
            f"**Structural inference:** Prediction 'lifted' from related biological contexts using fibration structure. "
            f"Example: if {drug} works in a similar disease type, it may work here too."
        )

    elif strategy_name == "topos_logic":
        return (
            f"**Evidence integration:** Combines partial evidence from multiple sources using topos logic (intuitionistic logic over the knowledge graph). "
            f"Higher score = more consistent partial evidence across different viewpoints."
        )

    return ""


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
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Ranking Score", f"{entry['score']:.3f}")
        c2.metric("Base (active signals)", f"{breakdown['base']:.3f}")
        c3.metric("Path Bonus", f"{breakdown['path_bonus']:.3f}")
        c4.metric("Yoneda Bonus", f"{breakdown.get('yoneda_bonus', 0.0):.3f}")
        if breakdown["mechanistic_discount"]:
            c5.metric("Mech. Discount", "0.80x applied")
        else:
            c5.metric("Mech. Discount", "none")
        label_rate = _benchmark_label_rate(entry["score"])
        if label_rate is not None:
            st.caption(
                f"Benchmark-calibrated label rate for this score bin: {label_rate:.1%}. "
                "This is derived from the validation benchmark and is not a clinical probability."
            )
        if breakdown["composition_count"] > 0:
            st.caption(
                f"Composition paths: {breakdown['composition_count']} | "
                f"Sum of path confidences: {breakdown['composition_weight']:.2f} | "
                f"Path bonus = min(0.25, 0.04 x {breakdown['composition_weight']:.2f}) = "
                f"{breakdown['path_bonus']:.3f}"
            )
    else:
        st.metric("Score", f"{entry['score']:.3f}")

    # ── Evidence Tier Breakdown ──────────────────────────────────────
    st.markdown("### Evidence Quality Tiers")
    st.caption("Evidence types from highest to lowest quality:")

    # Count tiers from chains
    tier_counts = {"MEASURED": 0, "ESTABLISHED": 0, "INFERRED": 0, "HYPOTHESIS": 0, "SPECULATIVE": 0, "NOISE": 0}
    total_edges = 0

    for chain in entry.get("chains", []):
        for edge in chain["edges"]:
            tier = edge.get("evidence_tier", "HYPOTHESIS")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            total_edges += 1

    if total_edges > 0:
        cols = st.columns(6)
        cols[0].metric("🔬 Measured", tier_counts.get("MEASURED", 0),
                       help="IC50 data, clinical outcomes, mutation frequencies")
        cols[1].metric("✅ Established", tier_counts.get("ESTABLISHED", 0),
                       help="FDA approved, KEGG canonical pathways")
        cols[2].metric("💡 Inferred", tier_counts.get("INFERRED", 0),
                       help="ESM2 similarity, STRING PPI (computed)")
        cols[3].metric("❓ Hypothesis", tier_counts.get("HYPOTHESIS", 0),
                       help="PubMed citations, not quantified")
        cols[4].metric("🔸 Speculative", tier_counts.get("SPECULATIVE", 0),
                       help="PubMed ORPHAN (isolated)")
        cols[5].metric("❌ Noise", tier_counts.get("NOISE", 0),
                       help="PubMed REJECT (contradictory)")

        # Show highest-tier evidence
        best_tier = None
        for tier in ["MEASURED", "ESTABLISHED", "INFERRED", "HYPOTHESIS", "SPECULATIVE"]:
            if tier_counts.get(tier, 0) > 0:
                best_tier = tier
                break

        if best_tier:
            tier_descriptions = {
                "MEASURED": "Experimental IC50/clinical data - highest quality evidence",
                "ESTABLISHED": "FDA/KEGG approved - regulatory authority",
                "INFERRED": "Computational similarity - requires validation",
                "HYPOTHESIS": "Literature citations - graph coherence only, not quantified",
                "SPECULATIVE": "Weak literature support - isolated edges",
            }
            st.info(f"**Highest evidence tier:** {best_tier} - {tier_descriptions.get(best_tier, '')}")
    else:
        st.warning("No mechanistic paths found - prediction based on strategy voting only")

    # ── Strategy votes ───────────────────────────────────────────────
    if entry["votes"]:
        st.markdown("**Strategy Signal Scores**")
        st.caption(
            "These are heuristic ranking signals, not calibrated probabilities or clinical confidence."
        )
        for name, conf in entry["votes"]:
            label = _strategy_label(name)
            hint = _strategy_hint(name)

            with st.expander(f"{label}: {conf:.2f}", expanded=False):
                st.caption(hint)

                # Generate case-specific explanation
                explanation = _generate_strategy_explanation(
                    name, entry["drug"], entry["disease"], conf, entry, g
                )
                if explanation:
                    st.markdown(explanation)

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
                    elif "PMID:" in prov:
                        # Extract all PMIDs using regex to handle "ABPP; PMID:1234" etc.
                        pmid_matches = re.findall(r"PMID:?\s*(\d+)", prov)
                        if pmid_matches:
                            links = [f"[PMID:{p}](https://pubmed.ncbi.nlm.nih.gov/{p})" for p in pmid_matches]
                            # Replace the PMID parts in the display
                            prov_display = prov
                            for p in pmid_matches:
                                prov_display = prov_display.replace(f"PMID:{p}", f"[PMID:{p}](https://pubmed.ncbi.nlm.nih.gov/{p})")
                        else:
                            prov_display = prov
                    else:
                        prov_display = prov
                    st.markdown(
                        f"- **{edge['source']}** -{edge['relation']}-> "
                        f"**{edge['target']}** "
                        f"(:{color}[conf: {conf:.2f}], {src_type} | {prov_display})"
                        f"  \n  source_type: `{edge.get('source_type', 'unknown_or_internal')}`; "
                        f"status: `{edge.get('validation_status', 'unclassified')}`"
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


# ── Decision ranking (OPERADUM) ──────────────────────────────────────

elif mode == "Decision ranking (OPERADUM)":
    st.title("Decision ranking (OPERADUM)")
    st.caption(
        "KOMPOSOS triage ranks candidates on graph evidence. OPERADUM re-ranks "
        "that same shortlist under a decision profile — folding in target "
        "engagement, structure binding, drug-likeness and risk — and names the "
        "best next action for each. Use PRONOIA audit when you want the separate "
        "prediction-grounding trail for a candidate."
    )
    with st.expander("How to read this (score direction, profiles, gating)"):
        st.markdown("""
- **Decision Score: lower is better, negative is good.** Strong candidates land
  clearly negative; weak ones sit near zero. Scores are only comparable *within*
  one ranking, not across diseases or profiles.
- **Profile** reweights the figures: *Portfolio* balances evidence + safety +
  developability (best default), *Evidence-first* lets evidence dominate,
  *Fastest next step* favours the quickest move.
- **"no feasible action"** = with the evidence requirement on, this candidate's
  best next step can't clear the 0.8 bar yet -- not currently backable without
  more evidence. Uncheck the box to see its unconstrained next step.

Full details under **How Scoring Works -> Decision ranking (OPERADUM)**.

OPERADUM is the action/prioritization layer. PRONOIA is the prediction audit
layer. They use the same KOMPOSOS evidence base but answer different questions.
""")

    disease = st.selectbox("Select disease", g["diseases"])
    shortlist_n = st.slider("Shortlist size (from KOMPOSOS triage)", 3, 25, 8)
    profile_name = st.selectbox("Decision profile", list(OPERADUM_PROFILES))
    require_evidence = st.checkbox(
        "Require strong evidence (>= 0.8) for the next action", value=True
    )

    if st.button("Rank candidates", type="primary"):
        with st.spinner("KOMPOSOS shortlist -> OPERADUM decision ranking..."):
            triaged = triage_disease(
                g["category"], g["strategies"], disease, g["positives"],
                g["provenance_index"], top_n=shortlist_n,
            )
            candidates = [
                Candidate(drug=r["drug"], target=_target_from_result(r))
                for r in triaged
            ]
            requirements = {"evidence_strength": 0.8} if require_evidence else None
            slate = rank_candidates(
                disease,
                candidates,
                client=operadum_client(),
                monoid=OPERADUM_PROFILES[profile_name],
                requirements=requirements,
            )

        if slate.winner is not None:
            st.success(
                f"Back **{slate.winner.candidate.drug}** "
                f"(score {slate.winner.score:+.2f}) — "
                f"next: {slate.winner.best_action_name or 'no feasible action'}"
            )

        rows = []
        for rank, a in enumerate(slate.assessments, start=1):
            ev = a.evidence
            rows.append({
                "Rank": rank,
                "Drug": a.candidate.drug,
                "Target": a.candidate.target or "-",
                "Decision Score": round(a.score, 2),
                "Next Action": a.best_action_name or "no feasible action",
                "Graph": round(ev["graph"].score, 2) if "graph" in ev else "-",
                "Engagement": round(ev["engagement"].score, 2) if "engagement" in ev else "-",
                "Binding": round(ev["binding"].score, 2) if "binding" in ev else "-",
                "Drug-likeness": round(ev["druglike"].score, 2) if "druglike" in ev else "-",
            })
        st.caption(f"Profile: {slate.monoid_name} — lower decision score is better.")
        st.dataframe(rows, use_container_width=True, hide_index=True)

        report_md = generate_operadum_report(slate, profile_name, require_evidence)
        st.download_button(
            "Download Decision Report",
            data=report_md,
            file_name=f"operadum_decision_{disease}_{profile_name.split()[0].lower()}.md",
            mime="text/markdown",
        )

        st.markdown(
            "*Note: structure binding uses OPERADUM's fallback unless Boltz is "
            "installed. Graph / engagement / drug-likeness read this checkout's "
            "real data.*"
        )

        st.markdown("---")
        st.subheader("Candidate Details")
        for assessment in slate.assessments[:5]:
            render_operadum_detail(assessment)
            st.markdown("---")


# ── Drug-first ───────────────────────────────────────────────────────

elif mode == "Prediction audit (PRONOIA)" and PRONOIA_AVAILABLE:
    st.title("Prediction audit (PRONOIA)")
    st.caption(
        "KOMPOSOS supplies graph evidence and provenance. OPERADUM supplies the "
        "candidate/decision layer. PRONOIA adds a prediction audit: mechanism "
        "strength, grounding, abstention, and raw MDL transparency."
    )
    with st.expander("How this differs from OPERADUM decision ranking"):
        st.markdown("""
- **KOMPOSOS triage** ranks graph evidence for drug-disease pairs.
- **OPERADUM decision ranking** asks which candidate to back next, folding graph,
  engagement, binding, drug-likeness, and risk into an action choice.
- **PRONOIA prediction audit** asks whether the candidate's stated treatment
  hypothesis is grounded by hidden-label mechanism/path evidence. It reports
  `BACK` or `ABSTAIN`, a PHARM v2 score, grounding, raw MDL gain, and the exact
  evidence trail with PMIDs/FDA provenance.

This mode is for expert review and report generation. It is not a clinical
recommendation.
""")

    disease = st.selectbox("Select disease", g["diseases"])
    shortlist_n = st.slider("Shortlist size (from KOMPOSOS triage)", 3, 30, 12)
    quality_tier = st.selectbox(
        "PRONOIA evidence quality tier",
        ["all", "high", "curated", "silver", "gold"],
        index=0,
    )
    remove_direct_labels = st.checkbox(
        "Hide direct Drug->Disease treatment labels from PRONOIA evidence",
        value=True,
    )
    min_grounding = st.slider("Minimum grounding", 0.0, 1.0, 0.20, 0.05)

    if st.button("Run PRONOIA audit", type="primary"):
        with st.spinner("KOMPOSOS shortlist -> PRONOIA prediction audit..."):
            triaged = triage_disease(
                g["category"], g["strategies"], disease, g["positives"],
                g["provenance_index"], top_n=shortlist_n,
            )
            candidates = [pharm_candidate(r["drug"], disease) for r in triaged]
            provider = pronoia_evidence_provider(remove_direct_labels, quality_tier)
            slate = rank_pharm_candidates_with_pronoia(
                candidates,
                evidence_provider=provider,
                score_config=PharmScoreConfig(min_grounding=float(min_grounding)),
                task="audit PHARM drug repurposing hypothesis from KOMPOSOS evidence",
            )

        if slate.winner is not None:
            st.success(
                f"Top PRONOIA-backed candidate: **{slate.winner.candidate.name}** "
                f"(score {slate.winner.score:.1f}, "
                f"grounding {slate.winner.metrics.get('grounding', 0.0):.3f})"
            )

        rows = []
        for rank, report in enumerate(slate.reports, start=1):
            top = _top_pronoia_evidence(report)
            pmids = _collect_pmids(top.metadata if top is not None else {})
            rows.append({
                "Rank": rank,
                "Drug": report.candidate.name,
                "Disease": report.candidate.target,
                "Local Label": _pronoia_label(report),
                "Decision": report.decision,
                "PRONOIA Score": round(float(report.score), 2),
                "Grounding": round(float(report.metrics.get("grounding", 0.0)), 3),
                "Base Strength": round(float(report.metrics.get("pharm_base_strength", 0.0)), 3),
                "Raw MDL Gain": round(float(report.metrics.get("raw_mdl_gain_bits", 0.0)), 1),
                "Top Evidence": top.claim if top is not None else "-",
                "PMIDs": ", ".join(pmids) if pmids else "-",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        settings = {
            "remove_direct_labels": remove_direct_labels,
            "quality_tier": quality_tier,
            "min_grounding": float(min_grounding),
        }
        report_md = generate_pronoia_audit_report(slate, disease, settings)
        st.download_button(
            "Download PRONOIA Audit Report",
            data=report_md,
            file_name=f"pronoia_audit_{disease}_{quality_tier}.md",
            mime="text/markdown",
        )

        st.markdown("---")
        st.subheader("Candidate Audit Details")
        for report in slate.reports[:5]:
            render_pronoia_detail(report)
            st.markdown("---")


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
    with st.expander("The Ranking Score Formula"):
        st.markdown("""
When you run a triage query, each drug-disease pair receives a ranking score.
This score is for prioritization and audit, not a calibrated probability.

**Step 1: Base score** = mean of active strategy signals

Configured strategies may abstain when their evidence is absent. The base score
is the mean of strategies that actually fire, excluding Yoneda distance when it
is present. Yoneda distance is not averaged with the other signals; it is used
only as a small additive bonus.

**Step 2: Path bonus** from compositional (mechanistic) paths

For every Drug -> Protein -> Disease path found, the composition strategy
reports the multiplicative path confidence. The path bonus rewards having many
high-quality mechanistic paths:
""")
        st.code(
            "path_confidence = drug_to_protein_conf * protein_to_disease_conf\n"
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

**Step 3: Yoneda distance bonus** from structural similarity
""")
        st.code(
            "yoneda_bonus = min(0.10, 0.06 * yoneda_similarity)",
            language="python",
        )
        st.markdown("""
The Yoneda distance strategy compares the drug's profile to visible known
treatments on the clean evidence subgraph. Direct Drug -> Disease labels are
excluded from fingerprints. Yoneda is included only when visible treatment
comparators exist; in the strict `remove_direct_labels` benchmark it is not an
active strategy because all Drug -> Disease comparator labels are removed.

If the drug looks structurally similar to an approved treatment for this
disease in the live triage graph, it gets a small additive bonus (capped at
0.10).

This can only help, never hurt -- even zero similarity adds nothing.

**Step 4: Mechanistic discount**

If the pair has **zero** composition paths (no Drug -> Protein -> Disease chain),
the score is penalized:
""")
        st.code(
            "if no_composition_paths:\n"
            "    score *= 0.80  # 20% penalty",
            language="python",
        )
        st.markdown("""
This keeps analogy-only predictions below mechanistically-supported candidates
at similar base scores.

**Final:**
""")
        st.code(
            "final = min(1.0, (base + path_bonus + yoneda_bonus) * discount)",
            language="python",
        )

    # ── Section D: IC50 to Confidence ────────────────────────────────
    with st.expander("Benchmark Calibration Is Separate"):
        st.markdown("""
The ranking score is converted to a **benchmark label rate** only after scoring.
This calibration layer does not change strategy signals and does not feed back
into the ranker.

Calibration artifact:
`reports/ranking_score_calibration_2026-05-27.json`

Current method:

1. Run the corrected `remove_direct_labels` benchmark.
2. Sort all drug-disease pairs by ranking score.
3. Split scores into quantile bins.
4. Report the observed FDA-label rate in each bin, with monotone bin smoothing.

The displayed benchmark label rate is useful for auditing score scale, but it is
not a clinical probability and not a probability that a drug will work.
""")

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
The **binding_evidence** strategy scores disease-connected drug-protein links by
combining 7 components:

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

**Per-target scoring:** For a Drug -> Disease pair, the strategy scores
intermediate proteins only when they sit on an observed Drug -> Protein ->
Disease path, then returns the best score across those disease-linked targets.
""")

    # ── Section F: How Researchers Should Use This ───────────────────
    with st.expander("How Researchers Should Use This"):
        st.markdown("""
**Interpreting scores:**

- **Ranking score 0.90+** with high-confidence edges (0.70+): Strong candidate.
  Follow the cited PMIDs and check if there are clinical trials.

- **Ranking score 0.70-0.89** with mixed-confidence edges: Worth investigating.
  Check how many strategies agreed and which evidence chains support them.

- **Ranking score 0.70+** with mostly low-confidence edges (0.20-0.35): Score may be
  inflated by many weak PubMed co-mention paths. Verify the mechanism
  independently before investing resources.

- **Ranking score < 0.50**: Weak candidate. Only worth pursuing if you have
  independent experimental evidence.

**What to look for in a triage report:**

1. **Strategy agreement**: How many strategies produced signals? More
   agreement = more robust prediction.
2. **Path quality**: Are the mechanistic chains built on high-confidence
   edges (ChEMBL, FDA) or speculative ones (PubMed co-mention)?
3. **IC50 data**: If the binding_evidence strategy voted AND there are
   ABPP IC50 values, those are experimental measurements -- the strongest
   evidence type in this system.
4. **Cited papers**: Every edge has a provenance/source string, but not every
   source is an edge-specific PMID. Follow PMID links where present and verify
   that the paper supports the exact edge.

**What this system does NOT do:**

- It does not replace clinical judgment
- It does not predict safety, toxicity, or pharmacokinetics
- It does not account for patient-specific factors
- AUROC of 0.9705 on the current strict 44-positive benchmark does not guarantee real-world
  performance
- The system surfaces auditable hypotheses from existing graph evidence; it does
  not by itself validate new clinical knowledge
""")

    if OPERADUM_AVAILABLE:
        with st.expander("Decision ranking (OPERADUM): scores, profiles, gating"):
            st.markdown("""
The **Decision ranking (OPERADUM)** mode answers a different question from the
rest of this app. KOMPOSOS triage ranks candidates on *graph evidence*. OPERADUM
takes that same shortlist and ranks the **decision**: which candidate to back,
folding evidence together with target engagement, structure binding,
drug-likeness, and risk -- then it names the best **next action** for each.

**Reading the Decision Score (lower is better, and negative is good):**

- The score is a single weighted number rolled up from every applicable
  evidence/action figure under the chosen profile. Figures you want to
  *maximize* (evidence strength, confidence, drug-likeness) count *negatively*,
  so a strong candidate lands at a clearly negative score (e.g. -75), while a
  weak one sits near zero (e.g. -10). Sort is ascending: top row is the pick.
- The numbers are only meaningful *relative to each other within one ranking* --
  don't compare a score across diseases or profiles.

**How the figures combine (not a simple average):**

- Time and money **add up** across actions.
- Confidence **multiplies** (you are only as sure as all independent checks
  agree).
- Evidence strength is **weakest-link** (the shakiest link caps the chain).
- Risks **accumulate** like a probability union (more ways to fail = more risk).

**The three profiles** just reweight those figures:

- **Portfolio** -- balances evidence, safety, and developability, and nearly
  cancels the fixed assay cost every candidate shares, so ranking turns on what
  *distinguishes* candidates. Good default for "which one do we back?".
- **Evidence-first** -- lets evidence strength and confidence dominate.
- **Fastest next step** -- favours the quickest cheapest move.

**"no feasible action"** is a verdict, not a bug. With *Require strong evidence*
on, any candidate whose best next step can't clear the 0.8 evidence bar is shown
as having no feasible action -- i.e. *not currently backable without gathering
more evidence first*. Turn the checkbox off to see the unconstrained next step.

**Honest limits:** structure binding uses OPERADUM's fallback unless Boltz is
installed (graph / target-engagement / drug-likeness read this checkout's real
data). The target column is inferred from the top mechanistic chain and may be
blank when no such path exists -- OPERADUM then ranks on fewer actions. Same
caveats as the rest of the app: this informs prioritization, it does not replace
clinical judgment.
""")


# ── About ────────────────────────────────────────────────────────────

    if PRONOIA_AVAILABLE:
        with st.expander("Prediction audit (PRONOIA): score, grounding, report trail"):
            st.markdown("""
The **Prediction audit (PRONOIA)** mode is separate from OPERADUM decision
ranking.

**Layer roles:**

- **KOMPOSOS-IV-PHARM** supplies the graph, mechanistic paths, edge confidence,
  PMIDs/FDA provenance, evidence tiers, and local benchmark labels.
- **OPERADUM** supplies the candidate/decision layer: which candidate/action is
  worth backing next under resource and evidence profiles.
- **PRONOIA** supplies the prediction audit: whether a candidate's stated
  treatment hypothesis is grounded by the available hidden-label evidence.

**PHARM v2 score:**
""")
            st.code(
                "score = 100 * max(mechanism_strength, path_strength)\n"
                "score -= grounding_penalty\n"
                "score -= contradiction_penalty  # placeholder in v2",
                language="python",
            )
            st.markdown("""
**Grounding** is the fraction of the candidate claim accounted for by the
evidence packet. If grounding is below the selected gate, PRONOIA abstains even
when the graph has some signal.

**Raw MDL gain** is shown for transparency, but it is not the primary PHARM
ranker. The benchmark showed raw zlib-MDL alone over-ranks broad/long evidence
packets, so PRONOIA v2 uses structured mechanism/path strength as the main
score.

**Report output:** the PRONOIA audit report exports the candidate ranking,
`BACK`/`ABSTAIN` decisions, grounding, raw MDL gain, top evidence paths, evidence
tiers, and PMID/FDA provenance carried from the local PHARM database.

**Honest limit:** PRONOIA v2 is an audit and expert-review tool. It is not a
clinical probability, and v3 still needs contradiction/residual and indication
context penalties.
""")


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

1. **Knowledge Graph**: {n_drugs} drugs, {n_obj - n_drugs - n_diseases} proteins, \
{n_diseases} diseases, {n_mor} edges ({g['provenance_rows']} provenance/source strings, {g['pmid_count']} PMID identifiers, {g['quantitative_edges']} graph edges with structured quantitative fields; ABPP measurements are loaded separately)
2. **Live triage strategy profile**: 8 active strategy modules
   (composition, Kan extensions, Yoneda patterns, topos logic, structural holes,
   fibration lifts, binding evidence, Yoneda distance)
3. **Binding Evidence**: IC50/engagement data from ABPP experiments, Boltz2
   heuristic binding, drug-likeness (Lipinski), drug-target molecular compatibility
4. **Yoneda Distance**: Structural similarity via presheaf fingerprints on clean
   evidence subgraph (MEASURED + ESTABLISHED edges only)
5. **Scoring**: Mean of active strategy signals + path bonus, plus a conditional
   Yoneda bonus when visible known-treatment comparators exist (see "How Scoring
   Works" page for the full formula)
6. **Evidence**: Predictions include traceable mechanistic paths when available,
   provenance/PMID links where present, and IC50 data where available
7. **Integrated audit layers**: OPERADUM provides decision/prioritization
   reports, while PRONOIA provides prediction-grounding audit reports when the
   bundled stack is available at `{OPERADUM_STACK_ROOT}`
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

    calibration = g.get("ranking_calibration")
    if calibration:
        cal_auroc = calibration.get("auroc")
        cal_auroc_text = f"{float(cal_auroc):.4f}" if cal_auroc is not None else "unknown"
        calibration_note = (
            f"Loaded `{DEFAULT_CALIBRATION_PATH}` "
            f"({calibration.get('protocol')}, {calibration.get('n_bins_requested')} bins, "
            f"benchmark AUROC {cal_auroc_text})."
        )
    else:
        calibration_note = (
            f"No calibration artifact loaded at `{DEFAULT_CALIBRATION_PATH}`. "
            "Run `python validation/build_ranking_score_calibration.py` to create it."
        )

    st.markdown(f"""
### Validation (strict remove_direct_labels protocol, 44 positives, full_typed view)

| Metric | Value |
|--------|-------|
| AUROC | 0.970549 [95% CI: 0.9519-0.9844] |
| AUPRC | 0.546427 [95% CI: 0.4025-0.6890] |
| Hits@5 | 1.000 |
| Hits@10 | 0.600 |
| Hits@20 | 0.600 |
| Strategy profile | 7 active modules; Yoneda distance excluded because no Drug->Disease comparators remain |
| Positives | 44 FDA-approved oncology indications |
| Strongest baseline (common_neighbor) | AUROC 0.6219 |
| Margin over strongest baseline | +0.3486 |
| PMID identifiers in DB | {g['pmid_count']} |

*Current audited strict run: 2026-06-02, after integrating 151 agent-adjudicated
mechanistic links and fixing the positive-label filter (positives are now only
`treats` edges, so 4 inferred `associated_with` HYPOTHESIS edges that were
wrongly counted as approvals are excluded -- this is why the count is 44, not 48,
and the AUROC rose). This protocol removes direct Drug->Disease edges and
protein->disease bridge edges explicitly derived from known drug indications.
Because all visible Drug->Disease comparators are removed, Yoneda distance is not
active in this strict benchmark. The previous 0.9689 AUROC / 0.661 AUPRC display
is retired because an earlier Yoneda cache could see held-out labels.*

### Additional executable validations (2026-06-02)

| Validation | Current result |
|------------|----------------|
| Corrected LOOCV | AUROC 0.9674, AUPRC 0.5165, Hits@10 0.600 |
| Hetionet CtD external positives | AUROC 0.6436, AUPRC 0.0095, Hits@20 0.000 |
| Temporal holdout, approvals > 2013 | AUROC 0.9706, AUPRC 0.1938, Hits@20 0.167 |
| Disease holdout, diseases with >=2 labels | Mean AUROC 0.9378, mean AUPRC 0.6021 across 7 folds |

### Ranking calibration

{calibration_note}

The calibrated value shown in candidate details is a benchmark FDA-label rate
for the score bin. It is separate from strategy signal scores and is not a
clinical probability.

### Limitations

- **Research prototype**: Not a clinical decision support system
- **Oncology only**: 20 cancer types currently
- **Small graph**: {n_obj} objects vs 47k+ in published systems like Rephetio
- **Open-world negatives**: Unlabeled pairs are unknowns, not confirmed negatives
- **Citation attribution risk remains**: Provenance/source strings exist for every edge, but
  the audit found PMID-without-context, measured-tier mismatch, and quantitative
  support issues that need edge-level verification before wet-lab claims
- **AUROC is sensitive to graph expansion**: Adding PubMed co-mention edges
  (low confidence) changes AUROC depending on protocol and quality tier filter
- **External generalization is weak**: The Hetionet CtD check is much harder than
  internal holdouts and currently has low precision-at-top
- **Core value**: AUROC is useful, but the research value is the auditable
  mechanistic trail, source typing, validation status, and citation provenance

### Citation

Hawkins, J.R. (2026). KOMPOSOS-IV-PHARM: Categorical Drug Repurposing.
Apache 2.0 / Commercial dual license.
""")
