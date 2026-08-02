#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

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
BUNDLED_OPERADUM_ROOT = APP_ROOT / "vendor" / "operadum"
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
from validation.disease_specificity import build_score_matrix, specificity_ranking, hub_summary
from validation.nonobvious import (
    FAMILIARITY_CAP,
    _load_cache as _load_comention_cache,
    _save_cache as _save_comention_cache,
    find_candidates as find_nonobvious_candidates,
    normalize_drug_name,
    rank_nonobvious,
)
from validation.enrichment_funnel import build_funnel
from validation.trace_prediction import _build_provenance_index, trace_pair
# Shared with the reviewer packet on purpose: the Evidence card and the packet
# sent to an external reviewer must never be able to disagree about which paths
# are strongest or what a candidate is missing.
from validation.build_reviewer_packet import (
    best_chains as _packet_best_chains,
    missing_evidence_line as _packet_missing_line,
    pmids_from_edge as _packet_pmids,
)
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


# ── Evidence standing ────────────────────────────────────────────────

def _evidence_standing(chains, score, disease):
    """Classify what the evidence actually supports. Never a clinical statement.

    The roadmap asks every result to declare its standing rather than hand over a
    bare number, because a score without a standing invites the reader to supply
    their own interpretation - which is usually more confident than the evidence.

    Deliberately conservative: the ceiling is SUPPORTED_FOR_REVIEW, meaning
    "worth a human's time", and reaching it requires a DIRECTED terminal hop.
    Only 60 edges in the current graph qualify, so most candidates land on WEAK,
    and that is the honest answer rather than a failure of the classifier.

    A qualifying terminal hop must:
      - land on THE TARGET DISEASE, not some intermediate disease the chain
        happened to pass through;
      - originate from a protein, not a drug;
      - not be a `treats` edge.

    The first draft of this function enforced none of those, and graded
    Nivolumab -> Melanoma as SUPPORTED_FOR_REVIEW on the strength of
    `Nivolumab -treats-> RCC`. That is a different disease's FDA label being read
    as mechanistic support - exactly the label leakage the strict benchmark
    protocol exists to prevent. The Evidence card now also runs on a
    label-removed view, so those edges are not present at all; these checks are
    the belt to that view's braces.
    """
    if not chains:
        return "NOT_ASSESSED", (
            "No composed Drug->Protein->Disease chain exists. Any ranking for "
            "this pair rests on analogy, not on mechanism in this graph."
        )

    edges = [e for c in chains for e in c["edges"]]
    terminal = [
        e for e in edges
        if e["target"] == disease and e["target_type"] == "Disease"
    ]
    directed = [
        e for e in terminal
        if e["relation"] not in ("associated_with", "treats")
    ]
    has_strong_drug_target = any(
        e["target_type"] != "Disease" and e["evidence_tier"] in ("MEASURED", "ESTABLISHED")
        for e in edges
    )
    # The TERMINAL hop's own tier is the thing that matters most, and an earlier
    # version of this function ignored it. After the 2026-08-01 re-tier that
    # produced a self-contradicting card: Sorafenib -> Melanoma read
    # SUPPORTED_FOR_REVIEW while displaying a SPECULATIVE badge on its own
    # BRAF -> Melanoma terminal edge, because a strong ChEMBL drug->protein edge
    # elsewhere in the chain satisfied the check. Meanwhile Aspirin ->
    # Colorectal_Cancer - one of the best-supported cheap-drug findings in
    # oncology - read WEAK. Backwards in both directions.
    strong_terminal = [
        e for e in directed
        if e["evidence_tier"] in ("MEASURED", "ESTABLISHED")
    ]

    if strong_terminal and has_strong_drug_target:
        e = strong_terminal[0]
        return "SUPPORTED_FOR_REVIEW", (
            f"A directed terminal hop ({e['source']} -{e['relation']}-> "
            f"{e['target']}, tier {e['evidence_tier']}) sits on top of a measured "
            "or established drug-target edge. Worth a reviewer's time. This is "
            "not evidence of efficacy."
        )
    if directed and not strong_terminal:
        e = directed[0]
        return "WEAK", (
            f"The terminal hop {e['source']} -{e['relation']}-> {e['target']} is "
            f"directed but only tier {e['evidence_tier']}. The relation may well "
            "be true - several such edges are textbook biology - but the citation "
            "attached does not establish it. Check that edge first."
        )
    if directed:
        return "WEAK", (
            "There is a directed terminal hop, but no MEASURED or ESTABLISHED "
            "drug-target edge underneath it. The mechanism is asserted at only "
            "one end of the chain."
        )
    if not terminal:
        return "NOT_ASSESSED", (
            f"No chain here terminates at {disease.replace('_', ' ')} through a "
            "protein. The paths shown reach it only by hopping through other "
            "diseases, which is co-occurrence between diseases, not mechanism."
        )
    return "WEAK", (
        "Every terminal Protein->Disease hop here is `associated_with` - "
        "co-occurrence in the literature, not a mechanistic claim. This is the "
        "graph's weakest layer and its binding constraint."
    )


# ── Cache heavy loads ────────────────────────────────────────────────

@st.cache_resource(show_spinner="Enumerating unfilled horns (discovery surface)...")
def load_horn_candidates():
    """Unfilled inner horns per disease - the discovery surface.

    An unfilled horn is Drug -mech-> X -> Disease with NO `treats` edge. It is a
    repurposing hypothesis the graph has not been told the answer to.

    This exists because OPERADUM and PRONOIA both take a CANDIDATE LIST as input
    and both were fed `triage_disease` output, which ranks pairs the system has
    already ranked. Neither could surface anything the base triage missed. Giving
    them the horn list points the same machinery at the unanswered cases.

    Audited 2026-08-01: the saved top-50 worklist records 19 APPROVED rows plus
    one APPROVED_WRONG_MECHANISM row. Ten had been verified before the completed
    audit. These are missing local labels, not evidence of novel discovery.

    Uses the label-visible graph deliberately: `filled_treats` is exactly what
    decides whether a horn is unfilled, so the labels must be present to exclude
    the known indications. The candidate itself is by definition unlabelled.
    """
    from oracle.horns import inner_horns, best_fillers
    category, _ = load_full_typed_view(DB_PATH)
    horns = inner_horns(category, a_type="Drug", c_type="Disease")
    unfilled = sorted((h for h in best_fillers(horns).values() if not h.filled_treats),
                      key=lambda h: -h.composite)
    by_disease = {}
    for h in unfilled:
        by_disease.setdefault(h.c, []).append(h)
    return by_disease


