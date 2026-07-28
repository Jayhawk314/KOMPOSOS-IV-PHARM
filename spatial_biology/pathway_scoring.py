# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Helpers for pathway-aware spatial motif scoring on public Noetik-style datasets.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple


@dataclass(frozen=True)
class MotifSpec:
    """Benchmarkable biological motif."""
    source_gene: str
    target_gene: str
    pathway_group: str
    label: str
    positive: bool
    interaction_type: str  # intercellular or intracellular


DEFAULT_POSITIVE_MOTIFS: List[MotifSpec] = [
    MotifSpec("CD274", "PDCD1", "immune_checkpoint", "PD-L1 -> PD-1", True, "intercellular"),
    MotifSpec("PDCD1LG2", "PDCD1", "immune_checkpoint", "PD-L2 -> PD-1", True, "intercellular"),
    MotifSpec("CD80", "CTLA4", "immune_checkpoint", "CD80 -> CTLA4", True, "intercellular"),
    MotifSpec("CD86", "CTLA4", "immune_checkpoint", "CD86 -> CTLA4", True, "intercellular"),
    MotifSpec("ICOSLG", "ICOS", "immune_checkpoint", "ICOSLG -> ICOS", True, "intercellular"),
    MotifSpec("LGALS9", "HAVCR2", "immune_checkpoint", "Galectin-9 -> TIM-3", True, "intercellular"),
    MotifSpec("EGF", "EGFR", "egfr_axis", "EGF -> EGFR", True, "intercellular"),
    MotifSpec("HGF", "MET", "egfr_axis", "HGF -> MET", True, "intercellular"),
    MotifSpec("NRG1", "ERBB3", "egfr_axis", "NRG1 -> ERBB3", True, "intercellular"),
    MotifSpec("EGFR", "KRAS", "egfr_axis", "EGFR -> KRAS", True, "intracellular"),
    MotifSpec("VEGFA", "KDR", "angiogenesis", "VEGFA -> VEGFR2", True, "intercellular"),
    MotifSpec("VEGFA", "FLT1", "angiogenesis", "VEGFA -> VEGFR1", True, "intercellular"),
    MotifSpec("ANGPT1", "TEK", "angiogenesis", "ANGPT1 -> TIE2", True, "intercellular"),
    MotifSpec("ANGPT2", "TEK", "angiogenesis", "ANGPT2 -> TIE2", True, "intercellular"),
    MotifSpec("CXCL12", "CXCR4", "chemokine", "CXCL12 -> CXCR4", True, "intercellular"),
    MotifSpec("CCL2", "CCR2", "chemokine", "CCL2 -> CCR2", True, "intercellular"),
    MotifSpec("CCL5", "CCR5", "chemokine", "CCL5 -> CCR5", True, "intercellular"),
    MotifSpec("CXCL9", "CXCR3", "chemokine", "CXCL9 -> CXCR3", True, "intercellular"),
    MotifSpec("IL6", "IL6R", "cytokine", "IL6 -> IL6R", True, "intercellular"),
    MotifSpec("IFNG", "IFNGR1", "cytokine", "IFNg -> IFNGR1", True, "intercellular"),
    MotifSpec("TNF", "TNFRSF1A", "cytokine", "TNF -> TNFRSF1A", True, "intercellular"),
    MotifSpec("TGFB1", "TGFBR1", "cytokine", "TGFB1 -> TGFBR1", True, "intercellular"),
    MotifSpec("ICAM1", "ITGAL", "adhesion", "ICAM1 -> ITGAL", True, "intercellular"),
    MotifSpec("VCAM1", "ITGA4", "adhesion", "VCAM1 -> ITGA4", True, "intercellular"),
    # CRC-specific motifs (WNT pathway, TGFb expansion, MMR)
    MotifSpec("WNT3A", "FZD1", "wnt_signaling", "WNT3A -> FZD1", True, "intercellular"),
    MotifSpec("WNT5A", "FZD2", "wnt_signaling", "WNT5A -> FZD2", True, "intercellular"),
    MotifSpec("WNT7B", "FZD5", "wnt_signaling", "WNT7B -> FZD5", True, "intercellular"),
    MotifSpec("RSPO1", "LGR5", "wnt_signaling", "RSPO1 -> LGR5", True, "intercellular"),
    MotifSpec("CTNNB1", "TCF7L2", "wnt_signaling", "CTNNB1 -> TCF7L2", True, "intracellular"),
    MotifSpec("TGFB2", "TGFBR2", "tgfb_signaling", "TGFB2 -> TGFBR2", True, "intercellular"),
    MotifSpec("TGFB3", "TGFBR1", "tgfb_signaling", "TGFB3 -> TGFBR1", True, "intercellular"),
]


NEGATIVE_GROUPS: Dict[str, List[str]] = {
    "tumor": ["EGFR", "KRAS", "MET", "KRT5", "EPCAM", "TP53", "VIM"],
    "immune": ["CD3E", "CD4", "CD8A", "PDCD1", "CTLA4", "TIGIT", "IFNG", "LAG3"],
    "vascular": ["VEGFA", "KDR", "FLT1", "ANGPT1", "TEK", "PECAM1", "VWF"],
    "chemokine": ["CXCL12", "CXCR4", "CCL2", "CCR2", "CCL5", "CCR5", "CXCL9", "CXCR3"],
    "cytokine": ["IL6", "IL6R", "TNF", "TNFRSF1A", "TGFB1", "TGFBR1"],
}


def available_motifs(available_genes: Set[str]) -> List[MotifSpec]:
    """Return curated positive motifs present in a dataset."""
    return [
        motif for motif in DEFAULT_POSITIVE_MOTIFS
        if motif.source_gene in available_genes and motif.target_gene in available_genes
    ]


def build_negative_motifs(
    available_genes: Set[str],
    known_pairs: Set[Tuple[str, str]],
    target_count: int = 24,
) -> List[MotifSpec]:
    """
    Build deterministic cross-category decoys present in the dataset.

    Decoys are selected from genes that are available but do not appear in the
    ligand-receptor database and are not in the curated positive set.
    """
    positives = {(m.source_gene, m.target_gene) for m in available_motifs(available_genes)}
    negatives: List[MotifSpec] = []

    candidate_group_order = [
        ("tumor", "immune"),
        ("immune", "tumor"),
        ("vascular", "immune"),
        ("immune", "vascular"),
        ("chemokine", "tumor"),
        ("cytokine", "tumor"),
    ]

    for src_group, tgt_group in candidate_group_order:
        for src_gene in NEGATIVE_GROUPS[src_group]:
            if src_gene not in available_genes:
                continue
            for tgt_gene in NEGATIVE_GROUPS[tgt_group]:
                if tgt_gene not in available_genes:
                    continue
                pair = (src_gene, tgt_gene)
                if pair in positives or pair in known_pairs:
                    continue
                negatives.append(
                    MotifSpec(
                        source_gene=src_gene,
                        target_gene=tgt_gene,
                        pathway_group=f"decoy_{src_group}_to_{tgt_group}",
                        label=f"{src_gene} -> {tgt_gene}",
                        positive=False,
                        interaction_type="intercellular",
                    )
                )
                if len(negatives) >= target_count:
                    return negatives

    return negatives


def group_motifs_by_pathway(motifs: Iterable[MotifSpec]) -> Dict[str, List[MotifSpec]]:
    """Group motifs by pathway group."""
    grouped: Dict[str, List[MotifSpec]] = {}
    for motif in motifs:
        grouped.setdefault(motif.pathway_group, []).append(motif)
    return grouped
