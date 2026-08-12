# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Build and run a real AlphaFold structural-coherence evaluation cohort.

Public sources:
  * AlphaFold DB API: current monomer coordinates and PAE
  * PDBe best-structures API: experimental PDB/chain to UniProt mappings
  * InterPro API: UniProt domain intervals
  * RCSB files: experimental mmCIF coordinates

Each family contains one AlphaFold model and at least two distinct experimental
PDB structures for the same UniProt accession. Domain pairs are chosen only
when the PDBe mappings cover both domains. Preference is given to pairs with
high AlphaFold pLDDT and low cross-domain PAE so the test can find confident
errors rather than merely restating AlphaFold uncertainty.

The downloader is cached and resumable. Raw external data belongs under the
ignored data/external tree; compact summaries are written under reports/.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import numpy as np


REPO = Path(__file__).resolve().parent.parent
DEFAULT_LEGACY_DIR = Path(r"C:\Users\JAMES\KOMPOSOS-III-LAMBDA-max-3D\data\proteins\structures")
DEFAULT_DATA_DIR = REPO / "data" / "external" / "alphafold_coherence_2026-08-12"
DEFAULT_REPORT_DIR = REPO / "reports" / "alphafold_coherence_2026-08-12"
SIFTS_OBSERVED_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/csv/"
    "uniprot_segments_observed.csv.gz"
)
USER_AGENT = "KOMPOSOS-IV structural-coherence research audit/1.0"


@dataclass(frozen=True)
class DomainInterval:
    domain_id: str
    interpro_accession: str
    name: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


@dataclass(frozen=True)
class ExperimentalMapping:
    pdb_id: str
    chain_id: str
    experimental_method: str
    resolution: Optional[float]
    unp_start: int
    unp_end: int
    coverage: float
    observed_segments: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class DomainPairChoice:
    first: DomainInterval
    second: DomainInterval
    eligible_structures: tuple[ExperimentalMapping, ...]
    first_mean_plddt: float
    second_mean_plddt: float
    cross_domain_pae: float
    assessable_by_af: bool


def _load_kernel():
    name = "komposos_alphafold_cohort_kernel"
    if name in sys.modules:
        return sys.modules[name]
    path = REPO / "geometry" / "alphafold_coherence.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load structural kernel from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def legacy_accessions(directory: Path) -> list[str]:
    accessions = set()
    if not directory.exists():
        return []
    for path in directory.glob("AF-*-F1-model_v*.pdb"):
        name = path.name
        if name.startswith("AF-") and "-F1-model_" in name:
            accessions.add(name[3:name.index("-F1-model_")].upper())
    return sorted(accessions)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _request_bytes(url: str, attempts: int = 4) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in {429, 500, 502, 503, 504}:
                raise
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
        time.sleep(1.5 * (2 ** attempt))
    assert last_error is not None
    raise last_error


def cached_download(url: str, path: Path, refresh: bool = False) -> Path:
    if path.exists() and path.stat().st_size > 0 and not refresh:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _request_bytes(url)
    if not payload:
        raise ValueError(f"empty response from {url}")
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return path


def cached_json(url: str, path: Path, refresh: bool = False) -> Any:
    cached_download(url, path, refresh=refresh)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_interpro_domains(payload: dict[str, Any], minimum_length: int = 20) -> list[DomainInterval]:
    domains: list[DomainInterval] = []
    for result in payload.get("results", []):
        metadata = result.get("metadata") or {}
        if str(metadata.get("type", "")).lower() != "domain":
            continue
        accession = str(metadata.get("accession", "UNKNOWN"))
        name = str(metadata.get("name", accession))
        for protein in result.get("proteins") or []:
            for location in protein.get("entry_protein_locations") or []:
                fragments = location.get("fragments") or []
                # A discontinuous domain cannot be represented by the current
                # contiguous-domain audit without including unrelated residues.
                if len(fragments) != 1:
                    continue
                fragment = fragments[0]
                start = int(fragment["start"])
                end = int(fragment["end"])
                if end - start + 1 < minimum_length:
                    continue
                domains.append(DomainInterval(
                    domain_id=f"{accession}_{start}_{end}",
                    interpro_accession=accession,
                    name=name,
                    start=start,
                    end=end,
                ))
    return deduplicate_domains(domains)


def interval_overlap(first: DomainInterval, second: DomainInterval) -> int:
    return max(0, min(first.end, second.end) - max(first.start, second.start) + 1)


