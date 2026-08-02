#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Build a reviewable ClinicalTrials.gov evidence inventory for drug-disease pairs.

This command does not decide whether a drug works. It records facts needed by a
reviewer and keeps states that the former ``whyStopped`` proxy collapsed:
active trials; completed trials with results or linked publications; completed
trials without located results; scientific, operational, mixed, or unclear
stops; query errors; and non-matching search hits.

``not approved`` and ``completed without results`` are not failure labels.
Result polarity is always left for human review.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = ",".join((
    "NCTId", "BriefTitle", "OverallStatus", "WhyStopped", "Phase",
    "StartDate", "CompletionDate", "Condition", "InterventionName",
    "InterventionOtherName", "HasResults", "ReferencePMID", "ReferenceType",
))

SCIENTIFIC = (
    "futility", "lack of efficacy", "no efficacy", "did not meet",
    "progression", "toxicity", "safety", "adverse", "insufficient activity",
    "no benefit", "interim analysis", "lack of benefit",
)
OPERATIONAL = (
    "accrual", "enrollment", "enrolment", "recruitment", "funding",
    "financial", "business", "sponsor decision", "strategic",
    "administrative", "pi left", "investigator", "supply", "covid", "slow",
)
ACTIVE_STATUSES = {
    "RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING",
}
STOPPED_STATUSES = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}
SALT_TOKENS = {
    "anhydrous", "citrate", "fumarate", "hydrate", "hydrochloride", "malate",
    "mesilate", "mesylate", "phosphate", "potassium", "s", "sodium", "sulfate",
}
DRUG_ALIASES = {
    "abemaciclib": ("LY2835219", "Verzenio"),
    "adagrasib": ("MRTX849", "Krazati"),
    "amivantamab": ("JNJ-61186372",),
    "beperminogene perplasmid": ("AMG0001", "Collategene"),
    "brigatinib": ("AP26113", "Alunbrig"),
    "cabozantinib": ("XL184", "Cabometyx", "Cometriq"),
    "capmatinib": ("INC280", "INCB28060", "Tabrecta"),
    "clascoterone": ("CB-03-01", "Winlevi"),
    "copanlisib": ("BAY 80-6946", "Aliqopa"),
    "crizotinib": ("PF-02341066", "Xalkori"),
    "dacomitinib": ("PF-00299804", "PF-299804", "Vizimpro"),
    "deuruxolitinib": ("CTP-543", "Leqselvi"),
    "fedratinib": ("TG101348", "Inrebic"),
    "filgotinib": ("GLPG0634", "Jyseleca"),
    "imetelstat": ("GRN163L", "Rytelo"),
    "lazertinib": ("YH25448", "Leclaza"),
    "palbociclib": ("PD-0332991", "Ibrance"),
    "ribociclib": ("LEE011", "Kisqali"),
    "sotorasib": ("AMG510", "Lumakras", "Lumykras"),
    "tepotinib": ("MSC2156119J", "Tepmetko"),
}
DISEASE_ALIASES = {
    "AML": ("acute myeloid leukemia", "acute myelogenous leukemia", "aml"),
    "Breast_Cancer": ("breast cancer", "breast carcinoma", "breast neoplasm"),
    "CLL": ("chronic lymphocytic leukemia", "chronic lymphocytic leukaemia", "cll", "small lymphocytic lymphoma"),
    "Colorectal_Cancer": ("colorectal cancer", "colon cancer", "rectal cancer", "colorectal carcinoma"),
    "GIST": ("gastrointestinal stromal tumor", "gastrointestinal stromal tumour", "gist"),
    "Glioblastoma": ("glioblastoma", "glioblastoma multiforme", "malignant glioma"),
    "HCC": ("hepatocellular carcinoma", "hcc", "liver cancer"),
    "Li_Fraumeni_Syndrome": ("li-fraumeni syndrome", "li fraumeni syndrome"),
    "Melanoma": ("melanoma",),
    "Multiple_Myeloma": ("multiple myeloma", "plasma cell myeloma"),
    "Myelofibrosis": ("myelofibrosis", "primary myelofibrosis"),
    "NSCLC": ("non-small cell lung cancer", "non-small-cell lung cancer", "nsclc"),
    "Pancreatic_Cancer": ("pancreatic cancer", "pancreatic adenocarcinoma", "pancreatic ductal adenocarcinoma"),
    "Prostate_Cancer": ("prostate cancer", "prostatic cancer", "prostate carcinoma"),
    "RCC": ("renal cell carcinoma", "kidney cancer", "renal cancer", "papillary renal cell carcinoma"),
    "Soft_Tissue_Sarcoma": ("soft tissue sarcoma", "soft-tissue sarcoma", "sarcoma", "sarcomas"),
}


