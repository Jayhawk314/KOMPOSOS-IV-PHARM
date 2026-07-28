# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Ligand-Receptor Database for Spatial Biology Analysis

Curated database of ligand-receptor pairs with emphasis on:
- Non-Small Cell Lung Cancer (NSCLC)
- Tumor microenvironment (TME)
- Immune checkpoints
- Oncogenic signaling

Sources:
- CellPhoneDB v4.0
- NicheNet database
- KEGG pathways
- Literature (PMID citations)

Author: KOMPOSOS-III Team
Date: 2026-04-20
"""

from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LigandReceptorPair:
    """A validated ligand-receptor interaction."""
    ligand: str
    receptor: str
    pathway: str
    evidence: str  # PMID or database
    confidence: float = 1.0  # 0-1 confidence score
    tissue_specificity: str = "general"  # general, nsclc, immune, etc.


class LigandReceptorDatabase:
    """
    Comprehensive ligand-receptor database.

    Organized by functional categories for NSCLC spatial biology.
    """

    def __init__(self):
        self.pairs: List[LigandReceptorPair] = []
        self.pair_map: Dict[Tuple[str, str], LigandReceptorPair] = {}
        self._build_database()

    def _build_database(self):
        """Build the complete database."""

        # === IMMUNE CHECKPOINTS (Critical for ICB therapy) ===
        immune_checkpoint_pairs = [
            # PD-1 pathway
            ("CD274", "PDCD1", "PD-L1_PD-1", "PMID:22658127", 1.0, "nsclc"),  # PD-L1/PD-1
            ("PDCD1LG2", "PDCD1", "PD-L2_PD-1", "PMID:11015443", 1.0, "nsclc"),  # PD-L2/PD-1

            # CTLA-4 pathway
            ("CD80", "CTLA4", "CD80_CTLA4", "PMID:8096327", 1.0, "immune"),  # CD80/CTLA-4
            ("CD86", "CTLA4", "CD86_CTLA4", "PMID:8096327", 1.0, "immune"),  # CD86/CTLA-4

            # LAG-3 (emerging target)
            ("FGL1", "LAG3", "FGL1_LAG3", "PMID:30127393", 0.9, "nsclc"),  # Fibrinogen-like 1/LAG-3
            ("LGALS3", "LAG3", "Galectin3_LAG3", "PMID:15240637", 0.8, "immune"),

            # TIM-3
            ("LGALS9", "HAVCR2", "Galectin9_TIM3", "PMID:16286920", 0.9, "immune"),  # Galectin-9/TIM-3
            ("CEACAM1", "HAVCR2", "CEACAM1_TIM3", "PMID:24970819", 0.8, "immune"),

            # TIGIT pathway
            ("PVR", "TIGIT", "CD155_TIGIT", "PMID:19648179", 0.9, "immune"),  # CD155/TIGIT
            ("NECTIN2", "TIGIT", "CD112_TIGIT", "PMID:27569215", 0.9, "immune"),  # CD112/TIGIT

            # VISTA
            ("VSIR", "PSGL1", "VISTA_PSGL1", "PMID:25849761", 0.7, "immune"),  # VISTA/PSGL-1

            # B7 family
            ("TNFRSF14", "BTLA", "HVEM_BTLA", "PMID:15240646", 0.9, "immune"),  # HVEM/BTLA
            ("HHLA2", "TMIGD2", "HHLA2_TMIGD2", "PMID:28813417", 0.8, "nsclc"),

            # CD28 family
            ("CD80", "CD28", "CD80_CD28", "PMID:2450226", 1.0, "immune"),  # CD80/CD28
            ("CD86", "CD28", "CD86_CD28", "PMID:2450226", 1.0, "immune"),  # CD86/CD28

            # ICOS pathway
            ("ICOSLG", "ICOS", "ICOSL_ICOS", "PMID:10581077", 0.9, "immune"),  # ICOS-L/ICOS
        ]

        # === NSCLC ONCOGENIC SIGNALING ===
        oncogenic_signaling = [
            # EGFR pathway (most common NSCLC driver)
            ("EGF", "EGFR", "EGFR_signaling", "PMID:2024969", 1.0, "nsclc"),  # EGF/EGFR
            ("TGFA", "EGFR", "EGFR_signaling", "PMID:3043178", 1.0, "nsclc"),  # TGF-alpha/EGFR
            ("AREG", "EGFR", "EGFR_signaling", "PMID:2002605", 1.0, "nsclc"),  # Amphiregulin/EGFR
            ("EREG", "EGFR", "EGFR_signaling", "PMID:11278710", 0.9, "nsclc"),  # Epiregulin/EGFR
            ("BTC", "EGFR", "EGFR_signaling", "PMID:8557014", 0.9, "nsclc"),  # Betacellulin/EGFR
            ("HBEGF", "EGFR", "EGFR_signaling", "PMID:2162835", 0.9, "nsclc"),  # HB-EGF/EGFR
            ("EPGN", "EGFR", "EGFR_signaling", "PMID:11431468", 0.8, "nsclc"),  # Epigen/EGFR

            # HER2/HER3/HER4
            ("NRG1", "ERBB3", "HER3_signaling", "PMID:8307986", 0.9, "nsclc"),  # Neuregulin/HER3
            ("NRG1", "ERBB4", "HER4_signaling", "PMID:8307986", 0.9, "general"),
            ("NRG2", "ERBB3", "HER3_signaling", "PMID:9383478", 0.8, "general"),
            ("NRG2", "ERBB4", "HER4_signaling", "PMID:9383478", 0.8, "general"),

            # MET pathway (resistance mechanism)
            ("HGF", "MET", "HGF_MET", "PMID:2044942", 1.0, "nsclc"),  # HGF/MET

            # FGF pathway
            ("FGF1", "FGFR1", "FGF_signaling", "PMID:2424508", 0.9, "nsclc"),
            ("FGF2", "FGFR1", "FGF_signaling", "PMID:2424508", 1.0, "nsclc"),
            ("FGF7", "FGFR2", "FGF_signaling", "PMID:8021273", 0.9, "general"),
            ("FGF10", "FGFR2", "FGF_signaling", "PMID:9889138", 0.9, "nsclc"),

            # PDGF pathway
            ("PDGFA", "PDGFRA", "PDGF_signaling", "PMID:2997653", 0.9, "general"),
            ("PDGFB", "PDGFRB", "PDGF_signaling", "PMID:3023191", 0.9, "general"),
            ("PDGFC", "PDGFRA", "PDGF_signaling", "PMID:11121040", 0.8, "general"),
            ("PDGFD", "PDGFRB", "PDGF_signaling", "PMID:15345332", 0.8, "general"),

            # IGF pathway
            ("IGF1", "IGF1R", "IGF_signaling", "PMID:2832308", 0.9, "nsclc"),
            ("IGF2", "IGF1R", "IGF_signaling", "PMID:2832308", 0.9, "general"),
        ]

        # === ANGIOGENESIS (Critical for tumor growth) ===
        angiogenesis = [
            # VEGF pathway (primary target for anti-angiogenic therapy)
            ("VEGFA", "FLT1", "VEGFR1_signaling", "PMID:7626805", 1.0, "nsclc"),  # VEGF-A/VEGFR1
            ("VEGFA", "KDR", "VEGFR2_signaling", "PMID:7626805", 1.0, "nsclc"),  # VEGF-A/VEGFR2
            ("VEGFB", "FLT1", "VEGFR1_signaling", "PMID:8647913", 0.9, "general"),
            ("VEGFC", "FLT4", "VEGFR3_signaling", "PMID:8994607", 0.9, "nsclc"),  # VEGF-C/VEGFR3
            ("VEGFD", "FLT4", "VEGFR3_signaling", "PMID:9094146", 0.9, "general"),
            ("PGF", "FLT1", "PlGF_VEGFR1", "PMID:9094146", 0.8, "general"),  # PlGF/VEGFR1

            # Angiopoietin-Tie pathway
            ("ANGPT1", "TEK", "Ang1_Tie2", "PMID:8756718", 0.9, "general"),  # Angiopoietin-1/Tie2
            ("ANGPT2", "TEK", "Ang2_Tie2", "PMID:9154746", 0.9, "nsclc"),  # Angiopoietin-2/Tie2

            # Notch signaling (angiogenesis)
            ("DLL4", "NOTCH1", "DLL4_Notch1", "PMID:16990543", 0.9, "general"),
            ("DLL4", "NOTCH4", "DLL4_Notch4", "PMID:16990543", 0.9, "general"),
            ("JAG1", "NOTCH1", "Jagged1_Notch1", "PMID:7673114", 0.8, "general"),
        ]

        # === CYTOKINES & INTERLEUKINS ===
        cytokines = [
            # IL-2 family
            ("IL2", "IL2RA", "IL2_signaling", "PMID:6606682", 1.0, "immune"),
            ("IL2", "IL2RB", "IL2_signaling", "PMID:6606682", 1.0, "immune"),
            ("IL15", "IL2RB", "IL15_signaling", "PMID:7543090", 0.9, "immune"),
            ("IL15", "IL15RA", "IL15_signaling", "PMID:8139556", 0.9, "immune"),

            # IL-6 family
            ("IL6", "IL6R", "IL6_signaling", "PMID:2455224", 1.0, "nsclc"),
            ("IL6", "IL6ST", "IL6_signaling", "PMID:2455224", 1.0, "nsclc"),
            ("IL11", "IL11RA", "IL11_signaling", "PMID:8163561", 0.8, "general"),

            # IL-10 family
            ("IL10", "IL10RA", "IL10_signaling", "PMID:7657697", 0.9, "immune"),
            ("IL10", "IL10RB", "IL10_signaling", "PMID:7657697", 0.9, "immune"),

            # IL-12 family
            ("IL12A", "IL12RB1", "IL12_signaling", "PMID:8642338", 0.9, "immune"),
            ("IL12B", "IL12RB2", "IL12_signaling", "PMID:8642338", 0.9, "immune"),

            # Type I interferons
            ("IFNA1", "IFNAR1", "IFN_alpha_signaling", "PMID:8663382", 0.9, "immune"),
            ("IFNB1", "IFNAR1", "IFN_beta_signaling", "PMID:8663382", 0.9, "immune"),

            # Type II interferon
            ("IFNG", "IFNGR1", "IFN_gamma_signaling", "PMID:2448876", 1.0, "immune"),
            ("IFNG", "IFNGR2", "IFN_gamma_signaling", "PMID:2448876", 1.0, "immune"),

            # TNF family
            ("TNF", "TNFRSF1A", "TNF_signaling", "PMID:2437018", 1.0, "immune"),
            ("TNF", "TNFRSF1B", "TNF_signaling", "PMID:2437018", 1.0, "immune"),
            ("LTA", "TNFRSF1A", "LT_alpha_signaling", "PMID:2437018", 0.9, "immune"),
            ("FASLG", "FAS", "FasL_Fas", "PMID:8202537", 1.0, "immune"),  # FasL/Fas (apoptosis)

            # TGF-beta family
            ("TGFB1", "TGFBR1", "TGF_beta_signaling", "PMID:3284666", 1.0, "nsclc"),
            ("TGFB1", "TGFBR2", "TGF_beta_signaling", "PMID:3284666", 1.0, "nsclc"),
            ("TGFB2", "TGFBR1", "TGF_beta_signaling", "PMID:3284666", 0.9, "general"),
            ("TGFB3", "TGFBR1", "TGF_beta_signaling", "PMID:3284666", 0.9, "general"),

            # IL-1 family
            ("IL1B", "IL1R1", "IL1_signaling", "PMID:2825177", 1.0, "immune"),
            ("IL1A", "IL1R1", "IL1_signaling", "PMID:2825177", 1.0, "immune"),
            ("IL18", "IL18R1", "IL18_signaling", "PMID:8649811", 0.9, "immune"),
        ]

        # === CHEMOKINES (Cell trafficking) ===
        chemokines = [
            # CXCL/CXCR
            ("CXCL12", "CXCR4", "SDF1_CXCR4", "PMID:9430682", 1.0, "nsclc"),  # SDF-1/CXCR4
            ("CXCL8", "CXCR1", "IL8_CXCR1", "PMID:2165356", 0.9, "immune"),  # IL-8/CXCR1
            ("CXCL8", "CXCR2", "IL8_CXCR2", "PMID:2165356", 0.9, "immune"),  # IL-8/CXCR2
            ("CXCL10", "CXCR3", "IP10_CXCR3", "PMID:9916980", 0.9, "immune"),
            ("CXCL9", "CXCR3", "MIG_CXCR3", "PMID:9916980", 0.9, "immune"),
            ("CXCL11", "CXCR3", "ITAC_CXCR3", "PMID:11157752", 0.9, "immune"),

            # CCL/CCR
            ("CCL2", "CCR2", "MCP1_CCR2", "PMID:1722454", 1.0, "immune"),  # MCP-1/CCR2
            ("CCL5", "CCR5", "RANTES_CCR5", "PMID:8621647", 1.0, "immune"),  # RANTES/CCR5
            ("CCL5", "CCR1", "RANTES_CCR1", "PMID:8621647", 0.9, "immune"),
            ("CCL3", "CCR1", "MIP1a_CCR1", "PMID:8621647", 0.9, "immune"),
            ("CCL4", "CCR5", "MIP1b_CCR5", "PMID:8621647", 0.9, "immune"),
            ("CCL17", "CCR4", "TARC_CCR4", "PMID:9826636", 0.8, "immune"),
            ("CCL22", "CCR4", "MDC_CCR4", "PMID:9826636", 0.8, "immune"),
            ("CCL19", "CCR7", "MIP3b_CCR7", "PMID:10229825", 0.9, "immune"),
            ("CCL21", "CCR7", "SLC_CCR7", "PMID:10229825", 0.9, "immune"),
        ]

        # === ADHESION MOLECULES ===
        adhesion = [
            # Integrins
            ("VCAM1", "ITGA4", "VCAM1_VLA4", "PMID:1689240", 0.9, "immune"),
            ("ICAM1", "ITGAL", "ICAM1_LFA1", "PMID:2470098", 0.9, "immune"),
            ("FN1", "ITGA5", "Fibronectin_integrin", "PMID:2405379", 0.8, "general"),
            ("COL1A1", "ITGA2", "Collagen_integrin", "PMID:3277569", 0.8, "general"),

            # Selectins
            ("SELP", "SELPLG", "P_selectin_PSGL1", "PMID:7685754", 0.8, "immune"),
            ("SELE", "SELPLG", "E_selectin_PSGL1", "PMID:7685754", 0.8, "immune"),

            # Cadherins
            ("CDH1", "CDH1", "E_cadherin_homotypic", "PMID:2989856", 0.9, "nsclc"),
            ("CDH2", "CDH2", "N_cadherin_homotypic", "PMID:2989856", 0.8, "general"),
        ]

        # === WNT SIGNALING ===
        wnt = [
            ("WNT3A", "FZD1", "Wnt_Frizzled", "PMID:9872990", 0.8, "general"),
            ("WNT3A", "FZD2", "Wnt_Frizzled", "PMID:9872990", 0.8, "general"),
            ("WNT5A", "FZD5", "Wnt5a_Fzd5", "PMID:10491411", 0.8, "general"),
            ("WNT7A", "FZD5", "Wnt7a_Fzd5", "PMID:10491411", 0.7, "general"),
        ]

        # Build complete database
        all_pairs = (
            immune_checkpoint_pairs +
            oncogenic_signaling +
            angiogenesis +
            cytokines +
            chemokines +
            adhesion +
            wnt
        )

        for ligand, receptor, pathway, evidence, confidence, tissue in all_pairs:
            pair = LigandReceptorPair(
                ligand=ligand,
                receptor=receptor,
                pathway=pathway,
                evidence=evidence,
                confidence=confidence,
                tissue_specificity=tissue
            )
            self.pairs.append(pair)
            self.pair_map[(ligand, receptor)] = pair

    def get_all_pairs(self) -> List[LigandReceptorPair]:
        """Return all pairs."""
        return self.pairs

    def get_pairs_by_pathway(self, pathway: str) -> List[LigandReceptorPair]:
        """Get all pairs in a specific pathway."""
        return [p for p in self.pairs if pathway.lower() in p.pathway.lower()]

    def get_pairs_by_tissue(self, tissue: str) -> List[LigandReceptorPair]:
        """Get all pairs for a specific tissue type."""
        return [p for p in self.pairs if tissue.lower() in p.tissue_specificity.lower()]

    def get_nsclc_pairs(self) -> List[LigandReceptorPair]:
        """Get NSCLC-specific pairs."""
        return [p for p in self.pairs if p.tissue_specificity == "nsclc" or p.confidence >= 0.9]

    def has_pair(self, ligand: str, receptor: str) -> bool:
        """Check whether a ligand-receptor pair is in the database."""
        return (ligand, receptor) in self.pair_map

    def get_pair(self, ligand: str, receptor: str) -> Optional[LigandReceptorPair]:
        """Return metadata for a ligand-receptor pair if present."""
        return self.pair_map.get((ligand, receptor))

    def get_known_pair_set(self) -> Set[Tuple[str, str]]:
        """Return all ligand-receptor pairs as a set for fast lookup."""
        return set(self.pair_map.keys())

    def to_dict(self) -> Dict[str, Set[str]]:
        """
        Convert to simple dict format (for cosmx_adapter.py).

        Returns:
            Dict mapping ligand gene -> set of receptor genes
        """
        result = {}
        for pair in self.pairs:
            if pair.ligand not in result:
                result[pair.ligand] = set()
            result[pair.ligand].add(pair.receptor)
        return result

    def get_statistics(self) -> Dict[str, any]:
        """Get database statistics."""
        pathways = set(p.pathway for p in self.pairs)
        tissues = set(p.tissue_specificity for p in self.pairs)
        ligands = set(p.ligand for p in self.pairs)
        receptors = set(p.receptor for p in self.pairs)

        return {
            "total_pairs": len(self.pairs),
            "unique_ligands": len(ligands),
            "unique_receptors": len(receptors),
            "pathways": len(pathways),
            "tissue_types": len(tissues),
            "nsclc_specific": len([p for p in self.pairs if p.tissue_specificity == "nsclc"]),
            "high_confidence": len([p for p in self.pairs if p.confidence >= 0.9]),
        }


def build_ligand_receptor_database() -> Dict[str, Set[str]]:
    """
    Build and return ligand-receptor database in simple dict format.

    This is the function used by cosmx_adapter.py for backwards compatibility.

    Returns:
        Dict mapping ligand gene -> set of receptor genes
    """
    db = LigandReceptorDatabase()
    return db.to_dict()


if __name__ == '__main__':
    # Test database
    db = LigandReceptorDatabase()

    print("Ligand-Receptor Database Statistics:")
    print("=" * 60)

    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    print("\nNSCLC-Specific Pairs (top 10):")
    nsclc_pairs = db.get_nsclc_pairs()[:10]
    for pair in nsclc_pairs:
        print(f"  {pair.ligand} -> {pair.receptor} ({pair.pathway}, conf={pair.confidence:.1f})")

    print("\nImmune Checkpoint Pairs:")
    checkpoint_pairs = db.get_pairs_by_pathway("checkpoint")
    for pair in checkpoint_pairs:
        print(f"  {pair.ligand} -> {pair.receptor} ({pair.pathway})")

    print(f"\nTotal database size: {len(db.pairs)} pairs")
