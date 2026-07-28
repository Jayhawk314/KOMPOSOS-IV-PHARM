# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Pharmaceutical Drug Property Database
======================================

Molecular properties for the 78 drugs in tier1.db, structured as
molecular_bridge.molecule_properties.Molecule objects so the molecular
interaction scorers can operate on them.

Properties verified against PubChem PUG REST API (2026-05-13).
Original values from DrugBank; 46/68 drugs corrected via PubChem CID lookup.
Monoclonal antibodies are flagged separately (is_antibody=True) since
they are proteins, not small molecules, and molecular scoring does not
apply.

This module bridges the gap between the materials-chemistry Molecule
database in molecular_bridge/ and the pharma drug graph in tier1.db.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from molecular_bridge.molecule_properties import Molecule, MoleculeClass


# ---------------------------------------------------------------------------
# Compact drug property table
# Keys: name -> (MW, logP, HBD, HBA, functional_groups, PubChem CID)
# Sources: DrugBank 5.1, PubChem, FDA labels
# Monoclonal antibodies have MW=0 as sentinel (scored separately)
# ---------------------------------------------------------------------------

_DRUG_DATA: Dict[str, dict] = {
    # -- Kinase inhibitors --
    "Adagrasib":    {"mw": 604.7, "logP": 4.5, "hbd": 0, "hba": 9, "fg": ["pyridine", "piperazine", "fluoride", "chloride"], "cid": 138611145},
    "Afatinib":     {"mw": 485.9, "logP": 3.6, "hbd": 2, "hba": 8, "fg": ["quinazoline", "amine", "amide", "fluoride", "ether"], "cid": 10184653},
    "Alectinib":    {"mw": 482.6, "logP": 5.2, "hbd": 1, "hba": 5, "fg": ["carbazole", "nitrile", "amine", "carbonyl"], "cid": 49806720},
    "Binimetinib":  {"mw": 441.2, "logP": 2.7, "hbd": 3, "hba": 7, "fg": ["pyridazine", "amine", "amide", "fluoride", "hydroxyl"], "cid": 10288191},
    "Brigatinib":   {"mw": 584.7, "logP": 4.6, "hbd": 2, "hba": 9, "fg": ["pyrimidine", "amine", "phosphine_oxide", "chloride"], "cid": 68165256},
    "Capmatinib":   {"mw": 412.4, "logP": 2.5, "hbd": 1, "hba": 6, "fg": ["quinoline", "pyridine", "amine", "fluoride"], "cid": 25145656},
    "Cobimetinib":  {"mw": 531.3, "logP": 3.9, "hbd": 3, "hba": 7, "fg": ["piperidine", "amide", "fluoride", "azetidine"], "cid": 16222096},
    "Crizotinib":   {"mw": 450.3, "logP": 3.7, "hbd": 2, "hba": 6, "fg": ["pyridine", "pyrazole", "amine", "halide", "fluoride"], "cid": 11626560},
    "Dabrafenib":   {"mw": 519.6, "logP": 4.8, "hbd": 2, "hba": 11, "fg": ["thiazole", "pyrimidine", "amine", "sulfonamide", "fluoride"], "cid": 44462760},
    "Encorafenib":  {"mw": 540.0, "logP": 2.7, "hbd": 3, "hba": 10, "fg": ["pyrazole", "carbamate", "sulfonamide", "chloride", "fluoride"], "cid": 50922675},
    "Entrectinib":  {"mw": 560.6, "logP": 5.7, "hbd": 3, "hba": 8, "fg": ["indazole", "pyrazine", "amine", "amide", "fluoride"], "cid": 25141092},
    "Erlotinib":    {"mw": 393.4, "logP": 3.3, "hbd": 1, "hba": 7, "fg": ["quinazoline", "amine", "ether", "alkyne"], "cid": 176870},
    "Gefitinib":    {"mw": 446.9, "logP": 4.1, "hbd": 1, "hba": 8, "fg": ["quinazoline", "amine", "ether", "fluoride", "chloride", "morpholine"], "cid": 123631},
    "Imatinib":     {"mw": 493.6, "logP": 3.5, "hbd": 2, "hba": 7, "fg": ["pyrimidine", "pyridine", "amine", "amide", "piperazine"], "cid": 5291},
    "Lapatinib":    {"mw": 581.1, "logP": 5.4, "hbd": 2, "hba": 9, "fg": ["quinazoline", "amine", "furan", "sulfonyl", "fluoride", "chloride"], "cid": 208908},
    "Larotrectinib": {"mw": 428.4, "logP": 1.5, "hbd": 2, "hba": 7, "fg": ["pyrazole", "pyridine", "amine", "amide", "fluoride"], "cid": 46188928},
    "Lorlatinib":   {"mw": 406.4, "logP": 2.0, "hbd": 1, "hba": 7, "fg": ["pyridine", "pyrazole", "amine", "amide", "fluoride", "nitrile"], "cid": 71731823},
    "Osimertinib":  {"mw": 499.6, "logP": 3.4, "hbd": 2, "hba": 7, "fg": ["pyrimidine", "amine", "amide", "indole", "acrylamide"], "cid": 71496458},
    "Palbociclib":  {"mw": 447.5, "logP": 1.5, "hbd": 2, "hba": 8, "fg": ["pyridine", "pyrimidine", "amine", "amide", "piperazine", "carbonyl"], "cid": 5330286},
    "Pralsetinib":  {"mw": 533.6, "logP": 3.1, "hbd": 3, "hba": 9, "fg": ["pyrazole", "pyridine", "amine", "amide", "fluoride"], "cid": 129073603},
    "Regorafenib":  {"mw": 482.8, "logP": 3.8, "hbd": 3, "hba": 8, "fg": ["pyridine", "urea", "amide", "fluoride", "chloride", "ether"], "cid": 11167602},
    "Ribociclib":   {"mw": 434.5, "logP": 2.3, "hbd": 2, "hba": 7, "fg": ["pyridine", "pyrimidine", "amine", "piperazine", "carbonyl"], "cid": 44631912},
    "Ruxolitinib":  {"mw": 306.4, "logP": 2.1, "hbd": 1, "hba": 4, "fg": ["pyrrole", "pyrazole", "nitrile", "amine"], "cid": 25126798},
    "Selpercatinib": {"mw": 525.6, "logP": 2.2, "hbd": 1, "hba": 9, "fg": ["pyridine", "pyrazine", "amine", "ether", "methoxy"], "cid": 134436906},
    "Sorafenib":    {"mw": 464.8, "logP": 3.8, "hbd": 3, "hba": 7, "fg": ["pyridine", "urea", "amide", "chloride", "fluoride", "ether"], "cid": 216239},
    "Sotorasib":    {"mw": 560.6, "logP": 4.0, "hbd": 1, "hba": 7, "fg": ["pyridine", "pyrimidine", "fluoride", "piperazine", "acrylamide"], "cid": 137278711},
    "Sunitinib":    {"mw": 398.5, "logP": 2.4, "hbd": 3, "hba": 4, "fg": ["indole", "pyrrole", "amine", "amide", "fluoride", "carbonyl"], "cid": 5329102},
    "Tepotinib":    {"mw": 492.6, "logP": 3.4, "hbd": 0, "hba": 7, "fg": ["pyridine", "pyrimidine", "amine", "ether", "quinoline"], "cid": 25171648},
    "Trametinib":   {"mw": 615.4, "logP": 3.4, "hbd": 2, "hba": 6, "fg": ["pyrimidine", "pyridone", "amine", "amide", "fluoride", "iodide"], "cid": 11707110},
    "Vemurafenib":  {"mw": 489.9, "logP": 5.0, "hbd": 2, "hba": 7, "fg": ["pyrrole", "sulfonamide", "fluoride", "chloride", "aromatic"], "cid": 42611257},

    # -- mTOR inhibitors --
    "Everolimus":   {"mw": 958.2, "logP": 5.9, "hbd": 3, "hba": 14, "fg": ["macrolide", "ester", "ether", "hydroxyl", "carbonyl"], "cid": 6442177},
    "Temsirolimus": {"mw": 1030.3, "logP": 5.5, "hbd": 4, "hba": 16, "fg": ["macrolide", "ester", "ether", "hydroxyl", "carbonyl"], "cid": 6918289},

    # -- PARP inhibitor --
    "Olaparib":     {"mw": 434.5, "logP": 1.5, "hbd": 1, "hba": 5, "fg": ["phthalazinone", "piperazine", "amide", "carbonyl", "fluoride"], "cid": 23725625},

    # -- BCL2 inhibitor --
    "Venetoclax":   {"mw": 868.4, "logP": 7.9, "hbd": 3, "hba": 11, "fg": ["sulfonamide", "amine", "ether", "chloride", "aromatic", "nitro"], "cid": 49846579},

    # -- Thalidomide/IMiD --
    "Thalidomide":  {"mw": 258.2, "logP": 0.3, "hbd": 1, "hba": 4, "fg": ["glutarimide", "phthalimide", "amide", "carbonyl"], "cid": 5426},

    # -- Platinum agents --
    "Carboplatin":  {"mw": 371.3, "logP": -2.3, "hbd": 2, "hba": 6, "fg": ["platinum_complex", "amine", "carboxylate"], "cid": 10339178},
    "Cisplatin":    {"mw": 300.1, "logP": -2.2, "hbd": 2, "hba": 2, "fg": ["platinum_complex", "amine", "chloride"], "cid": 5460033},
    "Oxaliplatin":  {"mw": 397.3, "logP": -1.6, "hbd": 4, "hba": 6, "fg": ["platinum_complex", "amine", "carboxylate"], "cid": 9887053},

    # -- Antimetabolites --
    "Fluorouracil": {"mw": 130.1, "logP": -0.9, "hbd": 2, "hba": 3, "fg": ["pyrimidine", "fluoride", "amide", "carbonyl"], "cid": 3385},
    "Pemetrexed":   {"mw": 427.4, "logP": 0.2, "hbd": 6, "hba": 7, "fg": ["pyrrole", "pyrimidine", "amine", "carboxyl", "amide"], "cid": 135410875},

    # -- Topoisomerase --
    "Irinotecan":   {"mw": 586.7, "logP": 2.9, "hbd": 1, "hba": 8, "fg": ["camptothecin", "ester", "amine", "lactone", "piperidine"], "cid": 60838},

    # -- COX inhibitors / NSAIDs --
    "Aspirin":      {"mw": 180.2, "logP": 1.2, "hbd": 1, "hba": 4, "fg": ["ester", "carboxyl", "aromatic"], "cid": 2244},
    "Celecoxib":    {"mw": 381.4, "logP": 3.5, "hbd": 1, "hba": 7, "fg": ["sulfonamide", "pyrazole", "amine", "fluoride", "aromatic"], "cid": 2662},
    "Diclofenac":   {"mw": 296.1, "logP": 4.5, "hbd": 2, "hba": 3, "fg": ["amine", "carboxyl", "chloride", "aromatic"], "cid": 3033},
    "Indomethacin": {"mw": 357.8, "logP": 4.3, "hbd": 1, "hba": 4, "fg": ["indole", "ether", "carboxyl", "chloride", "amide", "carbonyl"], "cid": 3715},

    # -- Repurposed drugs --
    "Artesunate":   {"mw": 384.4, "logP": 2.2, "hbd": 1, "hba": 8, "fg": ["endoperoxide", "ester", "lactone", "carboxyl"], "cid": 6917864},
    "Atorvastatin": {"mw": 558.6, "logP": 5.0, "hbd": 4, "hba": 6, "fg": ["pyrrole", "amide", "carboxyl", "hydroxyl", "fluoride", "aromatic"], "cid": 60823},
    "Auranofin":    {"mw": 678.5, "logP": 3.7, "hbd": 0, "hba": 10, "fg": ["gold_complex", "phosphine", "thiol", "ester", "acetyl"], "cid": 16667669},
    "Bazedoxifene": {"mw": 470.6, "logP": 5.8, "hbd": 2, "hba": 4, "fg": ["indole", "phenol", "amine", "aromatic", "piperidine"], "cid": 154257},
    "Chloroquine":  {"mw": 319.9, "logP": 4.6, "hbd": 1, "hba": 3, "fg": ["quinoline", "amine", "chloride"], "cid": 2719},
    "Cimetidine":   {"mw": 252.3, "logP": 0.4, "hbd": 3, "hba": 4, "fg": ["imidazole", "amine", "thioether", "guanidine", "nitrile"], "cid": 2756},
    "Clarithromycin": {"mw": 747.9, "logP": 3.2, "hbd": 4, "hba": 14, "fg": ["macrolide", "ester", "ether", "hydroxyl", "amine"], "cid": 84029},
    "Disulfiram":   {"mw": 296.5, "logP": 3.9, "hbd": 0, "hba": 4, "fg": ["thiocarbamate", "disulfide", "amine"], "cid": 3117},
    "Doxycycline":  {"mw": 444.4, "logP": -0.5, "hbd": 6, "hba": 9, "fg": ["tetracycline", "amide", "hydroxyl", "amine", "carbonyl", "phenol"], "cid": 54671203},
    "Itraconazole": {"mw": 705.6, "logP": 5.7, "hbd": 0, "hba": 9, "fg": ["triazole", "piperazine", "ether", "chloride", "ketone"], "cid": 55283},
    "Ivermectin":   {"mw": 875.1, "logP": 5.8, "hbd": 3, "hba": 14, "fg": ["macrolide", "ester", "ether", "hydroxyl"], "cid": 6321424},
    "Leflunomide":  {"mw": 270.2, "logP": 2.5, "hbd": 1, "hba": 6, "fg": ["isoxazole", "amide", "fluoride", "nitrile"], "cid": 3899},
    "Mebendazole":  {"mw": 295.3, "logP": 2.8, "hbd": 2, "hba": 4, "fg": ["benzimidazole", "carbamate", "amine", "carbonyl"], "cid": 4030},
    "Metformin":    {"mw": 129.2, "logP": -1.4, "hbd": 3, "hba": 1, "fg": ["guanidine", "amine"], "cid": 4091},
    "Nelfinavir":   {"mw": 567.8, "logP": 5.7, "hbd": 4, "hba": 6, "fg": ["amine", "hydroxyl", "amide", "thiol", "aromatic", "phenol"], "cid": 64143},
    "Niclosamide":  {"mw": 327.1, "logP": 3.9, "hbd": 2, "hba": 4, "fg": ["hydroxyl", "amide", "chloride", "nitro", "aromatic", "phenol"], "cid": 4477},
    "Nitroglycerin": {"mw": 227.1, "logP": 1.6, "hbd": 0, "hba": 9, "fg": ["nitrate", "ester"], "cid": 4510},
    "Pirfenidone":  {"mw": 185.2, "logP": 1.9, "hbd": 0, "hba": 1, "fg": ["pyridone", "aromatic", "carbonyl"], "cid": 40632},
    "Propranolol":  {"mw": 259.3, "logP": 3.5, "hbd": 2, "hba": 3, "fg": ["naphthalene", "ether", "amine", "hydroxyl", "aromatic"], "cid": 4946},
    "Ritonavir":    {"mw": 720.9, "logP": 5.9, "hbd": 4, "hba": 9, "fg": ["thiazole", "amine", "amide", "hydroxyl", "carbamate", "ether", "urea"], "cid": 392622},
    "Suramin":      {"mw": 1297.3, "logP": 1.5, "hbd": 12, "hba": 23, "fg": ["sulfonyl", "amine", "amide", "carboxyl", "aromatic", "urea"], "cid": 5361},
    "Valproic_Acid": {"mw": 144.2, "logP": 2.8, "hbd": 1, "hba": 2, "fg": ["carboxyl"], "cid": 3121},
    "Verapamil":    {"mw": 454.6, "logP": 3.8, "hbd": 0, "hba": 6, "fg": ["amine", "ether", "nitrile", "methoxy", "aromatic"], "cid": 2520},

    # -- Monoclonal antibodies (flagged, not small molecules) --
    "Atezolizumab": {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Bevacizumab":  {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Cetuximab":    {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Durvalumab":   {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Ipilimumab":   {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Nivolumab":    {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Pembrolizumab": {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Ramucirumab":  {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Trastuzumab":  {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody"], "cid": 0, "is_antibody": True},
    "Trastuzumab_deruxtecan": {"mw": 0, "logP": None, "hbd": 0, "hba": 0, "fg": ["antibody", "adc"], "cid": 0, "is_antibody": True},
}


# ---------------------------------------------------------------------------
# Protein target properties (approximate, for drug-target compatibility)
# Maps protein name -> dict of target-site properties
# ---------------------------------------------------------------------------

# Kinase domain proteins (have HRD/DFG active-site motifs)
_KINASE_TARGETS = {
    "ABL1", "ALK", "BRAF", "CDK4", "CDK6", "EGFR", "ERBB2", "ERBB4",
    "FLT3", "JAK2", "KDR", "KIT", "MAP2K1", "MAP2K2", "MEK1", "MET",
    "MST1R", "MTOR", "NTRK1", "NTRK2", "NTRK3", "PDGFRA", "PDGFRB",
    "RAF1", "RET", "ROS1", "VEGFR2", "BCR_ABL",
}

# Protease targets
_PROTEASE_TARGETS = {
    "MMP1", "MMP2", "MMP7", "MMP8", "MMP9", "MMP13", "TOP1", "TOP2A",
}

# Immune checkpoint / surface proteins
_IMMUNE_TARGETS = {
    "CD274", "PDCD1", "CTLA4", "CD4", "CD8A", "FOXP3",
}

# Approximate target properties for molecular compatibility scoring
# logP_pocket: hydrophobicity of binding pocket (higher = more hydrophobic)
# hba_pocket, hbd_pocket: H-bond capacity of binding pocket
_TARGET_PROPERTIES: Dict[str, dict] = {}
for _t in _KINASE_TARGETS:
    _TARGET_PROPERTIES[_t] = {"logP_pocket": 2.5, "hba_pocket": 4, "hbd_pocket": 3, "domain": "kinase"}
for _t in _PROTEASE_TARGETS:
    _TARGET_PROPERTIES[_t] = {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 4, "domain": "protease"}
for _t in _IMMUNE_TARGETS:
    _TARGET_PROPERTIES[_t] = {"logP_pocket": 0.5, "hba_pocket": 6, "hbd_pocket": 5, "domain": "immune_surface"}

# Override specific well-characterized targets
_TARGET_PROPERTIES.update({
    "HMGCR": {"logP_pocket": 3.0, "hba_pocket": 4, "hbd_pocket": 2, "domain": "reductase"},
    "COX2": {"logP_pocket": 3.5, "hba_pocket": 3, "hbd_pocket": 2, "domain": "cyclooxygenase"},
    "PTGS2": {"logP_pocket": 3.5, "hba_pocket": 3, "hbd_pocket": 2, "domain": "cyclooxygenase"},
    "DHODH": {"logP_pocket": 2.0, "hba_pocket": 5, "hbd_pocket": 3, "domain": "oxidoreductase"},
    "TYMS": {"logP_pocket": 0.5, "hba_pocket": 6, "hbd_pocket": 4, "domain": "transferase"},
    "FKBP1A": {"logP_pocket": 2.5, "hba_pocket": 4, "hbd_pocket": 3, "domain": "immunophilin"},
    "CRBN": {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 3, "domain": "ubiquitin_ligase"},
    "BCL2": {"logP_pocket": 4.0, "hba_pocket": 3, "hbd_pocket": 2, "domain": "bcl2_family"},
    "HDAC1": {"logP_pocket": 2.0, "hba_pocket": 5, "hbd_pocket": 3, "domain": "deacetylase"},
    "HDAC2": {"logP_pocket": 2.0, "hba_pocket": 5, "hbd_pocket": 3, "domain": "deacetylase"},
    "ALDH2": {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 4, "domain": "dehydrogenase"},
    "NPL4": {"logP_pocket": 2.0, "hba_pocket": 4, "hbd_pocket": 3, "domain": "ubiquitin"},
    "TXNRD1": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "reductase"},
    "ABCB1": {"logP_pocket": 4.0, "hba_pocket": 3, "hbd_pocket": 2, "domain": "transporter"},
    "BRCA1": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "dna_repair"},
    "BRCA2": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "dna_repair"},
    "HRH2": {"logP_pocket": 1.5, "hba_pocket": 4, "hbd_pocket": 3, "domain": "gpcr"},
    "AMPK": {"logP_pocket": 2.0, "hba_pocket": 5, "hbd_pocket": 3, "domain": "kinase"},
    "TGFB1": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "growth_factor"},
    "HIF1A": {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 4, "domain": "transcription_factor"},
    "VEGFA": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "growth_factor"},
    "IL6": {"logP_pocket": 0.5, "hba_pocket": 6, "hbd_pocket": 5, "domain": "cytokine"},
    "TP53": {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 4, "domain": "transcription_factor"},
    "KRAS": {"logP_pocket": 2.0, "hba_pocket": 4, "hbd_pocket": 3, "domain": "gtpase"},
    "NRAS": {"logP_pocket": 2.0, "hba_pocket": 4, "hbd_pocket": 3, "domain": "gtpase"},
    "NFKB1": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 4, "domain": "transcription_factor"},
    "STAT3": {"logP_pocket": 1.5, "hba_pocket": 5, "hbd_pocket": 4, "domain": "transcription_factor"},
    "AKT1": {"logP_pocket": 2.5, "hba_pocket": 4, "hbd_pocket": 3, "domain": "kinase"},
    "MYC": {"logP_pocket": 1.0, "hba_pocket": 5, "hbd_pocket": 5, "domain": "transcription_factor"},
    "MAPK1": {"logP_pocket": 2.5, "hba_pocket": 4, "hbd_pocket": 3, "domain": "kinase"},
})