def classify(why: str) -> str:
    """Classify a stop reason for triage; never interpret it as pair failure."""
    if not why:
        return "STOPPED_NO_REASON_NEEDS_HUMAN"
    lowered = why.lower()
    operational = any(term in lowered for term in OPERATIONAL)
    scientific = any(term in lowered for term in SCIENTIFIC)
    if operational and scientific:
        return "MIXED_NEEDS_HUMAN"
    if operational:
        return "OPERATIONAL"
    if scientific:
        return "SCIENTIFIC_NEEDS_HUMAN"
    return "UNCLEAR_NEEDS_HUMAN"


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _strip_salt(value: str) -> str:
    return " ".join(token for token in _normalise(value).split() if token not in SALT_TOKENS)


def _contains_token_phrase(container: str, phrase: str) -> bool:
    container_tokens = _normalise(container).split()
    phrase_tokens = _normalise(phrase).split()
    width = len(phrase_tokens)
    if not width:
        return False
    return any(
        container_tokens[index:index + width] == phrase_tokens
        for index in range(len(container_tokens) - width + 1)
    )


def intervention_names(study: dict) -> list[str]:
    module = study.get("protocolSection", {}).get("armsInterventionsModule", {})
    names: list[str] = []
    for intervention in module.get("interventions", []):
        if intervention.get("name"):
            names.append(intervention["name"])
        names.extend(intervention.get("otherNames", []))
    return sorted(set(names))


def intervention_matches(drug: str, names: Iterable[str]) -> bool:
    wanted = _strip_salt(drug)
    aliases = (drug, *DRUG_ALIASES.get(wanted, ()))
    return bool(wanted) and any(
        _strip_salt(name) == _strip_salt(alias)
        or _contains_token_phrase(name, alias)
        for name in names
        for alias in aliases
    )


def condition_names(study: dict) -> list[str]:
    module = study.get("protocolSection", {}).get("conditionsModule", {})
    return list(module.get("conditions", []))


def condition_matches(disease: str, names: Iterable[str]) -> bool:
    aliases = DISEASE_ALIASES.get(disease, (disease.replace("_", " "),))
    return any(
        _contains_token_phrase(name, alias)
        for name in names
        for alias in aliases
    )