def deduplicate_domains(domains: Iterable[DomainInterval]) -> list[DomainInterval]:
    """Collapse annotations describing essentially the same residue interval."""

    chosen: list[DomainInterval] = []
    for domain in sorted(domains, key=lambda item: (-item.length, item.start, item.domain_id)):
        duplicate = False
        for existing in chosen:
            overlap = interval_overlap(domain, existing)
            if overlap / min(domain.length, existing.length) >= 0.70:
                duplicate = True
                break
        if not duplicate:
            chosen.append(domain)
    return sorted(chosen, key=lambda item: (item.start, item.end, item.domain_id))


def load_observed_segments(
    path: Path,
    accessions: Optional[set[str]] = None,
) -> dict[tuple[str, str, str], tuple[tuple[int, int], ...]]:
    """Read SIFTS residue ranges actually observed in experimental coordinates."""

    collected: dict[tuple[str, str, str], list[tuple[int, int]]] = {}
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
        rows = (line for line in handle if not line.startswith("#"))
        for row in csv.DictReader(rows):
            accession = row["SP_PRIMARY"].upper()
            if accessions is not None and accession not in accessions:
                continue
            key = (accession, row["PDB"].lower(), row["CHAIN"])
            collected.setdefault(key, []).append((int(row["SP_BEG"]), int(row["SP_END"])))
    return {
        key: tuple(sorted(segments))
        for key, segments in collected.items()
    }


def parse_pdbe_mappings(
    payload: dict[str, Any],
    accession: str,
    observed: Optional[dict[tuple[str, str, str], tuple[tuple[int, int], ...]]] = None,
) -> list[ExperimentalMapping]:
    raw = payload.get(accession.upper(), payload.get(accession.lower(), []))
    by_pdb: dict[str, ExperimentalMapping] = {}
    for item in raw:
        method = str(item.get("experimental_method") or "")
        if method not in {"X-ray diffraction", "Electron Microscopy"}:
            continue
        mapping = ExperimentalMapping(
            pdb_id=str(item["pdb_id"]).lower(),
            chain_id=str(item["chain_id"]),
            experimental_method=method,
            resolution=(None if item.get("resolution") is None else float(item["resolution"])),
            unp_start=int(item["unp_start"]),
            unp_end=int(item["unp_end"]),
            coverage=float(item.get("coverage") or 0.0),
            observed_segments=(
                () if observed is None
                else observed.get(
                    (accession.upper(), str(item["pdb_id"]).lower(), str(item["chain_id"])),
                    (),
                )
            ),
        )
        previous = by_pdb.get(mapping.pdb_id)
        if previous is None or _mapping_order(mapping) < _mapping_order(previous):
            by_pdb[mapping.pdb_id] = mapping
    return sorted(by_pdb.values(), key=_mapping_order)


def _mapping_order(mapping: ExperimentalMapping) -> tuple[float, float, str, str]:
    resolution = mapping.resolution if mapping.resolution is not None else 99.0
    return (-mapping.coverage, resolution, mapping.pdb_id, mapping.chain_id)


def mapped_domain_coverage(domain: DomainInterval, mapping: ExperimentalMapping) -> float:
    segments = mapping.observed_segments or ((mapping.unp_start, mapping.unp_end),)
    observed_positions: set[int] = set()
    for start, end in segments:
        overlap_start = max(domain.start, start)
        overlap_end = min(domain.end, end)
        if overlap_end >= overlap_start:
            observed_positions.update(range(overlap_start, overlap_end + 1))
    return len(observed_positions) / domain.length


def _cross_domain_pae(model: Any, first: DomainInterval, second: DomainInterval) -> float:
    if model.pae is None:
        return math.inf
    first_indices = np.arange(first.start - 1, first.end)
    second_indices = np.arange(second.start - 1, second.end)
    values = np.concatenate((
        model.pae[np.ix_(first_indices, second_indices)].ravel(),
        model.pae[np.ix_(second_indices, first_indices)].ravel(),
    ))
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if finite.size else math.inf


