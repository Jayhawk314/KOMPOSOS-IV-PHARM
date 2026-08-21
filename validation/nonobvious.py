#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Non-obvious candidate finder: well-supported drug-disease paths the literature
has barely discussed.

Why this exists
---------------
Ranking by score alone surfaces what everyone already knows. The top of that list
is dominated by pan-cancer kinase hubs whose Drug->Protein->Disease trail is short,
famous, and adds nothing to a researcher's argument. The audit trail is only worth
something when it points somewhere the reader has NOT already been.

So rank on two axes instead of one:

    support   - strength of the mechanistic chain, from the existing scorer and
                the per-edge confidences already in the graph. Must be a REAL
                composed Drug->Protein->Disease path, not a similarity vote.
    novelty   - how little PubMed already co-mentions this drug and disease.
                Measured OUTSIDE the graph, or it is circular reasoning.

    nonobvious = support * novelty

The interesting quadrant is high support and low familiarity: a chain you can
defend edge-by-edge, about a pair nobody has written up.

Honest caveats (surface these to any user)
------------------------------------------
- A low PubMed count can mean "genuinely unexplored", but it can equally mean
  "tried, failed, never published" or "the drug name is ambiguous". This ranks
  candidates for a human to triage; it does not assert they will work.
- The terminal Protein->Disease hop is the weakest layer of this graph. A chain is
  only as good as that last edge, which is reported per-candidate as `weakest_hop`.
- Absence of literature is not evidence of efficacy.

Usage:
    python -m validation.nonobvious --disease Melanoma --top 15
    python -m validation.nonobvious --all-diseases --top 5 --json out.json
    python -m validation.nonobvious --disease AML --offline   # no network
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation.repurposing_benchmark import (
    drug_disease_pairs,
    load_full_typed_view,
    score_pair_detailed,
)
from validation.ncbi_client import ncbi_credentials, ncbi_min_interval
from validation.trace_prediction import _build_provenance_index, trace_pair

DB_PATH = "data/drugs/tier1.db"
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "pubmed_comention_cache.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Co-mention count at which a pair is considered fully "known". Chosen so that a
# textbook pair (Vemurafenib/Melanoma ~1950 hits) lands at novelty ~0.
FAMILIARITY_CAP = 2000

PROTEIN_TYPES = {
    "Protein", "Receptor", "Signaling", "Transcription", "TumorSuppressor",
    "Apoptosis", "Oncogene", "DNARepair", "CellCycle", "Regulator", "Splicing",
    "Epigenetic", "Metabolic", "Structural", "Chaperone", "Transporter",
    "Ligand", "Enzyme", "Marker",
}

# Salt and hydrate forms. ChEMBL ships "Dacomitinib Anhydrous" as a separate entity,
# but no abstract writes it that way, so the raw name returns ~0 co-mentions and
# fakes a perfect novelty score. Strip to the base INN before querying PubMed, and
# collapse forms that share a base so one drug cannot occupy four ranks.
# NOTE: biologic suffixes (Alfa, Beta, Pegol, Vedotin, ...) are part of the INN and
# distinguish real products - they are deliberately NOT stripped.
SALT_SUFFIXES = {
    "anhydrous", "monohydrate", "dihydrate", "hydrate", "hydrochloride", "hcl",
    "sodium", "disodium", "tetrasodium", "potassium", "calcium", "magnesium",
    "sulfate", "bisulfate", "besilate", "besylate", "mesylate", "tosylate",
    "maleate", "fumarate", "tartrate", "bitartrate", "citrate", "acetate",
    "phosphate", "diphosphate", "succinate", "malate", "s-malate", "oxalate",
    "hydrobromide", "bromide", "iodide", "nitrate", "gluconate", "lactate",
    "pamoate", "palmitate", "decanoate", "enanthate", "cypionate", "valerate",
    "propionate", "dipropionate", "pivalate", "butyrate", "probutate",
    "tromethamine", "dimeglumine", "meglumine", "olamine", "choline", "arginine",
    "picrate", "saccharate", "adipate", "aspartate", "diethylamine", "pidolate",
    "propanediol", "hyclate", "polistirex", "kamedoxomil", "cilexetil",
    "etexilate", "axetil", "proxetil", "lauroxil", "furoate", "carbonate",
}


def normalize_drug_name(name: str) -> str:
    """Strip trailing salt/hydrate tokens so PubMed sees the base INN."""
    tokens = name.split()
    while len(tokens) > 1 and tokens[-1].lower().strip("()") in SALT_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


# ── literature familiarity ───────────────────────────────────────────────────

def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1, sort_keys=True))


def _disease_query(disease: str) -> str:
    """Graph disease names are underscored tokens; PubMed wants prose."""
    return disease.replace("_", " ")