def query(drug: str, disease: str, page_size: int = 100) -> tuple[list[dict], str]:
    """Return search hits and an explicit query status."""
    params = {
        "query.intr": drug,
        "query.cond": disease.replace("_", " "),
        "fields": FIELDS,
        "pageSize": str(page_size),
    }
    studies: list[dict] = []
    try:
        while True:
            url = f"{API}?{urllib.parse.urlencode(params)}"
            request = urllib.request.Request(
                url, headers={"User-Agent": "KOMPOSOS-IV-PHARM/1.0"}
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            studies.extend(payload.get("studies", []))
            token = payload.get("nextPageToken")
            if not token:
                break
            params["pageToken"] = token
            time.sleep(0.35)
        return studies, "OK"
    except Exception as exc:  # pragma: no cover - external service
        return studies, f"ERROR:{type(exc).__name__}:{exc}"
    finally:
        time.sleep(0.35)


def _date_value(struct: dict) -> str:
    return (struct or {}).get("date", "")


def _years_since(value: str, today: date) -> float | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            return round((today - parsed).days / 365.25, 2)
        except ValueError:
            continue
    return None


def pair_linkage(study: dict, drug: str, disease: str) -> str:
    protocol = study.get("protocolSection", {})
    title = protocol.get("identificationModule", {}).get("briefTitle", "")
    if intervention_matches(drug, [title]) and condition_matches(disease, [title]):
        return "TITLE_EXPLICIT"
    module = protocol.get("armsInterventionsModule", {})
    intervention_count = len(module.get("interventions", []))
    if intervention_count == 1:
        return "SINGLE_INTERVENTION_CONDITION_MATCHED"
    return "MULTI_ARM_PAIR_LINKAGE_UNCONFIRMED"


def trial_record(
    study: dict, drug: str, disease: str, today: date | None = None,
) -> dict:
    today = today or date.today()
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    references = protocol.get("referencesModule", {}).get("references", [])
    result_pmids = sorted({
        reference.get("pmid", "")
        for reference in references
        if reference.get("pmid") and reference.get("type") == "RESULT"
    })
    completion = _date_value(status_module.get("completionDateStruct", {}))
    status = status_module.get("overallStatus", "UNKNOWN")
    why = status_module.get("whyStopped", "")
    has_results = bool(study.get("hasResults") or study.get("resultsSection"))
    return {
        "nct": identification.get("nctId", ""),
        "title": identification.get("briefTitle", ""),
        "status": status,
        "phases": design.get("phases", []),
        "completion_date": completion,
        "years_since_completion": _years_since(completion, today),
        "has_posted_results": has_results,
        "result_pmids": result_pmids,
        "why_stopped": why,
        "stop_class": classify(why) if status in STOPPED_STATUSES else "NOT_STOPPED",
        "interventions": intervention_names(study),
        "conditions": condition_names(study),
        "pair_linkage": pair_linkage(study, drug, disease),
        "result_polarity": "NOT_ASSESSED_BY_AUTOMATION",
    }


def evidence_flags(records: list[dict], aged_years: float = 2.0) -> list[str]:
    flags: set[str] = set()
    if not records:
        return ["NO_EXACT_TRIALS"]
    for record in records:
        if record["pair_linkage"] == "MULTI_ARM_PAIR_LINKAGE_UNCONFIRMED":
            flags.add("MULTI_ARM_PAIR_LINKAGE_UNCONFIRMED")
            continue
        status = record["status"]
        if status in ACTIVE_STATUSES:
            flags.add("ACTIVE_TRIAL_NO_RESULT_YET")
        elif status == "COMPLETED":
            if record["has_posted_results"]:
                flags.add("COMPLETED_RESULTS_POSTED_NEEDS_REVIEW")
            if record["result_pmids"]:
                flags.add("RESULT_PUBLICATION_LINKED_NEEDS_REVIEW")
            if not record["has_posted_results"] and not record["result_pmids"]:
                age = record["years_since_completion"]
                if age is not None and age >= aged_years:
                    flags.add("COMPLETED_NO_RESULTS_AGED_NOT_A_FAILURE_LABEL")
                else:
                    flags.add("COMPLETED_NO_RESULTS_RECENT_OR_UNDATED")
        elif status in STOPPED_STATUSES:
            flags.add(record["stop_class"])
        else:
            flags.add(f"STATUS_{status}_NEEDS_REVIEW")
    return sorted(flags)


def summarise(
    studies: list[dict], drug: str, disease: str, *, query_status: str = "OK",
    today: date | None = None,
) -> dict:
    exact: list[dict] = []
    excluded: list[dict] = []
    for study in studies:
        names = intervention_names(study)
        conditions = condition_names(study)
        drug_match = intervention_matches(drug, names)
        disease_match = condition_matches(disease, conditions)
        if drug_match and disease_match:
            exact.append(trial_record(study, drug, disease, today=today))
        else:
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            excluded.append({
                "nct": identification.get("nctId", ""),
                "title": identification.get("briefTitle", ""),
                "drug_match": drug_match,
                "disease_match": disease_match,
                "interventions": names,
                "conditions": conditions,
            })
    flags = ["QUERY_ERROR"] if query_status != "OK" else evidence_flags(exact)
    linked = [
        record for record in exact
        if record["pair_linkage"] != "MULTI_ARM_PAIR_LINKAGE_UNCONFIRMED"
    ]
    return {
        "query_status": query_status,
        "n_query_hits": len(studies),
        "n_exact_trials": len(exact),
        "n_pair_linked_trials": len(linked),
        "n_pair_linkage_unconfirmed": len(exact) - len(linked),
        "n_excluded_query_hits": len(excluded),
        "status_counts": dict(Counter(record["status"] for record in linked)),
        "evidence_flags": flags,
        "trials": exact,
        "excluded_query_hits": excluded,
        "pair_result_polarity": "NOT_ASSESSED_BY_AUTOMATION",
    }


def _row_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        if row.get(name):
            return row[name]
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worklist", default="reports/horn_audit_2026-08-01/HORN_TOP50.csv")
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    worklist = REPO / args.worklist
    rows = list(csv.DictReader(worklist.open(encoding="utf-8-sig")))
    if args.limit:
        rows = rows[:args.limit]
    out_path = REPO / (args.out or str(worklist.parent / "TRIAL_HISTORY.json"))

    results = {}
    print(f"querying ClinicalTrials.gov for {len(rows)} pairs\n")
    for index, row in enumerate(rows, 1):
        drug = _row_value(row, "drug_inn", "drug")
        disease = row["disease"]
        studies, query_status = query(drug, disease)
        info = summarise(studies, drug, disease, query_status=query_status)
        key = f"{drug}|{disease}"
        results[key] = {
            "drug": drug,
            "disease": disease,
            "review_id": _row_value(row, "review_id", "rank"),
            **info,
        }
        flags = ";".join(info["evidence_flags"])
        print(
            f"{index:>3}. {drug[:22]:<23}{disease:<22}"
            f"{info['n_pair_linked_trials']:>2}/{info['n_exact_trials']:>2}/{info['n_query_hits']:<3}"
            f" linked/module/query  {flags}"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(out_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(results, indent=1))
    temporary.replace(out_path)
    counts = Counter(flag for result in results.values() for flag in result["evidence_flags"])
    print(f"\nwrote {out_path}")
    print("\n=== EVIDENCE FLAGS (not verdicts) ===")
    for flag, count in counts.most_common():
        print(f"  {flag:<52}{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