def choose_domain_pair(
    domains: Sequence[DomainInterval],
    structures: Sequence[ExperimentalMapping],
    af_model: Any,
    minimum_mapping_coverage: float = 0.75,
    minimum_structures: int = 2,
    confident_plddt: float = 70.0,
    assessable_pae: float = 15.0,
) -> Optional[DomainPairChoice]:
    choices: list[DomainPairChoice] = []
    for first, second in combinations(domains, 2):
        if interval_overlap(first, second):
            continue
        if second.end > len(af_model.sequence):
            continue
        eligible = tuple(
            mapping for mapping in structures
            if mapped_domain_coverage(first, mapping) >= minimum_mapping_coverage
            and mapped_domain_coverage(second, mapping) >= minimum_mapping_coverage
        )
        if len(eligible) < minimum_structures:
            continue
        first_plddt = float(np.nanmean(af_model.plddt[first.start - 1:first.end]))
        second_plddt = float(np.nanmean(af_model.plddt[second.start - 1:second.end]))
        pae = _cross_domain_pae(af_model, first, second)
        assessable = (
            min(first_plddt, second_plddt) >= confident_plddt
            and pae <= assessable_pae
        )
        choices.append(DomainPairChoice(
            first=first,
            second=second,
            eligible_structures=eligible,
            first_mean_plddt=first_plddt,
            second_mean_plddt=second_plddt,
            cross_domain_pae=pae,
            assessable_by_af=assessable,
        ))
    if not choices:
        return None
    return max(choices, key=lambda choice: (
        int(choice.assessable_by_af),
        len(choice.eligible_structures),
        -choice.cross_domain_pae,
        min(choice.first_mean_plddt, choice.second_mean_plddt),
        choice.first.length + choice.second.length,
    ))


def select_experimental_structures(
    choice: DomainPairChoice,
    maximum: int,
) -> list[ExperimentalMapping]:
    return sorted(choice.eligible_structures, key=lambda mapping: (
        mapping.resolution if mapping.resolution is not None else 99.0,
        -min(
            mapped_domain_coverage(choice.first, mapping),
            mapped_domain_coverage(choice.second, mapping),
        ),
        mapping.pdb_id,
    ))[:maximum]


