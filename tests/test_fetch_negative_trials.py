from datetime import date

from validation.fetch_negative_trials import (
    classify,
    condition_matches,
    intervention_matches,
    summarise,
)


def _study(
    *, nct="NCT00000001", drug="Dacomitinib", condition="Glioblastoma",
    status="COMPLETED", completion="2017-01-01", why="", has_results=False,
    result_pmid="",
):
    references = []
    if result_pmid:
        references.append({"pmid": result_pmid, "type": "RESULT"})
    return {
        "hasResults": has_results,
        "protocolSection": {
            "identificationModule": {"nctId": nct, "briefTitle": "Test trial"},
            "statusModule": {
                "overallStatus": status,
                "whyStopped": why,
                "completionDateStruct": {"date": completion},
            },
            "designModule": {"phases": ["PHASE2"]},
            "conditionsModule": {"conditions": [condition]},
            "armsInterventionsModule": {
                "interventions": [{"name": drug, "otherNames": []}]
            },
            "referencesModule": {"references": references},
        },
    }


def test_exact_intervention_matching_accepts_salts_but_not_class_analogs():
    assert intervention_matches("Cabozantinib", ["Cabozantinib S-Malate"])
    assert intervention_matches("Dacomitinib", ["PF-299804 (Dacomitinib)"])
    assert intervention_matches("Adagrasib", ["MRTX849"])
    assert intervention_matches("Hydroxychloroquine", ["Hydroxychloroquine sulfate"])
    assert not intervention_matches("Chloroquine", ["Hydroxychloroquine sulfate"])


def test_condition_matching_uses_explicit_aliases_not_incidental_solid_tumor_text():
    assert condition_matches("RCC", ["Papillary Renal Cell Carcinoma"])
    assert condition_matches("RCC", ["Metastatic Papillary Renal Cell Carcinoma"])
    assert condition_matches("Soft_Tissue_Sarcoma", ["Sarcoma"])
    assert condition_matches("GIST", ["Metastatic Gastrointestinal Stromal Tumor"])
    assert not condition_matches("RCC", ["Advanced Solid Tumor"])


def test_stop_reason_is_triage_and_operational_wins_mixed_text():
    assert classify("Trial stopped for futility") == "SCIENTIFIC_NEEDS_HUMAN"
    assert classify("Slow accrual") == "OPERATIONAL"
    assert classify("Slow accrual in population likely to benefit; progression") == "MIXED_NEEDS_HUMAN"


def test_completed_no_results_is_not_called_failure():
    info = summarise(
        [_study()], "Dacomitinib", "Glioblastoma", today=date(2026, 8, 1)
    )
    assert info["n_exact_trials"] == 1
    assert info["pair_result_polarity"] == "NOT_ASSESSED_BY_AUTOMATION"
    assert info["evidence_flags"] == [
        "COMPLETED_NO_RESULTS_AGED_NOT_A_FAILURE_LABEL"
    ]


def test_posted_results_and_result_publication_are_queued_for_review():
    info = summarise(
        [_study(has_results=True, result_pmid="28575464")],
        "Dacomitinib",
        "Glioblastoma",
        today=date(2026, 8, 1),
    )
    assert info["evidence_flags"] == [
        "COMPLETED_RESULTS_POSTED_NEEDS_REVIEW",
        "RESULT_PUBLICATION_LINKED_NEEDS_REVIEW",
    ]
    assert info["trials"][0]["result_pmids"] == ["28575464"]


def test_false_positive_query_hits_are_retained_but_not_counted_as_exact_trials():
    hit = _study(drug="Hydroxychloroquine", condition="Chronic Lymphocytic Leukemia")
    info = summarise([hit], "Chloroquine", "CLL", today=date(2026, 8, 1))
    assert info["n_query_hits"] == 1
    assert info["n_exact_trials"] == 0
    assert info["n_excluded_query_hits"] == 1
    assert info["evidence_flags"] == ["NO_EXACT_TRIALS"]


def test_multi_arm_copresence_does_not_claim_pair_specific_trial_state():
    hit = _study(has_results=True)
    protocol = hit["protocolSection"]
    protocol["armsInterventionsModule"]["interventions"].append({
        "name": "Another drug", "otherNames": []
    })
    protocol["conditionsModule"]["conditions"].append("Another cancer")
    info = summarise([hit], "Dacomitinib", "Glioblastoma", today=date(2026, 8, 1))
    assert info["n_exact_trials"] == 1
    assert info["n_pair_linked_trials"] == 0
    assert info["n_pair_linkage_unconfirmed"] == 1
    assert info["evidence_flags"] == ["MULTI_ARM_PAIR_LINKAGE_UNCONFIRMED"]


def test_query_errors_are_not_rendered_as_no_trials():
    info = summarise([], "Mebendazole", "RCC", query_status="ERROR:Timeout")
    assert info["evidence_flags"] == ["QUERY_ERROR"]
    assert info["query_status"] == "ERROR:Timeout"
