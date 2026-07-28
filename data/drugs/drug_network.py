# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Curated Drug-Target-Disease Network for Drug Repurposing
========================================================

Real data from DrugBank, FDA approvals, and ClinicalTrials.gov.
All drugs are FDA-approved. All targets are experimentally verified.
All disease associations come from published literature.

Network structure:
  - Drug objects (type="Drug")
  - Protein/target objects (type="Protein") -- reuses cancer_proteins
  - Disease objects (type="Disease")
  - Drug->Protein morphisms ("targets", "inhibits", "activates")
  - Protein->Disease morphisms ("associated_with", "driver_of")
  - Drug->Disease morphisms ("treats") -- SOME deliberately held out

The holdout set contains known drug-disease associations that are
NOT loaded into the store. The conjecture engine should discover
them via compositional reasoning (Drug->Protein->Disease chains).

Sources:
  DrugBank 5.x (https://go.drugbank.com/)
  FDA Orange Book
  ClinicalTrials.gov
  KEGG DRUG
"""

# ============================================================================
# DRUGS -- FDA-approved, with real mechanisms of action
# ============================================================================

DRUGS = {
    # === Tyrosine Kinase Inhibitors ===
    "Imatinib": {
        "type": "Drug",
        "brand": "Gleevec",
        "drug_class": "Tyrosine kinase inhibitor",
        "mechanism": "BCR-ABL, KIT, PDGFR inhibitor",
        "fda_year": 2001,
        "drugbank_id": "DB00619",
    },
    "Erlotinib": {
        "type": "Drug",
        "brand": "Tarceva",
        "drug_class": "EGFR inhibitor",
        "mechanism": "Reversible EGFR tyrosine kinase inhibitor",
        "fda_year": 2004,
        "drugbank_id": "DB00530",
    },
    "Gefitinib": {
        "type": "Drug",
        "brand": "Iressa",
        "drug_class": "EGFR inhibitor",
        "mechanism": "Reversible EGFR tyrosine kinase inhibitor",
        "fda_year": 2003,
        "drugbank_id": "DB00317",
    },
    "Lapatinib": {
        "type": "Drug",
        "brand": "Tykerb",
        "drug_class": "Dual EGFR/HER2 inhibitor",
        "mechanism": "Reversible dual EGFR and HER2 inhibitor",
        "fda_year": 2007,
        "drugbank_id": "DB01259",
    },
    "Sorafenib": {
        "type": "Drug",
        "brand": "Nexavar",
        "drug_class": "Multi-kinase inhibitor",
        "mechanism": "RAF, VEGFR, PDGFR, KIT inhibitor",
        "fda_year": 2005,
        "drugbank_id": "DB00398",
    },
    "Sunitinib": {
        "type": "Drug",
        "brand": "Sutent",
        "drug_class": "Multi-kinase inhibitor",
        "mechanism": "VEGFR, PDGFR, KIT, FLT3 inhibitor",
        "fda_year": 2006,
        "drugbank_id": "DB01268",
    },
    "Crizotinib": {
        "type": "Drug",
        "brand": "Xalkori",
        "drug_class": "ALK/MET inhibitor",
        "mechanism": "ALK, MET, ROS1 tyrosine kinase inhibitor",
        "fda_year": 2011,
        "drugbank_id": "DB08865",
    },

    # === RAF/MEK/ERK Pathway ===
    "Vemurafenib": {
        "type": "Drug",
        "brand": "Zelboraf",
        "drug_class": "BRAF inhibitor",
        "mechanism": "Selective BRAF V600E inhibitor",
        "fda_year": 2011,
        "drugbank_id": "DB08881",
    },
    "Dabrafenib": {
        "type": "Drug",
        "brand": "Tafinlar",
        "drug_class": "BRAF inhibitor",
        "mechanism": "Selective BRAF inhibitor",
        "fda_year": 2013,
        "drugbank_id": "DB08912",
    },
    "Trametinib": {
        "type": "Drug",
        "brand": "Mekinist",
        "drug_class": "MEK inhibitor",
        "mechanism": "Selective MEK1/MEK2 inhibitor",
        "fda_year": 2013,
        "drugbank_id": "DB08911",
    },

    # === CDK Inhibitors ===
    "Palbociclib": {
        "type": "Drug",
        "brand": "Ibrance",
        "drug_class": "CDK4/6 inhibitor",
        "mechanism": "Selective CDK4 and CDK6 inhibitor",
        "fda_year": 2015,
        "drugbank_id": "DB09073",
    },
    "Ribociclib": {
        "type": "Drug",
        "brand": "Kisqali",
        "drug_class": "CDK4/6 inhibitor",
        "mechanism": "Selective CDK4 and CDK6 inhibitor",
        "fda_year": 2017,
        "drugbank_id": "DB11730",
    },

    # === MTOR Inhibitors ===
    "Everolimus": {
        "type": "Drug",
        "brand": "Afinitor",
        "drug_class": "MTOR inhibitor",
        "mechanism": "MTOR kinase inhibitor (rapamycin analog)",
        "fda_year": 2009,
        "drugbank_id": "DB01590",
    },
    "Temsirolimus": {
        "type": "Drug",
        "brand": "Torisel",
        "drug_class": "MTOR inhibitor",
        "mechanism": "MTOR kinase inhibitor",
        "fda_year": 2007,
        "drugbank_id": "DB06287",
    },

    # === Antibodies ===
    "Trastuzumab": {
        "type": "Drug",
        "brand": "Herceptin",
        "drug_class": "Monoclonal antibody",
        "mechanism": "HER2/ERBB2 extracellular domain blocker",
        "fda_year": 1998,
        "drugbank_id": "DB00072",
    },
    "Cetuximab": {
        "type": "Drug",
        "brand": "Erbitux",
        "drug_class": "Monoclonal antibody",
        "mechanism": "EGFR extracellular domain blocker",
        "fda_year": 2004,
        "drugbank_id": "DB00002",
    },
    "Bevacizumab": {
        "type": "Drug",
        "brand": "Avastin",
        "drug_class": "Monoclonal antibody",
        "mechanism": "VEGF-A ligand trap (anti-angiogenic)",
        "fda_year": 2004,
        "drugbank_id": "DB00112",
    },

    # === BCL2 / Apoptosis ===
    "Venetoclax": {
        "type": "Drug",
        "brand": "Venclexta",
        "drug_class": "BCL2 inhibitor",
        "mechanism": "Selective BCL2 inhibitor (BH3 mimetic)",
        "fda_year": 2016,
        "drugbank_id": "DB11581",
    },

    # === JAK Inhibitors ===
    "Ruxolitinib": {
        "type": "Drug",
        "brand": "Jakafi",
        "drug_class": "JAK inhibitor",
        "mechanism": "JAK1/JAK2 inhibitor",
        "fda_year": 2011,
        "drugbank_id": "DB08877",
    },

    # === DNA Damage / PARP ===
    "Olaparib": {
        "type": "Drug",
        "brand": "Lynparza",
        "drug_class": "PARP inhibitor",
        "mechanism": "PARP1/PARP2 inhibitor, synthetic lethality with BRCA",
        "fda_year": 2014,
        "drugbank_id": "DB09074",
    },

    # === REPURPOSING CANDIDATES (non-cancer drugs with known anti-cancer activity) ===
    "Metformin": {
        "type": "Drug",
        "brand": "Glucophage",
        "drug_class": "Biguanide (antidiabetic)",
        "mechanism": "AMPK activator, mTOR pathway inhibitor",
        "fda_year": 1995,
        "drugbank_id": "DB00331",
        "original_indication": "Type 2 Diabetes",
    },
    "Aspirin": {
        "type": "Drug",
        "brand": "Bayer Aspirin",
        "drug_class": "NSAID",
        "mechanism": "COX-1/COX-2 inhibitor, NF-kB modulator",
        "fda_year": 1899,
        "drugbank_id": "DB00945",
        "original_indication": "Pain/inflammation",
    },
    "Thalidomide": {
        "type": "Drug",
        "brand": "Thalomid",
        "drug_class": "Immunomodulatory",
        "mechanism": "Cereblon binding, anti-angiogenic, TNF-alpha modulator",
        "fda_year": 1998,
        "drugbank_id": "DB01041",
        "original_indication": "Leprosy/sedative",
        "repurposed_for": "Multiple myeloma",
    },
    "Disulfiram": {
        "type": "Drug",
        "brand": "Antabuse",
        "drug_class": "ALDH inhibitor",
        "mechanism": "Aldehyde dehydrogenase inhibitor, proteasome inhibitor",
        "fda_year": 1951,
        "drugbank_id": "DB00822",
        "original_indication": "Alcoholism",
    },

    # === ReDO PROJECT CANDIDATES (tested against Anticancer Fund's ReDO database) ===
    "Mebendazole": {
        "type": "Drug",
        "brand": "Vermox",
        "drug_class": "Benzimidazole anthelmintic",
        "mechanism": "Microtubule inhibitor, VEGFR2/BRAF kinase inhibitor",
        "fda_year": 1974,
        "drugbank_id": "DB00643",
        "original_indication": "Parasitic worm infections",
        "repurposing_status": "ReDO candidate, Phase II colorectal",
    },
    "Niclosamide": {
        "type": "Drug",
        "brand": "Niclocide",
        "drug_class": "Salicylanilide anthelmintic",
        "mechanism": "STAT3/mTOR/NF-kB pathway inhibitor, mitochondrial uncoupler",
        "fda_year": 1982,
        "drugbank_id": "DB06803",
        "original_indication": "Tapeworm infections",
        "repurposing_status": "ReDO candidate, NIKOLO Phase II colorectal",
    },
    "Ivermectin": {
        "type": "Drug",
        "brand": "Stromectol",
        "drug_class": "Avermectin antiparasitic",
        "mechanism": "PAK1 kinase inhibitor, AKT/mTOR/STAT3 pathway modulator",
        "fda_year": 1996,
        "drugbank_id": "DB00602",
        "original_indication": "Onchocerciasis (river blindness), strongyloidiasis",
        "repurposing_status": "ReDO candidate, Phase II with anti-PD-1",
    },
    "Atorvastatin": {
        "type": "Drug",
        "brand": "Lipitor",
        "drug_class": "HMG-CoA reductase inhibitor (statin)",
        "mechanism": "Blocks mevalonate synthesis, inhibits KRAS prenylation",
        "fda_year": 1996,
        "drugbank_id": "DB01076",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO candidate, epidemiological evidence in KRAS-mutant cancers",
    },
}


# ============================================================================
# ADDITIONAL PROTEINS (not in cancer_proteins.py, needed for drug paths)
# These are real targets from DrugBank/UniProt
# ============================================================================

ADDITIONAL_PROTEINS = {
    "KIT": {
        "type": "Receptor",
        "function": "Stem cell factor receptor, receptor tyrosine kinase",
        "pathways": ["MAPK", "PI3K-AKT"],
        "cancers": ["GIST", "AML", "melanoma"],
    },
    "ALK": {
        "type": "Receptor",
        "function": "Anaplastic lymphoma kinase, receptor tyrosine kinase",
        "pathways": ["MAPK", "PI3K-AKT", "JAK-STAT"],
        "cancers": ["NSCLC", "neuroblastoma", "lymphoma"],
    },
    "PDGFRA": {
        "type": "Receptor",
        "function": "Platelet-derived growth factor receptor alpha",
        "pathways": ["MAPK", "PI3K-AKT"],
        "cancers": ["GIST", "glioblastoma"],
    },
    "FLT3": {
        "type": "Receptor",
        "function": "FMS-like tyrosine kinase 3",
        "pathways": ["MAPK", "PI3K-AKT", "STAT5"],
        "cancers": ["AML"],
    },
    "AMPK": {
        "type": "Signaling",
        "function": "AMP-activated protein kinase, metabolic sensor",
        "pathways": ["AMPK-MTOR", "metabolism"],
        "cancers": ["multiple"],
    },
    "COX2": {
        "type": "Signaling",
        "function": "Cyclooxygenase-2, prostaglandin synthesis",
        "pathways": ["inflammation", "prostaglandin"],
        "cancers": ["colorectal", "gastric"],
    },
    "NFKB1": {
        "type": "Transcription",
        "function": "Nuclear factor kappa-B p65, inflammation master regulator",
        "pathways": ["NF-kB", "inflammation"],
        "cancers": ["multiple"],
    },
    "NPL4": {
        "type": "Regulator",
        "function": "Nuclear protein localization 4, p97/VCP cofactor",
        "pathways": ["proteasome", "ubiquitin"],
        "cancers": ["multiple"],
    },
    "ROS1": {
        "type": "Receptor",
        "function": "ROS proto-oncogene 1, receptor tyrosine kinase",
        "pathways": ["MAPK", "PI3K-AKT"],
        "cancers": ["NSCLC"],
    },
    "CRBN": {
        "type": "Regulator",
        "function": "Cereblon, E3 ubiquitin ligase substrate receptor",
        "pathways": ["ubiquitin", "proteasome"],
        "cancers": ["multiple_myeloma"],
    },
}


# ============================================================================
# DISEASES
# ============================================================================

DISEASES = {
    "NSCLC": {
        "type": "Disease",
        "full_name": "Non-small cell lung cancer",
        "prevalence": "common",
        "mesh_id": "D002289",
    },
    "CML": {
        "type": "Disease",
        "full_name": "Chronic myeloid leukemia",
        "prevalence": "rare",
        "mesh_id": "D015464",
    },
    "Melanoma": {
        "type": "Disease",
        "full_name": "Malignant melanoma",
        "prevalence": "common",
        "mesh_id": "D008545",
    },
    "Breast_Cancer": {
        "type": "Disease",
        "full_name": "Breast carcinoma",
        "prevalence": "common",
        "mesh_id": "D001943",
    },
    "Colorectal_Cancer": {
        "type": "Disease",
        "full_name": "Colorectal carcinoma",
        "prevalence": "common",
        "mesh_id": "D015179",
    },
    "RCC": {
        "type": "Disease",
        "full_name": "Renal cell carcinoma",
        "prevalence": "common",
        "mesh_id": "D002292",
    },
    "HCC": {
        "type": "Disease",
        "full_name": "Hepatocellular carcinoma",
        "prevalence": "common",
        "mesh_id": "D006528",
    },
    "GIST": {
        "type": "Disease",
        "full_name": "Gastrointestinal stromal tumor",
        "prevalence": "rare",
        "mesh_id": "D046152",
    },
    "Glioblastoma": {
        "type": "Disease",
        "full_name": "Glioblastoma multiforme",
        "prevalence": "rare",
        "mesh_id": "D005909",
    },
    "CLL": {
        "type": "Disease",
        "full_name": "Chronic lymphocytic leukemia",
        "prevalence": "common",
        "mesh_id": "D015451",
    },
    "AML": {
        "type": "Disease",
        "full_name": "Acute myeloid leukemia",
        "prevalence": "rare",
        "mesh_id": "D015470",
    },
    "Myelofibrosis": {
        "type": "Disease",
        "full_name": "Primary myelofibrosis",
        "prevalence": "rare",
        "mesh_id": "D055728",
    },
    "Ovarian_Cancer": {
        "type": "Disease",
        "full_name": "Ovarian carcinoma",
        "prevalence": "common",
        "mesh_id": "D010051",
    },
    "Pancreatic_Cancer": {
        "type": "Disease",
        "full_name": "Pancreatic adenocarcinoma",
        "prevalence": "common",
        "mesh_id": "D010190",
    },
    "Multiple_Myeloma": {
        "type": "Disease",
        "full_name": "Multiple myeloma",
        "prevalence": "common",
        "mesh_id": "D009101",
    },
    "Type2_Diabetes": {
        "type": "Disease",
        "full_name": "Type 2 diabetes mellitus",
        "prevalence": "very_common",
        "mesh_id": "D003924",
    },
    "Prostate_Cancer": {
        "type": "Disease",
        "full_name": "Prostate adenocarcinoma",
        "prevalence": "common",
        "mesh_id": "D011471",
    },
    "Soft_Tissue_Sarcoma": {
        "type": "Disease",
        "full_name": "Soft tissue sarcoma",
        "prevalence": "rare",
        "mesh_id": "D012509",
    },
    "Ewing_Sarcoma": {
        "type": "Disease",
        "full_name": "Ewing sarcoma",
        "prevalence": "rare",
        "mesh_id": "D012512",
    },
    "Li_Fraumeni_Syndrome": {
        "type": "Disease",
        "full_name": "Li-Fraumeni syndrome",
        "prevalence": "rare",
        "mesh_id": "D016864",
    },
}


# ============================================================================
# DRUG -> PROTEIN interactions (experimentally verified targets)
# Format: (drug, protein, relation, confidence, evidence)
# ============================================================================

DRUG_TARGET_INTERACTIONS = [
    # === Imatinib targets ===
    ("Imatinib", "KRAS", "pathway_modulator", 0.75, "Imatinib modulates RAS signaling via KIT/PDGFR"),
    ("Imatinib", "AKT1", "indirect_inhibitor", 0.70, "Downstream pathway suppression"),

    # === EGFR inhibitors ===
    ("Erlotinib", "EGFR", "inhibits", 0.97, "Direct EGFR kinase domain binding (Ki=2nM)"),
    ("Gefitinib", "EGFR", "inhibits", 0.96, "Direct EGFR kinase domain binding (Ki=1nM)"),
    ("Cetuximab", "EGFR", "inhibits", 0.95, "Blocks EGFR extracellular domain III"),
    ("Lapatinib", "EGFR", "inhibits", 0.94, "Dual EGFR kinase inhibitor"),
    ("Lapatinib", "ERBB2", "inhibits", 0.93, "Dual HER2 kinase inhibitor"),

    # === HER2 ===
    ("Trastuzumab", "ERBB2", "inhibits", 0.98, "Binds HER2 extracellular domain IV"),

    # === RAF/MEK ===
    ("Vemurafenib", "BRAF", "inhibits", 0.97, "Selective BRAF V600E inhibitor (IC50=31nM)"),
    ("Dabrafenib", "BRAF", "inhibits", 0.96, "Selective BRAF inhibitor (IC50=0.65nM)"),
    ("Sorafenib", "BRAF", "inhibits", 0.85, "RAF kinase inhibitor"),
    ("Sorafenib", "RAF1", "inhibits", 0.83, "C-RAF kinase inhibitor"),
    ("Sorafenib", "VEGFR2", "inhibits", 0.90, "VEGFR2 kinase inhibitor (IC50=90nM)"),
    ("Trametinib", "MEK1", "inhibits", 0.98, "Allosteric MEK1/2 inhibitor (IC50=0.7nM)"),

    # === Multi-kinase (Sunitinib) ===
    ("Sunitinib", "VEGFR2", "inhibits", 0.95, "VEGFR2 kinase inhibitor"),

    # === CDK4/6 ===
    ("Palbociclib", "CDK4", "inhibits", 0.97, "Selective CDK4 inhibitor (IC50=11nM)"),
    ("Palbociclib", "CDK6", "inhibits", 0.96, "Selective CDK6 inhibitor (IC50=16nM)"),
    ("Ribociclib", "CDK4", "inhibits", 0.96, "Selective CDK4 inhibitor"),
    ("Ribociclib", "CDK6", "inhibits", 0.95, "Selective CDK6 inhibitor"),

    # === MTOR ===
    ("Everolimus", "MTOR", "inhibits", 0.96, "MTOR complex 1 inhibitor (rapamycin analog)"),
    ("Temsirolimus", "MTOR", "inhibits", 0.95, "MTOR complex 1 inhibitor"),

    # === VEGF/Angiogenesis ===
    ("Bevacizumab", "VEGFR2", "indirect_inhibitor", 0.88, "Binds VEGF-A ligand, prevents VEGFR2 activation"),

    # === BCL2 ===
    ("Venetoclax", "BCL2", "inhibits", 0.98, "Selective BCL2 BH3 mimetic (Ki<0.01nM)"),

    # === JAK ===
    ("Ruxolitinib", "JAK2", "inhibits", 0.97, "JAK1/JAK2 inhibitor (IC50=3.3nM)"),

    # === ALK/MET ===
    ("Crizotinib", "MET", "inhibits", 0.93, "MET kinase inhibitor (IC50=8nM)"),

    # === PARP / DNA repair ===
    ("Olaparib", "BRCA1", "synthetic_lethal", 0.90, "Synthetic lethality in BRCA1-deficient cells"),
    ("Olaparib", "BRCA2", "synthetic_lethal", 0.92, "Synthetic lethality in BRCA2-deficient cells"),

    # === Imatinib additional targets ===
    ("Imatinib", "KIT", "inhibits", 0.96, "Direct KIT kinase inhibitor (IC50=100nM, DrugBank DB00619)"),
    ("Imatinib", "PDGFRA", "inhibits", 0.94, "PDGFRA kinase inhibitor (IC50=100nM)"),

    # === Sunitinib additional targets ===
    ("Sunitinib", "KIT", "inhibits", 0.94, "KIT kinase inhibitor (IC50=1-10nM, DrugBank DB01268)"),
    ("Sunitinib", "FLT3", "inhibits", 0.88, "FLT3 kinase inhibitor"),
    ("Sunitinib", "PDGFRA", "inhibits", 0.92, "PDGFRA kinase inhibitor"),

    # === Crizotinib additional targets ===
    ("Crizotinib", "ALK", "inhibits", 0.96, "ALK kinase inhibitor (IC50=24nM, DrugBank DB08865)"),
    ("Crizotinib", "ROS1", "inhibits", 0.91, "ROS1 kinase inhibitor"),

    # === REPURPOSING CANDIDATES (non-obvious connections) ===
    ("Metformin", "AMPK", "activates", 0.90, "Primary mechanism: AMPK activation (Zhou 2001)"),
    ("Metformin", "MTOR", "inhibits", 0.78, "AMPK activation suppresses mTOR signaling (Dowling 2007)"),
    ("Metformin", "AKT1", "indirect_inhibitor", 0.65, "AMPK-mediated AKT suppression"),
    ("Aspirin", "COX2", "inhibits", 0.95, "Primary mechanism: COX-2 inhibition (Vane 1971)"),
    ("Aspirin", "NFKB1", "inhibits", 0.70, "NF-kB pathway suppression (Kopp 1994)"),
    ("Aspirin", "STAT3", "inhibits", 0.60, "COX-independent STAT3 inhibition (Turkson 2005)"),
    ("Thalidomide", "CRBN", "binds", 0.95, "Primary target: cereblon binding (Ito 2010)"),
    ("Thalidomide", "VEGFR2", "indirect_inhibitor", 0.72, "Anti-angiogenic via VEGF downregulation"),
    ("Disulfiram", "NPL4", "inhibits", 0.80, "Binds NPL4 in Cu2+-dependent manner (Skrott 2017 Nature)"),
    ("Disulfiram", "TP53", "activator", 0.55, "Stabilizes p53 via proteasome inhibition (Skrott 2017)"),

    # === ReDO PROJECT CANDIDATES ===
    # Mebendazole targets (all proteins already in graph)
    ("Mebendazole", "VEGFR2", "inhibits", 0.82, "Inhibits VEGFR2 ATP-binding site at clinical concentrations (Pantziarka 2014, Nygren 2014)"),
    ("Mebendazole", "BRAF", "inhibits", 0.70, "Kinase inhibitor activity against BRAF V600E and wild-type (Simbulan-Rosenthal 2017)"),
    ("Mebendazole", "TP53", "activator", 0.65, "Induces p53 and p21 expression after 24h, caspase-mediated apoptosis (Mukhopadhyay 2002)"),
    # Niclosamide targets (all proteins already in graph)
    ("Niclosamide", "STAT3", "inhibits", 0.85, "Inhibits STAT3 phosphorylation and nuclear translocation (Li 2014)"),
    ("Niclosamide", "MTOR", "inhibits", 0.78, "Inhibits mTORC1 signaling (Chen 2014)"),
    ("Niclosamide", "NFKB1", "inhibits", 0.75, "Inhibits NF-kB pathway activation (Chen 2014)"),
    # Ivermectin targets (all proteins already in graph)
    ("Ivermectin", "STAT3", "inhibits", 0.70, "STAT3 pathway modulation (Dou 2020)"),
    ("Ivermectin", "AKT1", "indirect_inhibitor", 0.65, "PAK1 inhibition decreases AKT phosphorylation (Hashimoto 2009)"),
    ("Ivermectin", "MTOR", "indirect_inhibitor", 0.60, "Downstream of AKT inhibition, mTOR suppression (Dou 2020)"),
    # Atorvastatin targets -- KRAS prenylation block is the key mechanism
    ("Atorvastatin", "KRAS", "indirect_inhibitor", 0.72, "Blocks KRAS prenylation via mevalonate pathway inhibition (Gruenbacher 2021)"),
    ("Atorvastatin", "NRAS", "indirect_inhibitor", 0.68, "Blocks NRAS prenylation via same mechanism"),
    ("Atorvastatin", "MTOR", "indirect_inhibitor", 0.55, "Downstream mTOR suppression via reduced prenylation (Beckwitt 2018)"),
]


# ============================================================================
# PROTEIN -> DISEASE associations (from OMIM, COSMIC, KEGG Disease)
# Format: (protein, disease, relation, confidence, evidence)
# ============================================================================

PROTEIN_DISEASE_ASSOCIATIONS = [
    # === EGFR pathway diseases ===
    ("EGFR", "NSCLC", "driver_of", 0.95, "EGFR mutations in 15-30% of NSCLC (COSMIC)"),
    ("EGFR", "Glioblastoma", "driver_of", 0.85, "EGFR amplification in 40% of GBM"),
    ("EGFR", "Colorectal_Cancer", "associated_with", 0.80, "EGFR overexpression in CRC"),
    ("ERBB2", "Breast_Cancer", "driver_of", 0.95, "HER2 amplification in 20% of breast cancer"),
    ("ERBB2", "Colorectal_Cancer", "associated_with", 0.60, "HER2 in 3-5% of CRC"),

    # === RAS-MAPK diseases ===
    ("KRAS", "Pancreatic_Cancer", "driver_of", 0.97, "KRAS mutated in 90% of pancreatic cancer"),
    ("KRAS", "NSCLC", "driver_of", 0.88, "KRAS mutated in 25% of NSCLC"),
    ("KRAS", "Colorectal_Cancer", "driver_of", 0.90, "KRAS mutated in 40% of CRC"),
    ("BRAF", "Melanoma", "driver_of", 0.95, "BRAF V600E in 50% of melanoma (Davies 2002)"),
    ("BRAF", "Colorectal_Cancer", "associated_with", 0.75, "BRAF V600E in 8-12% of CRC"),

    # === PI3K-AKT-MTOR diseases ===
    ("PIK3CA", "Breast_Cancer", "driver_of", 0.88, "PIK3CA mutated in 30-40% breast cancer"),
    ("PTEN", "Glioblastoma", "driver_of", 0.90, "PTEN loss in 40% of GBM"),
    ("PTEN", "Prostate_Cancer", "driver_of", 0.85, "PTEN loss in 20-30% of prostate cancer"),
    ("MTOR", "RCC", "associated_with", 0.82, "mTOR pathway activation in ccRCC"),

    # === Cell cycle diseases ===
    ("CDK4", "Breast_Cancer", "associated_with", 0.80, "CDK4 overexpression in ER+ breast cancer"),
    ("CDK6", "Breast_Cancer", "associated_with", 0.78, "CDK6 amplification in breast cancer"),
    ("RB1", "Breast_Cancer", "associated_with", 0.85, "RB pathway disrupted in breast cancer"),
    ("CCND1", "Breast_Cancer", "driver_of", 0.88, "Cyclin D1 amplified in 15-20% breast cancer"),

    # === TP53 diseases ===
    ("TP53", "NSCLC", "associated_with", 0.90, "TP53 mutated in 50% of NSCLC"),
    ("TP53", "Colorectal_Cancer", "associated_with", 0.88, "TP53 mutated in 60% of CRC"),
    ("TP53", "Ovarian_Cancer", "associated_with", 0.92, "TP53 mutated in 96% of HGSOC"),
    ("TP53", "Breast_Cancer", "associated_with", 0.82, "TP53 mutated in 30% of breast cancer"),
    ("MDM2", "Glioblastoma", "associated_with", 0.75, "MDM2 amplification in GBM"),

    # === BCL2 / Apoptosis diseases ===
    ("BCL2", "CLL", "driver_of", 0.92, "BCL2 overexpression defines CLL biology"),
    ("BCL2", "AML", "associated_with", 0.78, "BCL2 overexpression in AML"),

    # === JAK-STAT diseases ===
    ("JAK2", "Myelofibrosis", "driver_of", 0.97, "JAK2 V617F in 60% of myelofibrosis"),
    ("JAK2", "AML", "associated_with", 0.70, "JAK2 mutations in some AML subtypes"),

    # === BRCA / DNA repair diseases ===
    ("BRCA1", "Breast_Cancer", "associated_with", 0.95, "BRCA1 mutations: 5-10% hereditary breast cancer"),
    ("BRCA1", "Ovarian_Cancer", "associated_with", 0.93, "BRCA1 mutations: 15% ovarian cancer"),
    ("BRCA2", "Breast_Cancer", "associated_with", 0.93, "BRCA2 mutations in hereditary breast cancer"),
    ("BRCA2", "Ovarian_Cancer", "associated_with", 0.88, "BRCA2 mutations in ovarian cancer"),
    ("BRCA2", "Pancreatic_Cancer", "associated_with", 0.75, "BRCA2 in 5-10% hereditary pancreatic"),

    # === Other ===
    ("MET", "NSCLC", "associated_with", 0.80, "MET amplification in NSCLC"),
    ("MET", "HCC", "associated_with", 0.78, "MET overexpression in HCC"),
    ("VEGFR2", "RCC", "driver_of", 0.88, "VEGF/VEGFR pathway drives ccRCC angiogenesis"),
    ("VEGFR2", "HCC", "driver_of", 0.82, "VEGF-driven angiogenesis essential in HCC"),
    ("STAT3", "AML", "associated_with", 0.72, "STAT3 constitutively active in AML"),

    # === New protein targets -> Disease (needed for drug paths) ===
    ("KIT", "GIST", "driver_of", 0.98, "KIT gain-of-function mutations in 85-95% of GIST (Hirota 1998)"),
    ("KIT", "AML", "associated_with", 0.75, "KIT mutations in 25-30% of core-binding factor AML"),
    ("ALK", "NSCLC", "driver_of", 0.92, "ALK rearrangements in 3-7% of NSCLC (Soda 2007)"),
    ("PDGFRA", "GIST", "driver_of", 0.85, "PDGFRA mutations in 5-10% of KIT-negative GIST"),
    ("PDGFRA", "Glioblastoma", "associated_with", 0.78, "PDGFRA amplification in proneural GBM"),
    ("FLT3", "AML", "driver_of", 0.90, "FLT3-ITD in 25-30% of AML (Nakao 1996)"),
    ("EGFR", "Pancreatic_Cancer", "associated_with", 0.65, "EGFR overexpression in pancreatic cancer"),
    ("MTOR", "Breast_Cancer", "associated_with", 0.80, "mTOR pathway hyperactivation in HR+ breast cancer"),
    ("COX2", "Colorectal_Cancer", "driver_of", 0.80, "COX-2 overexpression in 80% of CRC (Eberhart 1994)"),
    ("NFKB1", "Colorectal_Cancer", "associated_with", 0.72, "NF-kB constitutive activation in CRC"),
    ("NFKB1", "AML", "associated_with", 0.68, "NF-kB activation in AML blasts"),
    ("NPL4", "AML", "associated_with", 0.60, "Proteasome pathway dependency in AML"),
    ("NPL4", "Glioblastoma", "associated_with", 0.55, "Proteasome-dependent survival in GBM"),
    ("ROS1", "NSCLC", "driver_of", 0.85, "ROS1 fusions in 1-2% of NSCLC"),
    ("CRBN", "Multiple_Myeloma", "associated_with", 0.82, "Cereblon-dependent degradation in MM"),
    ("AMPK", "Breast_Cancer", "associated_with", 0.60, "AMPK loss associated with breast cancer progression"),
    ("AMPK", "Colorectal_Cancer", "associated_with", 0.58, "AMPK pathway downregulated in CRC"),
    ("AMPK", "Pancreatic_Cancer", "associated_with", 0.55, "AMPK metabolic role in pancreatic cancer"),
    ("RAF1", "RCC", "associated_with", 0.62, "RAF-MAPK pathway activation in RCC"),
    ("BRAF", "HCC", "associated_with", 0.50, "BRAF mutations in subset of HCC"),

    # === Sarcoma diseases ===
    ("TP53", "Soft_Tissue_Sarcoma", "driver_of", 0.85, "TP53 mutations in 20-60% of soft tissue sarcomas (COSMIC)"),
    ("RB1", "Soft_Tissue_Sarcoma", "associated_with", 0.75, "RB1 loss in leiomyosarcoma and osteosarcoma"),
    ("MDM2", "Soft_Tissue_Sarcoma", "driver_of", 0.82, "MDM2 amplification in well-differentiated liposarcoma (Oliner 1992)"),
    ("KIT", "Soft_Tissue_Sarcoma", "associated_with", 0.70, "KIT expression in subset of soft tissue sarcomas"),
    ("PDGFRA", "Soft_Tissue_Sarcoma", "associated_with", 0.68, "PDGFRA in dermatofibrosarcoma protuberans"),
    ("VEGFR2", "Soft_Tissue_Sarcoma", "associated_with", 0.65, "VEGF-driven angiogenesis in sarcoma progression"),
    ("CDK4", "Soft_Tissue_Sarcoma", "driver_of", 0.80, "CDK4 amplification in well-differentiated liposarcoma"),
    ("TP53", "Ewing_Sarcoma", "associated_with", 0.60, "TP53 mutations in 10-15% of Ewing sarcoma (secondary event)"),

    # === Li-Fraumeni Syndrome (TP53 germline) ===
    ("TP53", "Li_Fraumeni_Syndrome", "driver_of", 0.99, "Germline TP53 mutations define Li-Fraumeni syndrome (Li & Fraumeni 1969, Malkin 1990)"),
    ("MDM2", "Li_Fraumeni_Syndrome", "associated_with", 0.70, "MDM2 SNP309 modifies LFS cancer onset age (Bond 2004)"),
    ("CHEK2", "Li_Fraumeni_Syndrome", "associated_with", 0.55, "CHEK2 germline variants in LFS-like families without TP53 mutations"),
]


# ============================================================================
# DRUG -> DISEASE: FDA-approved indications (loaded into store)
# Only a SUBSET -- rest are holdouts for conjecture engine to discover
# ============================================================================

DRUG_DISEASE_APPROVED = [
    # Well-known, primary indications
    ("Imatinib", "CML", "treats", 0.99, "FDA approved 2001, BCR-ABL+ CML"),
    ("Erlotinib", "NSCLC", "treats", 0.95, "FDA approved 2004, EGFR+ NSCLC"),
    ("Trastuzumab", "Breast_Cancer", "treats", 0.98, "FDA approved 1998, HER2+ breast cancer"),
    ("Vemurafenib", "Melanoma", "treats", 0.97, "FDA approved 2011, BRAF V600E melanoma"),
    ("Palbociclib", "Breast_Cancer", "treats", 0.96, "FDA approved 2015, HR+/HER2- breast cancer"),
    ("Venetoclax", "CLL", "treats", 0.97, "FDA approved 2016, CLL with 17p deletion"),
    ("Ruxolitinib", "Myelofibrosis", "treats", 0.97, "FDA approved 2011, myelofibrosis"),
    ("Olaparib", "Ovarian_Cancer", "treats", 0.95, "FDA approved 2014, BRCA+ ovarian cancer"),
    ("Bevacizumab", "Colorectal_Cancer", "treats", 0.94, "FDA approved 2004, metastatic CRC"),
    ("Cetuximab", "Colorectal_Cancer", "treats", 0.93, "FDA approved 2004, EGFR+ CRC"),
    ("Metformin", "Type2_Diabetes", "treats", 0.99, "FDA approved 1995, first-line T2DM"),
    ("Thalidomide", "Multiple_Myeloma", "treats", 0.92, "FDA approved 2006, newly diagnosed MM"),
    ("Everolimus", "RCC", "treats", 0.93, "FDA approved 2009, advanced RCC"),
    ("Sunitinib", "RCC", "treats", 0.94, "FDA approved 2006, advanced RCC"),
    ("Dabrafenib", "Melanoma", "treats", 0.96, "FDA approved 2013, BRAF V600E melanoma"),
    ("Trametinib", "Melanoma", "treats", 0.95, "FDA approved 2013, BRAF V600 melanoma"),
]


# ============================================================================
# HOLDOUT SET: Known drug-disease associations NOT loaded into store
# The conjecture engine should discover these via compositional reasoning
# ============================================================================

HOLDOUT_EDGES = [
    # --- These are real FDA-approved or clinically validated ---

    # Imatinib also treats GIST (via KIT inhibition) - FDA 2002
    ("Imatinib", "GIST", "treats", 0.95, "FDA approved 2002 for GIST (KIT+ tumors)"),

    # Sorafenib treats HCC and RCC (via VEGFR/RAF)
    ("Sorafenib", "HCC", "treats", 0.93, "FDA approved 2007 for HCC"),
    ("Sorafenib", "RCC", "treats", 0.94, "FDA approved 2005 for RCC"),

    # Erlotinib also for pancreatic cancer
    ("Erlotinib", "Pancreatic_Cancer", "treats", 0.80, "FDA approved 2005, with gemcitabine"),

    # Lapatinib for breast cancer (HER2+)
    ("Lapatinib", "Breast_Cancer", "treats", 0.93, "FDA approved 2007 for HER2+ breast"),

    # Gefitinib for NSCLC
    ("Gefitinib", "NSCLC", "treats", 0.94, "FDA approved 2003 for EGFR+ NSCLC"),

    # Sunitinib also for GIST
    ("Sunitinib", "GIST", "treats", 0.92, "FDA approved 2006 for imatinib-resistant GIST"),

    # Olaparib also for breast cancer (BRCA+)
    ("Olaparib", "Breast_Cancer", "treats", 0.90, "FDA approved 2018 for BRCA+ breast"),

    # Venetoclax for AML
    ("Venetoclax", "AML", "treats", 0.91, "FDA approved 2018 for AML (with azacitidine)"),

    # Crizotinib for NSCLC (ALK+)
    ("Crizotinib", "NSCLC", "treats", 0.94, "FDA approved 2011 for ALK+ NSCLC"),

    # Everolimus also for breast cancer
    ("Everolimus", "Breast_Cancer", "treats", 0.88, "FDA approved 2012, HR+/HER2- with exemestane"),

    # Temsirolimus for RCC
    ("Temsirolimus", "RCC", "treats", 0.92, "FDA approved 2007 for advanced RCC"),

    # --- These are repurposing hypotheses with clinical evidence ---

    # Metformin anti-cancer (epidemiological + clinical trials)
    ("Metformin", "Breast_Cancer", "potential_treatment", 0.55, "Epidemiological: 25-30% cancer risk reduction (Evans 2005)"),
    ("Metformin", "Colorectal_Cancer", "potential_treatment", 0.50, "Multiple observational studies"),
    ("Metformin", "Pancreatic_Cancer", "potential_treatment", 0.45, "Li 2009, risk reduction in diabetics"),

    # Aspirin colorectal cancer prevention (strong evidence)
    ("Aspirin", "Colorectal_Cancer", "prevents", 0.75, "USPSTF recommendation, Rothwell 2011 Lancet"),

    # Disulfiram anti-cancer (emerging)
    ("Disulfiram", "AML", "potential_treatment", 0.40, "Skrott 2017 Nature, proteasome inhibition"),
    ("Disulfiram", "Glioblastoma", "potential_treatment", 0.35, "Triscott 2012, crosses BBB"),

    # === ReDO PROJECT HOLDOUTS (known associations the system should discover) ===
    # Mebendazole holdouts
    ("Mebendazole", "Melanoma", "potential_treatment", 0.60, "ReDO: BRAF inhibition in melanoma cell lines (Simbulan-Rosenthal 2017)"),
    ("Mebendazole", "RCC", "potential_treatment", 0.55, "ReDO: VEGFR2 inhibition, anti-angiogenic (Pantziarka 2014)"),
    ("Mebendazole", "HCC", "potential_treatment", 0.50, "ReDO: VEGFR2-mediated anti-angiogenic effect (Pantziarka 2014)"),
    ("Mebendazole", "Colorectal_Cancer", "potential_treatment", 0.65, "Phase II: 65% vs 10% response with bevacizumab/FOLFOX4 (2023)"),
    # Niclosamide holdouts
    ("Niclosamide", "AML", "potential_treatment", 0.55, "STAT3 inhibition in AML blasts (Jin 2010)"),
    ("Niclosamide", "Colorectal_Cancer", "potential_treatment", 0.60, "NIKOLO Phase II trial, STAT3/NF-kB pathway (Li 2014)"),
    ("Niclosamide", "RCC", "potential_treatment", 0.45, "mTOR pathway inhibition rationale (preclinical)"),
    # Ivermectin holdouts
    ("Ivermectin", "AML", "potential_treatment", 0.45, "STAT3 pathway inhibition in leukemia cells (preclinical)"),
    ("Ivermectin", "Breast_Cancer", "potential_treatment", 0.50, "Triple-negative breast cancer: immunogenic cell death + T-cell infiltration (2024)"),
    ("Ivermectin", "Ovarian_Cancer", "potential_treatment", 0.40, "AKT/mTOR pathway inhibition rationale (preclinical)"),
    # Atorvastatin holdouts
    ("Atorvastatin", "Pancreatic_Cancer", "potential_treatment", 0.55, "KRAS mutated in 90% of pancreatic cancer; statin blocks KRAS prenylation (Gruenbacher 2021)"),
    ("Atorvastatin", "Colorectal_Cancer", "potential_treatment", 0.50, "KRAS mutated in 40% of CRC; epidemiological evidence (Beckwitt 2018)"),
    ("Atorvastatin", "NSCLC", "potential_treatment", 0.45, "KRAS mutated in 25% of NSCLC; preclinical evidence"),
    # Sarcoma holdout
    ("Imatinib", "Soft_Tissue_Sarcoma", "treats", 0.70, "FDA approved for dermatofibrosarcoma protuberans (KIT/PDGFRA)"),
]


# ============================================================================
# DRUG COMBINATIONS (known synergies)
# Format: (drug1, drug2, relation, confidence, evidence)
# ============================================================================

DRUG_COMBINATIONS = [
    ("Dabrafenib", "Trametinib", "synergizes_with", 0.97, "FDA-approved combination for melanoma (BRAF+MEK)"),
    ("Venetoclax", "Ruxolitinib", "synergizes_with", 0.70, "Clinical trials in AML"),
    ("Palbociclib", "Trastuzumab", "synergizes_with", 0.75, "Clinical trials in HER2+ breast cancer"),
    ("Everolimus", "Erlotinib", "synergizes_with", 0.65, "Phase II trials in NSCLC"),
    ("Olaparib", "Bevacizumab", "synergizes_with", 0.80, "PAOLA-1 trial, ovarian cancer"),
]


def get_drug_network():
    """
    Returns (entities_dict, interactions_list).

    entities_dict: all Drug + Disease objects
    interactions_list: all Drug->Protein + Protein->Disease + Drug->Disease edges
                       (EXCLUDING holdout set)
    """
    entities = {}

    # Add drugs
    for name, data in DRUGS.items():
        entities[name] = data

    # Add diseases
    for name, data in DISEASES.items():
        entities[name] = data

    # Combine all non-holdout interactions
    interactions = (
        DRUG_TARGET_INTERACTIONS +
        PROTEIN_DISEASE_ASSOCIATIONS +
        DRUG_DISEASE_APPROVED +
        DRUG_COMBINATIONS
    )

    return entities, interactions


def get_holdout_edges(include_redo_expansion=True, include_redo_full=False):
    """
    Returns the holdout set of known drug-disease associations.
    These are NOT loaded into the store.
    The conjecture engine should discover them via composition.
    """
    edges = list(HOLDOUT_EDGES)
    if include_redo_expansion:
        try:
            from data.drugs.redo_expansion import REDO_HOLDOUT_EDGES
            edges.extend(REDO_HOLDOUT_EDGES)
        except ImportError:
            pass
    if include_redo_full:
        try:
            from data.drugs.redo_full_expansion import REDO_FULL_HOLDOUT_EDGES
            edges.extend(REDO_FULL_HOLDOUT_EDGES)
        except ImportError:
            pass
    return edges


def get_stats():
    """Print network statistics."""
    from collections import Counter

    entities, interactions = get_drug_network()
    holdouts = get_holdout_edges()

    drugs = {k: v for k, v in entities.items() if v["type"] == "Drug"}
    diseases = {k: v for k, v in entities.items() if v["type"] == "Disease"}

    print("Drug Repurposing Network Statistics:")
    print(f"  Total entities: {len(entities)}")
    print(f"    Drugs: {len(drugs)}")
    print(f"    Diseases: {len(diseases)}")
    print(f"  Total interactions: {len(interactions)}")
    print(f"  Holdout edges: {len(holdouts)}")
    print()

    # Count interaction types
    rel_types = Counter(i[2] for i in interactions)
    print("Interaction types:")
    for rtype, count in rel_types.most_common():
        print(f"  {rtype}: {count}")

    # Count drug classes
    classes = Counter(d.get("drug_class", "unknown") for d in drugs.values())
    print("\nDrug classes:")
    for cls, count in classes.most_common():
        print(f"  {cls}: {count}")


if __name__ == "__main__":
    get_stats()
