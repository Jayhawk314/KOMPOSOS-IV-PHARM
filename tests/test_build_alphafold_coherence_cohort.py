from types import SimpleNamespace

import numpy as np

from validation.build_alphafold_coherence_cohort import (
    DomainInterval,
    ExperimentalMapping,
    choose_domain_pair,
    load_observed_segments,
    mapped_domain_coverage,
    parse_interpro_domains,
    parse_pdbe_mappings,
    summarize_oracle,
)


def test_interpro_parser_flattens_locations_and_removes_overlapping_synonyms():
    payload = {
        "results": [
            {
                "metadata": {"accession": "IPR1", "name": "domain one", "type": "domain"},
                "proteins": [{"entry_protein_locations": [
                    {"fragments": [{"start": 10, "end": 60}]},
                    {"fragments": [{"start": 100, "end": 150}]},
                ]}],
            },
            {
                "metadata": {"accession": "IPR2", "name": "synonym", "type": "domain"},
                "proteins": [{"entry_protein_locations": [
                    {"fragments": [{"start": 12, "end": 58}]},
                ]}],
            },
            {
                "metadata": {"accession": "IPR3", "name": "family", "type": "family"},
                "proteins": [{"entry_protein_locations": [
                    {"fragments": [{"start": 200, "end": 250}]},
                ]}],
            },
            {
                "metadata": {"accession": "IPR4", "name": "discontinuous", "type": "domain"},
                "proteins": [{"entry_protein_locations": [
                    {"fragments": [{"start": 200, "end": 220}, {"start": 240, "end": 260}]},
                ]}],
            },
        ]
    }
    domains = parse_interpro_domains(payload)
    assert [(domain.domain_id, domain.start, domain.end) for domain in domains] == [
        ("IPR1_10_60", 10, 60),
        ("IPR1_100_150", 100, 150),
    ]


def test_pdbe_parser_filters_methods_and_keeps_one_chain_per_pdb():
    payload = {"P12345": [
        {
            "pdb_id": "1abc", "chain_id": "A", "experimental_method": "X-ray diffraction",
            "resolution": 2.0, "unp_start": 1, "unp_end": 200, "coverage": 0.9,
        },
        {
            "pdb_id": "1abc", "chain_id": "B", "experimental_method": "X-ray diffraction",
            "resolution": 2.0, "unp_start": 20, "unp_end": 180, "coverage": 0.7,
        },
        {
            "pdb_id": "2nmr", "chain_id": "A", "experimental_method": "Solution NMR",
            "resolution": None, "unp_start": 1, "unp_end": 200, "coverage": 1.0,
        },
        {
            "pdb_id": "3em1", "chain_id": "C", "experimental_method": "Electron Microscopy",
            "resolution": 3.2, "unp_start": 1, "unp_end": 200, "coverage": 1.0,
        },
    ]}
    mappings = parse_pdbe_mappings(payload, "P12345")
    assert [(item.pdb_id, item.chain_id) for item in mappings] == [("3em1", "C"), ("1abc", "A")]


def test_sifts_observed_segments_replace_construct_level_coverage(tmp_path):
    import gzip

    path = tmp_path / "observed.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("# release\n")
        handle.write("PDB,CHAIN,SP_PRIMARY,RES_BEG,RES_END,PDB_BEG,PDB_END,SP_BEG,SP_END\n")
        handle.write("1abc,A,P12345,1,31,1,31,100,130\n")
        handle.write("1abc,A,P12345,41,61,41,61,140,160\n")
    observed = load_observed_segments(path, {"P12345"})
    mapping = ExperimentalMapping(
        "1abc", "A", "X-ray diffraction", 2.0, 1, 300, 1.0,
        observed[("P12345", "1abc", "A")],
    )
    assert mapped_domain_coverage(DomainInterval("D", "D", "domain", 100, 160), mapping) == 52 / 61
    assert mapped_domain_coverage(DomainInterval("M", "M", "missing", 200, 250), mapping) == 0.0


def test_domain_pair_selection_prefers_low_pae_assessable_pair():
    domains = [
        DomainInterval("D1", "D1", "one", 1, 30),
        DomainInterval("D2", "D2", "two", 41, 70),
        DomainInterval("D3", "D3", "three", 81, 110),
    ]
    mappings = [
        ExperimentalMapping("1abc", "A", "X-ray diffraction", 2.0, 1, 110, 1.0),
        ExperimentalMapping("2abc", "A", "X-ray diffraction", 2.5, 1, 110, 1.0),
    ]
    pae = np.full((110, 110), 25.0)
    pae[:30, 40:70] = 3.0
    pae[40:70, :30] = 3.0
    model = SimpleNamespace(
        sequence="A" * 110,
        plddt=np.full(110, 90.0),
        pae=pae,
    )
    choice = choose_domain_pair(domains, mappings, model)
    assert choice is not None
    assert (choice.first.domain_id, choice.second.domain_id) == ("D1", "D2")
    assert choice.assessable_by_af is True
    assert choice.cross_domain_pae == 3.0
    assert mapped_domain_coverage(choice.first, mappings[0]) == 1.0


def test_summary_requires_experimental_consensus_for_af_specific_conflict():
    report = {
        "standing": "INCONSISTENT",
        "ranked_findings": [{}, {}],
        "audit_report": {
            "reference_model": "AF_X",
            "domain_arrangements": [
                {"source_model": "AF_X", "target_model": "PDB_1", "standing": "INCONSISTENT"},
                {"source_model": "AF_X", "target_model": "PDB_2", "standing": "INCONSISTENT"},
                {"source_model": "PDB_1", "target_model": "PDB_2", "standing": "CONSISTENT"},
            ],
        },
    }
    summary = summarize_oracle(report)
    assert summary["interpretation"] == "AF_SPECIFIC_CONFLICT"
    report["audit_report"]["domain_arrangements"][-1]["standing"] = "INCONSISTENT"
    assert summarize_oracle(report)["interpretation"] == "CONFORMATIONAL_OR_MAPPING_CONFLICT"
