# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Layer 2.5: Pfam Domain Validation

Cross-references predicted contacts against established Pfam domain annotations.
Agreement between ESM-2 predictions and Pfam active site annotations increases
confidence; disagreement flags contacts for investigation.

This is a verification layer — it does not generate new contacts, but it
provides independent, peer-reviewed evidence for or against existing predictions.

Integration:
- Sits between chemical validation (Layer 2) and semantic validation (Layer 3)
- Uses PfamDomainMapper from chemistry.pfam_domain_mapper
- Produces PfamIssue objects matching the ChemicalIssue pattern
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PfamIssue:
    """Pfam domain validation issue."""
    severity: str              # 'CRITICAL', 'WARNING', 'INFO'
    category: str              # 'domain_agreement', 'active_site', 'cross_domain'
    message: str
    details: Optional[Dict] = None


class PfamDomainValidator:
    """
    Validates contact predictions against Pfam domain annotations.

    Checks:
    1. Active site agreement: high-confidence contacts at known active sites (good)
    2. Domain coherence: contacts within annotated domains (expected)
    3. Cross-domain contacts: contacts bridging different domains (investigate)
    4. Unannotated region contacts: high-confidence contacts outside domains (flag)
    """

    def __init__(self, pfam_mapper=None):
        """
        Initialize the Pfam domain validator.

        Args:
            pfam_mapper: PfamDomainMapper instance. If None, validation is skipped.
        """
        self.pfam_mapper = pfam_mapper

        # Confidence thresholds for flagging
        self._high_confidence_threshold = 0.5
        self._active_site_report_threshold = 0.3

    def validate_domain_contact_agreement(
        self,
        sequence: str,
        contacts: np.ndarray,
        confidence: np.ndarray
    ) -> List[PfamIssue]:
        """
        Validate predicted contacts against Pfam domain annotations.

        Args:
            sequence: Amino acid sequence
            contacts: NxN binary contact map (1 = contact predicted)
            confidence: NxN confidence scores for each contact

        Returns:
            List of PfamIssue findings
        """
        issues: List[PfamIssue] = []

        if self.pfam_mapper is None:
            issues.append(PfamIssue(
                severity='INFO',
                category='pfam_status',
                message='Pfam domain validation skipped (no mapper configured)',
            ))
            return issues

        # Look up domains
        domains = self.pfam_mapper.lookup_domains(sequence)

        if not domains:
            issues.append(PfamIssue(
                severity='INFO',
                category='pfam_status',
                message='No Pfam domains found for this sequence',
                details={'sequence_length': len(sequence)},
            ))
            return issues

        # Report domain annotations found
        domain_summary = [
            f"{d.name} ({d.accession}): {d.start}-{d.end}"
            for d in domains
        ]
        issues.append(PfamIssue(
            severity='INFO',
            category='domain_annotation',
            message=f'Found {len(domains)} Pfam domain(s)',
            details={'domains': domain_summary},
        ))

        # Get active site residues
        active_sites = self.pfam_mapper.get_active_site_residues(sequence)

        # Build per-residue domain map
        domain_map = self.pfam_mapper.get_domain_map(sequence)

        # Analyze contacts
        L = len(sequence)
        active_site_contacts = 0
        same_domain_contacts = 0
        cross_domain_contacts = 0
        unannotated_high_conf = 0
        total_contacts = 0

        for i in range(L):
            for j in range(i + 1, L):
                if contacts[i, j] != 1:
                    continue

                total_contacts += 1
                conf = float(confidence[i, j])
                domain_i = domain_map.get(i)
                domain_j = domain_map.get(j)

                # Check 1: Contact involves active site residue
                if i in active_sites or j in active_sites:
                    active_site_contacts += 1

                # Check 2: Both residues in same domain
                if domain_i is not None and domain_j is not None:
                    if domain_i.accession == domain_j.accession:
                        same_domain_contacts += 1
                    else:
                        cross_domain_contacts += 1
                elif domain_i is None and domain_j is None:
                    # Both outside annotated domains
                    if conf >= self._high_confidence_threshold:
                        unannotated_high_conf += 1

        # Report active site agreement
        if active_site_contacts > 0:
            issues.append(PfamIssue(
                severity='INFO',
                category='active_site',
                message=(
                    f'{active_site_contacts} predicted contact(s) involve '
                    f'known active site residues — independent confirmation'
                ),
                details={
                    'active_site_contacts': active_site_contacts,
                    'total_active_site_residues': len(active_sites),
                },
            ))

        # Report domain coherence
        if same_domain_contacts > 0:
            issues.append(PfamIssue(
                severity='INFO',
                category='domain_agreement',
                message=(
                    f'{same_domain_contacts}/{total_contacts} contacts '
                    f'fall within annotated domains — domain-coherent'
                ),
                details={'same_domain_contacts': same_domain_contacts},
            ))

        # Flag cross-domain contacts
        if cross_domain_contacts > 0:
            severity = 'WARNING' if cross_domain_contacts > total_contacts * 0.3 else 'INFO'
            issues.append(PfamIssue(
                severity=severity,
                category='cross_domain',
                message=(
                    f'{cross_domain_contacts} contact(s) bridge different Pfam domains '
                    f'— may indicate domain interfaces or warrant investigation'
                ),
                details={'cross_domain_contacts': cross_domain_contacts},
            ))

        # Flag high-confidence contacts outside annotated regions
        if unannotated_high_conf > 0:
            severity = 'WARNING' if unannotated_high_conf > 5 else 'INFO'
            issues.append(PfamIssue(
                severity=severity,
                category='unannotated_region',
                message=(
                    f'{unannotated_high_conf} high-confidence contact(s) fall '
                    f'outside annotated Pfam domains — novel or unannotated region'
                ),
                details={
                    'unannotated_high_confidence': unannotated_high_conf,
                    'threshold': self._high_confidence_threshold,
                },
            ))

        return issues

    def generate_report(self, issues: List[PfamIssue]) -> str:
        """Generate human-readable report from Pfam validation issues."""
        lines = []
        lines.append("-" * 50)
        lines.append("PFAM DOMAIN VALIDATION")
        lines.append("-" * 50)

        if not issues:
            lines.append("  No Pfam issues found.")
            return "\n".join(lines)

        for issue in issues:
            prefix = {
                'CRITICAL': '[X]',
                'WARNING': '[!] ',
                'INFO': '[i] ',
            }.get(issue.severity, '    ')

            lines.append(f"  {prefix} [{issue.category}] {issue.message}")

        critical = len([i for i in issues if i.severity == 'CRITICAL'])
        warnings = len([i for i in issues if i.severity == 'WARNING'])
        info = len([i for i in issues if i.severity == 'INFO'])
        lines.append(f"  Summary: {critical} critical, {warnings} warnings, {info} info")
        lines.append("-" * 50)

        return "\n".join(lines)