def _horn_shortlist(disease, top_n):
    """(drug, target, composite, terminal_relation) for the top unfilled horns."""
    horns = load_horn_candidates().get(disease, [])
    seen, out = set(), []
    for h in horns:
        base = _nonobvious_normalize(h.a) if _nonobvious_normalize else h.a
        if base in seen:
            continue                      # collapse salt/hydrate duplicates
        seen.add(base)
        out.append((h.a, h.b, h.composite, h.g_name))
        if len(out) == top_n:
            break
    return out


try:
    from validation.nonobvious import normalize_drug_name as _nonobvious_normalize
except Exception:                                    # pragma: no cover
    _nonobvious_normalize = None


@st.cache_resource(show_spinner="Loading the strict (label-removed) graph...")
def load_strict_graph():
    """The graph with direct Drug->Disease labels removed.

    The Evidence card runs on this rather than on the default view, so the card
    shows what the system composes WITHOUT already being told the answer - the
    same protocol as the audited benchmark and the reviewer packet.

    On the default (labelled) view a drug's approval for a *different* disease
    appears as a Drug->Disease edge inside composed chains, which reads as
    evidence and is not. Removing the labels also removes the indication-derived
    bridge edges, which is what `remove_direct_labels` is for.
    """
    category, _ = load_full_typed_view(DB_PATH, remove_direct_labels=True)
    return {"category": category, "strategies": make_strategies(category)}


@st.cache_resource(show_spinner="Scoring all pairs for the enrichment funnel...")
def load_funnel():
    """Strict-protocol enrichment funnel, on the CORE 78-drug cohort.

    Deliberately pinned to `core` so the funnel stays comparable to the audited
    numbers. The rest of the app (graph stats, Non-obvious candidates) ranks over
    all 757 drugs, so this page states its cohort explicitly - otherwise a reader
    sees "757 drugs" in the sidebar and a 1,560-pair funnel and cannot reconcile them.
    """
    return build_funnel(DB_PATH, cohort="core")


@st.cache_resource(show_spinner="Scoring all Drug x Disease pairs for specificity...")
def load_score_matrix():
    """Full score matrix for the disease-specificity (hub-demotion) view."""
    return build_score_matrix(DB_PATH)


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

_modes = ["Evidence card", "Disease-first", "Disease-specific",
          "Non-obvious candidates", "Drug-first", "Pair detail", "Search speedup"]
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