def _make_molecule(name: str, d: dict) -> Molecule:
    """Build a Molecule from the compact data dict."""
    return Molecule(
        name=name,
        formula="",  # Not needed for scoring
        pubchem_cid=d.get("cid", 0),
        cas_number="",
        smiles="",
        molecular_weight=d["mw"],
        functional_groups=d.get("fg", []),
        logP=d.get("logP"),
        hbond_donors=d.get("hbd", 0),
        hbond_acceptors=d.get("hba", 0),
        molecule_class=MoleculeClass.OTHER,
    )


# Build the drug Molecule lookup
PHARMA_DRUGS: Dict[str, Molecule] = {}
ANTIBODY_DRUGS: set = set()

for _name, _data in _DRUG_DATA.items():
    if _data.get("is_antibody"):
        ANTIBODY_DRUGS.add(_name)
    PHARMA_DRUGS[_name] = _make_molecule(_name, _data)


def get_drug(name: str) -> Optional[Molecule]:
    """Look up a drug by name. Returns None if not found."""
    return PHARMA_DRUGS.get(name)


def is_antibody(name: str) -> bool:
    """Check if a drug is a monoclonal antibody (not a small molecule)."""
    return name in ANTIBODY_DRUGS


def get_target_properties(protein: str) -> Optional[dict]:
    """Get approximate binding-pocket properties for a protein target."""
    return _TARGET_PROPERTIES.get(protein)


