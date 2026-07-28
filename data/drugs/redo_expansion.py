# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
ReDO Project Drug Expansion -- Batch 1 (20 drugs)
===================================================

Extends the curated drug network with 20 additional drugs from the
Anticancer Fund's Repurposing Drugs in Oncology (ReDO) project.

All drugs are FDA-approved for non-cancer indications.
All targets are experimentally verified (DrugBank, published literature).
Disease associations come from OMIM, COSMIC, and published reviews.

Sources:
  Pantziarka et al. ecancermedicalscience 2014-2019
  DrugBank 5.x (https://go.drugbank.com/)
  ReDO Database (https://www.anticancerfund.org/en/redo-db)
"""

# ============================================================================
# REDO DRUGS -- Batch 1 (20 drugs)
# ============================================================================

REDO_DRUGS = {
    "Cimetidine": {
        "type": "Drug",
        "brand": "Tagamet",
        "drug_class": "H2 receptor antagonist",
        "mechanism": "Histamine H2 receptor blocker, immunomodulator, anti-angiogenic",
        "fda_year": 1977,
        "drugbank_id": "DB00501",
        "original_indication": "Peptic ulcer disease",
        "repurposing_status": "ReDO candidate, epidemiological evidence in CRC",
    },
    "Diclofenac": {
        "type": "Drug",
        "brand": "Voltaren",
        "drug_class": "NSAID",
        "mechanism": "COX-1/COX-2 inhibitor, MYC pathway modulator",
        "fda_year": 1988,
        "drugbank_id": "DB00586",
        "original_indication": "Pain/inflammation",
        "repurposing_status": "ReDO candidate, topical use in actinic keratosis",
    },
    "Propranolol": {
        "type": "Drug",
        "brand": "Inderal",
        "drug_class": "Beta-adrenergic blocker",
        "mechanism": "ADRB1/ADRB2 antagonist, anti-angiogenic, pro-apoptotic",
        "fda_year": 1967,
        "drugbank_id": "DB00571",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO candidate, angiosarcoma and melanoma trials",
    },
    "Itraconazole": {
        "type": "Drug",
        "brand": "Sporanox",
        "drug_class": "Triazole antifungal",
        "mechanism": "Hedgehog pathway inhibitor, VEGFR2 inhibitor, anti-angiogenic",
        "fda_year": 1992,
        "drugbank_id": "DB01167",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO candidate, Phase II NSCLC and BCC",
    },
    "Celecoxib": {
        "type": "Drug",
        "brand": "Celebrex",
        "drug_class": "COX-2 selective inhibitor",
        "mechanism": "Selective COX-2 inhibitor, anti-inflammatory",
        "fda_year": 1998,
        "drugbank_id": "DB00482",
        "original_indication": "Arthritis",
        "repurposing_status": "ReDO candidate, CRC prevention trials",
    },
    "Chloroquine": {
        "type": "Drug",
        "brand": "Aralen",
        "drug_class": "Aminoquinoline antimalarial",
        "mechanism": "Autophagy inhibitor, lysosomal pH disruptor",
        "fda_year": 1947,
        "drugbank_id": "DB00608",
        "original_indication": "Malaria",
        "repurposing_status": "ReDO candidate, autophagy inhibition in GBM",
    },
    "Auranofin": {
        "type": "Drug",
        "brand": "Ridaura",
        "drug_class": "Gold compound",
        "mechanism": "Thioredoxin reductase inhibitor, NF-kB modulator, ROS inducer",
        "fda_year": 1985,
        "drugbank_id": "DB00995",
        "original_indication": "Rheumatoid arthritis",
        "repurposing_status": "ReDO candidate, Phase II CLL and ovarian",
    },
    "Leflunomide": {
        "type": "Drug",
        "brand": "Arava",
        "drug_class": "DHODH inhibitor",
        "mechanism": "Dihydroorotate dehydrogenase inhibitor, pyrimidine synthesis blocker",
        "fda_year": 1998,
        "drugbank_id": "DB01097",
        "original_indication": "Rheumatoid arthritis",
        "repurposing_status": "ReDO DB entry, anti-proliferative",
    },
    "Nelfinavir": {
        "type": "Drug",
        "brand": "Viracept",
        "drug_class": "HIV protease inhibitor",
        "mechanism": "AKT pathway inhibitor, HSP90 client destabilizer, ER stress inducer",
        "fda_year": 1997,
        "drugbank_id": "DB00220",
        "original_indication": "HIV",
        "repurposing_status": "ReDO candidate, Phase II multiple cancer types",
    },
    "Ritonavir": {
        "type": "Drug",
        "brand": "Norvir",
        "drug_class": "HIV protease inhibitor",
        "mechanism": "AKT inhibitor, proteasome inhibitor, CYP3A4 modulator",
        "fda_year": 1996,
        "drugbank_id": "DB00503",
        "original_indication": "HIV",
        "repurposing_status": "ReDO DB entry, preclinical anti-cancer",
    },
    "Verapamil": {
        "type": "Drug",
        "brand": "Calan",
        "drug_class": "Calcium channel blocker",
        "mechanism": "L-type calcium channel blocker, P-glycoprotein (MDR1/ABCB1) inhibitor",
        "fda_year": 1981,
        "drugbank_id": "DB00661",
        "original_indication": "Hypertension/angina",
        "repurposing_status": "ReDO DB entry, MDR reversal agent",
    },
    "Clarithromycin": {
        "type": "Drug",
        "brand": "Biaxin",
        "drug_class": "Macrolide antibiotic",
        "mechanism": "Autophagy inhibitor, IL-6 suppressor, anti-angiogenic",
        "fda_year": 1991,
        "drugbank_id": "DB01211",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO candidate, multiple myeloma combination",
    },
    "Doxycycline": {
        "type": "Drug",
        "brand": "Vibramycin",
        "drug_class": "Tetracycline antibiotic",
        "mechanism": "MMP-2/MMP-9 inhibitor, anti-angiogenic, mitochondrial translation inhibitor",
        "fda_year": 1967,
        "drugbank_id": "DB00254",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO candidate, anti-metastatic",
    },
    "Pirfenidone": {
        "type": "Drug",
        "brand": "Esbriet",
        "drug_class": "Anti-fibrotic",
        "mechanism": "TGF-beta inhibitor, TNF-alpha modulator, anti-fibrotic",
        "fda_year": 2014,
        "drugbank_id": "DB04951",
        "original_indication": "Idiopathic pulmonary fibrosis",
        "repurposing_status": "ReDO DB entry, anti-fibrotic in tumor stroma",
    },
    "Valproic_Acid": {
        "type": "Drug",
        "brand": "Depakene",
        "drug_class": "HDAC inhibitor / anticonvulsant",
        "mechanism": "HDAC1/HDAC2 inhibitor, histone acetylation modulator",
        "fda_year": 1978,
        "drugbank_id": "DB00313",
        "original_indication": "Epilepsy",
        "repurposing_status": "ReDO candidate, Phase II AML and solid tumors",
    },
    "Indomethacin": {
        "type": "Drug",
        "brand": "Indocin",
        "drug_class": "NSAID",
        "mechanism": "Non-selective COX-1/COX-2 inhibitor",
        "fda_year": 1965,
        "drugbank_id": "DB00328",
        "original_indication": "Pain/inflammation",
        "repurposing_status": "ReDO DB entry, CRC and desmoid tumors",
    },
    "Nitroglycerin": {
        "type": "Drug",
        "brand": "Nitrostat",
        "drug_class": "Nitrate vasodilator",
        "mechanism": "NO donor, HIF-1alpha modulator, radiosensitizer",
        "fda_year": 1879,
        "drugbank_id": "DB00727",
        "original_indication": "Angina pectoris",
        "repurposing_status": "ReDO DB entry, NSCLC radiosensitization",
    },
    "Bazedoxifene": {
        "type": "Drug",
        "brand": "Duavee",
        "drug_class": "Selective estrogen receptor modulator",
        "mechanism": "IL-6/GP130 inhibitor, ESR1 modulator",
        "fda_year": 2013,
        "drugbank_id": "DB06401",
        "original_indication": "Osteoporosis",
        "repurposing_status": "ReDO DB entry, IL-6/STAT3 pathway",
    },
    "Artesunate": {
        "type": "Drug",
        "brand": "Artesunate",
        "drug_class": "Artemisinin derivative",
        "mechanism": "NF-kB inhibitor, ROS inducer, ferroptosis inducer, anti-angiogenic",
        "fda_year": 2020,
        "drugbank_id": "DB09274",
        "original_indication": "Malaria",
        "repurposing_status": "ReDO DB entry, Phase II CRC",
    },
    "Suramin": {
        "type": "Drug",
        "brand": "Germanin",
        "drug_class": "Polysulfonated naphthylurea",
        "mechanism": "FGF/PDGF/VEGF inhibitor, anti-parasitic",
        "fda_year": 1920,
        "drugbank_id": "DB04786",
        "original_indication": "Trypanosomiasis",
        "repurposing_status": "ReDO DB entry, anti-angiogenic",
    },
}


# ============================================================================
# ADDITIONAL PROTEINS needed for ReDO drug targets
# ============================================================================

REDO_ADDITIONAL_PROTEINS = {
    "TXNRD1": {
        "type": "Signaling",
        "function": "Thioredoxin reductase 1, selenocysteine-containing oxidoreductase",
        "pathways": ["redox", "apoptosis"],
        "cancers": ["multiple"],
    },
    "HDAC1": {
        "type": "Regulator",
        "function": "Histone deacetylase 1, transcriptional repressor",
        "pathways": ["chromatin_remodeling", "cell_cycle"],
        "cancers": ["AML", "breast", "colorectal"],
    },
    "HDAC2": {
        "type": "Regulator",
        "function": "Histone deacetylase 2, transcriptional repressor",
        "pathways": ["chromatin_remodeling", "cell_cycle"],
        "cancers": ["AML", "colorectal"],
    },
    "MMP2": {
        "type": "Signaling",
        "function": "Matrix metalloproteinase 2, extracellular matrix degradation",
        "pathways": ["extracellular_matrix", "metastasis"],
        "cancers": ["breast", "colorectal", "melanoma"],
    },
    "MMP9": {
        "type": "Signaling",
        "function": "Matrix metalloproteinase 9, extracellular matrix degradation",
        "pathways": ["extracellular_matrix", "metastasis", "angiogenesis"],
        "cancers": ["breast", "colorectal", "NSCLC"],
    },
    "ABCB1": {
        "type": "Transporter",
        "function": "P-glycoprotein / MDR1, ATP-dependent drug efflux pump",
        "pathways": ["drug_resistance", "transport"],
        "cancers": ["multiple"],
    },
    "HIF1A": {
        "type": "Transcription",
        "function": "Hypoxia-inducible factor 1-alpha, hypoxia response master regulator",
        "pathways": ["hypoxia", "angiogenesis", "metabolism"],
        "cancers": ["RCC", "pancreatic", "glioblastoma"],
    },
    "TGFB1": {
        "type": "Signaling",
        "function": "Transforming growth factor beta 1, immune/fibrosis regulator",
        "pathways": ["TGF-beta", "immune_regulation", "fibrosis"],
        "cancers": ["pancreatic", "colorectal"],
    },
    "IL6": {
        "type": "Signaling",
        "function": "Interleukin-6, pleiotropic cytokine",
        "pathways": ["JAK-STAT", "inflammation", "NF-kB"],
        "cancers": ["multiple_myeloma", "AML", "ovarian"],
    },
}


# ============================================================================
# ReDO DRUG -> PROTEIN interactions (experimentally verified targets)
# Format: (drug, protein, relation, confidence, evidence)
# ============================================================================

REDO_DRUG_TARGET_INTERACTIONS = [
    # Cimetidine
    ("Cimetidine", "VEGFR2", "indirect_inhibitor", 0.55, "Anti-angiogenic via VEGF downregulation (Natori 2005)"),
    ("Cimetidine", "NFKB1", "inhibits", 0.50, "NF-kB pathway modulation (Kubecova 2011)"),

    # Diclofenac
    ("Diclofenac", "COX2", "inhibits", 0.93, "Non-selective COX inhibitor (Pantziarka 2016)"),
    ("Diclofenac", "MYC", "indirect_inhibitor", 0.55, "MYC downregulation in colorectal cancer cells (Pantziarka 2016)"),

    # Propranolol
    ("Propranolol", "VEGFR2", "indirect_inhibitor", 0.60, "Anti-angiogenic via VEGF suppression (Pantziarka 2016)"),
    ("Propranolol", "NFKB1", "inhibits", 0.50, "NF-kB pathway modulation (Pantziarka 2016)"),

    # Itraconazole
    ("Itraconazole", "VEGFR2", "inhibits", 0.72, "VEGFR2 glycosylation and trafficking inhibition (Nacev 2011)"),
    ("Itraconazole", "MTOR", "inhibits", 0.60, "mTOR pathway inhibition via cholesterol trafficking (Xu 2010)"),

    # Celecoxib
    ("Celecoxib", "COX2", "inhibits", 0.97, "Selective COX-2 inhibitor (IC50=40nM)"),
    ("Celecoxib", "AKT1", "indirect_inhibitor", 0.55, "AKT phosphorylation reduction (Arico 2002)"),

    # Chloroquine
    ("Chloroquine", "MTOR", "indirect_inhibitor", 0.55, "Autophagy/mTOR pathway modulation via lysosomal disruption"),
    ("Chloroquine", "TP53", "activator", 0.50, "p53 stabilization via autophagy inhibition (Maclean 2008)"),

    # Auranofin
    ("Auranofin", "TXNRD1", "inhibits", 0.90, "Direct thioredoxin reductase inhibition (Roder 2015)"),
    ("Auranofin", "NFKB1", "inhibits", 0.72, "NF-kB pathway inhibition via IKK (Jeon 2003)"),

    # Leflunomide
    ("Leflunomide", "PDGFRA", "inhibits", 0.60, "PDGFR kinase inhibition (Xu 2013)"),
    ("Leflunomide", "STAT3", "indirect_inhibitor", 0.50, "STAT3 signaling reduction (preclinical)"),

    # Nelfinavir
    ("Nelfinavir", "AKT1", "inhibits", 0.75, "AKT phosphorylation inhibition (Gupta 2005)"),
    ("Nelfinavir", "MTOR", "indirect_inhibitor", 0.60, "Downstream of AKT inhibition"),

    # Ritonavir
    ("Ritonavir", "AKT1", "inhibits", 0.65, "AKT pathway inhibition (Srirangam 2006)"),
    ("Ritonavir", "NFKB1", "inhibits", 0.55, "NF-kB pathway modulation (Pati 2002)"),

    # Verapamil
    ("Verapamil", "ABCB1", "inhibits", 0.88, "P-glycoprotein inhibition, MDR reversal (Tsuruo 1981)"),

    # Clarithromycin
    ("Clarithromycin", "IL6", "inhibits", 0.65, "IL-6 secretion suppression (Nakamura 1999)"),
    ("Clarithromycin", "MTOR", "indirect_inhibitor", 0.50, "Autophagy modulation"),

    # Doxycycline
    ("Doxycycline", "MMP2", "inhibits", 0.80, "MMP-2 inhibition at sub-antimicrobial doses (Golub 1998)"),
    ("Doxycycline", "MMP9", "inhibits", 0.82, "MMP-9 inhibition at sub-antimicrobial doses (Golub 1998)"),

    # Pirfenidone
    ("Pirfenidone", "TGFB1", "inhibits", 0.82, "TGF-beta signaling inhibition (Iyer 1999)"),

    # Valproic Acid
    ("Valproic_Acid", "HDAC1", "inhibits", 0.85, "HDAC1 inhibition (IC50 ~0.4mM, Gottlicher 2001)"),
    ("Valproic_Acid", "HDAC2", "inhibits", 0.83, "HDAC2 inhibition (Gottlicher 2001)"),

    # Indomethacin
    ("Indomethacin", "COX2", "inhibits", 0.92, "Non-selective COX inhibitor"),
    ("Indomethacin", "NFKB1", "inhibits", 0.55, "NF-kB pathway suppression"),

    # Nitroglycerin
    ("Nitroglycerin", "HIF1A", "inhibits", 0.60, "HIF-1alpha inhibition via NO-mediated degradation (Yasuda 2006)"),

    # Bazedoxifene
    ("Bazedoxifene", "IL6", "inhibits", 0.75, "IL-6/GP130 binding inhibition (Li 2014)"),
    ("Bazedoxifene", "STAT3", "indirect_inhibitor", 0.65, "STAT3 suppression via IL-6/GP130 blockade"),

    # Artesunate
    ("Artesunate", "NFKB1", "inhibits", 0.70, "NF-kB pathway inhibition (Efferth 2007)"),
    ("Artesunate", "VEGFR2", "indirect_inhibitor", 0.55, "Anti-angiogenic via VEGF suppression"),

    # Suramin
    ("Suramin", "VEGFR2", "inhibits", 0.65, "VEGF/VEGFR pathway inhibition (Waltenberger 1996)"),
    ("Suramin", "PDGFRA", "inhibits", 0.62, "PDGF receptor inhibition"),
]


# ============================================================================
# ReDO PROTEIN -> DISEASE associations
# Format: (protein, disease, relation, confidence, evidence)
# ============================================================================

REDO_PROTEIN_DISEASE_ASSOCIATIONS = [
    # HDAC targets
    ("HDAC1", "AML", "associated_with", 0.75, "HDAC overexpression in AML (Tabe 2006)"),
    ("HDAC1", "Breast_Cancer", "associated_with", 0.70, "HDAC aberrant expression in breast cancer"),
    ("HDAC2", "Colorectal_Cancer", "associated_with", 0.72, "HDAC2 overexpression in CRC (Zhu 2004)"),
    ("HDAC2", "AML", "associated_with", 0.68, "HDAC2 in AML differentiation block"),

    # MMP targets
    ("MMP9", "Colorectal_Cancer", "associated_with", 0.72, "MMP9 in CRC invasion/metastasis"),
    ("MMP9", "Breast_Cancer", "associated_with", 0.68, "MMP9 in breast cancer metastasis"),
    ("MMP2", "Melanoma", "associated_with", 0.65, "MMP2 in melanoma invasion"),
    ("MMP2", "Breast_Cancer", "associated_with", 0.63, "MMP2 in breast cancer extracellular remodeling"),

    # HIF1A targets
    ("HIF1A", "RCC", "driver_of", 0.88, "HIF pathway drives ccRCC via VHL loss"),
    ("HIF1A", "Pancreatic_Cancer", "associated_with", 0.72, "Hypoxia in pancreatic tumor microenvironment"),
    ("HIF1A", "Glioblastoma", "associated_with", 0.75, "HIF-1alpha in GBM hypoxic core"),

    # TGFB1 targets
    ("TGFB1", "Pancreatic_Cancer", "associated_with", 0.78, "TGF-beta signaling in pancreatic cancer stroma"),
    ("TGFB1", "Colorectal_Cancer", "associated_with", 0.60, "TGF-beta pathway mutations in microsatellite-stable CRC"),

    # IL6 targets
    ("IL6", "Multiple_Myeloma", "driver_of", 0.85, "IL-6 drives myeloma cell survival (Hideshima 2007)"),
    ("IL6", "AML", "associated_with", 0.65, "IL-6 in AML blast proliferation"),
    ("IL6", "Ovarian_Cancer", "associated_with", 0.62, "IL-6 in ovarian cancer ascites"),

    # TXNRD1 targets
    ("TXNRD1", "AML", "associated_with", 0.60, "Thioredoxin system upregulated in AML (Shao 2001)"),
    ("TXNRD1", "Ovarian_Cancer", "associated_with", 0.55, "Elevated TXNRD1 in ovarian cancer"),

    # ABCB1 targets
    ("ABCB1", "AML", "associated_with", 0.72, "P-gp overexpression drives drug resistance in AML"),
    ("ABCB1", "Breast_Cancer", "associated_with", 0.60, "MDR1 in chemotherapy-resistant breast cancer"),
]


# ============================================================================
# ReDO HOLDOUT EDGES (known associations for validation)
# Format: (drug, disease, relation, confidence, evidence)
# ============================================================================

REDO_HOLDOUT_EDGES = [
    # Cimetidine -- CRC (epidemiological evidence)
    ("Cimetidine", "Colorectal_Cancer", "potential_treatment", 0.55,
     "Perioperative cimetidine improves CRC survival (Matsumoto 2002)"),

    # Diclofenac -- CRC and melanoma
    ("Diclofenac", "Colorectal_Cancer", "potential_treatment", 0.50,
     "COX-2 inhibition in CRC (epidemiological)"),

    # Itraconazole -- NSCLC
    ("Itraconazole", "NSCLC", "potential_treatment", 0.55,
     "Phase II: improved PFS in NSCLC (Rudin 2013)"),

    # Celecoxib -- CRC prevention
    ("Celecoxib", "Colorectal_Cancer", "potential_treatment", 0.65,
     "APC trial: reduced polyp recurrence (Bertagnolli 2006)"),

    # Auranofin -- CLL
    ("Auranofin", "CLL", "potential_treatment", 0.50,
     "Phase II: thioredoxin pathway in CLL (Saha 2015)"),

    # Valproic Acid -- AML
    ("Valproic_Acid", "AML", "potential_treatment", 0.55,
     "Phase II: HDAC inhibition in AML (Kuendgen 2006)"),

    # Nelfinavir -- multiple cancers via AKT
    ("Nelfinavir", "Pancreatic_Cancer", "potential_treatment", 0.45,
     "Phase II: radiosensitization in pancreatic cancer (Brunner 2008)"),

    # Clarithromycin -- Multiple Myeloma
    ("Clarithromycin", "Multiple_Myeloma", "potential_treatment", 0.50,
     "BiRd regimen: clarithromycin + lenalidomide + dex (Niesvizky 2008)"),

    # Bazedoxifene -- breast cancer via IL-6/STAT3
    ("Bazedoxifene", "Breast_Cancer", "potential_treatment", 0.45,
     "IL-6/GP130 inhibition in triple-negative breast cancer (preclinical)"),

    # Doxycycline -- breast cancer (anti-metastatic)
    ("Doxycycline", "Breast_Cancer", "potential_treatment", 0.45,
     "MMP inhibition reduces breast cancer metastasis (preclinical)"),
]