# SPECULATIVE was missing here, so after the 2026-08-01 re-tier the sidebar
# silently dropped 167 edges from its own count. The weakest tier is exactly the
# one a reader most needs to see.
_tier_order = ["MEASURED", "ESTABLISHED", "INFERRED", "HYPOTHESIS", "SPECULATIVE"]
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
    f"**Graph (scored)**: {g['n_objects']} objects, {g['n_morphisms']} edges\n\n"
    f"**Local benchmark positives**: {g['n_positives']} curated `treats` labels\n\n"
    f"**Self-check**: {g['check_recovered']}/{g['check_total']} recoverable\n\n"
    f"**Evidence tiers**: {_tier_str}\n\n"
    f"**Sources** (edges may cite several): {_source_str}\n\n"
    f"**Source fields**: {g['provenance_rows']}/{g['n_morphisms']} edges, "
    f"{g['pmid_count']} PMID IDs\n\n"
    f"**Quantitative evidence**: {g['abpp_measurements']} experimental ABPP "
    f"IC50/engagement measurements"
)
st.sidebar.caption(
    "The edge count is the SCORED graph. The database currently retains 424 "
    "ESMC protein-embedding similarity-transfer edges (tagged "
    "EMBEDDING-INFERRED), but scoring excludes them. A 2026-07-21 ablation of "
    "the then-current 422-edge layer found that removing it improved ranking. "
    "That is why these edges appear under Sources but not in "
    "the edge total."
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
            f"self-check {g['check_recovered']}/{g['check_total']} local positive labels recoverable",
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

    _RESEARCH_SUPPORTED_PAIRS = {
        ("Sotorasib", "Pancreatic_Cancer"):
            "External check found pancreatic KRAS G12C publication/trial context; use as research-review evidence, not a general treatment claim.",
        ("Adagrasib", "Pancreatic_Cancer"):
            "External check found pancreatic KRAS G12C trial context; use as research-review evidence, not a general treatment claim.",
        ("Adagrasib", "Colorectal_Cancer"):
            "External check found KRAS G12C colorectal approval/trial support; likely local label-table gap or underrepresented combination context.",
        ("Sotorasib", "Colorectal_Cancer"):
            "External check found KRAS G12C colorectal approval/trial support; likely local label-table gap or underrepresented combination context.",
        ("Trastuzumab_deruxtecan", "Breast_Cancer"):
            "External check found strong T-DXd breast cancer support; likely local label-table curation issue.",
        ("Lorlatinib", "NSCLC"):
            "External check found ALK/ROS1 NSCLC support; likely local label-table curation issue or underrepresented indication context.",
        ("Brigatinib", "NSCLC"):
            "External check found ALK-positive NSCLC support; likely local label-table curation issue or underrepresented indication context.",
    }

    _CALIBRATION_PAIRS = {
        ("Afatinib", "Breast_Cancer"):
            "Mechanism-rich ERBB2/EGFR trail, but external check was clinically mixed; useful for v3 indication-context penalties.",
        ("Cetuximab", "NSCLC"):
            "Mechanism-rich EGFR/NSCLC trail, but not enough as a standalone broad treatment claim; useful for v3 calibration.",
        ("Lapatinib", "NSCLC"):
            "Mechanism-rich EGFR/ERBB2 trail with weak/older clinical signal; useful for v3 calibration.",
    }

    _HIGH_EVIDENCE_TIERS = {"MEASURED", "ESTABLISHED"}

    def _pronoia_pair(report) -> tuple[str, str]:
        drug = report.candidate.metadata.get("drug", report.candidate.name)
        disease = report.candidate.metadata.get("disease", report.candidate.target)
        return str(drug), str(disease)

    def _pronoia_label(report) -> str:
        drug, disease = _pronoia_pair(report)
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

    def _has_established_inference(report) -> bool:
        for item in tuple(getattr(report.evidence, "items", ()) or ()):
            if item.source not in {"komposos_mechanism", "komposos_path"}:
                continue
            tiers = tuple(t.upper() for t in _evidence_tiers(item))
            if tiers and all(tier in _HIGH_EVIDENCE_TIERS for tier in tiers):
                return True
        return False

    def _relationship_status(report) -> tuple[str, str]:
        pair = _pronoia_pair(report)
        local_label = _pronoia_label(report)
        if local_label == "APPROVED":
            return (
                "Known label",
                "This drug-disease pair is positive in the local `treats` benchmark. PRONOIA may still be using hidden-label mechanism evidence to recover it.",
            )
        if pair in _CALIBRATION_PAIRS:
            return "Needs calibration / possible overreach", _CALIBRATION_PAIRS[pair]
        if pair in _RESEARCH_SUPPORTED_PAIRS:
            return "Research/trial-supported", _RESEARCH_SUPPORTED_PAIRS[pair]
        if _has_established_inference(report):
            return (
                "Inferred from established path",
                "No local positive label was visible, but the strongest mechanism/path evidence is built from measured or established graph edges.",
            )
        return (
            "Needs calibration / possible overreach",
            "No local positive label and no current external-review tag; treat as an inferred graph lead needing expert review.",
        )

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
            "## Relationship Status Legend",
            "",
            "- Known label: positive in the local PHARM `treats` benchmark.",
            "- Inferred from established path: not locally labeled positive, but supported by measured/established mechanism-path edges.",
            "- Research/trial-supported: externally checked lead with public research, trial, approval, or curation support.",
            "- Needs calibration / possible overreach: mechanism-rich signal that needs indication context, resistance context, or expert rejection.",
            "",
            "## Ranked Prediction Audit",
            "",
            "| Rank | Candidate | Local label | Relationship status | Decision | PRONOIA score | Grounding | Base strength | Raw MDL gain | Evidence | PMIDs |",
            "|---:|---|---|---|---|---:|---:|---:|---:|---|---|",
        ]
        for rank, report in enumerate(slate.reports, start=1):
            top = _top_pronoia_evidence(report)
            top_claim = top.claim if top is not None else "-"
            top_pmids = _collect_pmids(top.metadata if top is not None else {})
            status, _reason = _relationship_status(report)
            out.append(
                f"| {rank} | {report.candidate.name} -> {report.candidate.target} | "
                f"{_pronoia_label(report)} | {status} | {report.decision} | "
                f"{report.score:.2f} | {report.metrics.get('grounding', 0.0):.3f} | "
                f"{report.metrics.get('pharm_base_strength', 0.0):.3f} | "
                f"{report.metrics.get('raw_mdl_gain_bits', 0.0):.1f} | "
                f"{top_claim} | {_pmid_links(top_pmids)} |"
            )
        out += ["", "## Per-Candidate Evidence", ""]
        for report in slate.reports:
            status, reason = _relationship_status(report)
            out += [
                f"### {report.candidate.name} -> {report.candidate.target}",
                "",
                f"- Relationship status: {status}",
                f"- Status rationale: {reason}",
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
        status, reason = _relationship_status(report)
        st.info(f"**Relationship status:** {status}. {reason}")
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
            st.caption(
                "Rows are sorted strongest-first. A `-` in Tiers / PMIDs / "
                "Provenance means that evidence item has no recorded citation at "
                "that level yet (commonly the weaker disease-association items) -- "
                "it is thin provenance, not a truncated trail."
            )


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
            "Local label": r["label"],
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


def _honest_status(status: str) -> str:
    """Turn bare placeholder validation_status values into honest phrases.

    The raw defaults (`unclassified`, empty) read like a truncated/missing field;
    they actually mean 'this edge has no edge-level citation audit yet', which is
    a known open task — say so explicitly instead of showing a cryptic token.
    """
    s = (status or "").strip().lower()
    return {
        "": "no edge-level validation yet (open audit task)",
        "unclassified": "no edge-level validation yet (open audit task)",
        "citation_unverified": "citation present, relation not yet verified",
        "established_source": "established source",
        "database_record": "database record",
        "citation_verified": "citation-verified relation",
    }.get(s, status)


def _honest_source_type(source_type: str) -> str:
    """Turn the `unknown_or_internal` placeholder into an honest phrase."""
    s = (source_type or "").strip().lower()
    return {
        "": "internal / derived (no external source tag)",
        "unknown_or_internal": "internal / derived (no external source tag)",
    }.get(s, source_type)


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
        f"&nbsp; :{label_color}[local label: {entry['label']}]"
    )
    st.caption(
        "Local NOT_APPROVED means absent from this repository's 44 curated "
        "treats labels. It does not establish regulatory, trial, or scientific status."
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
                       help="Edges classified as experimental or quantitative; inspect the source record")
        cols[1].metric("✅ Established", tier_counts.get("ESTABLISHED", 0),
                       help="Edges classified from regulatory or curated sources; inspect the exact record")
        cols[2].metric("💡 Inferred", tier_counts.get("INFERRED", 0),
                       help="STRING PPI, embedding-inferred edges (computed; "
                            "ESMC similarity-transfer edges are excluded from scoring)")
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
                "MEASURED": "Classified as experimental or quantitative; inspect the source record",
                "ESTABLISHED": "Classified from regulatory or curated sources; inspect the exact record",
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
        st.caption(
            "Reading note: the final Protein \u2192 **Disease** hop is the "
            "least-verified layer in the graph -- those links are often "
            "literature co-mentions rather than edge-verified relations, so a "
            "sparse label on the *last* hop is expected, not a missing value."
        )

        for i, chain in enumerate(entry["chains"], 1):
            parts_p = [chain["edges"][0]["source"]]
            for edge in chain["edges"]:
                parts_p.append(f"\u2192 {edge['target']}")
            path_str = " ".join(parts_p)

            with st.expander(f"Path {i}: {path_str}"):
                n_edges = len(chain["edges"])
                for edge_idx, edge in enumerate(chain["edges"]):
                    conf = edge["confidence"]
                    prov = edge.get("provenance", "unknown")
                    src_type = _provenance_source_type(prov)
                    color = _confidence_color(conf)
                    is_terminal = (
                        edge_idx == n_edges - 1
                        or edge.get("target") == entry["disease"]
                    )
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
                    terminal_tag = " &nbsp;:gray[(disease link — weakest layer)]" if is_terminal else ""
                    status_txt = _honest_status(edge.get("validation_status", ""))
                    src_type_txt = _honest_source_type(edge.get("source_type", ""))
                    st.markdown(
                        f"- **{edge['source']}** -{edge['relation']}-> "
                        f"**{edge['target']}**{terminal_tag} "
                        f"(:{color}[conf: {conf:.2f}], {src_type} | {prov_display})"
                        f"  \n  source: {src_type_txt}; "
                        f"status: {status_txt}"
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


# ── Disease-specific (hub-demotion) ──────────────────────────────────

elif mode == "Disease-specific":
    st.title("Disease-specific candidates")
    st.caption(
        "Promiscuous multi-kinase inhibitors (Imatinib, Sunitinib, ...) top "
        "almost every disease, so the raw ranking keeps surfacing the same "
        "pan-cancer hubs you already know. This view re-ranks by LIFT = raw "
        "score minus the drug's mean across all diseases, demoting the hubs so "
        "the genuinely disease-specific candidates surface."
    )

    disease = st.selectbox("Select disease", g["diseases"])
    top_n = st.slider("Top N", 5, 30, 12)

    if st.button("Rank by specificity", type="primary"):
        matrix = load_score_matrix()
        rows = specificity_ranking(matrix, disease, top_n=top_n)

        st.subheader(f"Disease-specific lift ranking — {disease}")
        st.caption(
            "Lift is the disease-specific signal: how much more this drug prefers "
            "this disease than its own average. 'Hub' shows how many of the "
            f"{len(matrix.diseases)} diseases the drug tops (high = generic). "
            "Raw score is the unadjusted model score, shown for comparison."
        )
        st.dataframe(
            [{
                "Rank": i,
                "Drug": r.drug,
                "Lift": round(r.lift, 3),
                "Raw score": round(r.raw_score, 3),
                "Drug avg (all diseases)": round(r.drug_mean, 3),
                "Hub (tops N diseases)": f"{r.hub_count}/{len(matrix.diseases)}",
                "Local treats label": "TREATS" if r.is_positive else "-",
            } for i, r in enumerate(rows, start=1)],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Pan-cancer hubs being demoted")
        st.caption(
            "These drugs top the most disease lists; the specificity view pushes "
            "them down so they no longer crowd out disease-specific signal."
        )
        st.dataframe(
            [{
                "Drug": drug,
                "Tops N diseases": f"{count}/{len(matrix.diseases)}",
            } for drug, count in hub_summary(matrix)],
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "This is a presentation/triage lens — it does NOT change the scoring "
            "model or any AUROC. A positive lift means 'more specific to this "
            "disease than the drug's baseline', not 'more likely to work'. Use it "
            "to find candidates the raw ranking buries under generic hubs."
        )


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
    source = st.radio(
        "Candidate source",
        ["KOMPOSOS triage (re-rank known ranking)",
         "Unfilled horns (discovery surface)"],
        help=("Triage re-ranks pairs the system already ranked. Unfilled horns are "
              "Drug->target->Disease mechanisms with no local treats label - the "
              "hypotheses for which this graph has not been given a positive label."),
    )
    shortlist_n = st.slider("Shortlist size", 3, 25, 8)
    profile_name = st.selectbox("Decision profile", list(OPERADUM_PROFILES))
    require_evidence = st.checkbox(
        "Require strong evidence (>= 0.8) for the next action", value=True
    )

    if st.button("Rank candidates", type="primary"):
        use_horns = source.startswith("Unfilled")
        with st.spinner("Building shortlist -> OPERADUM decision ranking..."):
            if use_horns:
                horn_rows = _horn_shortlist(disease, shortlist_n)
                candidates = [Candidate(drug=d, target=t) for d, t, _, _ in horn_rows]
            else:
                triaged = triage_disease(
                    g["category"], g["strategies"], disease, g["positives"],
                    g["provenance_index"], top_n=shortlist_n,
                )
                candidates = [
                    Candidate(drug=r["drug"], target=_target_from_result(r))
                    for r in triaged
                ]
        if use_horns:
            if not candidates:
                st.warning(f"No unfilled horns for {disease.replace('_',' ')}.")
                st.stop()
            st.info(
                f"Ranking **{len(candidates)} unfilled horns** — mechanisms with no "
                "local treats label for this disease. Each is a hypothesis, not a "
                "finding. Note the known failure mode: the graph records no failed "
                "trials, so it will keep proposing things that were tried and did "
                "not work (several EGFR inhibitors in glioblastoma are clear examples)."
            )
            st.dataframe(
                [{"Drug": d, "via target": t, "Composite": round(c, 3),
                  "Terminal hop": "directed" if rel != "associated_with" else "co-occurrence"}
                 for d, t, c, rel in horn_rows],
                use_container_width=True, hide_index=True,
            )
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
    with st.expander("Relationship status legend"):
        st.markdown("""
- **Known label**: the pair is positive in the local PHARM `treats` benchmark.
- **Inferred from established path**: the pair is not locally labeled positive, but PRONOIA found measured/established mechanism-path evidence.
- **Research/trial-supported**: the pair matched the external validation leads already checked against public research, trials, approvals, or curation context.
- **Needs calibration / possible overreach**: the graph mechanism is real enough to review, but the treatment interpretation needs indication/resistance context or expert rejection.
""")

    disease = st.selectbox("Select disease", g["diseases"])
    pronoia_source = st.radio(
        "Candidate source",
        ["KOMPOSOS triage (re-rank known ranking)",
         "Unfilled horns (discovery surface)"],
        help=("Auditing unfilled horns asks the question PRONOIA is actually for: "
              "is this UNANSWERED hypothesis grounded, or does its rank ride on "
              "ungrounded claims?"),
        key="pronoia_source",
    )
    shortlist_n = st.slider("Shortlist size", 3, 30, 12)
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
        use_horns = pronoia_source.startswith("Unfilled")
        with st.spinner("Building shortlist -> PRONOIA prediction audit..."):
            if use_horns:
                horn_rows = _horn_shortlist(disease, shortlist_n)
                candidates = [pharm_candidate(d, disease) for d, _, _, _ in horn_rows]
            else:
                triaged = triage_disease(
                    g["category"], g["strategies"], disease, g["positives"],
                    g["provenance_index"], top_n=shortlist_n,
                )
                candidates = [pharm_candidate(r["drug"], disease) for r in triaged]
        if use_horns and not candidates:
            st.warning(f"No unfilled horns for {disease.replace('_',' ')}.")
            st.stop()
        if use_horns:
            st.info(
                f"Auditing **{len(candidates)} unfilled horns** — hypotheses with no "
                "local treats label. Note that when the source is triage, the "
                "shortlist is chosen on the label-visible graph even with the "
                "hide-labels box ticked; that box only affects PRONOIA's evidence, "
                "not which candidates were selected. Horn candidates are unlabelled "
                "by construction, so that asymmetry does not apply here."
            )
        st.caption(
            "PRONOIA's `grounding` is a compression statistic. Measured 2026-08-01 "
            "on this graph's proof sentences, it separates real from scrambled "
            "pairings only because the target name literally appears in the "
            "sentence (120/120 real vs 4/120 scrambled); with that overlap removed "
            "there were zero comparable cases left. Read grounding as lexical "
            "overlap, not as biological support."
        )
        with st.spinner("PRONOIA prediction audit..."):
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
            status, reason = _relationship_status(report)
            rows.append({
                "Rank": rank,
                "Drug": report.candidate.name,
                "Disease": report.candidate.target,
                "Local Label": _pronoia_label(report),
                "Relationship Status": status,
                "Decision": report.decision,
                "PRONOIA Score": round(float(report.score), 2),
                "Grounding": round(float(report.metrics.get("grounding", 0.0)), 3),
                "Base Strength": round(float(report.metrics.get("pharm_base_strength", 0.0)), 3),
                "Raw MDL Gain": round(float(report.metrics.get("raw_mdl_gain_bits", 0.0)), 1),
                "Top Evidence": top.claim if top is not None else "-",
                "Status Rationale": reason,
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

elif mode == "Evidence card":
    st.title("Evidence card")
    st.caption(
        "One candidate, its three strongest paths, and what it does not have. "
        "Runs on the **strict label-removed graph**, so the card cannot see the "
        "local `treats` label it is being asked to recover — the same protocol as the "
        "audited benchmark. **Pair detail** shows every chain on the full graph."
    )

    col1, col2 = st.columns(2)
    _ec_drug = col1.selectbox("Drug", g["drugs"], key="ec_drug")
    _ec_disease = col2.selectbox("Disease", g["diseases"], key="ec_disease")

    if st.button("Build card", type="primary"):
        with st.spinner("Composing evidence..."):
            # Strict, label-removed view: the card must not be able to see the
            # answer it is being asked to justify.
            _strict = load_strict_graph()
            _ec_detail = score_pair_detailed(
                _strict["strategies"], _ec_drug, _ec_disease)
            _ec_trace = trace_pair(
                _strict["category"], _ec_drug, _ec_disease,
                _strict["strategies"], g["provenance_index"],
            )
            # Same functions the reviewer packet uses, so the screen and the
            # packet cannot drift apart.
            _ec_chains = _packet_best_chains(_ec_trace, k=3)
            _ec_missing = _packet_missing_line(_ec_chains)
            _ec_standing, _ec_why = _evidence_standing(
                _ec_chains, _ec_detail["score"], _ec_disease)

        _ec_label = _label_for_pair((_ec_drug, _ec_disease), g["positives"])

        st.markdown(f"## {_ec_drug} → {_ec_disease.replace('_', ' ')}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Ranking score", f"{_ec_detail['score']:.3f}")
        c2.metric("Composed chains", _ec_trace["n_chains"])
        c3.metric(
            "Local benchmark label",
            "recorded" if _ec_label == "APPROVED" else "not recorded",
        )

        _standing_render = {
            "SUPPORTED_FOR_REVIEW": st.success,
            "WEAK": st.warning,
            "NOT_ASSESSED": st.error,
        }[_ec_standing]
        _standing_render(f"**{_ec_standing}** — {_ec_why}")

        st.caption(
            "The score is a ranking signal on a curated graph. It is **not** a "
            "probability, not an efficacy estimate, and not a clinical "
            "recommendation."
        )

        if not _ec_chains:
            st.info(
                "No composed Drug→Protein→Disease chain exists for this pair. "
                "Anything shown elsewhere for it rests on analogy, not mechanism."
            )
        for _i, _chain in enumerate(_ec_chains, 1):
            _edges = _chain["edges"]
            _arrow = " → ".join(
                [_edges[0]["source"]] + [e["target"] for e in _edges]
            )
            _via_disease = any(
                e["target_type"] == "Disease" and e is not _edges[-1] for e in _edges
            )
            st.markdown(f"**Path {_i}** · `{_arrow}`")
            if _via_disease:
                st.caption(
                    "⚠ Routes through another disease — that is co-occurrence, "
                    "not a mechanistic claim."
                )
            st.table([
                {
                    "edge": f"{e['source']} → {e['target']}",
                    "relation": e["relation"],
                    "tier": e["evidence_tier"],
                    "PMID": ", ".join(_packet_pmids(e)[:2]) or "—",
                    "conf": f"{e['confidence']:.2f}",
                }
                for e in _edges
            ])

        st.markdown("#### What this candidate does not have")
        st.warning(_ec_missing)

        st.markdown("#### How to read this")
        st.markdown(
            "- A **PMID on a terminal Protein→Disease edge is not validation.** "
            "Those citations were gathered *after* the edge was proposed, and a "
            "permutation control found the step carries no measurable signal "
            "(12.5% vs 7.5% on scrambled pairs, p=0.28). Read it as *\"not "
            "absurd, start here\"*.\n"
            "- **Drug→Protein citations are unaffected** — ChEMBL and FDA labels "
            "are independently derived.\n"
            "- An **`associated_with`** terminal hop is co-occurrence. Only 60 "
            "edges in the whole graph are directed `driver_of`.\n"
            "- Absence of a label is **not** a negative. See **About**."
        )


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


# ── Search speedup (enrichment funnel) ───────────────────────────────

elif mode == "Search speedup":
    st.title("Search speedup")
    st.caption(
        "How much of the candidate search the ranker lets you skip. Strict "
        "protocol: each drug-disease label is removed from the graph before "
        "scoring, so the ranker cannot read the answer it is graded on."
    )

    st.info(
        "**Cohort: the 78 curated core drugs** (1,560 pairs), not the "
        "full 757-drug graph shown in the sidebar. The funnel is pinned to this "
        "cohort so it stays comparable to the audited numbers. Expanding to 757 "
        "adds ~13,500 mostly-unscoreable pairs while the positive count stays at 44, "
        "which inflates enrichment without meaning anything. See HONEST_VALUE.md."
    )

    funnel = load_funnel()

    c1, c2, c3 = st.columns(3)
    c1.metric("Search space", f"{funnel.n_pairs} pairs")
    c2.metric("Known positives", f"{funnel.n_positives}")
    c3.metric("Base hit rate", f"{funnel.base_rate * 100:.2f}%")

    st.subheader("Screen the top X%, catch how many real hits")
    st.table({
        "Screen top": [f"{r.fraction * 100:.0f}%" for r in funnel.rows],
        "Pairs": [r.n_screened for r in funnel.rows],
        "Hits caught": [
            f"{r.captured}/{funnel.n_positives} ({r.capture_rate * 100:.0f}%)"
            for r in funnel.rows
        ],
        "Enrichment vs random": [f"{r.enrichment:.1f}x" for r in funnel.rows],
    })

    st.subheader("Or: how little you must screen to catch K% of hits")
    for t in funnel.capture_targets:
        st.markdown(
            f"- Catch **{t.target_rate * 100:.0f}%** of known hits by screening "
            f"**{t.fraction_screened * 100:.0f}%** of the list "
            f"(**skip {t.skip_fraction * 100:.0f}%** of the search)."
        )

    st.info(
        "Measured on **known** positives (recovery), so it quantifies search "
        "acceleration on the curated graph — not a novel-discovery hit rate. "
        "What happens on genuinely novel pairs is **currently unmeasured**: the "
        "external check is not reproducible and the temporal holdout is leaky "
        "and counts approved drugs as negatives. See **About** for why no "
        "precision claim is made in either direction."
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
| 0.90 - 1.00 | Regulatory records, ChEMBL records | High-priority source class; confidence is not a probability | **Inspect** the exact record and indication context |
| 0.70 - 0.89 | ChEMBL binding, KEGG pathways, curated interactions | Curated or database evidence for this relationship | **Inspect** the exact evidence and direction |
| 0.50 - 0.69 | STRING PPI, established mechanisms (ESM2/ESMC similarity-transfer edges are now EXCLUDED from scoring -- see note) | Computational or curated evidence, not direct measurement | **Investigate** -- check the cited paper |
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
**Why confidence-weighted?** A single high-confidence path (confidence 0.90)
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

If the drug looks structurally similar to a locally labelled treatment for this
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
4. Report the observed local `treats`-label rate in each bin, with monotone bin smoothing.

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
3. **The terminal hop is the weakest**: The final Protein -> Disease link of a
   chain is the least-verified layer (often a literature co-mention, not an
   edge-verified relation). A sparse label there is expected -- scrutinize it.
4. **IC50 data**: If the binding_evidence strategy voted AND there are
   ABPP IC50 values, those are experimental measurements -- the strongest
   evidence type in this system.
5. **Cited papers**: Every edge has a provenance/source string, but not every
   source is an edge-specific PMID. Follow PMID links where present and verify
   that the paper supports the exact edge.

**Watch for the hub-drug bias:** promiscuous multi-kinase inhibitors (Imatinib
tops 14/20 diseases, Sunitinib 10/20) float to the top of *most* disease lists,
so a high rank for one of them is weak disease-specific evidence -- it's partly
real pan-cancer biology, partly a promiscuity bias. Use the **Disease-specific**
view to demote the hubs and surface candidates particular to your disease.

**What this system does NOT do:**

- It does not replace clinical judgment
- It does not predict safety, toxicity, or pharmacokinetics
- It does not account for patient-specific factors
- It does not discover novel targets; it accelerates and explains a search over
  pharmacology already in the graph. Top-of-list precision on genuinely novel
  pairs is **not currently measurable** — the external check is not reproducible
  and the temporal holdout counts approved drugs as negatives (see **About**).
- AUROC of 0.9763 on the current strict 44-positive benchmark does not guarantee real-world
  performance
- The system surfaces auditable hypotheses from existing graph evidence; it does
  not by itself validate new clinical knowledge

_See **HONEST_VALUE.md** in the repo root for the full conservative assessment._
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

**Relationship status** separates the final pair from the evidence trail:
`Known label` means the pair is already positive in the local benchmark;
`Inferred from established path` means trusted graph edges imply a locally
unlabeled pair; `Research/trial-supported` means the lead matched the external
validation packet; and `Needs calibration / possible overreach` marks mechanism
signals that need more indication context.

**Honest limit:** PRONOIA v2 is an audit and expert-review tool. It is not a
clinical probability, and v3 still needs contradiction/residual and indication
context penalties. Any PRONOIA v2 AUROC (e.g. ~0.98 in the presentation packet)
is an **in-graph hidden-label** benchmark on the same 44 positives as KOMPOSOS,
not an external test -- it is not evidence of better generalization to novel
pairs. External generalization is **unmeasured for both**: the Hetionet check is
not reproducible (its inputs are absent from the repository) and the temporal
holdout is leaky. The old ~0.64 figure has been retired, not refreshed.
""")


elif mode == "Non-obvious candidates":
    st.title("Non-obvious candidates")
    st.caption(
        "Ranking by score alone surfaces what everyone already knows — the top of "
        "that list is pan-cancer kinase hubs whose evidence trail is short, famous, "
        "and adds nothing to your argument. This view ranks on two axes instead: "
        "**support** (strength of a real Drug→Protein→Disease chain) × **novelty** "
        "(how little PubMed already co-mentions the pair). The interesting quadrant "
        "is a chain you can defend edge-by-edge about a pair nobody has written up."
    )

    st.warning(
        "**Novelty is measured outside the graph.** Co-mention counts come from live "
        "PubMed queries, because deriving novelty from the same graph that produced "
        "the ranking would be circular. First run for a disease is slow (NCBI allows "
        "3 requests/sec); results are cached afterwards."
    )

    nb_disease = st.selectbox("Select disease", g["diseases"], key="nb_disease")
    nb_c1, nb_c2, nb_c3 = st.columns(3)
    nb_top = nb_c1.slider("Show top", 5, 30, 12, key="nb_top")
    nb_shortlist = nb_c2.slider(
        "PubMed lookups", 10, 60, 30, key="nb_shortlist",
        help="Pairs sent to PubMed per run. Higher = slower first run, wider search.",
    )
    nb_min_support = nb_c3.slider(
        "Min support", 0.0, 1.0, 0.5, 0.05, key="nb_min_support",
        help="Discard chains weaker than this before spending a PubMed lookup.",
    )
    nb_mech_only = st.checkbox(
        "Mechanistic terminal hop only (exclude `associated_with`)",
        value=False, key="nb_mech_only",
        help="`associated_with` is co-occurrence, not a mechanism. Tick this to see "
             "only chains that reach the disease through a directed relation.",
    )

    if st.button("Find non-obvious candidates", type="primary"):
        with st.spinner(f"Scoring chains and querying PubMed for {nb_disease}..."):
            nb_cache = _load_comention_cache()
            try:
                nb_rows = find_nonobvious_candidates(
                    nb_disease, g["category"], g["strategies"], g["positives"],
                    g["provenance_index"], sorted(g["drugs"]),
                    nb_min_support, nb_shortlist,
                )
                nb_rows = rank_nonobvious(nb_rows, nb_cache, offline=False)
            finally:
                _save_comention_cache(nb_cache)

        if nb_mech_only:
            nb_rows = [r for r in nb_rows if r["terminal_is_directed"]]

        if not nb_rows:
            st.info(
                "No candidates cleared the filters. Lower **Min support**, or untick "
                "the mechanistic-only box — for most diseases the terminal "
                "Protein→Disease hop is `associated_with`."
            )
        else:
            st.subheader(f"Ranked by support × novelty — {nb_disease}")
            st.dataframe(
                [{
                    "Rank": i,
                    "Drug": r["drug"],
                    "Support": r["support"],
                    "PubMed co-mentions": r["comentions"],
                    "Novelty": r["novelty"],
                    "Non-obvious score": r["nonobvious"],
                    "Terminal hop": "mechanistic" if r["terminal_is_directed"] else "association",
                    "Weakest hop": r["weakest_hop"],
                    "Cited edges": r["cited_edges"],
                } for i, r in enumerate(nb_rows[:nb_top], start=1)],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                f"Novelty = 1 − log(co-mentions)/log({FAMILIARITY_CAP}), so a textbook "
                "pair scores ~0 and an unwritten one scores ~1."
            )

            st.subheader("Audit trail")
            st.caption(
                "The score IS the evidence — every hop below is an edge you can reject "
                "by hand. Check the terminal Protein→Disease hop first; it is the "
                "weakest layer in this graph."
            )
            st.warning(
                "**A PMID on the terminal Protein→Disease hop is not validation.** Those "
                "citations were found *after* the edge was proposed, and a permutation "
                "control shows randomly-paired proteins and diseases ground at a "
                "statistically indistinguishable rate (7.5% vs 12.5%, p=0.28). Read them "
                "as *\"this is not absurd, start reading here\"* — not as confirmation. "
                "The Drug→Protein hops (ChEMBL, FDA) are independently derived and do not "
                "carry this caveat."
            )
            for r in nb_rows[:nb_top]:
                flag = "" if r["terminal_is_directed"] else "  ⚠ association-only terminal hop"
                with st.expander(
                    f"{r['drug']} → {r['disease']}  ·  non-obvious {r['nonobvious']}  "
                    f"·  {r['comentions']} PubMed co-mentions{flag}"
                ):
                    if normalize_drug_name(r["drug"]) != r["drug"]:
                        st.caption(
                            f"PubMed queried as **{normalize_drug_name(r['drug'])}** "
                            "(salt/hydrate form stripped)."
                        )
                    for i, edge in enumerate(r["chain"]["edges"], start=1):
                        prov = edge.get("provenance") or "unknown"
                        prov_md = re.sub(
                            r"PMID:?\s*(\d+)",
                            lambda m: f"[PMID:{m.group(1)}](https://pubmed.ncbi.nlm.nih.gov/{m.group(1)})",
                            prov,
                        )
                        quant = ""
                        if edge.get("quantitative_value") is not None:
                            quant = f" · **{edge['quantitative_value']} {edge.get('value_unit') or ''}**"
                        st.markdown(
                            f"{i}. `{edge['source']}` —**{edge['relation']}**→ "
                            f"`{edge['target']}` ({edge.get('target_type','?')})  \n"
                            f"    confidence {edge.get('confidence')} · tier "
                            f"{edge.get('evidence_tier')} · {prov_md}{quant}"
                        )
                    st.markdown(
                        f"[Search PubMed for this pair]"
                        f"(https://pubmed.ncbi.nlm.nih.gov/?term="
                        f"%22{normalize_drug_name(r['drug']).replace(' ', '+')}%22"
                        f"+AND+%22{r['disease'].replace('_', '+')}%22)"
                    )

            st.error(
                "**Absence of literature is not evidence of efficacy.** A low "
                "co-mention count can mean genuinely unexplored, tried-and-never-"
                "published, or an ambiguous drug name. This is a triage queue for a "
                "human to work through, not a prediction that anything will work."
            )


elif mode == "About":
    st.title("About KOMPOSOS-IV-PHARM")

    n_drugs = len(g["drugs"])
    n_diseases = len(g["diseases"])
    n_obj = g["n_objects"]
    n_mor = g["n_morphisms"]
    n_pos = g["n_positives"]

    st.info(
        "For a deliberately conservative, self-critical account of what this "
        "system is and is not worth, read **HONEST_VALUE.md** in the repo root."
    )

    st.markdown(f"""
KOMPOSOS-IV-PHARM is a **categorical AI runtime** for drug repurposing. In
practice the ranking is driven mostly by **confidence-weighted mechanistic path
composition** (Drug -> Protein -> Disease) plus a structural-similarity bonus;
the category-theoretic layer (Kan extensions, Yoneda lemma, topos logic,
fibrations) is the organizing framework around that core, not the main source of
the measured performance. It **prioritizes and explains** existing drugs as
auditable hypotheses for disease pairs absent from its local label set -- it does not
predict that a drug will actually work.

### How It Works

1. **Knowledge Graph**: {n_drugs} drugs, {n_obj - n_drugs - n_diseases} proteins, \
{n_diseases} diseases, {n_mor} edges ({g['provenance_rows']} provenance/source strings, {g['pmid_count']} PMID identifiers, {g['quantitative_edges']} graph edges with structured quantitative fields; ABPP measurements are loaded separately)
2. **Live triage strategy profile**: 8 configured strategy modules
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
| AUROC | 0.9763 |
| AUROC, scored pairs only | **0.9609** |
| AUPRC | 0.5920 |
| precision@5 | 1.000 |
| precision@10 | 0.700 |
| precision@20 | 0.700 |
| Coverage | 962 of 1,560 pairs scored; 598 abstentions |
| Strategy profile | 7 active modules; Yoneda distance excluded because no Drug->Disease comparators remain |
| Positives | 44 `treats` labels (43 oncology + 1 Metformin/Type2_Diabetes) |
| Strongest baseline (common_neighbor) | AUROC 0.7483 |
| Margin over strongest baseline | +0.2280 |
| PMID identifiers in DB | {g['pmid_count']} |

**Two things this table used to get wrong, corrected 2026-07-31.**
*(1) The metric the code calls "Hits@k" is `hits / min(positives, k)` — that is
**precision@k**, which is why it falls from k=5 to k=10; a real Hits@k cannot.
(2) The 598 abstentions are scored 0.0 and sit inside the headline AUROC. All of
them are negatives, so restricting to the 962 actually-scored pairs gives AUROC
**0.9609**. AUPRC is unaffected. Roughly 0.015 of the headline is coverage rather
than ranking skill.*

**Cohort: `core` (78 curated drugs, 1,560 pairs).** Quote this number, not the
757-drug figure. On the full cohort AUROC reads ~0.99, but that is an artifact of
~13,500 added easy negatives: AUPRC *falls* and the margin over common-neighbor
collapses to ~+0.05. The two cohorts are not comparable.

*Current audited strict run: 2026-08-01, on the ESMC-excluded default graph:
AUROC 0.9763, AUPRC 0.5920, with a +0.2280 margin over common-neighbor. Separately,
a 2026-07-21 ablation ([validation/esmc_ablation.py](.)) removed the then-current
422 protein-embedding similarity-transfer edges and improved AUROC
0.9691 -> 0.9784 and AUPRC 0.5661 -> 0.6128. The database now contains 424 such
edges; all remain excluded from scoring. The protocol removes direct Drug->Disease edges and protein->disease
bridge edges derived from known indications; with all visible Drug->Disease
comparators removed, Yoneda distance is inactive here.*

### External performance: undetermined, not weak

*Revised 2026-07-31 after an independent audit. This section previously reported
an external and a temporal number as if both were current. Neither survived.*

> **PHARM performs strong internal recovery on its curated graph. Its external
> precision is currently undetermined, because external data, temporal
> provenance, and label completeness are all inadequate.**

| Validation | Status |
|------------|--------|
| Hetionet CtD external | **RETIRED — not reproducible.** `data/external/` is absent from the repository and gitignored, so the script raises `FileNotFoundError` on a clean clone. The old 0.6436 / 0.0095 was also computed on the forbidden `all` cohort. |
| Temporal holdout, approvals > 2013 | **STALE and leaky.** Rerun 2026-07-31 it gives AUROC 0.996 / AUPRC 0.156 on 15,114 `all`-cohort pairs. It removes only the *label*, leaving 2026-derived Protein->Disease edges in the graph, so post-cutoff literature leaks into every "held-out" prediction. |
| Corrected LOOCV | Not re-measured since the ESMC exclusion. Unverified. |
| Disease holdout | Not re-measured since the ESMC exclusion. Unverified. |

**Why "undetermined" rather than "weak".** The temporal holdout's top-ranked
*negative* is **Dacomitinib -> NSCLC**, an FDA-approved indication since
2018-09-27. Lorlatinib, Brigatinib and Amivantamab in NSCLC and Avapritinib in
GIST sit in the same top 20 — all approved, all counted as false positives. The
44-label gold set covers only the 78 curated drugs, while the graph carries 679
more from ChEMBL. **The evaluation cannot currently tell a false positive from a
true positive it never labelled.** That is not evidence performance is good; it
means the question is open, and no precision claim in either direction is made
here until a complete label set exists.

### Ranking calibration

{calibration_note}

The calibrated value shown in candidate details is a local benchmark-label rate
for the score bin. It is separate from strategy signal scores and is not a
clinical probability.

### Limitations

- **Research prototype**: Not a clinical decision support system
- **20 diseases, oncology-dominated but not oncology-only**: the set includes
  `Type2_Diabetes` and `Li_Fraumeni_Syndrome` (a predisposition syndrome, not a
  tumour type). **6 of the 20 carry zero positives** -- AML, Glioblastoma,
  Ewing_Sarcoma, Prostate_Cancer, Soft_Tissue_Sarcoma, Li_Fraumeni -- so
  disease-specific performance is undefined for 30% of the graph. AML has no
  `treats` label at all.
- **Small graph**: {n_obj} objects vs 47k+ in published systems like Rephetio
- **Open-world negatives**: Unlabeled pairs are unknowns, not confirmed negatives.
  This is not a formality -- see the external section above, where treating
  absence as a negative counted five approved drugs as false positives.
- **Hub-drug bias**: Promiscuous multi-kinase inhibitors (Imatinib tops 14/20
  diseases) crowd the top of most disease rankings -- partly real pan-cancer
  biology and partly a promiscuity bias. Current strict metrics are AUPRC 0.5920
  and AUROC 0.9763. Use the **Disease-specific** view to demote the hubs.
- **A PMID on a Protein->Disease edge is NOT validation** (measured 2026-07-20):
  those citations were gathered *after* the edge was proposed. A permutation
  negative control -- same proteins, randomly reassigned diseases -- grounded at
  7.5% versus 12.5% for the real pairings (Fisher exact p=0.28, 95% CI on the
  difference includes zero), at comparable adjudicated quality. So the proposal
  step adds no measurable signal; this layer is **literature mining, not
  prediction validation**. Read such a PMID as *"this is not absurd, start
  reading here"*. Drug->Protein citations (ChEMBL, FDA) are independently derived
  and unaffected. See HONEST_VALUE.md and `data/GROUNDING_NEGATIVE_CONTROL.json`.
- **Weakest at the disease link -- and this is the binding constraint.**
  Re-measured 2026-08-01. On the default ESMC-excluded graph, **111**
  non-drug/non-disease nodes carry a disease edge, across **806** terminal edges:
  **746 are `associated_with`** (co-occurrence, not mechanism) and **60 are
  directed `driver_of`**, spanning 45 sources. **153 of 757 drugs** complete any
  Drug->Protein->Disease path; through a **directed** terminal hop, **191 pairs**
  are reachable. Every candidate this system produces traces back to one of those
  60 directed edges, so their citation quality is the ceiling on everything it
  can claim.
- **Citation attribution risk remains**: Provenance/source strings exist for every edge, but
  the audit found PMID-without-context, measured-tier mismatch, and quantitative
  support issues that need edge-level verification before wet-lab claims
- **AUROC is sensitive to graph expansion**: Adding PubMed co-mention edges
  (low confidence) changes AUROC depending on protocol and quality tier filter
- **External generalization is UNMEASURED**: not weak, not strong. See the
  external section above. Making either claim would outrun the evidence.
- **Packaging was repaired on 2026-07-31**: the current checkout uses
  `setuptools.build_meta`, declares its runtime dependencies, and includes the
  packages used by the benchmark. Older checkouts did not build.
- **Quantitative columns are empty**: `quantitative_value` and `sample_size` read
  NULL for all 2,462 database edges; ABPP measurements are loaded separately.
- **Core value**: AUROC is useful, but the research value is the auditable
  mechanistic trail, source typing, validation status, and citation provenance

### Citation

Hawkins, J.R. (2026). KOMPOSOS-IV-PHARM: Categorical Drug Repurposing.
Apache 2.0 / Commercial dual license.
""")
