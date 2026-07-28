# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Noetik-Focused Drug Network Expansion
======================================

Adds FDA-approved cancer drugs for NSCLC/CRC (Noetik's GSK partnership focus).
All drugs are FDA-approved. All targets are experimentally verified.

Sources:
  FDA Approved Drugs
  DrugBank 5.x
  ClinicalTrials.gov
  KEGG DRUG
  PubMed literature
"""

# ============================================================================
# NEW DRUGS (Noetik-aligned: NSCLC, CRC, immunotherapy)
# ============================================================================

NOETIK_DRUGS = {
    # === EGFR Inhibitors (NSCLC) ===
    "Osimertinib": {
        "type": "Drug",
        "brand": "Tagrisso",
        "drug_class": "EGFR inhibitor (3rd gen)",
        "mechanism": "Irreversible EGFR T790M mutant-selective inhibitor",
        "fda_year": 2015,
        "drugbank_id": "DB09330",
    },
    "Afatinib": {
        "type": "Drug",
        "brand": "Gilotrif",
        "drug_class": "Pan-ERBB inhibitor",
        "mechanism": "Irreversible pan-ERBB (EGFR, HER2, HER4) inhibitor",
        "fda_year": 2013,
        "drugbank_id": "DB08916",
    },

    # === PD-1/PD-L1 Checkpoint Inhibitors (NSCLC, CRC) ===
    "Pembrolizumab": {
        "type": "Drug",
        "brand": "Keytruda",
        "drug_class": "Anti-PD-1 antibody",
        "mechanism": "Blocks PD-1/PD-L1 interaction, activates T cells",
        "fda_year": 2014,
        "drugbank_id": "DB09037",
    },
    "Nivolumab": {
        "type": "Drug",
        "brand": "Opdivo",
        "drug_class": "Anti-PD-1 antibody",
        "mechanism": "Blocks PD-1/PD-L1 interaction, activates T cells",
        "fda_year": 2014,
        "drugbank_id": "DB09035",
    },
    "Atezolizumab": {
        "type": "Drug",
        "brand": "Tecentriq",
        "drug_class": "Anti-PD-L1 antibody",
        "mechanism": "Blocks PD-L1, prevents T cell inactivation",
        "fda_year": 2016,
        "drugbank_id": "DB11945",
    },
    "Durvalumab": {
        "type": "Drug",
        "brand": "Imfinzi",
        "drug_class": "Anti-PD-L1 antibody",
        "mechanism": "Blocks PD-L1, prevents T cell inactivation",
        "fda_year": 2017,
        "drugbank_id": "DB11714",
    },

    # === KRAS Inhibitors (NSCLC, CRC) ===
    "Sotorasib": {
        "type": "Drug",
        "brand": "Lumakras",
        "drug_class": "KRAS G12C inhibitor",
        "mechanism": "Selective KRAS G12C covalent inhibitor",
        "fda_year": 2021,
        "drugbank_id": "DB15608",
    },
    "Adagrasib": {
        "type": "Drug",
        "brand": "Krazati",
        "drug_class": "KRAS G12C inhibitor",
        "mechanism": "Selective KRAS G12C covalent inhibitor",
        "fda_year": 2022,
        "drugbank_id": "DB17133",
    },

    # === BRAF/MEK Inhibitors (CRC, melanoma) ===
    "Encorafenib": {
        "type": "Drug",
        "brand": "Braftovi",
        "drug_class": "BRAF inhibitor",
        "mechanism": "Selective BRAF V600E/K inhibitor",
        "fda_year": 2018,
        "drugbank_id": "DB11973",
    },
    "Cobimetinib": {
        "type": "Drug",
        "brand": "Cotellic",
        "drug_class": "MEK inhibitor",
        "mechanism": "Selective MEK1/MEK2 inhibitor",
        "fda_year": 2015,
        "drugbank_id": "DB11496",
    },
    "Binimetinib": {
        "type": "Drug",
        "brand": "Mektovi",
        "drug_class": "MEK inhibitor",
        "mechanism": "Selective MEK1/MEK2 inhibitor",
        "fda_year": 2018,
        "drugbank_id": "DB12191",
    },

    # === ALK Inhibitors (NSCLC) ===
    "Alectinib": {
        "type": "Drug",
        "brand": "Alecensa",
        "drug_class": "ALK inhibitor (2nd gen)",
        "mechanism": "Selective ALK and RET inhibitor, CNS-penetrant",
        "fda_year": 2015,
        "drugbank_id": "DB11363",
    },
    "Brigatinib": {
        "type": "Drug",
        "brand": "Alunbrig",
        "drug_class": "ALK inhibitor (2nd gen)",
        "mechanism": "ALK and EGFR T790M inhibitor",
        "fda_year": 2017,
        "drugbank_id": "DB11732",
    },
    "Lorlatinib": {
        "type": "Drug",
        "brand": "Lorbrena",
        "drug_class": "ALK inhibitor (3rd gen)",
        "mechanism": "Pan-ALK/ROS1 inhibitor, overcomes resistance",
        "fda_year": 2018,
        "drugbank_id": "DB11879",
    },

    # === VEGF/Angiogenesis Inhibitors (NSCLC, CRC) ===
    "Ramucirumab": {
        "type": "Drug",
        "brand": "Cyramza",
        "drug_class": "Anti-VEGFR2 antibody",
        "mechanism": "Blocks VEGFR2, inhibits angiogenesis",
        "fda_year": 2014,
        "drugbank_id": "DB09129",
    },
    "Regorafenib": {
        "type": "Drug",
        "brand": "Stivarga",
        "drug_class": "Multi-kinase inhibitor",
        "mechanism": "VEGFR1/2/3, KIT, PDGFR, FGFR, RET inhibitor",
        "fda_year": 2012,
        "drugbank_id": "DB08896",
    },

    # === HER2 ADC (some NSCLC) ===
    "Trastuzumab_deruxtecan": {
        "type": "Drug",
        "brand": "Enhertu",
        "drug_class": "HER2 antibody-drug conjugate",
        "mechanism": "Anti-HER2 antibody conjugated to topoisomerase I inhibitor",
        "fda_year": 2019,
        "drugbank_id": "DB15146",
    },

    # === ROS1/NTRK Inhibitors (NSCLC, pan-cancer) ===
    "Entrectinib": {
        "type": "Drug",
        "brand": "Rozlytrek",
        "drug_class": "ROS1/NTRK/ALK inhibitor",
        "mechanism": "Pan-TRK, ROS1, ALK inhibitor, CNS-penetrant",
        "fda_year": 2019,
        "drugbank_id": "DB11986",
    },
    "Larotrectinib": {
        "type": "Drug",
        "brand": "Vitrakvi",
        "drug_class": "Pan-TRK inhibitor",
        "mechanism": "Selective NTRK1/2/3 fusion inhibitor",
        "fda_year": 2018,
        "drugbank_id": "DB12267",
    },

    # === MET Inhibitors (NSCLC) ===
    "Capmatinib": {
        "type": "Drug",
        "brand": "Tabrecta",
        "drug_class": "MET inhibitor",
        "mechanism": "Selective MET inhibitor for MET exon 14 skipping",
        "fda_year": 2020,
        "drugbank_id": "DB15469",
    },
    "Tepotinib": {
        "type": "Drug",
        "brand": "Tepmetko",
        "drug_class": "MET inhibitor",
        "mechanism": "Selective MET inhibitor for MET exon 14 skipping",
        "fda_year": 2021,
        "drugbank_id": "DB15610",
    },

    # === RET Inhibitors (NSCLC, thyroid) ===
    "Selpercatinib": {
        "type": "Drug",
        "brand": "Retevmo",
        "drug_class": "RET inhibitor",
        "mechanism": "Selective RET fusion/mutation inhibitor",
        "fda_year": 2020,
        "drugbank_id": "DB15274",
    },
    "Pralsetinib": {
        "type": "Drug",
        "brand": "Gavreto",
        "drug_class": "RET inhibitor",
        "mechanism": "Selective RET fusion/mutation inhibitor",
        "fda_year": 2020,
        "drugbank_id": "DB15619",
    },

    # === CTLA-4 Inhibitor (combo with PD-1) ===
    "Ipilimumab": {
        "type": "Drug",
        "brand": "Yervoy",
        "drug_class": "Anti-CTLA-4 antibody",
        "mechanism": "Blocks CTLA-4, enhances T cell activation",
        "fda_year": 2011,
        "drugbank_id": "DB08835",
    },

    # === Chemotherapy (still used in NSCLC/CRC) ===
    "Cisplatin": {
        "type": "Drug",
        "brand": "Platinol",
        "drug_class": "Platinum-based chemotherapy",
        "mechanism": "DNA crosslinking, induces apoptosis",
        "fda_year": 1978,
        "drugbank_id": "DB00515",
    },
    "Carboplatin": {
        "type": "Drug",
        "brand": "Paraplatin",
        "drug_class": "Platinum-based chemotherapy",
        "mechanism": "DNA crosslinking, less toxic than cisplatin",
        "fda_year": 1989,
        "drugbank_id": "DB00958",
    },
    "Pemetrexed": {
        "type": "Drug",
        "brand": "Alimta",
        "drug_class": "Antifolate chemotherapy",
        "mechanism": "Inhibits thymidylate synthase, DHFR, GARFT",
        "fda_year": 2004,
        "drugbank_id": "DB00642",
    },
    "Fluorouracil": {
        "type": "Drug",
        "brand": "5-FU, Adrucil",
        "drug_class": "Pyrimidine analog",
        "mechanism": "Inhibits thymidylate synthase, DNA/RNA damage",
        "fda_year": 1962,
        "drugbank_id": "DB00544",
    },
    "Oxaliplatin": {
        "type": "Drug",
        "brand": "Eloxatin",
        "drug_class": "Platinum-based chemotherapy",
        "mechanism": "DNA crosslinking, synergistic with 5-FU",
        "fda_year": 2002,
        "drugbank_id": "DB00526",
    },
    "Irinotecan": {
        "type": "Drug",
        "brand": "Camptosar",
        "drug_class": "Topoisomerase I inhibitor",
        "mechanism": "Inhibits DNA topoisomerase I, DNA damage",
        "fda_year": 1996,
        "drugbank_id": "DB00762",
    },
}


# ============================================================================
# NEW PROTEINS/TARGETS (Spatial biomarkers for Noetik integration)
# ============================================================================

NOETIK_PROTEINS = {
    # Immune checkpoint targets
    "PDCD1": {
        "type": "Receptor",
        "function": "Programmed cell death protein 1 (PD-1), T cell checkpoint",
        "pathways": ["T cell activation", "immune checkpoint"],
        "cancers": ["NSCLC", "melanoma", "RCC", "Hodgkin"],
    },
    "CD274": {
        "type": "Ligand",
        "function": "Programmed death-ligand 1 (PD-L1), inhibits T cells",
        "pathways": ["T cell inhibition", "immune evasion"],
        "cancers": ["NSCLC", "triple-negative breast", "urothelial"],
    },
    "CTLA4": {
        "type": "Receptor",
        "function": "Cytotoxic T-lymphocyte-associated protein 4, T cell checkpoint",
        "pathways": ["T cell activation", "immune checkpoint"],
        "cancers": ["melanoma", "RCC"],
    },

    # T cell markers (spatial biology)
    "CD8A": {
        "type": "Marker",
        "function": "CD8 alpha chain, cytotoxic T cell marker",
        "pathways": ["T cell cytotoxicity"],
        "cancers": ["prognostic in many cancers"],
    },
    "CD4": {
        "type": "Marker",
        "function": "CD4 glycoprotein, T helper cell marker",
        "pathways": ["T cell help"],
        "cancers": ["prognostic in many cancers"],
    },
    "FOXP3": {
        "type": "Transcription",
        "function": "Forkhead box P3, regulatory T cell marker",
        "pathways": ["immune suppression"],
        "cancers": ["poor prognosis in many cancers"],
    },

    # Macrophage markers
    "CD68": {
        "type": "Marker",
        "function": "CD68 antigen, pan-macrophage marker",
        "pathways": ["phagocytosis", "inflammation"],
        "cancers": ["tumor-associated macrophages"],
    },
    "CD163": {
        "type": "Marker",
        "function": "CD163 antigen, M2 macrophage marker",
        "pathways": ["anti-inflammatory", "tumor promotion"],
        "cancers": ["poor prognosis"],
    },

    # Angiogenesis
    "VEGFA": {
        "type": "Ligand",
        "function": "Vascular endothelial growth factor A",
        "pathways": ["angiogenesis", "vascular permeability"],
        "cancers": ["promotes metastasis"],
    },
    "KDR": {
        "type": "Receptor",
        "function": "Kinase insert domain receptor (VEGFR2)",
        "pathways": ["angiogenesis", "endothelial proliferation"],
        "cancers": ["therapeutic target"],
    },

    # MAP kinase pathway (downstream of EGFR, KRAS, BRAF)
    "MAP2K1": {
        "type": "Signaling",
        "function": "Mitogen-activated protein kinase kinase 1 (MEK1)",
        "pathways": ["MAPK/ERK", "cell proliferation"],
        "cancers": ["NSCLC", "melanoma", "CRC"],
    },
    "MAPK1": {
        "type": "Signaling",
        "function": "Mitogen-activated protein kinase 1 (ERK2)",
        "pathways": ["MAPK/ERK", "cell proliferation"],
        "cancers": ["many cancers"],
    },

    # PI3K/AKT/mTOR pathway components
    "PIK3CA": {
        "type": "Signaling",
        "function": "Phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha",
        "pathways": ["PI3K-AKT", "cell survival"],
        "cancers": ["breast", "colorectal", "endometrial"],
    },

    # Fusion/mutation targets
    "NTRK1": {
        "type": "Receptor",
        "function": "Neurotrophic receptor tyrosine kinase 1 (TrkA)",
        "pathways": ["neurotrophin signaling"],
        "cancers": ["NTRK fusions in many cancers"],
    },
    "NTRK2": {
        "type": "Receptor",
        "function": "Neurotrophic receptor tyrosine kinase 2 (TrkB)",
        "pathways": ["neurotrophin signaling"],
        "cancers": ["NTRK fusions"],
    },
    "NTRK3": {
        "type": "Receptor",
        "function": "Neurotrophic receptor tyrosine kinase 3 (TrkC)",
        "pathways": ["neurotrophin signaling"],
        "cancers": ["NTRK fusions"],
    },
    "RET": {
        "type": "Receptor",
        "function": "Ret proto-oncogene, receptor tyrosine kinase",
        "pathways": ["MAPK", "PI3K-AKT"],
        "cancers": ["NSCLC RET fusions", "thyroid RET mutations"],
    },

    # Chemotherapy targets
    "TYMS": {
        "type": "Metabolic",
        "function": "Thymidylate synthase, DNA synthesis enzyme",
        "pathways": ["nucleotide synthesis"],
        "cancers": ["chemotherapy target"],
    },
    "TOP1": {
        "type": "Enzyme",
        "function": "DNA topoisomerase I",
        "pathways": ["DNA replication"],
        "cancers": ["irinotecan target"],
    },
    "TOP2A": {
        "type": "Enzyme",
        "function": "DNA topoisomerase II alpha",
        "pathways": ["DNA replication"],
        "cancers": ["chemotherapy target"],
    },
}


# ============================================================================
# DRUG -> PROTEIN INTERACTIONS (Noetik expansion)
# Format: (drug, protein, relation, confidence, evidence)
# ============================================================================

NOETIK_DRUG_TARGETS = [
    # === EGFR inhibitors ===
    ("Osimertinib", "EGFR", "inhibits", 0.98, "Selective EGFR T790M inhibitor (IC50=12nM wild-type, 1nM T790M)"),
    ("Afatinib", "EGFR", "inhibits", 0.97, "Irreversible EGFR inhibitor (IC50=0.5nM)"),
    ("Afatinib", "ERBB2", "inhibits", 0.95, "Irreversible HER2 inhibitor (IC50=14nM)"),

    # === PD-1/PD-L1 inhibitors ===
    ("Pembrolizumab", "PDCD1", "inhibits", 0.99, "Anti-PD-1 monoclonal antibody (KD=29pM)"),
    ("Nivolumab", "PDCD1", "inhibits", 0.99, "Anti-PD-1 monoclonal antibody"),
    ("Atezolizumab", "CD274", "inhibits", 0.98, "Anti-PD-L1 monoclonal antibody"),
    ("Durvalumab", "CD274", "inhibits", 0.98, "Anti-PD-L1 monoclonal antibody"),

    # === KRAS inhibitors ===
    ("Sotorasib", "KRAS", "inhibits", 0.97, "Covalent KRAS G12C inhibitor (IC50=0.2µM)"),
    ("Adagrasib", "KRAS", "inhibits", 0.97, "Covalent KRAS G12C inhibitor (IC50=0.01µM)"),

    # === BRAF/MEK inhibitors ===
    ("Encorafenib", "BRAF", "inhibits", 0.97, "BRAF V600E inhibitor (IC50=0.35nM)"),
    ("Cobimetinib", "MAP2K1", "inhibits", 0.98, "MEK1/2 allosteric inhibitor (IC50=0.9nM)"),
    ("Binimetinib", "MAP2K1", "inhibits", 0.98, "MEK1/2 allosteric inhibitor (IC50=12nM)"),

    # === ALK inhibitors ===
    ("Alectinib", "ALK", "inhibits", 0.98, "ALK inhibitor (IC50=1.9nM), overcomes Crizotinib resistance"),
    ("Alectinib", "RET", "inhibits", 0.85, "Cross-reactive RET inhibitor"),
    ("Brigatinib", "ALK", "inhibits", 0.98, "ALK inhibitor (IC50=0.6nM)"),
    ("Brigatinib", "EGFR", "inhibits", 0.75, "EGFR T790M inhibitor"),
    ("Lorlatinib", "ALK", "inhibits", 0.99, "Pan-ALK inhibitor (IC50=0.07nM)"),
    ("Lorlatinib", "ROS1", "inhibits", 0.95, "ROS1 inhibitor (IC50=0.07nM)"),

    # === VEGF/Angiogenesis ===
    ("Ramucirumab", "KDR", "inhibits", 0.98, "Anti-VEGFR2 monoclonal antibody"),
    ("Regorafenib", "KDR", "inhibits", 0.90, "VEGFR2 kinase inhibitor (IC50=4.2nM)"),
    ("Regorafenib", "RET", "inhibits", 0.88, "RET kinase inhibitor"),

    # === HER2 ADC ===
    ("Trastuzumab_deruxtecan", "ERBB2", "inhibits", 0.98, "Anti-HER2 antibody"),
    ("Trastuzumab_deruxtecan", "TOP1", "inhibits", 0.95, "Deruxtecan payload inhibits topoisomerase I"),

    # === ROS1/NTRK inhibitors ===
    ("Entrectinib", "ROS1", "inhibits", 0.97, "ROS1 inhibitor (IC50=0.2nM)"),
    ("Entrectinib", "NTRK1", "inhibits", 0.96, "TrkA inhibitor (IC50=0.1nM)"),
    ("Entrectinib", "NTRK2", "inhibits", 0.96, "TrkB inhibitor"),
    ("Entrectinib", "NTRK3", "inhibits", 0.96, "TrkC inhibitor"),
    ("Entrectinib", "ALK", "inhibits", 0.90, "ALK inhibitor"),
    ("Larotrectinib", "NTRK1", "inhibits", 0.98, "Selective TrkA inhibitor (IC50=5nM)"),
    ("Larotrectinib", "NTRK2", "inhibits", 0.98, "Selective TrkB inhibitor"),
    ("Larotrectinib", "NTRK3", "inhibits", 0.98, "Selective TrkC inhibitor"),

    # === MET inhibitors ===
    ("Capmatinib", "MET", "inhibits", 0.98, "Selective MET inhibitor (IC50=0.13nM)"),
    ("Tepotinib", "MET", "inhibits", 0.98, "Selective MET inhibitor (IC50=3nM)"),

    # === RET inhibitors ===
    ("Selpercatinib", "RET", "inhibits", 0.99, "Selective RET inhibitor (IC50=14nM wild-type, 0.5nM V804M)"),
    ("Pralsetinib", "RET", "inhibits", 0.99, "Selective RET inhibitor (IC50=0.4nM)"),

    # === CTLA-4 ===
    ("Ipilimumab", "CTLA4", "inhibits", 0.98, "Anti-CTLA-4 monoclonal antibody"),

    # === Chemotherapy ===
    ("Cisplatin", "TP53", "activator", 0.85, "DNA damage activates p53-mediated apoptosis"),
    ("Carboplatin", "TP53", "activator", 0.83, "DNA damage activates p53-mediated apoptosis"),
    ("Pemetrexed", "TYMS", "inhibits", 0.95, "Thymidylate synthase inhibitor (Ki=1.3nM)"),
    ("Fluorouracil", "TYMS", "inhibits", 0.93, "Thymidylate synthase inhibitor"),
    ("Oxaliplatin", "TP53", "activator", 0.84, "DNA damage activates p53-mediated apoptosis"),
    ("Irinotecan", "TOP1", "inhibits", 0.96, "Topoisomerase I inhibitor (IC50=2.5µM)"),

    # === Pathway cross-talk (for compositional reasoning) ===
    ("Osimertinib", "MAPK1", "indirect_inhibitor", 0.75, "Downstream ERK suppression via EGFR inhibition"),
    ("Sotorasib", "MAP2K1", "indirect_inhibitor", 0.80, "Downstream MEK suppression via KRAS inhibition"),
    ("Pembrolizumab", "CD8A", "enhances", 0.88, "Enhances CD8+ T cell function by blocking PD-1"),
    ("Nivolumab", "CD8A", "enhances", 0.88, "Enhances CD8+ T cell function by blocking PD-1"),
]


# ============================================================================
# Helper function to get all Noetik expansion data
# ============================================================================

def get_noetik_expansion():
    """Return (drugs, proteins, drug_target_interactions) for Noetik expansion."""
    return NOETIK_DRUGS, NOETIK_PROTEINS, NOETIK_DRUG_TARGETS