def get_drug_likeness(name: str) -> Optional[float]:
    """
    Compute Lipinski Rule-of-Five drug-likeness score.

    Returns 0-1 score based on how many of the 4 Lipinski rules
    are satisfied. Returns None for antibodies.
    """
    if is_antibody(name):
        return None
    mol = PHARMA_DRUGS.get(name)
    if mol is None:
        return None

    violations = 0
    if mol.molecular_weight > 500:
        violations += 1
    if mol.logP is not None and mol.logP > 5:
        violations += 1
    if mol.hbond_donors > 5:
        violations += 1
    if mol.hbond_acceptors > 10:
        violations += 1

    return 1.0 - (violations * 0.25)


def compute_drug_target_compatibility(drug_name: str, protein_name: str) -> Optional[float]:
    """
    Compute drug-target molecular compatibility score.

    Uses logP matching (hydrophobic complementarity) and H-bond
    complementarity between drug functional groups and binding pocket.

    Returns 0-1 score or None if insufficient data.
    """
    drug = PHARMA_DRUGS.get(drug_name)
    target = _TARGET_PROPERTIES.get(protein_name)
    if drug is None or target is None:
        return None
    if is_antibody(drug_name):
        return None  # Antibodies need different scoring

    score = 0.5  # baseline

    # logP complementarity: drug logP should be moderate (2-4) for cell permeability
    # AND compatible with target pocket hydrophobicity
    if drug.logP is not None:
        pocket_logP = target.get("logP_pocket", 2.0)
        logP_diff = abs(drug.logP - pocket_logP)
        # Best when drug logP matches pocket: Gaussian with sigma=2
        import math
        logP_match = math.exp(-(logP_diff ** 2) / (2 * 2.0 ** 2))
        score += 0.2 * logP_match

    # H-bond complementarity: drug donors match pocket acceptors and vice versa
    pocket_hba = target.get("hba_pocket", 3)
    pocket_hbd = target.get("hbd_pocket", 3)
    hbond_pairs = min(drug.hbond_donors, pocket_hba) + min(drug.hbond_acceptors, pocket_hbd)
    total_sites = drug.hbond_donors + drug.hbond_acceptors + pocket_hba + pocket_hbd
    if total_sites > 0:
        complementarity = (2.0 * hbond_pairs) / total_sites
        score += 0.15 * min(1.0, complementarity)

    # Functional group bonus: kinase inhibitors targeting kinases
    drug_fg = set(g.lower() for g in drug.functional_groups)
    target_domain = target.get("domain", "")
    if target_domain == "kinase" and ("amine" in drug_fg or "amide" in drug_fg):
        score += 0.1  # Kinase inhibitors typically have amine/amide for hinge binding
    if target_domain == "cyclooxygenase" and "carboxyl" in drug_fg:
        score += 0.1  # NSAIDs bind COX active site with carboxyl group

    return min(1.0, score)
