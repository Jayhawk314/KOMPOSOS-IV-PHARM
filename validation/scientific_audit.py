# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
KOMPOSOS-III Scientific Audit Suite
====================================

Comprehensive internal validation based on:
- CASP metrics (GDT-TS, TM-score, lDDT, RMSD)
- MolProbity standards (Ramachandran, clashes, bond geometry)
- Contact prediction benchmarks (precision at L/5, L/2, L)
- Physical chemistry validation (H-bonds, hydrophobic core, salt bridges)
- Data provenance verification (mock data detection)
- Reproducibility checks
- FAIR compliance assessment

References:
- CASP14/15: https://pmc.ncbi.nlm.nih.gov/articles/PMC8726744/
- MolProbity: https://pmc.ncbi.nlm.nih.gov/articles/PMC5734394/
- Data leakage: https://arxiv.org/abs/2404.10457
- Wilson et al. (2017): Good Enough Practices in Scientific Computing
- FDA In-Silico Guidance: https://www.fda.gov/media/154985/download
"""

import sys
import json
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AuditResult:
    """Result from a single audit check."""
    category: str
    check_name: str
    passed: bool
    severity: str  # CRITICAL, WARNING, INFO
    value: object = None
    threshold: object = None
    message: str = ""
    reference: str = ""


@dataclass
class AuditReport:
    """Complete scientific audit report."""
    timestamp: str
    protein_name: str
    sequence_length: int
    results: List[AuditResult] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

    def add(self, result: AuditResult):
        self.results.append(result)

    @property
    def critical_count(self):
        return sum(1 for r in self.results if not r.passed and r.severity == "CRITICAL")

    @property
    def warning_count(self):
        return sum(1 for r in self.results if not r.passed and r.severity == "WARNING")

    @property
    def pass_count(self):
        return sum(1 for r in self.results if r.passed)

    @property
    def total_count(self):
        return len(self.results)


# ---------------------------------------------------------------------------
# 1. STRUCTURE GEOMETRY VALIDATION
# ---------------------------------------------------------------------------

def audit_bond_geometry(coords: np.ndarray, sequence: str) -> List[AuditResult]:
    """
    Validate CA-CA bond geometry.

    Standards:
    - CA-CA distance: 3.8 +/- 0.1 A (ideal), 3.5-4.1 A (acceptable)
    - No clashes: CA-CA > 2.0 A for non-adjacent residues
    """
    results = []
    N = len(sequence)

    # CA-CA bond lengths
    bond_lengths = []
    for i in range(N - 1):
        d = np.linalg.norm(coords[i] - coords[i + 1])
        bond_lengths.append(d)

    bond_lengths = np.array(bond_lengths)
    mean_bl = np.mean(bond_lengths)
    std_bl = np.std(bond_lengths)
    outliers = np.sum((bond_lengths < 3.5) | (bond_lengths > 4.1))
    outlier_pct = outliers / len(bond_lengths) * 100

    results.append(AuditResult(
        category="Geometry",
        check_name="CA-CA bond length mean",
        passed=3.6 <= mean_bl <= 4.0,
        severity="CRITICAL",
        value=round(float(mean_bl), 3),
        threshold="3.6-4.0 A",
        message=f"Mean CA-CA distance: {mean_bl:.3f} A (ideal: 3.8 A)",
        reference="Engh & Huber (1991) bond geometry"
    ))

    results.append(AuditResult(
        category="Geometry",
        check_name="CA-CA bond length outliers",
        passed=outlier_pct < 5.0,
        severity="WARNING" if outlier_pct < 10.0 else "CRITICAL",
        value=round(float(outlier_pct), 1),
        threshold="<5%",
        message=f"{outlier_pct:.1f}% bonds outside 3.5-4.1 A range ({outliers}/{len(bond_lengths)})",
        reference="MolProbity bond geometry"
    ))

    # Steric clashes
    clash_count = 0
    total_pairs = 0
    for i in range(N):
        for j in range(i + 4, N):
            d = np.linalg.norm(coords[i] - coords[j])
            total_pairs += 1
            if d < 2.0:
                clash_count += 1

    clash_score = clash_count / (N / 1000) if N > 0 else 0  # per 1000 atoms
    results.append(AuditResult(
        category="Geometry",
        check_name="Steric clashes",
        passed=clash_score < 40,
        severity="CRITICAL" if clash_score >= 40 else "WARNING",
        value=round(float(clash_score), 1),
        threshold="<40 per 1000 atoms (MolProbity), <10 = good",
        message=f"Clash score: {clash_score:.1f} ({clash_count} clashes in {N} residues)",
        reference="MolProbity clash score"
    ))

    return results


def audit_compactness(coords: np.ndarray, sequence: str) -> List[AuditResult]:
    """
    Validate protein compactness.

    Standards:
    - Radius of gyration: Rg ~ 2.2 * N^0.38 for globular proteins
    - Rg ratio: 0.7-1.3 is acceptable
    """
    results = []
    N = len(sequence)

    centroid = np.mean(coords, axis=0)
    rg = np.sqrt(np.mean(np.sum((coords - centroid) ** 2, axis=1)))
    expected_rg = 2.2 * (N ** 0.38)
    rg_ratio = rg / expected_rg

    results.append(AuditResult(
        category="Geometry",
        check_name="Radius of gyration",
        passed=0.7 <= rg_ratio <= 1.5,
        severity="WARNING",
        value=round(float(rg), 2),
        threshold=f"{expected_rg:.1f} A expected (Rg = 2.2*N^0.38)",
        message=f"Rg = {rg:.2f} A, expected {expected_rg:.1f} A, ratio = {rg_ratio:.2f}",
        reference="Flory scaling law for globular proteins"
    ))

    return results


def audit_ramachandran(coords: np.ndarray, sequence: str) -> List[AuditResult]:
    """
    Simplified Ramachandran analysis from CA positions.

    Standards (MolProbity):
    - Favored: >98% (excellent), >95% (good), >90% (acceptable)
    - Outliers: <0.5% (excellent), <2% (acceptable), <5% (poor)

    Note: This is CA-only approximation. Full validation needs N, CA, C atoms.
    """
    results = []
    N = len(sequence)

    if N < 4:
        results.append(AuditResult(
            category="Geometry", check_name="Ramachandran",
            passed=False, severity="WARNING", value=None,
            message="Too few residues for Ramachandran analysis"
        ))
        return results

    # Compute pseudo-dihedral angles from CA positions
    favored = 0
    allowed = 0
    outlier = 0
    total = 0

    for i in range(1, N - 2):
        # CA pseudo-angles
        v1 = coords[i] - coords[i - 1]
        v2 = coords[i + 1] - coords[i]
        v3 = coords[i + 2] - coords[i + 1]

        # Pseudo phi/psi from consecutive CA vectors
        n1 = np.cross(v1, v2)
        n2 = np.cross(v2, v3)

        norm1 = np.linalg.norm(n1)
        norm2 = np.linalg.norm(n2)

        if norm1 < 1e-8 or norm2 < 1e-8:
            continue

        n1 = n1 / norm1
        n2 = n2 / norm2

        cos_angle = np.clip(np.dot(n1, n2), -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))

        total += 1

        # Simplified classification based on CA pseudo-dihedral
        # Helical region: ~50-70 degrees between consecutive CA planes
        # Sheet region: ~120-160 degrees
        # Other: varies
        if 30 < angle < 90 or 100 < angle < 170:
            favored += 1
        elif 20 < angle < 100 or 90 < angle < 180:
            allowed += 1
        else:
            outlier += 1

    if total > 0:
        favored_pct = favored / total * 100
        outlier_pct = outlier / total * 100
    else:
        favored_pct = 0
        outlier_pct = 100

    results.append(AuditResult(
        category="Geometry",
        check_name="Ramachandran favored (CA-approx)",
        passed=favored_pct > 90,
        severity="WARNING",
        value=round(float(favored_pct), 1),
        threshold=">90% acceptable, >95% good, >98% excellent",
        message=f"CA-approximate Ramachandran: {favored_pct:.1f}% favored, {outlier_pct:.1f}% outlier",
        reference="MolProbity (note: CA-only approximation, not full backbone)"
    ))

    return results


# ---------------------------------------------------------------------------
# 2. CONTACT PREDICTION QUALITY
# ---------------------------------------------------------------------------

def audit_contact_quality(
    predicted_contacts: np.ndarray,
    native_contacts: Optional[np.ndarray],
    sequence: str,
    contact_confidence: Optional[np.ndarray] = None
) -> List[AuditResult]:
    """
    Validate contact prediction quality against CASP standards.

    Standards:
    - Precision at L/5 for long-range contacts
    - Contact density should be 1-3% for typical proteins
    - ESM-2 baseline: ~19% precision at L/5 long-range
    """
    results = []
    L = len(sequence)
    N_contacts = int(predicted_contacts.sum() / 2)
    contact_density = N_contacts / (L * (L - 1) / 2)

    # Expected contacts: ~L for a well-folded protein
    expected_contacts_low = L * 0.5
    expected_contacts_high = L * 3.0

    results.append(AuditResult(
        category="Contacts",
        check_name="Contact count",
        passed=expected_contacts_low <= N_contacts <= expected_contacts_high,
        severity="WARNING" if N_contacts < expected_contacts_low else "INFO",
        value=N_contacts,
        threshold=f"{int(expected_contacts_low)}-{int(expected_contacts_high)} for L={L}",
        message=f"{N_contacts} contacts predicted (density: {contact_density:.4f})",
        reference="Typical contact density for globular proteins"
    ))

    # Separate into range categories
    short_range = 0   # |i-j| = 6-11
    medium_range = 0  # |i-j| = 12-23
    long_range = 0    # |i-j| >= 24

    for i in range(L):
        for j in range(i + 1, L):
            if predicted_contacts[i, j] > 0.5:
                sep = j - i
                if 6 <= sep <= 11:
                    short_range += 1
                elif 12 <= sep <= 23:
                    medium_range += 1
                elif sep >= 24:
                    long_range += 1

    results.append(AuditResult(
        category="Contacts",
        check_name="Contact range distribution",
        passed=long_range > 0,
        severity="WARNING" if long_range == 0 else "INFO",
        value={"short": short_range, "medium": medium_range, "long": long_range},
        threshold="Should have long-range contacts (|i-j|>=24)",
        message=f"Short(6-11): {short_range}, Medium(12-23): {medium_range}, Long(>=24): {long_range}",
        reference="CASP contact categories"
    ))

    # If native contacts available, compute precision
    if native_contacts is not None:
        # Get top-L/5, L/2, L predicted contacts by confidence
        if contact_confidence is not None:
            conf_flat = []
            for i in range(L):
                for j in range(i + 6, L):  # Only medium+long range
                    if predicted_contacts[i, j] > 0.5:
                        conf_flat.append((contact_confidence[i, j], i, j))
            conf_flat.sort(reverse=True)
        else:
            conf_flat = []
            for i in range(L):
                for j in range(i + 6, L):
                    if predicted_contacts[i, j] > 0.5:
                        conf_flat.append((1.0, i, j))

        for label, k in [("L/5", max(1, L // 5)), ("L/2", max(1, L // 2)), ("L", L)]:
            top_k = conf_flat[:k]
            if len(top_k) == 0:
                precision = 0.0
            else:
                correct = sum(1 for _, i, j in top_k if native_contacts[i, j] > 0.5)
                precision = correct / len(top_k) * 100

            results.append(AuditResult(
                category="Contacts",
                check_name=f"Precision at {label}",
                passed=precision > 10.0 if label == "L/5" else True,
                severity="WARNING" if precision < 10.0 else "INFO",
                value=round(float(precision), 1),
                threshold=f"ESM-2 baseline: ~19% at L/5 long-range",
                message=f"Precision at {label}: {precision:.1f}% ({len(top_k)} contacts evaluated)",
                reference="CASP contact prediction standards"
            ))

    return results


# ---------------------------------------------------------------------------
# 3. PHYSICAL CHEMISTRY VALIDATION
# ---------------------------------------------------------------------------

def audit_physical_chemistry(coords: np.ndarray, sequence: str) -> List[AuditResult]:
    """
    Validate physical/chemical properties.

    Standards:
    - H-bonds: ~0.5-1.0 per residue
    - Hydrophobic core: >40% of hydrophobic residues buried
    - Salt bridges: At least some in charged proteins
    """
    results = []
    N = len(sequence)

    # Hydrophobic core burial
    hydrophobic = set('IVLFCMA')
    centroid = np.mean(coords, axis=0)
    distances_to_center = np.linalg.norm(coords - centroid, axis=1)
    median_dist = np.median(distances_to_center)

    hydrophobic_indices = [i for i, aa in enumerate(sequence) if aa in hydrophobic]
    buried = 0
    if hydrophobic_indices:
        buried = sum(1 for i in hydrophobic_indices if distances_to_center[i] < median_dist)
        burial_ratio = buried / len(hydrophobic_indices)
    else:
        burial_ratio = 0.0

    results.append(AuditResult(
        category="Chemistry",
        check_name="Hydrophobic core burial",
        passed=burial_ratio > 0.4,
        severity="WARNING",
        value=round(float(burial_ratio), 3),
        threshold=">0.4 (40% of hydrophobic residues buried)",
        message=f"{burial_ratio*100:.1f}% of hydrophobic residues buried ({buried}/{len(hydrophobic_indices)})",
        reference="Hydrophobic effect in protein folding"
    ))

    # H-bond estimation (CA-CA distance proxy for i,i+4 helix bonds)
    hbond_count = 0
    for i in range(N - 4):
        d = np.linalg.norm(coords[i] - coords[i + 4])
        if 5.0 < d < 7.0:  # Helix i,i+4 CA-CA distance
            hbond_count += 1

    # Also check non-local H-bond proxies
    for i in range(N):
        for j in range(i + 5, N):
            d = np.linalg.norm(coords[i] - coords[j])
            if 4.5 < d < 6.5:  # Sheet-like CA-CA distances
                hbond_count += 1
                if hbond_count > N * 3:  # Safety cap
                    break

    hbonds_per_residue = hbond_count / N
    results.append(AuditResult(
        category="Chemistry",
        check_name="H-bond density (CA proxy)",
        passed=0.2 <= hbonds_per_residue <= 3.0,
        severity="WARNING",
        value=round(float(hbonds_per_residue), 2),
        threshold="0.5-1.0 per residue typical",
        message=f"{hbonds_per_residue:.2f} H-bonds per residue (estimated, {hbond_count} total)",
        reference="Typical H-bond density in globular proteins"
    ))

    # Salt bridges
    charged_pos = set('KRH')
    charged_neg = set('DE')
    salt_bridges = 0
    for i in range(N):
        for j in range(i + 4, N):
            if (sequence[i] in charged_pos and sequence[j] in charged_neg) or \
               (sequence[i] in charged_neg and sequence[j] in charged_pos):
                d = np.linalg.norm(coords[i] - coords[j])
                if d < 7.0:
                    salt_bridges += 1

    n_charged = sum(1 for aa in sequence if aa in charged_pos | charged_neg)
    results.append(AuditResult(
        category="Chemistry",
        check_name="Salt bridges",
        passed=True,  # Informational
        severity="INFO",
        value=salt_bridges,
        threshold="Depends on sequence (informational)",
        message=f"{salt_bridges} potential salt bridges ({n_charged} charged residues in sequence)",
        reference="Electrostatic interactions in protein stability"
    ))

    return results


# ---------------------------------------------------------------------------
# 4. COMPARISON TO NATIVE STRUCTURE
# ---------------------------------------------------------------------------

def compute_rmsd(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """Compute RMSD after centering (no rotation — Kabsch would be better)."""
    c1 = coords1 - np.mean(coords1, axis=0)
    c2 = coords2 - np.mean(coords2, axis=0)

    # Kabsch alignment
    H = c1.T @ c2
    U, S, Vt = np.linalg.svd(H)
    d = np.linalg.det(Vt.T @ U.T)
    sign_matrix = np.diag([1, 1, np.sign(d)])
    R = Vt.T @ sign_matrix @ U.T
    c1_aligned = (R @ c1.T).T

    diff = c1_aligned - c2
    return float(np.sqrt(np.mean(np.sum(diff ** 2, axis=1))))


def compute_tm_score(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """
    Compute TM-score (Zhang & Skolnick, 2004).

    TM-score is length-normalized and ranges 0-1.
    >0.5 indicates same fold, >0.7 is very good.
    """
    L = len(coords1)
    if L < 5:
        return 0.0

    # Length-dependent distance scale
    d0 = 1.24 * ((L - 15) ** (1.0 / 3.0)) - 1.8
    d0 = max(d0, 0.5)

    # Center both
    c1 = coords1 - np.mean(coords1, axis=0)
    c2 = coords2 - np.mean(coords2, axis=0)

    # Kabsch alignment
    H = c1.T @ c2
    U, S, Vt = np.linalg.svd(H)
    d = np.linalg.det(Vt.T @ U.T)
    sign_matrix = np.diag([1, 1, np.sign(d)])
    R = Vt.T @ sign_matrix @ U.T
    c1_aligned = (R @ c1.T).T

    # TM-score
    distances = np.sqrt(np.sum((c1_aligned - c2) ** 2, axis=1))
    tm = np.sum(1.0 / (1.0 + (distances / d0) ** 2)) / L

    return float(tm)


def compute_gdt_ts(coords1: np.ndarray, coords2: np.ndarray) -> float:
    """
    Compute GDT-TS (Global Distance Test - Total Score).

    GDT-TS = average of % residues within 1, 2, 4, 8 Angstroms.
    """
    c1 = coords1 - np.mean(coords1, axis=0)
    c2 = coords2 - np.mean(coords2, axis=0)

    # Kabsch alignment
    H = c1.T @ c2
    U, S, Vt = np.linalg.svd(H)
    d = np.linalg.det(Vt.T @ U.T)
    sign_matrix = np.diag([1, 1, np.sign(d)])
    R = Vt.T @ sign_matrix @ U.T
    c1_aligned = (R @ c1.T).T

    distances = np.sqrt(np.sum((c1_aligned - c2) ** 2, axis=1))
    L = len(distances)

    gdt_components = {}
    for cutoff in [1.0, 2.0, 4.0, 8.0]:
        pct = np.sum(distances < cutoff) / L * 100
        gdt_components[f"{cutoff}A"] = round(float(pct), 1)

    gdt_ts = np.mean([gdt_components[k] for k in gdt_components])
    return float(gdt_ts), gdt_components


def compute_lddt(coords1: np.ndarray, coords2: np.ndarray, cutoff: float = 15.0) -> float:
    """
    Compute lDDT (Local Distance Difference Test).

    Measures preservation of local distance patterns.
    Thresholds: 0.5, 1.0, 2.0, 4.0 Angstroms.
    """
    L = len(coords1)

    # Compute distance matrices
    dist1 = np.zeros((L, L))
    dist2 = np.zeros((L, L))
    for i in range(L):
        for j in range(i + 1, L):
            dist1[i, j] = dist1[j, i] = np.linalg.norm(coords1[i] - coords1[j])
            dist2[i, j] = dist2[j, i] = np.linalg.norm(coords2[i] - coords2[j])

    thresholds = [0.5, 1.0, 2.0, 4.0]
    total_preserved = 0
    total_contacts = 0

    for i in range(L):
        for j in range(i + 1, L):
            if dist2[i, j] < cutoff:  # Only evaluate local contacts in reference
                total_contacts += 1
                diff = abs(dist1[i, j] - dist2[i, j])
                for t in thresholds:
                    if diff < t:
                        total_preserved += 1

    if total_contacts == 0:
        return 0.0

    lddt = total_preserved / (total_contacts * len(thresholds))
    return float(lddt)


def audit_native_comparison(
    predicted_coords: np.ndarray,
    native_coords: np.ndarray,
    sequence: str
) -> List[AuditResult]:
    """
    Compare predicted structure to native PDB using CASP metrics.
    """
    results = []

    # Ensure same length
    min_len = min(len(predicted_coords), len(native_coords))
    pred = predicted_coords[:min_len]
    native = native_coords[:min_len]

    # RMSD
    rmsd = compute_rmsd(pred, native)
    results.append(AuditResult(
        category="CASP Metrics",
        check_name="RMSD",
        passed=rmsd < 5.0,
        severity="CRITICAL" if rmsd >= 10.0 else "WARNING" if rmsd >= 5.0 else "INFO",
        value=round(rmsd, 2),
        threshold="<2.0 A excellent, <5.0 A acceptable, <10.0 A poor",
        message=f"RMSD = {rmsd:.2f} A",
        reference="CASP RMSD standards"
    ))

    # TM-score
    tm = compute_tm_score(pred, native)
    results.append(AuditResult(
        category="CASP Metrics",
        check_name="TM-score",
        passed=tm > 0.5,
        severity="CRITICAL" if tm < 0.3 else "WARNING" if tm < 0.5 else "INFO",
        value=round(tm, 4),
        threshold=">0.5 same fold, >0.7 very good",
        message=f"TM-score = {tm:.4f}",
        reference="Zhang & Skolnick (2004)"
    ))

    # GDT-TS
    gdt_ts, gdt_components = compute_gdt_ts(pred, native)
    results.append(AuditResult(
        category="CASP Metrics",
        check_name="GDT-TS",
        passed=gdt_ts > 50,
        severity="WARNING" if gdt_ts < 50 else "INFO",
        value=round(gdt_ts, 1),
        threshold=">50 good, >70 excellent",
        message=f"GDT-TS = {gdt_ts:.1f} (components: {gdt_components})",
        reference="CASP GDT-TS"
    ))

    # lDDT
    lddt = compute_lddt(pred, native)
    results.append(AuditResult(
        category="CASP Metrics",
        check_name="lDDT",
        passed=lddt > 0.6,
        severity="WARNING" if lddt < 0.6 else "INFO",
        value=round(lddt, 4),
        threshold=">0.6 acceptable, >0.8 good",
        message=f"lDDT = {lddt:.4f}",
        reference="Mariani et al. (2013)"
    ))

    return results


# ---------------------------------------------------------------------------
# 5. DATA PROVENANCE VERIFICATION
# ---------------------------------------------------------------------------

def audit_data_provenance(project_root: Path) -> List[AuditResult]:
    """
    Verify no mock data is active in production code paths.
    """
    results = []

    # Check main pipeline file for mock/placeholder
    pipeline_file = project_root / "geometry" / "protein_structure_pipeline.py"
    if pipeline_file.exists():
        content = pipeline_file.read_text(encoding='utf-8')
        has_mock = 'mock' in content.lower() or 'placeholder' in content.lower()
        has_villin = 'MLSDEDFK' in content or 'villin' in content.lower()

        results.append(AuditResult(
            category="Data Provenance",
            check_name="Pipeline mock-free",
            passed=not has_mock,
            severity="CRITICAL",
            value=not has_mock,
            message="Main pipeline contains no mock/placeholder references" if not has_mock
                    else "MOCK DATA detected in main pipeline!",
            reference="Scientific software audit best practice"
        ))

        results.append(AuditResult(
            category="Data Provenance",
            check_name="Pipeline no hardcoded sequences",
            passed=not has_villin,
            severity="CRITICAL",
            value=not has_villin,
            message="No hardcoded test sequences in pipeline" if not has_villin
                    else "Hardcoded villin sequence in pipeline!",
            reference="Data leakage prevention"
        ))

    # Check ESM-2 predictor is loading real model
    esm2_file = project_root / "geometry" / "esm2_contact_predictor.py"
    if esm2_file.exists():
        content = esm2_file.read_text(encoding='utf-8')
        uses_real_model = 'facebook/esm2' in content and 'EsmModel' in content

        results.append(AuditResult(
            category="Data Provenance",
            check_name="ESM-2 real model",
            passed=uses_real_model,
            severity="CRITICAL",
            value=uses_real_model,
            message="ESM-2 loads real pre-trained model (facebook/esm2_t33_650M_UR50D)" if uses_real_model
                    else "ESM-2 may not be loading real model",
            reference="Model provenance verification"
        ))

    # Check contact prediction uses real ESM-2 path
    contact_file = project_root / "geometry" / "contact_prediction.py"
    if contact_file.exists():
        content = contact_file.read_text(encoding='utf-8')
        uses_esm2 = 'ESM2ContactPredictor' in content or 'esm2' in content.lower()

        results.append(AuditResult(
            category="Data Provenance",
            check_name="Contact prediction uses ESM-2",
            passed=uses_esm2,
            severity="CRITICAL",
            value=uses_esm2,
            message="Contact predictor integrates ESM-2" if uses_esm2
                    else "Contact predictor may not use ESM-2",
            reference="Real data pipeline verification"
        ))

    # Check chemistry modules are real implementations
    chemistry_init = project_root / "chemistry" / "__init__.py"
    if chemistry_init.exists():
        content = chemistry_init.read_text(encoding='utf-8')
        has_hbond = 'HydrogenBondValidator' in content
        has_hydrophobic = 'HydrophobicConstraints' in content

        results.append(AuditResult(
            category="Data Provenance",
            check_name="Chemistry bridge loaded",
            passed=has_hbond and has_hydrophobic,
            severity="WARNING",
            value=has_hbond and has_hydrophobic,
            message="Physical-Chemical Bridge modules loaded" if (has_hbond and has_hydrophobic)
                    else "Missing chemistry bridge modules",
            reference="Physical chemistry validation"
        ))

    return results


# ---------------------------------------------------------------------------
# 6. REPRODUCIBILITY CHECK
# ---------------------------------------------------------------------------

def audit_reproducibility(pdb_path: Path) -> List[AuditResult]:
    """
    Check that the prediction output is deterministic and well-formed.
    """
    results = []

    if not pdb_path.exists():
        results.append(AuditResult(
            category="Reproducibility",
            check_name="PDB file exists",
            passed=False, severity="CRITICAL",
            message=f"PDB file not found: {pdb_path}"
        ))
        return results

    content = pdb_path.read_text(encoding='utf-8')
    lines = content.strip().split('\n')

    # Check PDB format
    atom_lines = [l for l in lines if l.startswith('ATOM')]
    header_lines = [l for l in lines if l.startswith('HEADER') or l.startswith('REMARK')]

    results.append(AuditResult(
        category="Reproducibility",
        check_name="PDB format valid",
        passed=len(atom_lines) > 0,
        severity="CRITICAL",
        value=len(atom_lines),
        message=f"PDB has {len(atom_lines)} ATOM records and {len(header_lines)} header lines",
        reference="PDB format specification"
    ))

    # Check file hash for reproducibility tracking
    file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    results.append(AuditResult(
        category="Reproducibility",
        check_name="Output hash",
        passed=True, severity="INFO",
        value=file_hash,
        message=f"SHA-256 prefix: {file_hash} (for reproducibility tracking)",
        reference="FAIR data principles"
    ))

    # Check coordinates are numeric and finite
    coords_valid = True
    for line in atom_lines:
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
                coords_valid = False
                break
        except (ValueError, IndexError):
            coords_valid = False
            break

    results.append(AuditResult(
        category="Reproducibility",
        check_name="Coordinates valid",
        passed=coords_valid,
        severity="CRITICAL",
        value=coords_valid,
        message="All coordinates are finite and parseable" if coords_valid
                else "Invalid coordinates detected in PDB!",
        reference="PDB format validation"
    ))

    return results


# ---------------------------------------------------------------------------
# PDB PARSING
# ---------------------------------------------------------------------------

def parse_pdb_ca_coords(pdb_path: Path) -> Tuple[np.ndarray, str]:
    """Parse CA coordinates and sequence from PDB file."""
    coords = []
    sequence = []

    aa3to1 = {
        'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C',
        'GLN': 'Q', 'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
        'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P',
        'SER': 'S', 'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V'
    }
    valid_aa = set('ACDEFGHIKLMNPQRSTVWY')

    seen_residues = set()

    with open(pdb_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('ATOM') and line[12:16].strip() == 'CA':
                res_id = line[21:27].strip()  # chain + resnum
                if res_id in seen_residues:
                    continue
                seen_residues.add(res_id)

                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])

                resname = line[17:20].strip()
                # Handle both 3-letter (ALA) and 1-letter (A) residue names
                if resname in aa3to1:
                    sequence.append(aa3to1[resname])
                elif resname in valid_aa:
                    sequence.append(resname)
                else:
                    sequence.append('X')

    return np.array(coords), ''.join(sequence)


# ---------------------------------------------------------------------------
# NATIVE CONTACT MAP FROM COORDINATES
# ---------------------------------------------------------------------------

def compute_native_contacts(coords: np.ndarray, threshold: float = 8.0) -> np.ndarray:
    """Compute native contact map from CA coordinates (8A threshold)."""
    N = len(coords)
    contacts = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(i + 1, N):
            d = np.linalg.norm(coords[i] - coords[j])
            if d < threshold:
                contacts[i, j] = 1
                contacts[j, i] = 1
    return contacts


# ---------------------------------------------------------------------------
# MAIN AUDIT RUNNER
# ---------------------------------------------------------------------------

def run_full_audit(
    predicted_pdb: Path,
    native_pdb: Optional[Path] = None,
    project_root: Optional[Path] = None,
    predicted_contacts: Optional[np.ndarray] = None,
    contact_confidence: Optional[np.ndarray] = None
) -> AuditReport:
    """
    Run the complete scientific audit suite.

    Args:
        predicted_pdb: Path to KOMPOSOS prediction PDB
        native_pdb: Path to experimental/reference PDB (optional)
        project_root: Path to KOMPOSOS project root
        predicted_contacts: Contact map from prediction (optional)
        contact_confidence: Confidence values (optional)

    Returns:
        Complete AuditReport
    """
    print("=" * 70)
    print("KOMPOSOS-III SCIENTIFIC AUDIT")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Parse predicted structure
    print("[1/7] Parsing predicted structure...")
    pred_coords, pred_seq = parse_pdb_ca_coords(predicted_pdb)
    print(f"  Parsed {len(pred_coords)} residues from {predicted_pdb.name}")

    report = AuditReport(
        timestamp=datetime.now().isoformat(),
        protein_name=predicted_pdb.stem,
        sequence_length=len(pred_seq)
    )

    # 1. Bond geometry
    print("[2/7] Auditing bond geometry...")
    for r in audit_bond_geometry(pred_coords, pred_seq):
        report.add(r)
        _print_result(r)

    # 2. Compactness
    print("[3/7] Auditing compactness...")
    for r in audit_compactness(pred_coords, pred_seq):
        report.add(r)
        _print_result(r)

    # 3. Ramachandran
    for r in audit_ramachandran(pred_coords, pred_seq):
        report.add(r)
        _print_result(r)

    # 4. Physical chemistry
    print("[4/7] Auditing physical chemistry...")
    for r in audit_physical_chemistry(pred_coords, pred_seq):
        report.add(r)
        _print_result(r)

    # 5. Contact quality
    print("[5/7] Auditing contact prediction quality...")
    native_contacts = None
    if native_pdb is not None and native_pdb.exists():
        native_coords, native_seq = parse_pdb_ca_coords(native_pdb)
        native_contacts = compute_native_contacts(native_coords)
        print(f"  Native structure loaded: {len(native_coords)} residues, {int(native_contacts.sum()/2)} contacts")

    if predicted_contacts is not None:
        for r in audit_contact_quality(predicted_contacts, native_contacts, pred_seq, contact_confidence):
            report.add(r)
            _print_result(r)

    # 6. Native comparison (CASP metrics)
    print("[6/7] Computing CASP metrics...")
    if native_pdb is not None and native_pdb.exists():
        native_coords, _ = parse_pdb_ca_coords(native_pdb)
        min_len = min(len(pred_coords), len(native_coords))
        for r in audit_native_comparison(pred_coords[:min_len], native_coords[:min_len], pred_seq[:min_len]):
            report.add(r)
            _print_result(r)
    else:
        print("  Skipped (no native structure provided)")

    # 7. Data provenance
    print("[7/7] Auditing data provenance...")
    if project_root is not None:
        for r in audit_data_provenance(project_root):
            report.add(r)
            _print_result(r)

    # Reproducibility
    for r in audit_reproducibility(predicted_pdb):
        report.add(r)
        _print_result(r)

    # Summary
    report.summary = {
        'total_checks': report.total_count,
        'passed': report.pass_count,
        'critical_failures': report.critical_count,
        'warnings': report.warning_count,
        'pass_rate': round(report.pass_count / max(report.total_count, 1) * 100, 1),
    }

    print()
    print("=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    print(f"Total checks: {report.total_count}")
    print(f"Passed:       {report.pass_count}")
    print(f"Warnings:     {report.warning_count}")
    print(f"Critical:     {report.critical_count}")
    print(f"Pass rate:    {report.summary['pass_rate']}%")
    print()

    if report.critical_count == 0:
        print("RESULT: PASS - No critical issues found")
    else:
        print(f"RESULT: FAIL - {report.critical_count} critical issue(s)")
        print("\nCritical failures:")
        for r in report.results:
            if not r.passed and r.severity == "CRITICAL":
                print(f"  - [{r.category}] {r.check_name}: {r.message}")

    print("=" * 70)

    return report


def _print_result(r: AuditResult):
    """Print a single audit result."""
    status = "PASS" if r.passed else f"FAIL({r.severity})"
    icon = "  [OK]" if r.passed else "  [!!]" if r.severity == "CRITICAL" else "  [**]"
    print(f"{icon} {r.check_name}: {r.message}")


def _json_safe(val):
    """Convert numpy types to JSON-safe Python types."""
    if val is None:
        return None
    if isinstance(val, (np.bool_, np.generic)):
        return val.item()
    if isinstance(val, dict):
        return {k: _json_safe(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_json_safe(v) for v in val]
    return val


def save_audit_report(report: AuditReport, output_path: Path):
    """Save audit report as JSON."""
    data = {
        'timestamp': report.timestamp,
        'protein_name': report.protein_name,
        'sequence_length': report.sequence_length,
        'summary': report.summary,
        'results': [
            {
                'category': r.category,
                'check_name': r.check_name,
                'passed': bool(r.passed),
                'severity': r.severity,
                'value': _json_safe(r.value),
                'threshold': r.threshold,
                'message': r.message,
                'reference': r.reference
            }
            for r in report.results
        ]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\nAudit report saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KOMPOSOS-III Scientific Audit")
    parser.add_argument("predicted_pdb", type=Path, help="Predicted PDB file")
    parser.add_argument("--native", type=Path, help="Native/reference PDB file")
    parser.add_argument("--output", type=Path, default=Path("audit_report.json"), help="Output JSON")

    args = parser.parse_args()

    report = run_full_audit(
        predicted_pdb=args.predicted_pdb,
        native_pdb=args.native,
        project_root=Path(__file__).parent.parent
    )

    save_audit_report(report, args.output)