def build_manifest(
    accession: str,
    af_path: Path,
    pae_path: Path,
    choice: DomainPairChoice,
    experiments: Sequence[tuple[ExperimentalMapping, Path]],
    manifest_path: Path,
) -> dict[str, Any]:
    models: list[dict[str, Any]] = [{
        "model_id": f"AF_{accession}",
        "kind": "prediction",
        "path": str(af_path.resolve()),
        "chain": "A",
        "pae_path": str(pae_path.resolve()),
    }]
    for mapping, path in experiments:
        models.append({
            "model_id": f"PDB_{mapping.pdb_id.upper()}_{mapping.chain_id}",
            "kind": "experimental",
            "path": str(path.resolve()),
            "chain": mapping.chain_id,
        })
    manifest = {
        "schema_version": 1,
        "family_id": accession,
        "reference_model": f"AF_{accession}",
        "models": models,
        "domains": [
            {"domain_id": choice.first.domain_id, "start": choice.first.start, "end": choice.first.end},
            {"domain_id": choice.second.domain_id, "start": choice.second.start, "end": choice.second.end},
        ],
        "config": {
            "minimum_residues": 20,
            "minimum_domain_coverage": 0.60,
            "minimum_plddt": 50.0,
            "maximum_assessable_pae": 15.0,
            "arrangement_rmsd_threshold": 5.0,
            "arrangement_rotation_threshold_deg": 20.0,
            "composition_rmsd_threshold": 2.0,
            "composition_rotation_threshold_deg": 10.0,
            "require_pae_for_predictions": True,
            "quarantine_on_any_missing_check": True,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def run_oracle(manifest: Path, report: Path) -> None:
    command = [
        sys.executable,
        str(REPO / "scripts" / "run_structural_coherence_oracle.py"),
        str(manifest),
        "--output",
        str(report),
    ]
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(
            f"structural Oracle failed ({completed.returncode}):\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def summarize_oracle(report: dict[str, Any]) -> dict[str, Any]:
    reference = report["audit_report"]["reference_model"]
    domain_checks = report["audit_report"]["domain_arrangements"]
    af_checks = [
        check for check in domain_checks
        if reference in {check["source_model"], check["target_model"]}
    ]
    experimental_checks = [
        check for check in domain_checks
        if reference not in {check["source_model"], check["target_model"]}
    ]
    af_inconsistent = sum(check["standing"] == "INCONSISTENT" for check in af_checks)
    af_quarantine = sum(check["standing"] == "QUARANTINE" for check in af_checks)
    exp_inconsistent = sum(
        check["standing"] == "INCONSISTENT" for check in experimental_checks
    )
    exp_consistent = sum(check["standing"] == "CONSISTENT" for check in experimental_checks)
    exp_quarantine = sum(check["standing"] == "QUARANTINE" for check in experimental_checks)
    if af_inconsistent and exp_inconsistent == 0 and exp_consistent:
        interpretation = "AF_SPECIFIC_CONFLICT"
    elif af_inconsistent and exp_inconsistent:
        interpretation = "CONFORMATIONAL_OR_MAPPING_CONFLICT"
    elif af_quarantine:
        interpretation = "AF_QUARANTINE"
    elif exp_inconsistent:
        interpretation = "EXPERIMENTAL_CONFORMATIONAL_VARIATION"
    elif af_checks and all(check["standing"] == "CONSISTENT" for check in af_checks):
        interpretation = "NO_AF_CONFLICT"
    else:
        interpretation = "INSUFFICIENT_CHECKS"
    return {
        "oracle_standing": report["standing"],
        "interpretation": interpretation,
        "af_checks": len(af_checks),
        "af_inconsistent": af_inconsistent,
        "af_quarantine": af_quarantine,
        "experimental_checks": len(experimental_checks),
        "experimental_consistent": exp_consistent,
        "experimental_inconsistent": exp_inconsistent,
        "experimental_quarantine": exp_quarantine,
        "ranked_findings": len(report.get("ranked_findings", [])),
    }


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_one(
    accession: str,
    data_dir: Path,
    refresh: bool,
    maximum_experimental: int,
    skip_oracle: bool,
    observed_segments: dict[tuple[str, str, str], tuple[tuple[int, int], ...]],
) -> dict[str, Any]:
    family_dir = data_dir / accession
    family_dir.mkdir(parents=True, exist_ok=True)
    row: dict[str, Any] = {"accession": accession, "status": "STARTED"}
    try:
        af_api = f"https://alphafold.ebi.ac.uk/api/prediction/{accession}"
        af_payload = cached_json(af_api, family_dir / "alphafold_api.json", refresh)
        if not isinstance(af_payload, list) or not af_payload:
            raise ValueError("AlphaFold API returned no prediction")
        af_metadata = af_payload[0]
        af_path = cached_download(af_metadata["pdbUrl"], family_dir / "alphafold.pdb", refresh)
        pae_path = cached_download(af_metadata["paeDocUrl"], family_dir / "pae.json", refresh)

        interpro_url = (
            "https://www.ebi.ac.uk/interpro/api/entry/interpro/protein/uniprot/"
            f"{accession}?format=json&page_size=200"
        )
        interpro = cached_json(interpro_url, family_dir / "interpro.json", refresh)
        domains = parse_interpro_domains(interpro)
        row["interpro_domains"] = len(domains)
        if len(domains) < 2:
            row.update(status="SKIPPED", reason="fewer than two non-overlapping domain annotations")
            return row

        pdbe_url = f"https://www.ebi.ac.uk/pdbe/api/mappings/best_structures/{accession}"
        pdbe = cached_json(pdbe_url, family_dir / "pdbe_best_structures.json", refresh)
        mappings = parse_pdbe_mappings(pdbe, accession, observed=observed_segments)
        mappings = [mapping for mapping in mappings if mapping.observed_segments]
        row["distinct_pdb_entries"] = len(mappings)
        if len(mappings) < 2:
            row.update(status="SKIPPED", reason="fewer than two mapped X-ray/cryo-EM PDB entries")
            return row

        kernel = _load_kernel()
        af_model = kernel.load_structure(
            af_path, model_id=f"AF_{accession}", kind="prediction", chain="A", pae_path=pae_path
        )
        choice = choose_domain_pair(domains, mappings, af_model)
        if choice is None:
            row.update(status="SKIPPED", reason="no domain pair covered by two experimental structures")
            return row
        selected = select_experimental_structures(choice, maximum_experimental)
        row.update({
            "domain_1": choice.first.domain_id,
            "domain_1_name": choice.first.name,
            "domain_1_start": choice.first.start,
            "domain_1_end": choice.first.end,
            "domain_1_mean_plddt": round(choice.first_mean_plddt, 4),
            "domain_2": choice.second.domain_id,
            "domain_2_name": choice.second.name,
            "domain_2_start": choice.second.start,
            "domain_2_end": choice.second.end,
            "domain_2_mean_plddt": round(choice.second_mean_plddt, 4),
            "cross_domain_pae": round(choice.cross_domain_pae, 4),
            "af_pair_preassessable": choice.assessable_by_af,
            "experimental_models": len(selected),
            "pdb_ids": ";".join(mapping.pdb_id.upper() for mapping in selected),
        })
        experiments: list[tuple[ExperimentalMapping, Path]] = []
        for mapping in selected:
            pdb_url = f"https://files.rcsb.org/download/{mapping.pdb_id.upper()}.cif"
            pdb_path = cached_download(
                pdb_url, family_dir / f"{mapping.pdb_id.lower()}.cif", refresh
            )
            experiments.append((mapping, pdb_path))
        manifest_path = family_dir / "manifest.json"
        build_manifest(accession, af_path, pae_path, choice, experiments, manifest_path)
        provenance = {
            "accession": accession,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "alphafold_api": af_api,
                "alphafold_model": af_metadata["pdbUrl"],
                "alphafold_pae": af_metadata["paeDocUrl"],
                "interpro": interpro_url,
                "pdbe_best_structures": pdbe_url,
                "sifts_observed_segments": SIFTS_OBSERVED_URL,
                "experimental_coordinates": [
                    f"https://files.rcsb.org/download/{mapping.pdb_id.upper()}.cif"
                    for mapping in selected
                ],
            },
            "files": {
                path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in [af_path, pae_path, *(path for _, path in experiments)]
            },
            "domain_pair": {
                "first": asdict(choice.first),
                "second": asdict(choice.second),
                "selection_reason": (
                    "maximized AlphaFold assessability, number of distinct mapped PDB entries, "
                    "low cross-domain PAE, pLDDT, then domain coverage"
                ),
            },
            "experimental_mappings": [asdict(mapping) for mapping in selected],
        }
        (family_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
        )
        if not skip_oracle:
            oracle_path = family_dir / "oracle_report.json"
            run_oracle(manifest_path, oracle_path)
            with oracle_path.open(encoding="utf-8") as handle:
                oracle_report = json.load(handle)
            row.update(summarize_oracle(oracle_report))
        row["status"] = "COMPLETE"
        row["reason"] = ""
        return row
    except Exception as error:
        row.update(status="ERROR", reason=f"{type(error).__name__}: {error}")
        return row


def run_cohort(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.accessions:
        accessions = sorted({item.upper() for item in args.accessions})
    else:
        accessions = legacy_accessions(args.legacy_dir)
    if args.max_accessions:
        accessions = accessions[:args.max_accessions]
    if not accessions:
        raise ValueError("no accessions supplied or discovered")
    args.data_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    sifts_path = cached_download(
        SIFTS_OBSERVED_URL,
        args.data_dir / "_sifts" / "uniprot_segments_observed.csv.gz",
        refresh=args.refresh,
    )
    observed_segments = load_observed_segments(sifts_path, set(accessions))
    (args.report_dir / "SOURCE_ACCESSIONS.json").write_text(
        json.dumps(accessions, indent=2) + "\n", encoding="utf-8"
    )
    rows: list[dict[str, Any]] = []
    for index, accession in enumerate(accessions, start=1):
        print(f"[{index}/{len(accessions)}] {accession}", flush=True)
        row = build_one(
            accession=accession,
            data_dir=args.data_dir,
            refresh=args.refresh,
            maximum_experimental=args.max_experimental,
            skip_oracle=args.skip_oracle,
            observed_segments=observed_segments,
        )
        rows.append(row)
        print(f"  {row['status']}: {row.get('interpretation') or row.get('reason') or 'ready'}", flush=True)
        _write_csv(args.report_dir / "SUMMARY.csv", rows)
        (args.report_dir / "COHORT.json").write_text(
            json.dumps(rows, indent=2) + "\n", encoding="utf-8"
        )
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accessions_requested": len(accessions),
        "complete": sum(row["status"] == "COMPLETE" for row in rows),
        "skipped": sum(row["status"] == "SKIPPED" for row in rows),
        "errors": sum(row["status"] == "ERROR" for row in rows),
        "data_dir": str(args.data_dir.resolve()),
        "arguments": {
            "max_experimental": args.max_experimental,
            "refresh": args.refresh,
            "skip_oracle": args.skip_oracle,
        },
    }
    (args.report_dir / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accessions", nargs="*", help="explicit UniProt accessions")
    parser.add_argument("--legacy-dir", type=Path, default=DEFAULT_LEGACY_DIR)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--max-accessions", type=int, default=0)
    parser.add_argument("--max-experimental", type=int, default=3)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--skip-oracle", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    rows = run_cohort(args)
    complete = sum(row["status"] == "COMPLETE" for row in rows)
    errors = sum(row["status"] == "ERROR" for row in rows)
    print(f"Finished: {complete} complete, {errors} errors, {len(rows) - complete - errors} skipped")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