def pubmed_comentions(drug: str, disease: str, cache: dict,
                      sleep: float | None = None) -> int | None:
    """PubMed title/abstract co-mention count, or None if the lookup failed."""
    base = normalize_drug_name(drug)
    key = f"{base}|{disease}"
    if key in cache:
        return cache[key]

    if sleep is None:
        sleep = ncbi_min_interval()
    term = f'"{base}"[tiab] AND "{_disease_query(disease)}"[tiab]'
    query = {"db": "pubmed", "term": term, "rettype": "count", "retmode": "json"}
    query.update(ncbi_credentials())
    url = f"{EUTILS}?{urllib.parse.urlencode(query)}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
        count = int(payload["esearchresult"]["count"])
    except Exception:
        return None
    finally:
        time.sleep(sleep)

    cache[key] = count
    return count


def novelty_from_count(count: int) -> float:
    """Map a co-mention count to [0,1]; 0 hits -> 1.0, >=CAP hits -> 0.0."""
    return max(0.0, 1.0 - math.log1p(count) / math.log1p(FAMILIARITY_CAP))


# ── candidate construction ───────────────────────────────────────────────────

def _mechanistic_chains(trace: dict) -> list[dict]:
    """Chains that actually route Drug -> Protein -> ... -> Disease."""
    out = []
    for chain in trace["chains"]:
        edges = chain["edges"]
        if len(edges) < 2:
            continue
        if edges[0].get("target_type") not in PROTEIN_TYPES:
            continue
        out.append(chain)
    return out


def _weakest_hop(chain: dict) -> dict:
    return min(chain["edges"], key=lambda e: e.get("confidence") or 0.0)


def _cited_fraction(chain: dict) -> tuple[int, int]:
    cited = sum(1 for e in chain["edges"] if "PMID" in (e.get("provenance") or ""))
    return cited, len(chain["edges"])


def find_candidates(disease: str, category, strategies, positives,
                    provenance_index, drugs: list[str],
                    min_support: float, shortlist: int) -> list[dict]:
    """Score every drug against one disease, keep mechanistically-supported unknowns."""
    rows = []
    for drug in drugs:
        if (drug, disease) in positives:
            continue  # already an approved indication - by definition not novel

        trace = trace_pair(category, drug, disease, None, provenance_index)
        chains = _mechanistic_chains(trace)
        if not chains:
            continue  # no auditable path -> nothing to show a researcher

        detail = score_pair_detailed(strategies, drug, disease)
        if detail["composition_count"] == 0:
            continue  # similarity votes only, no composed mechanism
        if detail["score"] < min_support:
            continue

        best = chains[0]
        weak = _weakest_hop(best)
        cited, total = _cited_fraction(best)
        terminal = best["edges"][-1]
        rows.append({
            "drug": drug,
            "base_name": normalize_drug_name(drug),
            "disease": disease,
            # `associated_with` is an undirected co-occurrence relation, not a
            # mechanistic claim. A chain that lands on the disease through one is
            # far weaker than `driver_of`/`inhibits`, so surface it explicitly.
            "terminal_relation": terminal["relation"],
            "terminal_is_directed": terminal["relation"] != "associated_with",
            "support": round(detail["score"], 4),
            "n_chains": len(chains),
            "path_confidence": round(best["path_confidence"], 4),
            "path": " -> ".join(
                [best["edges"][0]["source"]] + [e["target"] for e in best["edges"]]
            ),
            "weakest_hop": f"{weak['source']} -{weak['relation']}-> {weak['target']}",
            "weakest_hop_confidence": round(weak.get("confidence") or 0.0, 3),
            "weakest_hop_tier": weak.get("evidence_tier", "HYPOTHESIS"),
            "cited_edges": f"{cited}/{total}",
            "chain": best,
        })

    # Collapse salt/hydrate forms of the same drug, keeping the best-supported one,
    # so "Dacomitinib" and "Dacomitinib Anhydrous" cannot both occupy the ranking.
    best_by_base: dict[str, dict] = {}
    for row in rows:
        prior = best_by_base.get(row["base_name"])
        if prior is None or row["support"] > prior["support"]:
            if prior is not None:
                row["collapsed_forms"] = prior.get("collapsed_forms", 0) + 1
            best_by_base[row["base_name"]] = row
        else:
            prior["collapsed_forms"] = prior.get("collapsed_forms", 0) + 1

    deduped = sorted(best_by_base.values(), key=lambda r: -r["support"])
    return deduped[:shortlist]


