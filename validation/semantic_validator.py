# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Layer 3: Semantic Validation

Uses sentence embeddings to catch interpretation errors:
- Terminology consistency (is "Ricci curvature" used correctly?)
- Mathematical vs physical confusion (curvature ≠ mechanism)
- Overclaiming (claiming causation from correlation)
- Claim-limitation consistency
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class SemanticIssue:
    """Semantic validation issue"""
    severity: str
    category: str
    message: str
    details: Optional[Dict] = None


class ProteinInterpretationValidator:
    """
    Validates interpretations using semantic analysis.

    Falls back to rule-based checking if sentence-transformers not available.
    """

    def __init__(self):
        # Try to import sentence transformers
        self.use_embeddings = False
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
        except ImportError:
            print("Warning: sentence-transformers not installed. Using rule-based validation only.")
            print("Install with: pip install sentence-transformers")
            self.model = None

        # Correct definitions of mathematical terms
        self.correct_definitions = {
            'ricci curvature': 'Geometric property measuring local curvature of contact network graph',
            'spectral gap': 'Difference between largest and second-largest eigenvalue of graph Laplacian',
            'nash equilibrium': 'Game-theoretic stable state where no agent benefits from unilateral change',
            'persistent homology': 'Topological features (components, loops, voids) across spatial filtration scales',
            'algebraic connectivity': 'Second-smallest eigenvalue of graph Laplacian measuring connectivity',
            'radius of gyration': 'Root-mean-square distance of atoms from center of mass',
            'contact map': 'Binary matrix indicating which residue pairs are spatially close',
            'kan extension': 'Universal construction in category theory for extending functors',
            'natural transformation': 'Structure-preserving map between functors',
            'homotopy': 'Continuous deformation between paths or functions',
            'functor': 'Structure-preserving map between categories',
            'cellular automaton': 'Discrete dynamical system on grid of cells with local rules',
            # Chemistry-specific terms (Physical-Chemical Bridge)
            'energy minimization': 'Computational gradient descent optimization to reduce calculated energy function',
            'statistical potential': 'Knowledge-based energy term derived from observed frequencies in PDB structures',
            'dunbrack rotamer': 'Backbone-dependent side chain conformation from statistical rotamer library',
            'ramachandran validation': 'Check of backbone dihedral angles against allowed conformational regions',
            'clash detection': 'Geometric identification of atoms closer than sum of van der Waals radii',
            'energy function': 'Mathematical approximation summing weighted physical and statistical energy terms',
            'force field': 'Set of equations and parameters for computing interatomic energies and forces',
            'native state': 'Biologically functional protein conformation observed in vivo (requires experimental validation)',
            'energy convergence': 'Numerical optimization reaching local minimum where gradient approaches zero',
            'rotamer library': 'Statistical database of observed side chain conformations from experimental structures'
        }

        # Mathematical vs Physical terms
        self.mathematical_terms = [
            'eigenvalue', 'curvature', 'spectral gap', 'equilibrium',
            'homology', 'functor', 'natural transformation', 'morphism',
            'category', 'homotopy', 'kan extension', 'algebraic connectivity',
            'graph laplacian', 'adjacency matrix', 'contact matrix'
        ]

        self.physical_terms = [
            'folding mechanism', 'stability', 'energy', 'binding',
            'conformational change', 'catalysis', 'allosteric', 'dynamics',
            'thermodynamic', 'kinetic', 'enthalpic', 'entropic',
            'solvation', 'hydrophobic effect', 'hydrogen bonding'
        ]

        # Chemistry-specific: Mathematical/Computational vs Biological
        self.mathematical_chemistry = [
            'energy minimum', 'convergence', 'gradient descent',
            'lennard-jones', 'coulomb', 'optimization', 'computed energy',
            'force field', 'statistical potential', 'energy function',
            'numerical minimization', 'local minimum'
        ]

        self.biological_chemistry = [
            'native state', 'folded structure', 'biological function',
            'protein stability', 'binding affinity', 'catalytic activity',
            'in vivo behavior', 'physiological condition', 'functional conformation',
            'biologically active', 'native fold', 'functional state'
        ]

        # Causal claim patterns
        self.causal_patterns = [
            'causes', 'leads to', 'results in', 'produces', 'generates',
            'creates', 'drives', 'induces', 'triggers', 'determines',
            'proves', 'demonstrates', 'shows that', 'reveals that',
            'confirms', 'indicates that', 'is the mechanism',
            'is the reason', 'explains why'
        ]

        # Correlation patterns (acceptable)
        self.correlation_patterns = [
            'correlates with', 'associated with', 'consistent with',
            'suggests', 'may indicate', 'compatible with',
            'resembles', 'similar to', 'pattern observed'
        ]

    def validate_interpretation(self, structure_data: Dict, interpretation: str) -> List[SemanticIssue]:
        """
        Validate interpretation text.

        Args:
            structure_data: Dict with coords, sequence, frameworks results
            interpretation: Text interpretation to validate

        Returns:
            List of semantic issues
        """
        issues = []

        # Check 1: Terminology consistency
        issues.extend(self._check_terminology_consistency(interpretation))

        # Check 2: Mathematical vs Physical confusion
        issues.extend(self._check_math_physics_confusion(interpretation))

        # Check 3: Overclaiming detection
        issues.extend(self._check_overclaiming(interpretation))

        # Check 4: Confidence appropriate to evidence
        issues.extend(self._check_confidence_level(interpretation, structure_data))

        return issues

    def _check_terminology_consistency(self, text: str) -> List[SemanticIssue]:
        """Check if terms are used consistently with their definitions"""
        issues = []

        text_lower = text.lower()

        for term, correct_def in self.correct_definitions.items():
            if term not in text_lower:
                continue

            # Extract sentences containing this term
            sentences = self._extract_sentences_with_term(text, term)

            for sentence in sentences:
                if self.use_embeddings:
                    # Use embeddings to check consistency
                    similarity = self._compute_similarity(correct_def, sentence)

                    if similarity < 0.4:  # Low similarity = inconsistent usage
                        issues.append(SemanticIssue(
                            severity='WARNING',
                            category='terminology',
                            message=f'Term "{term}" may be used inconsistently',
                            details={
                                'term': term,
                                'correct_definition': correct_def,
                                'usage': sentence,
                                'similarity': float(similarity),
                                'recommendation': 'Verify term usage matches mathematical definition'
                            }
                        ))
                else:
                    # Rule-based check: look for causal claims about mathematical terms
                    if any(pattern in sentence.lower() for pattern in self.causal_patterns):
                        issues.append(SemanticIssue(
                            severity='WARNING',
                            category='terminology',
                            message=f'Causal claim made about mathematical term "{term}"',
                            details={
                                'term': term,
                                'sentence': sentence,
                                'recommendation': 'Mathematical terms describe patterns, not mechanisms'
                            }
                        ))

        return issues

    def _check_math_physics_confusion(self, text: str) -> List[SemanticIssue]:
        """Detect confusion between mathematical metrics and physical mechanisms"""
        issues = []

        sentences = self._split_into_sentences(text)

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check if sentence mentions both mathematical and physical terms
            has_math = any(term in sentence_lower for term in self.mathematical_terms)
            has_physics = any(term in sentence_lower for term in self.physical_terms)

            if has_math and has_physics:
                # Check if causal language is used
                has_causal = any(pattern in sentence_lower for pattern in self.causal_patterns)

                if has_causal:
                    # This is likely problematic
                    issues.append(SemanticIssue(
                        severity='CRITICAL',
                        category='math_physics_confusion',
                        message='Mathematical metric interpreted as physical mechanism',
                        details={
                            'sentence': sentence,
                            'problem': 'Using causal language to connect math and physics',
                            'recommendation': 'Use "correlates with" or "consistent with" instead of causal language',
                            'example': 'Change "curvature determines folding" -> "curvature correlates with folding pattern"'
                        }
                    ))
                elif self.use_embeddings:
                    # Check semantic similarity between sentence and known confusions
                    confusion_examples = [
                        "Ricci curvature is the folding mechanism",
                        "Spectral gap causes protein stability",
                        "Nash equilibrium proves thermodynamic stability"
                    ]

                    max_similarity = max(self._compute_similarity(sentence, ex) for ex in confusion_examples)

                    if max_similarity > 0.7:
                        issues.append(SemanticIssue(
                            severity='WARNING',
                            category='math_physics_confusion',
                            message='Sentence resembles mathematical-physical confusion',
                            details={
                                'sentence': sentence,
                                'similarity_to_confusion': float(max_similarity),
                                'recommendation': 'Clarify distinction between mathematical description and physical mechanism'
                            }
                        ))

        return issues

    def _check_overclaiming(self, text: str) -> List[SemanticIssue]:
        """Detect claims that exceed available evidence"""
        issues = []

        # Known limitations of KOMPOSOS-III
        limitations = [
            'No experimental validation performed',
            'No folding kinetics measured',
            'No binding affinities computed',
            'No mutation effects tested experimentally',
            'Geometric analysis not equivalent to energy calculation',
            'Contact maps are static, not dynamic',
            'Category theory provides structure, not physical forces'
        ]

        # Strong claim patterns
        strong_claims = [
            'proves', 'demonstrates', 'confirms', 'establishes',
            'definitively', 'conclusively', 'certainly',
            'this is the mechanism', 'this explains', 'the cause is'
        ]

        text_lower = text.lower()

        # Check for strong claims
        found_strong_claims = []
        for pattern in strong_claims:
            if pattern in text_lower:
                found_strong_claims.append(pattern)

        if found_strong_claims:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='overclaiming',
                message=f'Strong claims detected: {", ".join(found_strong_claims)}',
                details={
                    'patterns': found_strong_claims,
                    'recommendation': 'Soften claims with "suggests", "consistent with", "may indicate"',
                    'rationale': 'Computational analysis should be validated experimentally'
                }
            ))

        # Check if text acknowledges limitations
        acknowledges_limitations = any(word in text_lower for word in [
            'may', 'might', 'could', 'suggests', 'indicates',
            'preliminary', 'needs validation', 'requires confirmation'
        ])

        if not acknowledges_limitations and len(text) > 100:
            issues.append(SemanticIssue(
                severity='INFO',
                category='overclaiming',
                message='Interpretation does not acknowledge limitations',
                details={
                    'recommendation': 'Add caveats about computational vs experimental validation',
                    'example': 'Add: "These results require experimental validation"'
                }
            ))

        return issues

    def _check_confidence_level(self, text: str, structure_data: Dict) -> List[SemanticIssue]:
        """Check if confidence level matches quality of data"""
        issues = []

        # Check structure quality
        if 'structure' in structure_data:
            mean_plddt = structure_data['structure'].get('mean_plddt', 100)

            if mean_plddt < 70:
                # Low confidence structure - interpretations should be cautious
                text_lower = text.lower()

                # Check if text acknowledges low confidence
                acknowledges_quality = any(word in text_lower for word in [
                    'low confidence', 'uncertain', 'tentative',
                    'preliminary', 'questionable', 'unreliable'
                ])

                if not acknowledges_quality:
                    issues.append(SemanticIssue(
                        severity='WARNING',
                        category='confidence',
                        message=f'Low structure confidence (pLDDT={mean_plddt:.1f}) not acknowledged',
                        details={
                            'mean_plddt': mean_plddt,
                            'recommendation': 'Add warning about low structure quality',
                            'example': f'Add: "Note: Structure has low confidence (pLDDT {mean_plddt:.1f})"'
                        }
                    ))

        return issues

    def check_chemistry_claims(self, text: str, evidence: Dict) -> List[SemanticIssue]:
        """
        Validate chemistry-related claims against available evidence.

        This method prevents overclaiming from Physical-Chemical Bridge results.
        Similar to climate analysis validation - prevents technically correct
        calculations from leading to invalid biological conclusions.

        Args:
            text: Interpretation text
            evidence: Dict with:
                - num_tests: How many structures tested?
                - benchmarked: Compared to baselines?
                - using_defaults: Using simplified data?
                - experimental_validation: Ground truth available?

        Returns:
            List of semantic issues
        """
        issues = []

        text_lower = text.lower()

        # Check 1: Claiming "production ready" without benchmarking
        production_claims = ['production', 'ready for use', 'deployment', 'ready to deploy']
        has_production_claim = any(claim in text_lower for claim in production_claims)

        if has_production_claim and not evidence.get('benchmarked', False):
            issues.append(SemanticIssue(
                severity='CRITICAL',
                category='overclaiming',
                message='Claiming production readiness without benchmark validation',
                details={
                    'claim_type': 'production readiness',
                    'evidence_missing': 'No CASP/CAMEO-style benchmarking performed',
                    'recommendation': 'Benchmark on 50+ diverse proteins vs AlphaFold/Rosetta before claiming production-ready'
                }
            ))

        # Check 2: Claiming from insufficient tests
        num_tests = evidence.get('num_tests', 0)
        strong_verbs = ['works', 'fixes', 'solves', 'resolves', 'handles', 'achieves']
        has_strong_claim = any(verb in text_lower for verb in strong_verbs)

        if has_strong_claim and num_tests < 10:
            issues.append(SemanticIssue(
                severity='WARNING',
                category='insufficient_evidence',
                message=f'Strong generalization based on only {num_tests} test(s)',
                details={
                    'num_tests': num_tests,
                    'recommendation': 'Test on diverse set (50+ structures, various folds/lengths) before generalizing',
                    'alternative': f'Say "works on tested case(s)" not "works" generally'
                }
            ))

        # Check 3: Using defaults but not acknowledging
        if evidence.get('using_defaults', False):
            disclaimers = ['default', 'simplified', 'approximation', 'preliminary']
            has_disclaimer = any(word in text_lower for word in disclaimers)

            if not has_disclaimer:
                issues.append(SemanticIssue(
                    severity='WARNING',
                    category='missing_disclaimer',
                    message='Using default/simplified parameters not acknowledged',
                    details={
                        'problem': 'Rotamer library and PDB statistics use defaults',
                        'impact': 'Accuracy may be lower than with real data',
                        'recommendation': 'Add: "Using simplified parameters; production requires real Dunbrack library and PDB-derived statistics"'
                    }
                ))

        # Check 4: Confusing computational results with biological reality
        # Use embeddings if available for sophisticated checking
        if self.use_embeddings:
            confusion_examples = [
                "Energy minimum proves this is the native state",
                "Low energy means biologically stable",
                "Convergence confirms biological correctness",
                "The mathematics shows this is the functional structure"
            ]

            for example in confusion_examples:
                similarity = self._compute_similarity(text, example)
                if similarity > 0.65:
                    issues.append(SemanticIssue(
                        severity='CRITICAL',
                        category='math_biology_confusion',
                        message='Computational result interpreted as biological truth',
                        details={
                            'problem': 'Energy minimum (computational) ≠ native state (biological)',
                            'similarity': float(similarity),
                            'recommendation': 'Clarify: "Low computed energy suggests stability; requires experimental validation"',
                            'example': 'Change "This IS the native state" → "This MAY represent a stable conformation"'
                        }
                    ))
                    break  # Only report once

        # Check 5: Look for computational-biological confusion in same sentence
        for sentence in self._split_into_sentences(text):
            sentence_lower = sentence.lower()

            has_math_chem = any(term in sentence_lower for term in self.mathematical_chemistry)
            has_bio_chem = any(term in sentence_lower for term in self.biological_chemistry)

            if has_math_chem and has_bio_chem:
                # Check if using causal language
                has_causal = any(pattern in sentence_lower for pattern in self.causal_patterns)

                if has_causal:
                    issues.append(SemanticIssue(
                        severity='CRITICAL',
                        category='math_biology_confusion',
                        message='Causal claim linking computational metric to biological property',
                        details={
                            'sentence': sentence,
                            'problem': 'Using causal language to connect math and biology',
                            'recommendation': 'Use "correlates with" or "suggests" instead of causal language',
                            'example': '"Energy minimum determines stability" → "Low energy correlates with stability"'
                        }
                    ))

        # Check 6: Benchmark comparisons without actual benchmarking
        comparison_terms = ['better than', 'outperforms', 'superior to', 'competitive with', 'matches']
        has_comparison = any(term in text_lower for term in comparison_terms)

        if has_comparison and not evidence.get('benchmarked', False):
            issues.append(SemanticIssue(
                severity='CRITICAL',
                category='unsupported_comparison',
                message='Comparison claim without actual benchmarking',
                details={
                    'problem': 'Claiming superiority/competitiveness without direct comparison',
                    'recommendation': 'Run head-to-head comparison on same test set before making comparative claims'
                }
            ))

        return issues

    def _extract_sentences_with_term(self, text: str, term: str) -> List[str]:
        """Extract sentences containing a specific term"""
        sentences = self._split_into_sentences(text)
        term_lower = term.lower()
        return [s for s in sentences if term_lower in s.lower()]

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity using embeddings"""
        if not self.use_embeddings:
            # Fallback: simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            return len(words1 & words2) / len(words1 | words2)

        # Use sentence embeddings
        emb1 = self.model.encode(text1)
        emb2 = self.model.encode(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def generate_report(self, issues: List[SemanticIssue]) -> str:
        """Generate human-readable report"""
        lines = []
        lines.append("=" * 70)
        lines.append("SEMANTIC VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        if not issues:
            lines.append("[OK] INTERPRETATION PASSES SEMANTIC CHECKS")
            lines.append("")
        else:
            # Group by severity
            for severity in ['CRITICAL', 'WARNING', 'INFO']:
                severity_issues = [i for i in issues if i.severity == severity]
                if severity_issues:
                    lines.append(f"{severity} ({len(severity_issues)}):")
                    for issue in severity_issues:
                        lines.append(f"  • [{issue.category}] {issue.message}")
                        if issue.details:
                            for key, value in issue.details.items():
                                if key == 'recommendation':
                                    lines.append(f"    -> {value}")
                                elif key == 'example':
                                    lines.append(f"    Example: {value}")
                                elif key not in ['sentence', 'usage', 'correct_definition']:
                                    lines.append(f"    - {key}: {value}")
                            if 'sentence' in issue.details:
                                lines.append(f"    Sentence: \"{issue.details['sentence']}\"")
                    lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)