def rank_nonobvious(rows: list[dict], cache: dict, offline: bool) -> list[dict]:
    """Attach literature familiarity and compute the non-obviousness score."""
    for row in rows:
        if offline:
            row["comentions"] = None
            row["novelty"] = None
            row["nonobvious"] = None
            continue
        count = pubmed_comentions(row["drug"], row["disease"], cache)
        row["comentions"] = count
        if count is None:
            row["novelty"] = None
            row["nonobvious"] = None
        else:
            row["novelty"] = round(novelty_from_count(count), 4)
            row["nonobvious"] = round(row["support"] * row["novelty"], 4)

    scored = [r for r in rows if r["nonobvious"] is not None]
    unscored = [r for r in rows if r["nonobvious"] is None]
    scored.sort(key=lambda r: -r["nonobvious"])
    return scored + unscored


# ── reporting ────────────────────────────────────────────────────────────────

def format_table(rows: list[dict], disease: str, top: int) -> str:
    lines = [
        f"Non-obvious candidates for {disease}",
        "  ranked by support x novelty (novelty = 1 - log(PubMed co-mentions)/log(%d))" % FAMILIARITY_CAP,
        "",
        f"{'drug':<26} {'supp':>5} {'PMIDs':>6} {'novel':>6} {'SCORE':>6} {'term':>5}  {'weakest hop':<34} {'cited'}",
        "-" * 120,
    ]
    for row in rows[:top]:
        cm = "n/a" if row["comentions"] is None else str(row["comentions"])
        nv = "n/a" if row["novelty"] is None else f"{row['novelty']:.3f}"
        sc = "n/a" if row["nonobvious"] is None else f"{row['nonobvious']:.3f}"
        term = "mech" if row["terminal_is_directed"] else "assoc"
        lines.append(
            f"{row['drug'][:25]:<26} {row['support']:>5.3f} {cm:>6} {nv:>6} {sc:>6} {term:>5}  "
            f"{row['weakest_hop'][:33]:<34} {row['cited_edges']}"
        )
    lines += [
        "",
        "term=assoc means the chain reaches the disease through `associated_with`, a",
        "co-occurrence relation, not a mechanistic one - treat those as much weaker.",
        "",
        "Read this as a triage queue, not a result. Low co-mention counts can mean",
        "unexplored, or tried-and-unpublished, or an ambiguous drug name. The terminal",
        "Protein->Disease hop is the weakest layer of this graph - check it first.",
    ]
    return "\n".join(lines)


def format_audit(row: dict) -> str:
    lines = [
        f"AUDIT TRAIL  {row['drug']} -> {row['disease']}",
        f"  support {row['support']}  |  PubMed co-mentions {row['comentions']}  "
        f"|  non-obvious {row['nonobvious']}",
        f"  {row['n_chains']} mechanistic chain(s); best path confidence {row['path_confidence']}",
        "",
    ]
    for i, edge in enumerate(row["chain"]["edges"], 1):
        prov = edge.get("provenance") or "unknown"
        quant = ""
        if edge.get("quantitative_value") is not None:
            quant = f"  [{edge['quantitative_value']} {edge.get('value_unit') or ''}]"
        lines.append(
            f"  {i}. {edge['source']} --{edge['relation']}--> {edge['target']} "
            f"({edge.get('target_type','?')})"
        )
        lines.append(
            f"       conf {edge.get('confidence')}  tier {edge.get('evidence_tier')}"
            f"  prov {prov}{quant}"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Find well-supported, under-discussed drug-disease pairs.")
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--disease", help="Disease to analyse.")
    ap.add_argument("--all-diseases", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--shortlist", type=int, default=40,
                    help="Max pairs per disease sent to PubMed (network is the bottleneck).")
    ap.add_argument("--min-support", type=float, default=0.5)
    ap.add_argument("--offline", action="store_true", help="Skip PubMed; report support only.")
    ap.add_argument("--audit", action="store_true", help="Print the full trail for the top hit.")
    ap.add_argument("--json", dest="json_out", help="Write results to a JSON file.")
    args = ap.parse_args()

    from validation.repurposing_benchmark import make_strategies

    category, _ = load_full_typed_view(args.db)
    drugs, diseases, positives = drug_disease_pairs(category)
    strategies = make_strategies(category)
    provenance_index = _build_provenance_index(args.db)

    if args.all_diseases:
        targets = sorted(diseases)
    elif args.disease:
        targets = [args.disease]
    else:
        ap.error("pass --disease NAME or --all-diseases")

    cache = _load_cache()
    all_rows = []
    try:
        for disease in targets:
            rows = find_candidates(
                disease, category, strategies, positives, provenance_index,
                sorted(drugs), args.min_support, args.shortlist,
            )
            rows = rank_nonobvious(rows, cache, args.offline)
            all_rows.extend(rows)
            print(format_table(rows, disease, args.top))
            print()
            if args.audit and rows:
                print(format_audit(rows[0]))
                print()
    finally:
        _save_cache(cache)

    if args.json_out:
        slim = [{k: v for k, v in r.items() if k != "chain"} for r in all_rows]
        Path(args.json_out).write_text(json.dumps(slim, indent=2))
        print(f"wrote {len(slim)} rows -> {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
