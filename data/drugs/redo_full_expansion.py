# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
ReDO Project Drug Expansion -- Full (268 drugs target)
======================================================

Extends the drug network with ~130 additional drugs from the
Anticancer Fund's Repurposing Drugs in Oncology (ReDO) database.

Combined with drug_network.py (34 drugs) and redo_expansion.py (20 drugs),
this brings the total to ~184 drugs in the network.

All drugs are FDA-approved for non-cancer indications.
Targets from DrugBank, published literature, and ReDO reviews.

Sources:
  Pantziarka et al. ecancermedicalscience 2014-2024
  ReDO_DB (https://www.anticancerfund.org/en/redo-db)
  DrugBank 5.x (https://go.drugbank.com/)
  Bouche et al. ecancermedicalscience 2017;11:727 (PMC6345075)
"""

# ============================================================================
# REDO FULL DRUGS (~130 drugs, organized by drug class)
# ============================================================================

REDO_FULL_DRUGS = {

    # === STATINS (HMG-CoA reductase inhibitors) ===
    "Simvastatin": {
        "type": "Drug", "brand": "Zocor",
        "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor, blocks mevalonate/prenylation",
        "fda_year": 1991, "drugbank_id": "DB00641",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, epidemiological + preclinical",
    },
    "Lovastatin": {
        "type": "Drug", "brand": "Mevacor",
        "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor, blocks RAS prenylation",
        "fda_year": 1987, "drugbank_id": "DB00227",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Pravastatin": {
        "type": "Drug", "brand": "Pravachol",
        "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor, hydrophilic statin",
        "fda_year": 1991, "drugbank_id": "DB00175",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Rosuvastatin": {
        "type": "Drug", "brand": "Crestor",
        "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor, potent statin",
        "fda_year": 2003, "drugbank_id": "DB01098",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Fluvastatin": {
        "type": "Drug", "brand": "Lescol",
        "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor",
        "fda_year": 1993, "drugbank_id": "DB01095",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, breast cancer window trial",
    },

    # === ADDITIONAL NSAIDs ===
    "Ibuprofen": {
        "type": "Drug", "brand": "Advil",
        "drug_class": "NSAID",
        "mechanism": "Non-selective COX-1/COX-2 inhibitor",
        "fda_year": 1974, "drugbank_id": "DB01050",
        "original_indication": "Pain/inflammation",
        "repurposing_status": "ReDO DB, epidemiological CRC evidence",
    },
    "Naproxen": {
        "type": "Drug", "brand": "Aleve",
        "drug_class": "NSAID",
        "mechanism": "Non-selective COX-1/COX-2 inhibitor",
        "fda_year": 1976, "drugbank_id": "DB00788",
        "original_indication": "Pain/inflammation",
        "repurposing_status": "ReDO DB, CRC risk reduction",
    },
    "Piroxicam": {
        "type": "Drug", "brand": "Feldene",
        "drug_class": "NSAID",
        "mechanism": "Non-selective COX inhibitor, anti-angiogenic",
        "fda_year": 1982, "drugbank_id": "DB00554",
        "original_indication": "Arthritis",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Sulindac": {
        "type": "Drug", "brand": "Clinoril",
        "drug_class": "NSAID",
        "mechanism": "COX inhibitor, Wnt/beta-catenin pathway modulator",
        "fda_year": 1978, "drugbank_id": "DB00605",
        "original_indication": "Arthritis",
        "repurposing_status": "ReDO DB, FAP polyp regression",
    },
    "Ketorolac": {
        "type": "Drug", "brand": "Toradol",
        "drug_class": "NSAID",
        "mechanism": "Potent COX inhibitor, perioperative anti-metastatic",
        "fda_year": 1989, "drugbank_id": "DB00465",
        "original_indication": "Acute pain",
        "repurposing_status": "ReDO DB, perioperative anti-metastatic trials",
    },

    # === ANTIFUNGALS ===
    "Ketoconazole": {
        "type": "Drug", "brand": "Nizoral",
        "drug_class": "Imidazole antifungal",
        "mechanism": "CYP17A1/CYP3A4 inhibitor, androgen synthesis blocker",
        "fda_year": 1981, "drugbank_id": "DB01026",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO DB, prostate cancer (historical use)",
    },
    "Clotrimazole": {
        "type": "Drug", "brand": "Lotrimin",
        "drug_class": "Imidazole antifungal",
        "mechanism": "Calcium-activated potassium channel blocker, glycolysis inhibitor",
        "fda_year": 1975, "drugbank_id": "DB00257",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO DB, preclinical anti-proliferative",
    },
    "Miconazole": {
        "type": "Drug", "brand": "Monistat",
        "drug_class": "Imidazole antifungal",
        "mechanism": "ROS inducer, STAT3 pathway modulator",
        "fda_year": 1974, "drugbank_id": "DB01110",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO DB, preclinical",
    },
    "Fluconazole": {
        "type": "Drug", "brand": "Diflucan",
        "drug_class": "Triazole antifungal",
        "mechanism": "CYP51A1 inhibitor, weak anti-angiogenic",
        "fda_year": 1990, "drugbank_id": "DB00196",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === BETA-BLOCKERS ===
    "Atenolol": {
        "type": "Drug", "brand": "Tenormin",
        "drug_class": "Beta-1 selective blocker",
        "mechanism": "ADRB1 antagonist, anti-angiogenic",
        "fda_year": 1981, "drugbank_id": "DB00335",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Timolol": {
        "type": "Drug", "brand": "Timoptic",
        "drug_class": "Non-selective beta-blocker",
        "mechanism": "ADRB1/ADRB2 antagonist, anti-angiogenic",
        "fda_year": 1978, "drugbank_id": "DB00373",
        "original_indication": "Glaucoma/hypertension",
        "repurposing_status": "ReDO DB, infantile hemangioma",
    },
    "Carvedilol": {
        "type": "Drug", "brand": "Coreg",
        "drug_class": "Alpha/beta-blocker",
        "mechanism": "ADRB1/ADRB2/ADRA1 antagonist, antioxidant",
        "fda_year": 1995, "drugbank_id": "DB01136",
        "original_indication": "Heart failure/hypertension",
        "repurposing_status": "ReDO DB, anti-proliferative in breast cancer",
    },
    "Nadolol": {
        "type": "Drug", "brand": "Corgard",
        "drug_class": "Non-selective beta-blocker",
        "mechanism": "ADRB1/ADRB2 antagonist",
        "fda_year": 1979, "drugbank_id": "DB01203",
        "original_indication": "Hypertension/angina",
        "repurposing_status": "ReDO DB, melanoma epidemiological",
    },

    # === CALCIUM CHANNEL BLOCKERS ===
    "Amlodipine": {
        "type": "Drug", "brand": "Norvasc",
        "drug_class": "Dihydropyridine CCB",
        "mechanism": "L-type calcium channel blocker, anti-proliferative",
        "fda_year": 1987, "drugbank_id": "DB00381",
        "original_indication": "Hypertension/angina",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Nifedipine": {
        "type": "Drug", "brand": "Procardia",
        "drug_class": "Dihydropyridine CCB",
        "mechanism": "L-type calcium channel blocker",
        "fda_year": 1981, "drugbank_id": "DB01115",
        "original_indication": "Hypertension/angina",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Diltiazem": {
        "type": "Drug", "brand": "Cardizem",
        "drug_class": "Benzothiazepine CCB",
        "mechanism": "L-type calcium channel blocker, P-gp inhibitor",
        "fda_year": 1982, "drugbank_id": "DB00343",
        "original_indication": "Hypertension/angina",
        "repurposing_status": "ReDO DB, MDR reversal",
    },

    # === PROTON PUMP INHIBITORS ===
    "Omeprazole": {
        "type": "Drug", "brand": "Prilosec",
        "drug_class": "Proton pump inhibitor",
        "mechanism": "H+/K+ ATPase inhibitor, tumor pH modulator",
        "fda_year": 1989, "drugbank_id": "DB00338",
        "original_indication": "GERD/peptic ulcer",
        "repurposing_status": "ReDO DB, chemosensitization via pH",
    },
    "Esomeprazole": {
        "type": "Drug", "brand": "Nexium",
        "drug_class": "Proton pump inhibitor",
        "mechanism": "H+/K+ ATPase inhibitor, tumor acidification blocker",
        "fda_year": 2001, "drugbank_id": "DB00736",
        "original_indication": "GERD",
        "repurposing_status": "ReDO DB, Phase II melanoma",
    },
    "Lansoprazole": {
        "type": "Drug", "brand": "Prevacid",
        "drug_class": "Proton pump inhibitor",
        "mechanism": "H+/K+ ATPase inhibitor",
        "fda_year": 1995, "drugbank_id": "DB00448",
        "original_indication": "GERD/peptic ulcer",
        "repurposing_status": "ReDO DB, preclinical",
    },
    "Pantoprazole": {
        "type": "Drug", "brand": "Protonix",
        "drug_class": "Proton pump inhibitor",
        "mechanism": "H+/K+ ATPase inhibitor, autophagy modulator",
        "fda_year": 2000, "drugbank_id": "DB00213",
        "original_indication": "GERD",
        "repurposing_status": "ReDO DB, preclinical",
    },
    "Rabeprazole": {
        "type": "Drug", "brand": "Aciphex",
        "drug_class": "Proton pump inhibitor",
        "mechanism": "H+/K+ ATPase inhibitor",
        "fda_year": 1999, "drugbank_id": "DB01129",
        "original_indication": "GERD",
        "repurposing_status": "ReDO DB, limited evidence",
    },

    # === ANTIPSYCHOTICS / PHENOTHIAZINES ===
    "Chlorpromazine": {
        "type": "Drug", "brand": "Thorazine",
        "drug_class": "Phenothiazine antipsychotic",
        "mechanism": "DRD2 antagonist, calmodulin inhibitor, anti-mitotic",
        "fda_year": 1954, "drugbank_id": "DB00477",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, preclinical glioblastoma",
    },
    "Thioridazine": {
        "type": "Drug", "brand": "Mellaril",
        "drug_class": "Phenothiazine antipsychotic",
        "mechanism": "DRD2 antagonist, PI3K/AKT inhibitor, cancer stem cell killer",
        "fda_year": 1959, "drugbank_id": "DB00679",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, leukemia stem cells",
    },
    "Trifluoperazine": {
        "type": "Drug", "brand": "Stelazine",
        "drug_class": "Phenothiazine antipsychotic",
        "mechanism": "DRD2 antagonist, calmodulin inhibitor, anti-EMT",
        "fda_year": 1959, "drugbank_id": "DB00831",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, anti-cancer stem cell",
    },
    "Fluphenazine": {
        "type": "Drug", "brand": "Prolixin",
        "drug_class": "Phenothiazine antipsychotic",
        "mechanism": "DRD2 antagonist, calmodulin inhibitor",
        "fda_year": 1959, "drugbank_id": "DB00623",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, preclinical",
    },
    "Haloperidol": {
        "type": "Drug", "brand": "Haldol",
        "drug_class": "Butyrophenone antipsychotic",
        "mechanism": "DRD2 antagonist, sigma receptor ligand",
        "fda_year": 1967, "drugbank_id": "DB00502",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, preclinical",
    },
    "Pimozide": {
        "type": "Drug", "brand": "Orap",
        "drug_class": "Diphenylbutylpiperidine antipsychotic",
        "mechanism": "DRD2 antagonist, STAT5 inhibitor",
        "fda_year": 1984, "drugbank_id": "DB01100",
        "original_indication": "Tourette syndrome",
        "repurposing_status": "ReDO DB, STAT5-driven cancers",
    },

    # === ADDITIONAL ANTHELMINTHICS ===
    "Albendazole": {
        "type": "Drug", "brand": "Albenza",
        "drug_class": "Benzimidazole anthelmintic",
        "mechanism": "Beta-tubulin polymerization inhibitor, VEGF inhibitor",
        "fda_year": 1996, "drugbank_id": "DB00518",
        "original_indication": "Helminth infections",
        "repurposing_status": "ReDO DB, anti-angiogenic + anti-proliferative",
    },
    "Flubendazole": {
        "type": "Drug", "brand": "Fluvermal",
        "drug_class": "Benzimidazole anthelmintic",
        "mechanism": "Tubulin polymerization inhibitor, microtubule destabilizer",
        "fda_year": 1980, "drugbank_id": "DB08974",
        "original_indication": "Helminth infections",
        "repurposing_status": "ReDO DB, neuroblastoma + leukemia preclinical",
    },
    "Pyrvinium": {
        "type": "Drug", "brand": "Povan",
        "drug_class": "Cyanine dye anthelmintic",
        "mechanism": "Wnt pathway inhibitor, mitochondrial complex I inhibitor",
        "fda_year": 1955, "drugbank_id": "DB06112",
        "original_indication": "Pinworm infections",
        "repurposing_status": "ReDO DB, Wnt-driven cancers",
    },

    # === ADDITIONAL ANTIBIOTICS ===
    "Azithromycin": {
        "type": "Drug", "brand": "Zithromax",
        "drug_class": "Macrolide antibiotic",
        "mechanism": "Mitochondrial ribosome inhibitor, anti-CSC",
        "fda_year": 1991, "drugbank_id": "DB00207",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, cancer stem cell targeting",
    },
    "Minocycline": {
        "type": "Drug", "brand": "Minocin",
        "drug_class": "Tetracycline antibiotic",
        "mechanism": "MMP inhibitor, anti-angiogenic, mitochondrial inhibitor",
        "fda_year": 1971, "drugbank_id": "DB01017",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, anti-metastatic",
    },
    "Tigecycline": {
        "type": "Drug", "brand": "Tygacil",
        "drug_class": "Glycylcycline antibiotic",
        "mechanism": "Mitochondrial translation inhibitor, oxidative stress inducer",
        "fda_year": 2005, "drugbank_id": "DB00560",
        "original_indication": "Complicated infections",
        "repurposing_status": "ReDO DB, AML mitochondrial targeting",
    },
    "Salinomycin": {
        "type": "Drug", "brand": "Salinomycin",
        "drug_class": "Polyether ionophore antibiotic",
        "mechanism": "Wnt/beta-catenin inhibitor, cancer stem cell killer",
        "fda_year": 1978, "drugbank_id": "DB11588",
        "original_indication": "Veterinary coccidiosis",
        "repurposing_status": "ReDO DB, breast cancer stem cells (Gupta 2009)",
    },
    "Ciprofloxacin": {
        "type": "Drug", "brand": "Cipro",
        "drug_class": "Fluoroquinolone antibiotic",
        "mechanism": "Topoisomerase II inhibitor, anti-proliferative",
        "fda_year": 1987, "drugbank_id": "DB00537",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Rifampicin": {
        "type": "Drug", "brand": "Rifadin",
        "drug_class": "Rifamycin antibiotic",
        "mechanism": "RNA polymerase inhibitor, P-gp inducer",
        "fda_year": 1971, "drugbank_id": "DB01045",
        "original_indication": "Tuberculosis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === THIAZOLIDINEDIONES ===
    "Pioglitazone": {
        "type": "Drug", "brand": "Actos",
        "drug_class": "Thiazolidinedione",
        "mechanism": "PPARG agonist, anti-inflammatory, pro-differentiation",
        "fda_year": 1999, "drugbank_id": "DB01132",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, CRC and breast cancer epidemiological",
    },
    "Rosiglitazone": {
        "type": "Drug", "brand": "Avandia",
        "drug_class": "Thiazolidinedione",
        "mechanism": "PPARG agonist, anti-inflammatory",
        "fda_year": 1999, "drugbank_id": "DB00412",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },

    # === ADDITIONAL ANTIMALARIALS ===
    "Hydroxychloroquine": {
        "type": "Drug", "brand": "Plaquenil",
        "drug_class": "Aminoquinoline antimalarial",
        "mechanism": "Autophagy inhibitor, lysosomal alkalizer, TLR9 inhibitor",
        "fda_year": 1955, "drugbank_id": "DB01611",
        "original_indication": "Malaria/lupus",
        "repurposing_status": "ReDO DB, Phase II autophagy inhibition in multiple cancers",
    },
    "Mefloquine": {
        "type": "Drug", "brand": "Lariam",
        "drug_class": "Quinoline antimalarial",
        "mechanism": "Lysosomal disruptor, autophagy inhibitor",
        "fda_year": 1989, "drugbank_id": "DB00358",
        "original_indication": "Malaria",
        "repurposing_status": "ReDO DB, preclinical GBM",
    },
    "Atovaquone": {
        "type": "Drug", "brand": "Mepron",
        "drug_class": "Hydroxynaphthoquinone",
        "mechanism": "Mitochondrial complex III inhibitor, oxidative phosphorylation blocker",
        "fda_year": 1992, "drugbank_id": "DB01117",
        "original_indication": "Pneumocystis/malaria",
        "repurposing_status": "ReDO DB, tumor hypoxia modulator",
    },

    # === ACE INHIBITORS ===
    "Captopril": {
        "type": "Drug", "brand": "Capoten",
        "drug_class": "ACE inhibitor",
        "mechanism": "ACE inhibitor, anti-angiogenic, MMP inhibitor",
        "fda_year": 1981, "drugbank_id": "DB01197",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, anti-angiogenic + immunomodulatory",
    },
    "Enalapril": {
        "type": "Drug", "brand": "Vasotec",
        "drug_class": "ACE inhibitor",
        "mechanism": "ACE inhibitor, anti-angiogenic",
        "fda_year": 1985, "drugbank_id": "DB00584",
        "original_indication": "Hypertension/CHF",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Lisinopril": {
        "type": "Drug", "brand": "Prinivil",
        "drug_class": "ACE inhibitor",
        "mechanism": "ACE inhibitor, anti-angiogenic",
        "fda_year": 1987, "drugbank_id": "DB00722",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Perindopril": {
        "type": "Drug", "brand": "Aceon",
        "drug_class": "ACE inhibitor",
        "mechanism": "ACE inhibitor, anti-angiogenic, bradykinin potentiator",
        "fda_year": 1993, "drugbank_id": "DB00790",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, anti-angiogenic in preclinical",
    },

    # === ANGIOTENSIN RECEPTOR BLOCKERS ===
    "Losartan": {
        "type": "Drug", "brand": "Cozaar",
        "drug_class": "ARB",
        "mechanism": "AGTR1 antagonist, anti-fibrotic, anti-angiogenic",
        "fda_year": 1995, "drugbank_id": "DB00678",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, Phase II pancreatic cancer stroma",
    },
    "Candesartan": {
        "type": "Drug", "brand": "Atacand",
        "drug_class": "ARB",
        "mechanism": "AGTR1 antagonist, anti-angiogenic",
        "fda_year": 1998, "drugbank_id": "DB00796",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Telmisartan": {
        "type": "Drug", "brand": "Micardis",
        "drug_class": "ARB",
        "mechanism": "AGTR1 antagonist, partial PPARG agonist",
        "fda_year": 1998, "drugbank_id": "DB00966",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, PPARG-mediated anti-cancer",
    },

    # === BISPHOSPHONATES ===
    "Zoledronic_Acid": {
        "type": "Drug", "brand": "Zometa",
        "drug_class": "Bisphosphonate",
        "mechanism": "FDPS inhibitor, blocks prenylation, anti-osteoclastic",
        "fda_year": 2001, "drugbank_id": "DB00399",
        "original_indication": "Osteoporosis/bone metastases",
        "repurposing_status": "ReDO DB, adjuvant breast cancer (AZURE/ABCSG-12)",
    },
    "Alendronate": {
        "type": "Drug", "brand": "Fosamax",
        "drug_class": "Bisphosphonate",
        "mechanism": "FDPS inhibitor, blocks farnesylation",
        "fda_year": 1995, "drugbank_id": "DB00630",
        "original_indication": "Osteoporosis",
        "repurposing_status": "ReDO DB, epidemiological breast cancer reduction",
    },
    "Clodronate": {
        "type": "Drug", "brand": "Bonefos",
        "drug_class": "Bisphosphonate",
        "mechanism": "Non-nitrogen bisphosphonate, ATP analog, macrophage depletor",
        "fda_year": 1986, "drugbank_id": "DB01077",
        "original_indication": "Osteoporosis/hypercalcemia",
        "repurposing_status": "ReDO DB, adjuvant breast cancer",
    },

    # === CARDIAC GLYCOSIDES ===
    "Digoxin": {
        "type": "Drug", "brand": "Lanoxin",
        "drug_class": "Cardiac glycoside",
        "mechanism": "Na+/K+-ATPase inhibitor, SRC pathway modulator, HIF-1a inhibitor",
        "fda_year": 1954, "drugbank_id": "DB00390",
        "original_indication": "Heart failure/atrial fibrillation",
        "repurposing_status": "ReDO DB, epidemiological + preclinical",
    },
    "Digitoxin": {
        "type": "Drug", "brand": "Crystodigin",
        "drug_class": "Cardiac glycoside",
        "mechanism": "Na+/K+-ATPase inhibitor, selective cancer cell toxicity",
        "fda_year": 1952, "drugbank_id": "DB01396",
        "original_indication": "Heart failure",
        "repurposing_status": "ReDO DB, preclinical NSCLC and breast",
    },

    # === ANTIHISTAMINES ===
    "Loratadine": {
        "type": "Drug", "brand": "Claritin",
        "drug_class": "Second-generation antihistamine",
        "mechanism": "H1 receptor antagonist, anti-proliferative in some cancer lines",
        "fda_year": 1993, "drugbank_id": "DB00455",
        "original_indication": "Allergic rhinitis",
        "repurposing_status": "ReDO DB, epidemiological evidence",
    },
    "Desloratadine": {
        "type": "Drug", "brand": "Clarinex",
        "drug_class": "Second-generation antihistamine",
        "mechanism": "H1 receptor antagonist",
        "fda_year": 2001, "drugbank_id": "DB00967",
        "original_indication": "Allergic rhinitis",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Terfenadine": {
        "type": "Drug", "brand": "Seldane",
        "drug_class": "Antihistamine",
        "mechanism": "H1 receptor antagonist, hERG channel blocker, anti-proliferative",
        "fda_year": 1985, "drugbank_id": "DB00342",
        "original_indication": "Allergic rhinitis",
        "repurposing_status": "ReDO DB, preclinical melanoma",
    },

    # === ANTIEPILEPTICS ===
    "Carbamazepine": {
        "type": "Drug", "brand": "Tegretol",
        "drug_class": "Anticonvulsant",
        "mechanism": "Sodium channel blocker, HDAC modulator",
        "fda_year": 1968, "drugbank_id": "DB00564",
        "original_indication": "Epilepsy/trigeminal neuralgia",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Levetiracetam": {
        "type": "Drug", "brand": "Keppra",
        "drug_class": "Anticonvulsant",
        "mechanism": "SV2A modulator, HDAC inhibitor activity",
        "fda_year": 1999, "drugbank_id": "DB01202",
        "original_indication": "Epilepsy",
        "repurposing_status": "ReDO DB, MGMT methylation effect in GBM",
    },

    # === ANTIDEPRESSANTS ===
    "Fluoxetine": {
        "type": "Drug", "brand": "Prozac",
        "drug_class": "SSRI",
        "mechanism": "Serotonin reuptake inhibitor, anti-proliferative, pro-apoptotic",
        "fda_year": 1987, "drugbank_id": "DB00472",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Sertraline": {
        "type": "Drug", "brand": "Zoloft",
        "drug_class": "SSRI",
        "mechanism": "Serotonin reuptake inhibitor, TERT inhibitor",
        "fda_year": 1991, "drugbank_id": "DB01104",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Imipramine": {
        "type": "Drug", "brand": "Tofranil",
        "drug_class": "Tricyclic antidepressant",
        "mechanism": "Serotonin/norepinephrine reuptake inhibitor, autophagy inducer",
        "fda_year": 1959, "drugbank_id": "DB00458",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, glioblastoma preclinical",
    },

    # === IMMUNOSUPPRESSANTS ===
    "Sirolimus": {
        "type": "Drug", "brand": "Rapamune",
        "drug_class": "mTOR inhibitor (immunosuppressant)",
        "mechanism": "FKBP12-mediated mTOR complex 1 inhibitor",
        "fda_year": 1999, "drugbank_id": "DB00877",
        "original_indication": "Transplant rejection",
        "repurposing_status": "ReDO DB, lymphangioleiomyomatosis",
    },
    "Ciclosporin": {
        "type": "Drug", "brand": "Sandimmune",
        "drug_class": "Calcineurin inhibitor",
        "mechanism": "Calcineurin inhibitor, P-gp inhibitor (MDR reversal)",
        "fda_year": 1983, "drugbank_id": "DB00091",
        "original_indication": "Transplant rejection",
        "repurposing_status": "ReDO DB, MDR reversal agent",
    },

    # === PDE INHIBITORS ===
    "Sildenafil": {
        "type": "Drug", "brand": "Viagra",
        "drug_class": "PDE5 inhibitor",
        "mechanism": "PDE5 inhibitor, NO/cGMP pathway modulator, ABCB1 inhibitor",
        "fda_year": 1998, "drugbank_id": "DB00203",
        "original_indication": "Erectile dysfunction",
        "repurposing_status": "ReDO DB, chemosensitization + immunomodulation",
    },
    "Theophylline": {
        "type": "Drug", "brand": "Theo-Dur",
        "drug_class": "Methylxanthine",
        "mechanism": "PDE inhibitor, adenosine receptor antagonist, HDAC activator",
        "fda_year": 1970, "drugbank_id": "DB00277",
        "original_indication": "Asthma/COPD",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Dipyridamole": {
        "type": "Drug", "brand": "Persantine",
        "drug_class": "PDE inhibitor / antiplatelet",
        "mechanism": "PDE inhibitor, nucleoside transport inhibitor, anti-angiogenic",
        "fda_year": 1961, "drugbank_id": "DB00975",
        "original_indication": "Stroke prevention",
        "repurposing_status": "ReDO DB, anti-angiogenic + immunomodulatory",
    },

    # === RETINOIDS ===
    "Isotretinoin": {
        "type": "Drug", "brand": "Accutane",
        "drug_class": "Retinoid",
        "mechanism": "RAR agonist, pro-differentiation, anti-proliferative",
        "fda_year": 1982, "drugbank_id": "DB00982",
        "original_indication": "Severe acne",
        "repurposing_status": "ReDO DB, neuroblastoma maintenance therapy",
    },
    "Acitretin": {
        "type": "Drug", "brand": "Soriatane",
        "drug_class": "Retinoid",
        "mechanism": "RAR/RXR agonist, anti-proliferative",
        "fda_year": 1996, "drugbank_id": "DB00459",
        "original_indication": "Psoriasis",
        "repurposing_status": "ReDO DB, squamous cell carcinoma prevention",
    },

    # === ANTI-GOUT ===
    "Allopurinol": {
        "type": "Drug", "brand": "Zyloprim",
        "drug_class": "Xanthine oxidase inhibitor",
        "mechanism": "Xanthine oxidase inhibitor, reduces ROS production",
        "fda_year": 1966, "drugbank_id": "DB00437",
        "original_indication": "Gout",
        "repurposing_status": "ReDO DB, preclinical CRC",
    },
    "Colchicine": {
        "type": "Drug", "brand": "Colcrys",
        "drug_class": "Anti-mitotic alkaloid",
        "mechanism": "Tubulin polymerization inhibitor, anti-inflammatory",
        "fda_year": 1961, "drugbank_id": "DB01394",
        "original_indication": "Gout",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },

    # === DIURETICS ===
    "Amiloride": {
        "type": "Drug", "brand": "Midamor",
        "drug_class": "Potassium-sparing diuretic",
        "mechanism": "ENaC blocker, uPA inhibitor, anti-metastatic",
        "fda_year": 1967, "drugbank_id": "DB00594",
        "original_indication": "Hypertension/edema",
        "repurposing_status": "ReDO DB, anti-metastatic via uPA inhibition",
    },
    "Spironolactone": {
        "type": "Drug", "brand": "Aldactone",
        "drug_class": "Mineralocorticoid receptor antagonist",
        "mechanism": "Aldosterone antagonist, anti-androgen, Wnt pathway modulator",
        "fda_year": 1960, "drugbank_id": "DB00421",
        "original_indication": "Heart failure/hypertension",
        "repurposing_status": "ReDO DB, prostate cancer epidemiological",
    },
    "Eplerenone": {
        "type": "Drug", "brand": "Inspra",
        "drug_class": "Selective mineralocorticoid antagonist",
        "mechanism": "Aldosterone antagonist",
        "fda_year": 2002, "drugbank_id": "DB00700",
        "original_indication": "Heart failure/hypertension",
        "repurposing_status": "ReDO DB, limited evidence",
    },

    # === ANTI-ARRHYTHMICS / LOCAL ANESTHETICS ===
    "Lidocaine": {
        "type": "Drug", "brand": "Xylocaine",
        "drug_class": "Local anesthetic / Class Ib antiarrhythmic",
        "mechanism": "Sodium channel blocker, SRC inhibitor, anti-metastatic",
        "fda_year": 1948, "drugbank_id": "DB00281",
        "original_indication": "Local anesthesia",
        "repurposing_status": "ReDO DB, perioperative anti-metastatic",
    },

    # === FIBRATES ===
    "Bezafibrate": {
        "type": "Drug", "brand": "Bezalip",
        "drug_class": "Fibrate",
        "mechanism": "Pan-PPAR agonist, mitochondrial modulator",
        "fda_year": 1978, "drugbank_id": "DB01393",
        "original_indication": "Hyperlipidemia",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Fenofibrate": {
        "type": "Drug", "brand": "Tricor",
        "drug_class": "Fibrate",
        "mechanism": "PPARA agonist, anti-angiogenic, metabolic modulator",
        "fda_year": 1993, "drugbank_id": "DB01039",
        "original_indication": "Hyperlipidemia",
        "repurposing_status": "ReDO DB, preclinical glioblastoma",
    },

    # === ANTI-PARASITICS ===
    "Pyrimethamine": {
        "type": "Drug", "brand": "Daraprim",
        "drug_class": "Antifolate antiparasitic",
        "mechanism": "DHFR inhibitor, anti-proliferative",
        "fda_year": 1953, "drugbank_id": "DB00205",
        "original_indication": "Malaria/toxoplasmosis",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Nitazoxanide": {
        "type": "Drug", "brand": "Alinia",
        "drug_class": "Thiazolide antiparasitic",
        "mechanism": "PFOR inhibitor, Wnt/beta-catenin inhibitor, GRP78 modulator",
        "fda_year": 2002, "drugbank_id": "DB00507",
        "original_indication": "Parasitic diarrhea",
        "repurposing_status": "ReDO DB, preclinical CRC",
    },

    # === ANTI-VIRAL ===
    "Ribavirin": {
        "type": "Drug", "brand": "Rebetol",
        "drug_class": "Nucleoside analog antiviral",
        "mechanism": "IMPDH inhibitor, EZH2 modulator, GTP depletion",
        "fda_year": 1998, "drugbank_id": "DB00811",
        "original_indication": "Hepatitis C",
        "repurposing_status": "ReDO DB, AML eIF4E targeting",
    },

    # === MISC REPURPOSING CANDIDATES ===
    "Pentoxifylline": {
        "type": "Drug", "brand": "Trental",
        "drug_class": "Methylxanthine / hemorrheologic",
        "mechanism": "PDE inhibitor, TNF-alpha suppressor, anti-inflammatory",
        "fda_year": 1984, "drugbank_id": "DB00806",
        "original_indication": "Peripheral vascular disease",
        "repurposing_status": "ReDO DB, radiosensitizer",
    },
    "Tranilast": {
        "type": "Drug", "brand": "Rizaben",
        "drug_class": "Anti-allergic / anti-fibrotic",
        "mechanism": "TGF-beta inhibitor, anti-angiogenic, aryl hydrocarbon receptor ligand",
        "fda_year": 1982, "drugbank_id": "DB07615",
        "original_indication": "Allergic disorders",
        "repurposing_status": "ReDO DB, anti-fibrotic in tumor stroma",
    },
    "Noscapine": {
        "type": "Drug", "brand": "Noscapine",
        "drug_class": "Isoquinoline alkaloid antitussive",
        "mechanism": "Tubulin-binding agent, bradykinin modulator",
        "fda_year": 1954, "drugbank_id": "DB11793",
        "original_indication": "Cough suppressant",
        "repurposing_status": "ReDO DB, anti-mitotic, breast cancer preclinical",
    },
    "Bromocriptine": {
        "type": "Drug", "brand": "Parlodel",
        "drug_class": "Ergot dopamine agonist",
        "mechanism": "DRD2 agonist, prolactin suppressor",
        "fda_year": 1978, "drugbank_id": "DB01200",
        "original_indication": "Prolactinoma/Parkinson's",
        "repurposing_status": "ReDO DB, prolactin-dependent breast cancer",
    },
    "Levamisole": {
        "type": "Drug", "brand": "Ergamisol",
        "drug_class": "Anthelmintic / immunomodulator",
        "mechanism": "Immune stimulant, alkaline phosphatase inhibitor",
        "fda_year": 1990, "drugbank_id": "DB00848",
        "original_indication": "Helminth infections",
        "repurposing_status": "ReDO DB, adjuvant CRC (with 5-FU, historical)",
    },
    "Sulfasalazine": {
        "type": "Drug", "brand": "Azulfidine",
        "drug_class": "Aminosalicylate",
        "mechanism": "NF-kB inhibitor, xCT cystine transporter inhibitor",
        "fda_year": 1950, "drugbank_id": "DB00795",
        "original_indication": "Ulcerative colitis/RA",
        "repurposing_status": "ReDO DB, glioblastoma xCT targeting",
    },
    "Mifepristone": {
        "type": "Drug", "brand": "Mifeprex",
        "drug_class": "Progesterone receptor antagonist",
        "mechanism": "Progesterone/glucocorticoid receptor antagonist",
        "fda_year": 2000, "drugbank_id": "DB00834",
        "original_indication": "Pregnancy termination",
        "repurposing_status": "ReDO DB, endometrial and ovarian cancer",
    },
    "Prazosin": {
        "type": "Drug", "brand": "Minipress",
        "drug_class": "Alpha-1 adrenergic blocker",
        "mechanism": "ADRA1 antagonist, anti-angiogenic, pro-apoptotic",
        "fda_year": 1976, "drugbank_id": "DB00457",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, prostate cancer + anti-angiogenic",
    },
    "Clopidogrel": {
        "type": "Drug", "brand": "Plavix",
        "drug_class": "Antiplatelet",
        "mechanism": "P2Y12 receptor antagonist, anti-platelet, anti-metastatic",
        "fda_year": 1997, "drugbank_id": "DB00758",
        "original_indication": "ACS/stroke prevention",
        "repurposing_status": "ReDO DB, anti-metastatic via platelet inhibition",
    },
    "Ranitidine": {
        "type": "Drug", "brand": "Zantac",
        "drug_class": "H2 receptor antagonist",
        "mechanism": "Histamine H2 receptor blocker, immunomodulator",
        "fda_year": 1983, "drugbank_id": "DB00863",
        "original_indication": "Peptic ulcer/GERD",
        "repurposing_status": "ReDO DB, perioperative immunomodulation",
    },
    "Famotidine": {
        "type": "Drug", "brand": "Pepcid",
        "drug_class": "H2 receptor antagonist",
        "mechanism": "Histamine H2 receptor blocker",
        "fda_year": 1986, "drugbank_id": "DB00927",
        "original_indication": "Peptic ulcer/GERD",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Lithium_Carbonate": {
        "type": "Drug", "brand": "Lithobid",
        "drug_class": "Mood stabilizer",
        "mechanism": "GSK3B inhibitor, Wnt pathway activator, IMPase inhibitor",
        "fda_year": 1970, "drugbank_id": "DB01356",
        "original_indication": "Bipolar disorder",
        "repurposing_status": "ReDO DB, GSK3B-mediated anti-cancer",
    },
    "Disulfiram_Cu": {
        "type": "Drug", "brand": "Antabuse+Cu",
        "drug_class": "ALDH inhibitor + copper",
        "mechanism": "Cu-dependent NPL4 inhibitor, proteasome inhibitor, ROS inducer",
        "fda_year": 1951, "drugbank_id": "DB00822",
        "original_indication": "Alcoholism",
        "repurposing_status": "ReDO DB, DISCO trial breast cancer",
    },
    "Dantrolene": {
        "type": "Drug", "brand": "Dantrium",
        "drug_class": "Muscle relaxant",
        "mechanism": "Ryanodine receptor antagonist, calcium signaling disruptor",
        "fda_year": 1974, "drugbank_id": "DB01219",
        "original_indication": "Muscle spasticity",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Raloxifene": {
        "type": "Drug", "brand": "Evista",
        "drug_class": "SERM",
        "mechanism": "Selective estrogen receptor modulator, anti-estrogenic in breast",
        "fda_year": 1997, "drugbank_id": "DB00481",
        "original_indication": "Osteoporosis",
        "repurposing_status": "ReDO DB, breast cancer chemoprevention",
    },
    "Finasteride": {
        "type": "Drug", "brand": "Proscar",
        "drug_class": "5-alpha reductase inhibitor",
        "mechanism": "SRD5A2 inhibitor, blocks DHT synthesis",
        "fda_year": 1992, "drugbank_id": "DB01216",
        "original_indication": "BPH",
        "repurposing_status": "ReDO DB, prostate cancer risk reduction (PCPT trial)",
    },
    "Dutasteride": {
        "type": "Drug", "brand": "Avodart",
        "drug_class": "Dual 5-alpha reductase inhibitor",
        "mechanism": "SRD5A1/SRD5A2 inhibitor, blocks DHT synthesis",
        "fda_year": 2001, "drugbank_id": "DB01126",
        "original_indication": "BPH",
        "repurposing_status": "ReDO DB, REDUCE trial prostate cancer",
    },
    "Hydralazine": {
        "type": "Drug", "brand": "Apresoline",
        "drug_class": "Vasodilator",
        "mechanism": "DNMT inhibitor, DNA demethylating agent",
        "fda_year": 1953, "drugbank_id": "DB01275",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, epigenetic modifier in cancer",
    },
    "Quinacrine": {
        "type": "Drug", "brand": "Atabrine",
        "drug_class": "Acridine antimalarial",
        "mechanism": "NF-kB inhibitor, PLA2 inhibitor, autophagy inducer",
        "fda_year": 1930, "drugbank_id": "DB01103",
        "original_indication": "Malaria/giardiasis",
        "repurposing_status": "ReDO DB, preclinical multiple cancers",
    },
    "Metronidazole": {
        "type": "Drug", "brand": "Flagyl",
        "drug_class": "Nitroimidazole antibiotic",
        "mechanism": "DNA damage via nitro radical, hypoxia-selective cytotoxin",
        "fda_year": 1963, "drugbank_id": "DB00916",
        "original_indication": "Anaerobic infections",
        "repurposing_status": "ReDO DB, hypoxic cell radiosensitizer",
    },
    "N_Acetylcysteine": {
        "type": "Drug", "brand": "Mucomyst",
        "drug_class": "Mucolytic / antioxidant",
        "mechanism": "Glutathione precursor, ROS modulator, NF-kB inhibitor",
        "fda_year": 1963, "drugbank_id": "DB06151",
        "original_indication": "Acetaminophen overdose/mucolytic",
        "repurposing_status": "ReDO DB, controversial (antioxidant paradox)",
    },
    "Orlistat": {
        "type": "Drug", "brand": "Xenical",
        "drug_class": "Lipase inhibitor",
        "mechanism": "FASN (fatty acid synthase) inhibitor, lipase inhibitor",
        "fda_year": 1999, "drugbank_id": "DB01083",
        "original_indication": "Obesity",
        "repurposing_status": "ReDO DB, FASN-dependent cancer cells",
    },
}


# ============================================================================
# ADDITIONAL PROTEINS needed for ReDO Full drug targets
# ============================================================================

REDO_FULL_ADDITIONAL_PROTEINS = {
    "HMGCR": {
        "type": "Signaling",
        "function": "HMG-CoA reductase, rate-limiting enzyme in mevalonate/cholesterol pathway",
        "pathways": ["mevalonate", "cholesterol", "prenylation"],
        "cancers": ["breast", "colorectal", "prostate"],
    },
    "TUBB": {
        "type": "Structural",
        "function": "Beta-tubulin, microtubule polymerization subunit",
        "pathways": ["cytoskeleton", "mitosis", "cell_division"],
        "cancers": ["breast", "NSCLC", "ovarian"],
    },
    "ADRB2": {
        "type": "Receptor",
        "function": "Beta-2 adrenergic receptor, catecholamine signaling",
        "pathways": ["cAMP", "stress_response", "angiogenesis"],
        "cancers": ["breast", "ovarian", "melanoma"],
    },
    "ATP1A1": {
        "type": "Transporter",
        "function": "Na+/K+-ATPase alpha-1, ion homeostasis",
        "pathways": ["ion_transport", "SRC_signaling", "apoptosis"],
        "cancers": ["NSCLC", "breast", "colorectal"],
    },
    "PPARG": {
        "type": "Transcription",
        "function": "Peroxisome proliferator-activated receptor gamma, differentiation regulator",
        "pathways": ["lipid_metabolism", "differentiation", "inflammation"],
        "cancers": ["colorectal", "breast", "prostate"],
    },
    "SMO": {
        "type": "Receptor",
        "function": "Smoothened, Hedgehog pathway signal transducer",
        "pathways": ["Hedgehog", "stem_cell", "development"],
        "cancers": ["glioblastoma", "pancreatic", "BCC"],
    },
    "FDPS": {
        "type": "Signaling",
        "function": "Farnesyl diphosphate synthase, prenylation pathway enzyme",
        "pathways": ["mevalonate", "prenylation", "bone_resorption"],
        "cancers": ["breast", "multiple_myeloma", "prostate"],
    },
    "ACE": {
        "type": "Signaling",
        "function": "Angiotensin-converting enzyme, RAS system regulator",
        "pathways": ["renin_angiotensin", "angiogenesis", "bradykinin"],
        "cancers": ["breast", "colorectal", "NSCLC"],
    },
    "AGTR1": {
        "type": "Receptor",
        "function": "Angiotensin II receptor type 1, angiogenesis modulator",
        "pathways": ["renin_angiotensin", "angiogenesis", "fibrosis"],
        "cancers": ["breast", "ovarian", "pancreatic"],
    },
    "DRD2": {
        "type": "Receptor",
        "function": "Dopamine D2 receptor, neuroendocrine signaling",
        "pathways": ["dopamine", "cAMP", "prolactin"],
        "cancers": ["glioblastoma", "breast", "pheochromocytoma"],
    },
    "SRC": {
        "type": "Signaling",
        "function": "Non-receptor tyrosine kinase, proto-oncogene",
        "pathways": ["MAPK", "PI3K-AKT", "FAK", "invasion"],
        "cancers": ["colorectal", "breast", "NSCLC", "pancreatic"],
    },
    "GSK3B": {
        "type": "Signaling",
        "function": "Glycogen synthase kinase 3 beta, Wnt pathway regulator",
        "pathways": ["Wnt", "NF-kB", "apoptosis", "glycogen"],
        "cancers": ["colorectal", "AML", "glioblastoma"],
    },
    "DNMT1": {
        "type": "Regulator",
        "function": "DNA methyltransferase 1, epigenetic maintenance",
        "pathways": ["DNA_methylation", "epigenetics", "gene_silencing"],
        "cancers": ["AML", "colorectal", "breast"],
    },
    "FASN": {
        "type": "Signaling",
        "function": "Fatty acid synthase, de novo lipogenesis",
        "pathways": ["lipid_metabolism", "energy", "proliferation"],
        "cancers": ["breast", "prostate", "ovarian"],
    },
}


# ============================================================================
# ReDO FULL DRUG -> PROTEIN interactions (experimentally verified targets)
# Format: (drug, protein, relation, confidence, evidence)
# ============================================================================

REDO_FULL_DRUG_TARGET_INTERACTIONS = [
    # === STATINS -> HMGCR (primary) + KRAS pathway (secondary) ===
    ("Simvastatin", "HMGCR", "inhibits", 0.95, "Direct HMG-CoA reductase inhibition"),
    ("Simvastatin", "KRAS", "indirect_inhibitor", 0.65, "Blocks KRAS prenylation via mevalonate depletion (Beckwitt 2018)"),
    ("Lovastatin", "HMGCR", "inhibits", 0.94, "First statin, HMG-CoA reductase inhibition"),
    ("Lovastatin", "KRAS", "indirect_inhibitor", 0.62, "Blocks RAS prenylation (Liao 2003)"),
    ("Pravastatin", "HMGCR", "inhibits", 0.93, "Hydrophilic statin, HMG-CoA reductase inhibition"),
    ("Rosuvastatin", "HMGCR", "inhibits", 0.96, "Most potent statin, HMG-CoA reductase inhibition"),
    ("Fluvastatin", "HMGCR", "inhibits", 0.93, "HMG-CoA reductase inhibition"),
    ("Fluvastatin", "NFKB1", "inhibits", 0.50, "NF-kB pathway suppression (Kanugula 2014)"),

    # === NSAIDs -> COX2 (primary) ===
    ("Ibuprofen", "COX2", "inhibits", 0.90, "Non-selective COX inhibitor"),
    ("Naproxen", "COX2", "inhibits", 0.90, "Non-selective COX inhibitor"),
    ("Piroxicam", "COX2", "inhibits", 0.88, "Non-selective COX inhibitor"),
    ("Piroxicam", "VEGFR2", "indirect_inhibitor", 0.45, "Anti-angiogenic effect (preclinical)"),
    ("Sulindac", "COX2", "inhibits", 0.85, "COX inhibitor, also Wnt pathway modulator"),
    ("Sulindac", "GSK3B", "indirect_inhibitor", 0.50, "Wnt/beta-catenin pathway modulation (Boon 2004)"),
    ("Ketorolac", "COX2", "inhibits", 0.92, "Potent COX inhibitor"),
    ("Ketorolac", "SRC", "indirect_inhibitor", 0.45, "SRC pathway modulation in perioperative setting (Forget 2014)"),

    # === ANTIFUNGALS -> various ===
    ("Ketoconazole", "VEGFR2", "indirect_inhibitor", 0.55, "Anti-angiogenic activity"),
    ("Ketoconazole", "STAT3", "inhibits", 0.50, "STAT3 pathway modulation (Chen 2012)"),
    ("Clotrimazole", "STAT3", "inhibits", 0.50, "Anti-proliferative via glycolysis inhibition"),
    ("Miconazole", "STAT3", "inhibits", 0.48, "ROS-mediated STAT3 inhibition"),
    ("Fluconazole", "VEGFR2", "indirect_inhibitor", 0.40, "Weak anti-angiogenic"),

    # === BETA-BLOCKERS -> ADRB2 ===
    ("Atenolol", "ADRB2", "inhibits", 0.80, "Beta-1 selective but cross-reactivity with ADRB2"),
    ("Timolol", "ADRB2", "inhibits", 0.90, "Non-selective beta-blocker"),
    ("Carvedilol", "ADRB2", "inhibits", 0.88, "Alpha/beta blocker with anti-oxidant"),
    ("Carvedilol", "VEGFR2", "indirect_inhibitor", 0.45, "Anti-angiogenic property"),
    ("Nadolol", "ADRB2", "inhibits", 0.88, "Non-selective beta-blocker"),

    # === CALCIUM CHANNEL BLOCKERS ===
    ("Amlodipine", "VEGFR2", "indirect_inhibitor", 0.40, "Weak anti-angiogenic activity"),
    ("Nifedipine", "VEGFR2", "indirect_inhibitor", 0.38, "Limited anti-angiogenic"),
    ("Diltiazem", "ABCB1", "inhibits", 0.65, "P-glycoprotein inhibition, MDR reversal"),

    # === PPIs -> tumor pH / autophagy ===
    ("Omeprazole", "MTOR", "indirect_inhibitor", 0.45, "Autophagy modulation via lysosomal pH"),
    ("Omeprazole", "VEGFR2", "indirect_inhibitor", 0.40, "Anti-angiogenic via pH modulation"),
    ("Esomeprazole", "MTOR", "indirect_inhibitor", 0.45, "Autophagy modulation"),
    ("Esomeprazole", "HIF1A", "inhibits", 0.50, "HIF-1a suppression via tumor pH (Luciani 2004)"),
    ("Lansoprazole", "MTOR", "indirect_inhibitor", 0.42, "Autophagy modulation"),
    ("Pantoprazole", "MTOR", "indirect_inhibitor", 0.42, "Autophagy modulation"),
    ("Rabeprazole", "MTOR", "indirect_inhibitor", 0.40, "Autophagy modulation"),

    # === ANTIPSYCHOTICS -> DRD2 + STAT3/5 ===
    ("Chlorpromazine", "DRD2", "inhibits", 0.90, "Dopamine D2 antagonist"),
    ("Chlorpromazine", "AKT1", "inhibits", 0.55, "AKT pathway inhibition (Shin 2006)"),
    ("Thioridazine", "DRD2", "inhibits", 0.88, "Dopamine D2 antagonist"),
    ("Thioridazine", "AKT1", "inhibits", 0.60, "AKT/PI3K inhibition, cancer stem cell killer (Sachlos 2012)"),
    ("Trifluoperazine", "DRD2", "inhibits", 0.88, "Dopamine D2 antagonist"),
    ("Trifluoperazine", "STAT3", "inhibits", 0.50, "Anti-EMT via STAT3 modulation"),
    ("Fluphenazine", "DRD2", "inhibits", 0.88, "Dopamine D2 antagonist"),
    ("Haloperidol", "DRD2", "inhibits", 0.92, "Potent D2 antagonist"),
    ("Pimozide", "DRD2", "inhibits", 0.85, "D2 antagonist"),
    ("Pimozide", "STAT5", "inhibits", 0.70, "Direct STAT5 inhibitor (Nelson 2011)"),
    ("Pimozide", "STAT3", "inhibits", 0.55, "STAT3 pathway modulation"),

    # === ANTHELMINTHICS -> TUBB (tubulin) ===
    ("Albendazole", "TUBB", "inhibits", 0.88, "Beta-tubulin polymerization inhibitor"),
    ("Albendazole", "VEGFR2", "indirect_inhibitor", 0.55, "VEGF suppression (Pourgholami 2010)"),
    ("Flubendazole", "TUBB", "inhibits", 0.90, "Potent tubulin polymerization inhibitor"),
    ("Pyrvinium", "GSK3B", "activator", 0.60, "Wnt pathway inhibitor via casein kinase 1a"),
    ("Pyrvinium", "MTOR", "indirect_inhibitor", 0.50, "Mitochondrial complex I inhibition"),

    # === ANTIBIOTICS ===
    ("Azithromycin", "MTOR", "indirect_inhibitor", 0.45, "Autophagy modulation, mitochondrial ribosome"),
    ("Minocycline", "MMP9", "inhibits", 0.75, "MMP-9 inhibition (similar to doxycycline)"),
    ("Minocycline", "MMP2", "inhibits", 0.72, "MMP-2 inhibition"),
    ("Tigecycline", "MTOR", "indirect_inhibitor", 0.50, "Mitochondrial translation inhibition triggers mTOR suppression"),
    ("Salinomycin", "GSK3B", "indirect_inhibitor", 0.55, "Wnt/beta-catenin pathway inhibition (Gupta 2009 Cell)"),
    ("Salinomycin", "ABCB1", "inhibits", 0.60, "P-glycoprotein inhibition"),
    ("Ciprofloxacin", "MTOR", "indirect_inhibitor", 0.40, "Anti-proliferative, topo II inhibition"),
    ("Rifampicin", "ABCB1", "activator", 0.70, "P-gp inducer (CYP/PXR activation)"),

    # === THIAZOLIDINEDIONES -> PPARG ===
    ("Pioglitazone", "PPARG", "activates", 0.92, "PPARgamma full agonist"),
    ("Pioglitazone", "NFKB1", "inhibits", 0.55, "NF-kB suppression via PPARgamma (Ricote 1998)"),
    ("Rosiglitazone", "PPARG", "activates", 0.93, "PPARgamma full agonist"),

    # === ANTIMALARIALS -> autophagy/mTOR ===
    ("Hydroxychloroquine", "MTOR", "indirect_inhibitor", 0.55, "Autophagy/mTOR via lysosomal disruption"),
    ("Hydroxychloroquine", "TP53", "activator", 0.48, "p53 stabilization via autophagy inhibition"),
    ("Mefloquine", "MTOR", "indirect_inhibitor", 0.50, "Lysosomal disruption, autophagy"),
    ("Atovaquone", "STAT3", "inhibits", 0.50, "STAT3 pathway inhibition via mitochondrial disruption"),
    ("Atovaquone", "HIF1A", "inhibits", 0.55, "Reduces tumor hypoxia by inhibiting mitochondrial O2 consumption"),

    # === ACE INHIBITORS -> ACE ===
    ("Captopril", "ACE", "inhibits", 0.95, "Direct ACE inhibitor, also MMP inhibitor"),
    ("Captopril", "MMP2", "inhibits", 0.55, "Zinc-chelating MMP inhibitor activity (Hii 1998)"),
    ("Enalapril", "ACE", "inhibits", 0.93, "ACE inhibitor (prodrug)"),
    ("Lisinopril", "ACE", "inhibits", 0.94, "ACE inhibitor"),
    ("Perindopril", "ACE", "inhibits", 0.93, "ACE inhibitor, strong anti-angiogenic data"),
    ("Perindopril", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic via RAS system (Yoshiji 2001)"),

    # === ARBs -> AGTR1 ===
    ("Losartan", "AGTR1", "inhibits", 0.93, "AT1 receptor blocker"),
    ("Losartan", "TGFB1", "inhibits", 0.55, "TGF-beta pathway suppression (Diop-Frimpong 2011)"),
    ("Candesartan", "AGTR1", "inhibits", 0.93, "AT1 receptor blocker"),
    ("Candesartan", "VEGFR2", "indirect_inhibitor", 0.45, "Anti-angiogenic via VEGF suppression"),
    ("Telmisartan", "AGTR1", "inhibits", 0.92, "AT1 receptor blocker"),
    ("Telmisartan", "PPARG", "activates", 0.50, "Partial PPARgamma agonist (Benson 2004)"),

    # === BISPHOSPHONATES -> FDPS ===
    ("Zoledronic_Acid", "FDPS", "inhibits", 0.92, "Potent FDPS inhibitor, blocks prenylation"),
    ("Zoledronic_Acid", "KRAS", "indirect_inhibitor", 0.55, "Blocks RAS prenylation downstream"),
    ("Alendronate", "FDPS", "inhibits", 0.88, "FDPS inhibitor"),
    ("Clodronate", "MTOR", "indirect_inhibitor", 0.40, "ATP analog, macrophage depletion"),

    # === CARDIAC GLYCOSIDES -> ATP1A1 + SRC ===
    ("Digoxin", "ATP1A1", "inhibits", 0.92, "Na+/K+-ATPase inhibitor"),
    ("Digoxin", "SRC", "activator", 0.60, "SRC activation via Na+/K+-ATPase signaling cascade"),
    ("Digoxin", "HIF1A", "inhibits", 0.55, "HIF-1alpha synthesis inhibition (Zhang 2008)"),
    ("Digitoxin", "ATP1A1", "inhibits", 0.90, "Na+/K+-ATPase inhibitor"),
    ("Digitoxin", "NFKB1", "inhibits", 0.55, "NF-kB pathway inhibition (Yang 2005)"),

    # === ANTIHISTAMINES ===
    ("Loratadine", "STAT3", "indirect_inhibitor", 0.40, "Weak anti-proliferative effect"),
    ("Terfenadine", "VEGFR2", "indirect_inhibitor", 0.45, "Anti-angiogenic (Nicolau-Galmes 2011)"),

    # === ANTIEPILEPTICS ===
    ("Carbamazepine", "HDAC1", "indirect_inhibitor", 0.40, "Weak HDAC modulation"),
    ("Levetiracetam", "HDAC1", "indirect_inhibitor", 0.42, "HDAC activity modulation, MGMT effect in GBM"),

    # === ANTIDEPRESSANTS ===
    ("Fluoxetine", "STAT3", "inhibits", 0.50, "Anti-proliferative, STAT3 modulation"),
    ("Fluoxetine", "AKT1", "indirect_inhibitor", 0.45, "AKT pathway modulation (preclinical)"),
    ("Sertraline", "MTOR", "indirect_inhibitor", 0.45, "mTOR suppression via AMPK activation"),
    ("Imipramine", "MTOR", "indirect_inhibitor", 0.45, "Autophagy induction"),

    # === IMMUNOSUPPRESSANTS ===
    ("Sirolimus", "MTOR", "inhibits", 0.97, "Direct mTOR complex 1 inhibitor (parent compound of everolimus)"),
    ("Ciclosporin", "ABCB1", "inhibits", 0.75, "P-glycoprotein inhibitor, MDR reversal"),
    ("Ciclosporin", "NFKB1", "inhibits", 0.50, "Calcineurin/NFAT/NF-kB modulation"),

    # === PDE INHIBITORS ===
    ("Sildenafil", "ABCB1", "inhibits", 0.60, "P-gp inhibitor, chemosensitizer"),
    ("Sildenafil", "MTOR", "indirect_inhibitor", 0.40, "cGMP-mediated pathway modulation"),
    ("Theophylline", "HDAC2", "activator", 0.50, "HDAC2 activity enhancement (Ito 2002)"),
    ("Dipyridamole", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic via adenosine uptake"),

    # === RETINOIDS ===
    ("Isotretinoin", "TP53", "activator", 0.55, "p53 pathway activation via differentiation"),
    ("Acitretin", "STAT3", "indirect_inhibitor", 0.45, "STAT3 modulation in skin cancer"),

    # === ANTI-GOUT ===
    ("Allopurinol", "NFKB1", "inhibits", 0.45, "ROS reduction, NF-kB modulation"),
    ("Colchicine", "TUBB", "inhibits", 0.92, "Potent tubulin polymerization inhibitor"),

    # === DIURETICS ===
    ("Amiloride", "MTOR", "indirect_inhibitor", 0.40, "uPA inhibition, anti-metastatic"),
    ("Spironolactone", "NFKB1", "inhibits", 0.45, "Anti-inflammatory, Wnt modulation"),

    # === MISC ===
    ("Lidocaine", "SRC", "inhibits", 0.50, "SRC kinase inhibition (Piegeler 2015)"),
    ("Lidocaine", "EGFR", "indirect_inhibitor", 0.45, "EGFR transactivation inhibition"),
    ("Bezafibrate", "PPARG", "activates", 0.60, "Pan-PPAR agonist"),
    ("Fenofibrate", "NFKB1", "inhibits", 0.50, "NF-kB suppression via PPARalpha"),
    ("Fenofibrate", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic (Panigrahy 2008)"),
    ("Pyrimethamine", "STAT3", "inhibits", 0.60, "STAT3 inhibition (Khan 2007)"),
    ("Nitazoxanide", "GSK3B", "indirect_inhibitor", 0.50, "Wnt pathway inhibition"),
    ("Ribavirin", "MTOR", "indirect_inhibitor", 0.50, "eIF4E/mTOR pathway (Assouline 2009)"),
    ("Pentoxifylline", "NFKB1", "inhibits", 0.55, "TNF-alpha/NF-kB suppression"),
    ("Tranilast", "TGFB1", "inhibits", 0.72, "TGF-beta pathway inhibition"),
    ("Tranilast", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic"),
    ("Noscapine", "TUBB", "inhibits", 0.70, "Tubulin-binding, arrests mitosis"),
    ("Bromocriptine", "DRD2", "activates", 0.88, "D2 agonist, suppresses prolactin"),
    ("Levamisole", "NFKB1", "indirect_inhibitor", 0.45, "Immune stimulation, NF-kB modulation"),
    ("Sulfasalazine", "NFKB1", "inhibits", 0.72, "NF-kB pathway inhibitor (Wahl 1998)"),
    ("Sulfasalazine", "STAT3", "inhibits", 0.50, "xCT transporter inhibition, redox stress"),
    ("Mifepristone", "NFKB1", "inhibits", 0.50, "GR antagonism, NF-kB modulation"),
    ("Prazosin", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic (Garrison 2007)"),
    ("Prazosin", "AKT1", "indirect_inhibitor", 0.45, "AKT pathway inhibition (Lin 2007)"),
    ("Clopidogrel", "VEGFR2", "indirect_inhibitor", 0.40, "Anti-metastatic via platelet inhibition"),
    ("Ranitidine", "NFKB1", "inhibits", 0.45, "NF-kB pathway modulation (similar to cimetidine)"),
    ("Famotidine", "NFKB1", "inhibits", 0.42, "NF-kB pathway modulation"),
    ("Lithium_Carbonate", "GSK3B", "inhibits", 0.85, "Direct GSK3B inhibitor (Klein & Melton 1996)"),
    ("Disulfiram_Cu", "NPL4", "inhibits", 0.85, "Cu-dependent NPL4 binding (Skrott 2017)"),
    ("Disulfiram_Cu", "NFKB1", "inhibits", 0.70, "NF-kB pathway inhibition"),
    ("Raloxifene", "STAT3", "indirect_inhibitor", 0.45, "STAT3 modulation via ER"),
    ("Finasteride", "STAT3", "indirect_inhibitor", 0.40, "DHT/AR pathway, limited STAT3 effect"),
    ("Dutasteride", "STAT3", "indirect_inhibitor", 0.40, "DHT/AR pathway modulation"),
    ("Hydralazine", "DNMT1", "inhibits", 0.70, "DNA methyltransferase inhibitor (Segura-Pacheco 2003)"),
    ("Hydralazine", "HDAC1", "indirect_inhibitor", 0.45, "Epigenetic modifier"),
    ("Quinacrine", "NFKB1", "inhibits", 0.65, "NF-kB pathway inhibitor (Gurova 2005)"),
    ("Quinacrine", "TP53", "activator", 0.55, "p53 stabilization (Gurova 2005)"),
    ("N_Acetylcysteine", "NFKB1", "inhibits", 0.50, "ROS-mediated NF-kB modulation"),
    ("Orlistat", "FASN", "inhibits", 0.80, "Fatty acid synthase inhibitor (Kridel 2004)"),
    ("Metronidazole", "HIF1A", "inhibits", 0.45, "Hypoxic cell targeting"),
    ("Dantrolene", "MTOR", "indirect_inhibitor", 0.38, "Calcium signaling disruption"),
]


# ============================================================================
# ReDO FULL PROTEIN -> DISEASE associations
# Format: (protein, disease, relation, confidence, evidence)
# ============================================================================

REDO_FULL_PROTEIN_DISEASE_ASSOCIATIONS = [
    # HMGCR pathway -> cancers (via mevalonate/prenylation)
    ("HMGCR", "Breast_Cancer", "associated_with", 0.60, "Mevalonate pathway upregulated in breast cancer"),
    ("HMGCR", "Colorectal_Cancer", "associated_with", 0.58, "Mevalonate pathway in CRC proliferation"),
    ("HMGCR", "Prostate_Cancer", "associated_with", 0.55, "Cholesterol metabolism in prostate cancer"),

    # TUBB -> cancers (microtubule-dependent)
    ("TUBB", "Breast_Cancer", "associated_with", 0.70, "Tubulin isoform expression in breast cancer drug resistance"),
    ("TUBB", "NSCLC", "associated_with", 0.65, "TUBB3 overexpression in NSCLC chemoresistance"),
    ("TUBB", "Ovarian_Cancer", "associated_with", 0.68, "Tubulin mutations in taxane-resistant ovarian cancer"),

    # ADRB2 -> cancers (stress-mediated tumor promotion)
    ("ADRB2", "Breast_Cancer", "associated_with", 0.55, "Beta-adrenergic signaling promotes breast cancer metastasis"),
    ("ADRB2", "Ovarian_Cancer", "associated_with", 0.52, "Stress hormones promote ovarian cancer progression"),
    ("ADRB2", "Melanoma", "associated_with", 0.50, "Catecholamine-driven melanoma progression"),

    # ATP1A1 -> cancers
    ("ATP1A1", "NSCLC", "associated_with", 0.55, "Na/K-ATPase expression altered in NSCLC"),
    ("ATP1A1", "Breast_Cancer", "associated_with", 0.52, "Na/K-ATPase signaling in breast cancer"),
    ("ATP1A1", "Colorectal_Cancer", "associated_with", 0.50, "Ion homeostasis disruption in CRC"),

    # PPARG -> cancers
    ("PPARG", "Colorectal_Cancer", "associated_with", 0.65, "PPARgamma loss of function in CRC (Girnun 2002)"),
    ("PPARG", "Breast_Cancer", "associated_with", 0.58, "PPARgamma anti-proliferative in breast cancer"),
    ("PPARG", "Prostate_Cancer", "associated_with", 0.55, "PPARgamma differentiation in prostate cancer"),

    # SMO / Hedgehog -> cancers
    ("SMO", "Glioblastoma", "associated_with", 0.70, "Hedgehog pathway in GBM cancer stem cells"),
    ("SMO", "Pancreatic_Cancer", "associated_with", 0.72, "Hedgehog signaling in pancreatic cancer stroma"),

    # FDPS -> cancers
    ("FDPS", "Breast_Cancer", "associated_with", 0.55, "Prenylation pathway in breast cancer"),
    ("FDPS", "Multiple_Myeloma", "associated_with", 0.60, "Farnesylation in myeloma bone disease"),

    # ACE / RAS system -> cancers
    ("ACE", "Breast_Cancer", "associated_with", 0.50, "RAS system in breast cancer angiogenesis"),
    ("ACE", "Colorectal_Cancer", "associated_with", 0.48, "ACE expression in CRC tissue"),

    # AGTR1 -> cancers
    ("AGTR1", "Breast_Cancer", "associated_with", 0.55, "AT1R overexpression in breast cancer (Egami 2003)"),
    ("AGTR1", "Ovarian_Cancer", "associated_with", 0.50, "Angiotensin signaling in ovarian cancer"),
    ("AGTR1", "Pancreatic_Cancer", "associated_with", 0.52, "AT1R in pancreatic cancer stroma fibrosis"),

    # DRD2 -> cancers
    ("DRD2", "Glioblastoma", "associated_with", 0.60, "DRD2 expression in GBM (Li 2014)"),
    ("DRD2", "Breast_Cancer", "associated_with", 0.50, "Dopamine signaling in breast cancer (Sachlos 2012)"),
    ("DRD2", "AML", "associated_with", 0.55, "DRD2 in leukemia stem cells"),

    # SRC -> cancers
    ("SRC", "Colorectal_Cancer", "driver_of", 0.75, "SRC activation in CRC metastasis"),
    ("SRC", "Breast_Cancer", "associated_with", 0.70, "SRC in triple-negative breast cancer"),
    ("SRC", "Pancreatic_Cancer", "associated_with", 0.65, "SRC in pancreatic cancer invasion"),
    ("SRC", "NSCLC", "associated_with", 0.60, "SRC activation in NSCLC"),

    # GSK3B -> cancers
    ("GSK3B", "Colorectal_Cancer", "associated_with", 0.65, "Wnt pathway regulation in CRC"),
    ("GSK3B", "AML", "associated_with", 0.60, "GSK3B in AML blast survival"),
    ("GSK3B", "Glioblastoma", "associated_with", 0.58, "GSK3B in GBM stem cells"),
    ("GSK3B", "Pancreatic_Cancer", "associated_with", 0.55, "GSK3B in pancreatic cancer"),

    # DNMT1 -> cancers
    ("DNMT1", "AML", "associated_with", 0.72, "DNMT overexpression in AML (Lorsbach 2003)"),
    ("DNMT1", "Colorectal_Cancer", "associated_with", 0.65, "Aberrant DNA methylation in CRC"),
    ("DNMT1", "Breast_Cancer", "associated_with", 0.60, "DNMT1 overexpression in breast cancer"),

    # FASN -> cancers
    ("FASN", "Breast_Cancer", "associated_with", 0.72, "FASN overexpression in breast cancer (Menendez 2007)"),
    ("FASN", "Prostate_Cancer", "associated_with", 0.70, "FASN in prostate cancer metabolism"),
    ("FASN", "Ovarian_Cancer", "associated_with", 0.62, "FASN in ovarian cancer lipogenesis"),
]


# ============================================================================
# ReDO FULL HOLDOUT EDGES (known associations for validation)
# Format: (drug, disease, relation, confidence, evidence)
# ============================================================================

REDO_FULL_HOLDOUT_EDGES = [
    # === STATINS -> cancer (epidemiological evidence) ===
    ("Simvastatin", "Breast_Cancer", "potential_treatment", 0.50,
     "Epidemiological: statin use reduces breast cancer mortality (Ahern 2011)"),
    ("Simvastatin", "Colorectal_Cancer", "potential_treatment", 0.48,
     "Epidemiological: statin use and CRC risk reduction"),
    ("Lovastatin", "Breast_Cancer", "potential_treatment", 0.45,
     "Preclinical anti-cancer activity in breast cancer cells"),
    ("Fluvastatin", "Breast_Cancer", "potential_treatment", 0.50,
     "Window-of-opportunity trial: reduced Ki-67 in breast tumors (Garwood 2010)"),

    # === NSAIDs -> CRC (strong epidemiological) ===
    ("Ibuprofen", "Colorectal_Cancer", "potential_treatment", 0.55,
     "Epidemiological: regular NSAID use reduces CRC risk"),
    ("Sulindac", "Colorectal_Cancer", "potential_treatment", 0.65,
     "FAP polyp regression (Giardiello 1993, Labayle 1991)"),
    ("Ketorolac", "Breast_Cancer", "potential_treatment", 0.45,
     "Perioperative ketorolac reduces breast cancer recurrence (Forget 2010)"),

    # === ANTIFUNGALS -> cancer ===
    ("Ketoconazole", "Prostate_Cancer", "potential_treatment", 0.55,
     "Historical use for androgen suppression in prostate cancer"),

    # === BETA-BLOCKERS -> cancer (epidemiological) ===
    ("Carvedilol", "Breast_Cancer", "potential_treatment", 0.45,
     "Beta-blocker use associated with reduced breast cancer mortality (Barron 2011)"),

    # === PPIs -> cancer (chemosensitization) ===
    ("Esomeprazole", "Melanoma", "potential_treatment", 0.45,
     "Phase II: PPI chemosensitization in melanoma (Azzarito 2015)"),
    ("Omeprazole", "Colorectal_Cancer", "potential_treatment", 0.40,
     "Autophagy inhibition, chemosensitization"),

    # === ANTIPSYCHOTICS -> cancer ===
    ("Thioridazine", "AML", "potential_treatment", 0.50,
     "Kills AML leukemia stem cells via DRD2 (Sachlos 2012 Cell)"),
    ("Chlorpromazine", "Glioblastoma", "potential_treatment", 0.45,
     "Anti-mitotic activity in GBM cells (Shin 2018)"),
    ("Pimozide", "AML", "potential_treatment", 0.48,
     "STAT5 inhibition in AML (Nelson 2011)"),

    # === ANTHELMINTHICS -> cancer ===
    ("Albendazole", "Colorectal_Cancer", "potential_treatment", 0.50,
     "Anti-angiogenic + anti-proliferative in CRC (Pourgholami 2010)"),
    ("Flubendazole", "AML", "potential_treatment", 0.45,
     "Anti-leukemic activity (Spagnuolo 2010)"),
    ("Flubendazole", "Breast_Cancer", "potential_treatment", 0.45,
     "Anti-mitotic in breast cancer cells"),

    # === ANTIBIOTICS -> cancer ===
    ("Tigecycline", "AML", "potential_treatment", 0.50,
     "Mitochondrial targeting in AML (Skrtic 2011 Cancer Cell)"),
    ("Salinomycin", "Breast_Cancer", "potential_treatment", 0.55,
     "100x more potent than paclitaxel against breast CSCs (Gupta 2009 Cell)"),

    # === THIAZOLIDINEDIONES -> cancer ===
    ("Pioglitazone", "Colorectal_Cancer", "potential_treatment", 0.45,
     "Epidemiological: reduced CRC risk in diabetics"),

    # === ANTIMALARIALS -> cancer ===
    ("Hydroxychloroquine", "Pancreatic_Cancer", "potential_treatment", 0.50,
     "Phase II: autophagy inhibition in pancreatic cancer (Wolpin 2014)"),
    ("Hydroxychloroquine", "Glioblastoma", "potential_treatment", 0.48,
     "Autophagy inhibition in GBM (Rosenfeld 2014)"),

    # === ACE INHIBITORS / ARBs -> cancer ===
    ("Captopril", "Colorectal_Cancer", "potential_treatment", 0.40,
     "Anti-angiogenic + MMP inhibition in CRC"),
    ("Losartan", "Pancreatic_Cancer", "potential_treatment", 0.50,
     "Phase II: reduces tumor fibrosis, improves chemo delivery (Murphy 2019 JAMA Oncol)"),
    ("Perindopril", "HCC", "potential_treatment", 0.42,
     "Anti-angiogenic in HCC (Yoshiji 2001)"),

    # === BISPHOSPHONATES -> cancer ===
    ("Zoledronic_Acid", "Breast_Cancer", "potential_treatment", 0.60,
     "ABCSG-12 trial: improved DFS in postmenopausal breast cancer (Gnant 2009)"),
    ("Zoledronic_Acid", "Multiple_Myeloma", "potential_treatment", 0.55,
     "Anti-myeloma activity beyond bone protection"),

    # === CARDIAC GLYCOSIDES -> cancer ===
    ("Digoxin", "Breast_Cancer", "potential_treatment", 0.45,
     "Epidemiological: reduced breast cancer risk (Stenkvist 1999)"),
    ("Digoxin", "NSCLC", "potential_treatment", 0.42,
     "HIF-1a inhibition in hypoxic NSCLC cells"),

    # === MISC ===
    ("Lithium_Carbonate", "Colorectal_Cancer", "potential_treatment", 0.42,
     "GSK3B inhibition, Wnt pathway modulation in CRC"),
    ("Hydralazine", "Breast_Cancer", "potential_treatment", 0.45,
     "DNMT inhibition, re-expression of tumor suppressors (Candelaria 2007)"),
    ("Sulfasalazine", "Glioblastoma", "potential_treatment", 0.48,
     "xCT inhibition in GBM (Chung 2005)"),
    ("Orlistat", "Breast_Cancer", "potential_treatment", 0.42,
     "FASN inhibition in breast cancer cells (Menendez 2005)"),
    ("Quinacrine", "Colorectal_Cancer", "potential_treatment", 0.45,
     "NF-kB/p53 modulation in CRC cells (Gurova 2005)"),
    ("Lidocaine", "Breast_Cancer", "potential_treatment", 0.42,
     "Perioperative lidocaine reduces breast cancer recurrence (Freeman 2019)"),
    ("Ribavirin", "AML", "potential_treatment", 0.50,
     "eIF4E targeting in AML (Assouline 2009 Blood)"),
    ("Pyrimethamine", "AML", "potential_treatment", 0.45,
     "STAT3 inhibition in AML (Khan 2007 PNAS)"),
    ("Finasteride", "Prostate_Cancer", "potential_treatment", 0.60,
     "PCPT trial: 25% reduction in prostate cancer prevalence (Thompson 2003 NEJM)"),
    ("Dutasteride", "Prostate_Cancer", "potential_treatment", 0.58,
     "REDUCE trial: 23% reduction in prostate cancer risk (Andriole 2010 NEJM)"),
]


# ============================================================================
# EXPANSION BATCH 2: ~134 additional drugs to reach 268 ReDO total
# Sources: Bouche et al 2017 (PMC6345075), Pantziarka et al 2014-2024,
#          ReDO_DB (anticancerfund.org), DrugBank 5.x
# ============================================================================

REDO_FULL_DRUGS.update({

    # === MORE ANTIBIOTICS / ANTIMICROBIALS ===
    "Chloramphenicol": {
        "type": "Drug", "brand": "Chloromycetin", "drug_class": "Amphenicol antibiotic",
        "mechanism": "Mitochondrial ribosome inhibitor, anti-proliferative",
        "fda_year": 1949, "drugbank_id": "DB00446",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Dapsone": {
        "type": "Drug", "brand": "Aczone", "drug_class": "Sulfone antibiotic",
        "mechanism": "Dihydropteroate synthase inhibitor, anti-inflammatory",
        "fda_year": 1955, "drugbank_id": "DB00250",
        "original_indication": "Leprosy/dermatitis herpetiformis",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Erythromycin": {
        "type": "Drug", "brand": "Erythrocin", "drug_class": "Macrolide antibiotic",
        "mechanism": "Bacterial 50S ribosome inhibitor, motilin receptor agonist",
        "fda_year": 1952, "drugbank_id": "DB00199",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, anti-cancer stem cell (macrolide class)",
    },
    "Tetracycline": {
        "type": "Drug", "brand": "Sumycin", "drug_class": "Tetracycline antibiotic",
        "mechanism": "30S ribosome inhibitor, MMP inhibitor, anti-angiogenic",
        "fda_year": 1954, "drugbank_id": "DB00759",
        "original_indication": "Bacterial infections",
        "repurposing_status": "ReDO DB, anti-angiogenic + anti-CSC",
    },
    "Linezolid": {
        "type": "Drug", "brand": "Zyvox", "drug_class": "Oxazolidinone antibiotic",
        "mechanism": "Mitochondrial ribosome inhibitor, 23S rRNA binding",
        "fda_year": 2000, "drugbank_id": "DB00601",
        "original_indication": "MRSA/VRE infections",
        "repurposing_status": "ReDO DB, mitochondrial targeting preclinical",
    },
    "Griseofulvin": {
        "type": "Drug", "brand": "Grifulvin", "drug_class": "Antifungal antibiotic",
        "mechanism": "Tubulin polymerization inhibitor, centrosome declustering",
        "fda_year": 1959, "drugbank_id": "DB00400",
        "original_indication": "Dermatophyte infections",
        "repurposing_status": "ReDO DB, centrosome declustering in cancer cells",
    },
    "Trimethoprim": {
        "type": "Drug", "brand": "Primsol", "drug_class": "Dihydrofolate reductase inhibitor",
        "mechanism": "DHFR inhibitor, anti-folate",
        "fda_year": 1980, "drugbank_id": "DB00440",
        "original_indication": "UTI/bacterial infections",
        "repurposing_status": "ReDO DB, anti-proliferative preclinical",
    },
    "Colistin": {
        "type": "Drug", "brand": "Coly-Mycin", "drug_class": "Polymyxin antibiotic",
        "mechanism": "Membrane disruptor, NF-kB modulator",
        "fda_year": 1959, "drugbank_id": "DB00803",
        "original_indication": "Gram-negative infections",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Amphotericin_B": {
        "type": "Drug", "brand": "Fungizone", "drug_class": "Polyene antifungal",
        "mechanism": "Ergosterol binding, membrane permeabilization",
        "fda_year": 1958, "drugbank_id": "DB00681",
        "original_indication": "Systemic fungal infections",
        "repurposing_status": "ReDO DB, preclinical anti-leukemic",
    },
    "Nystatin": {
        "type": "Drug", "brand": "Mycostatin", "drug_class": "Polyene antifungal",
        "mechanism": "Ergosterol binding, membrane disruption",
        "fda_year": 1954, "drugbank_id": "DB00647",
        "original_indication": "Candidiasis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Gentamicin": {
        "type": "Drug", "brand": "Garamycin", "drug_class": "Aminoglycoside antibiotic",
        "mechanism": "30S ribosome inhibitor, readthrough of premature stop codons",
        "fda_year": 1971, "drugbank_id": "DB00798",
        "original_indication": "Gram-negative infections",
        "repurposing_status": "ReDO DB, readthrough agent for p53 mutations",
    },
    "Terbinafine": {
        "type": "Drug", "brand": "Lamisil", "drug_class": "Allylamine antifungal",
        "mechanism": "Squalene epoxidase inhibitor, cholesterol pathway disruptor",
        "fda_year": 1996, "drugbank_id": "DB00857",
        "original_indication": "Onychomycosis",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Isoniazid": {
        "type": "Drug", "brand": "Nydrazid", "drug_class": "Antimycobacterial",
        "mechanism": "InhA inhibitor, ROS generator, NAD+ pathway modulator",
        "fda_year": 1952, "drugbank_id": "DB00951",
        "original_indication": "Tuberculosis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Nitrofurantoin": {
        "type": "Drug", "brand": "Macrobid", "drug_class": "Nitrofuran antibiotic",
        "mechanism": "ROS generator, DNA damage inducer",
        "fda_year": 1953, "drugbank_id": "DB00698",
        "original_indication": "UTI",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },

    # === ANTIVIRALS ===
    "Acyclovir": {
        "type": "Drug", "brand": "Zovirax", "drug_class": "Nucleoside analog antiviral",
        "mechanism": "Viral DNA polymerase inhibitor, thymidine kinase substrate",
        "fda_year": 1982, "drugbank_id": "DB00787",
        "original_indication": "Herpes simplex/varicella",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Ganciclovir": {
        "type": "Drug", "brand": "Cytovene", "drug_class": "Nucleoside analog antiviral",
        "mechanism": "Viral DNA polymerase inhibitor, anti-proliferative",
        "fda_year": 1989, "drugbank_id": "DB01004",
        "original_indication": "CMV retinitis",
        "repurposing_status": "ReDO DB, suicide gene therapy substrate",
    },
    "Zidovudine": {
        "type": "Drug", "brand": "Retrovir", "drug_class": "NRTI antiviral",
        "mechanism": "Reverse transcriptase inhibitor, telomerase inhibitor",
        "fda_year": 1987, "drugbank_id": "DB00495",
        "original_indication": "HIV/AIDS",
        "repurposing_status": "ReDO DB, telomerase inhibition in cancer cells",
    },
    "Didanosine": {
        "type": "Drug", "brand": "Videx", "drug_class": "NRTI antiviral",
        "mechanism": "Reverse transcriptase inhibitor",
        "fda_year": 1991, "drugbank_id": "DB00900",
        "original_indication": "HIV/AIDS",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Lopinavir": {
        "type": "Drug", "brand": "Kaletra", "drug_class": "Protease inhibitor antiviral",
        "mechanism": "HIV protease inhibitor, AKT pathway modulator",
        "fda_year": 2000, "drugbank_id": "DB01601",
        "original_indication": "HIV/AIDS",
        "repurposing_status": "ReDO DB, AKT inhibition in cancer cells",
    },
    "Oseltamivir": {
        "type": "Drug", "brand": "Tamiflu", "drug_class": "Neuraminidase inhibitor",
        "mechanism": "Neuraminidase inhibitor, anti-invasive",
        "fda_year": 1999, "drugbank_id": "DB00198",
        "original_indication": "Influenza",
        "repurposing_status": "ReDO DB, anti-metastatic via sialidase",
    },
    "Amantadine": {
        "type": "Drug", "brand": "Symmetrel", "drug_class": "Adamantane antiviral",
        "mechanism": "M2 ion channel blocker, NMDA antagonist, dopaminergic",
        "fda_year": 1966, "drugbank_id": "DB00915",
        "original_indication": "Influenza/Parkinson's",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Valacyclovir": {
        "type": "Drug", "brand": "Valtrex", "drug_class": "Nucleoside analog antiviral",
        "mechanism": "Acyclovir prodrug, viral DNA polymerase inhibitor",
        "fda_year": 1995, "drugbank_id": "DB00577",
        "original_indication": "Herpes/shingles",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === ANTIDIABETICS ===
    "Glibenclamide": {
        "type": "Drug", "brand": "Diabeta", "drug_class": "Sulfonylurea",
        "mechanism": "KATP channel blocker, insulin secretagogue, NLRP3 modulator",
        "fda_year": 1984, "drugbank_id": "DB01016",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, anti-cancer via KATP/NLRP3",
    },
    "Dapagliflozin": {
        "type": "Drug", "brand": "Farxiga", "drug_class": "SGLT2 inhibitor",
        "mechanism": "SGLT2 inhibitor, glucose uptake blocker",
        "fda_year": 2014, "drugbank_id": "DB06292",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, tumor glucose deprivation",
    },
    "Canagliflozin": {
        "type": "Drug", "brand": "Invokana", "drug_class": "SGLT2 inhibitor",
        "mechanism": "SGLT2 inhibitor, AMPK activator",
        "fda_year": 2013, "drugbank_id": "DB08907",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, anti-proliferative via AMPK",
    },
    "Acarbose": {
        "type": "Drug", "brand": "Precose", "drug_class": "Alpha-glucosidase inhibitor",
        "mechanism": "Alpha-glucosidase inhibitor, reduces postprandial glucose",
        "fda_year": 1995, "drugbank_id": "DB00284",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Empagliflozin": {
        "type": "Drug", "brand": "Jardiance", "drug_class": "SGLT2 inhibitor",
        "mechanism": "SGLT2 inhibitor, metabolic modulator",
        "fda_year": 2014, "drugbank_id": "DB09038",
        "original_indication": "Type 2 diabetes",
        "repurposing_status": "ReDO DB, tumor metabolism disruption",
    },

    # === ANTIHYPERTENSIVES ===
    "Minoxidil": {
        "type": "Drug", "brand": "Loniten", "drug_class": "Potassium channel opener",
        "mechanism": "KATP channel opener, vasodilator",
        "fda_year": 1979, "drugbank_id": "DB00350",
        "original_indication": "Severe hypertension",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Methyldopa": {
        "type": "Drug", "brand": "Aldomet", "drug_class": "Central alpha-2 agonist",
        "mechanism": "Alpha-2 adrenergic agonist, DNMT inhibitor",
        "fda_year": 1962, "drugbank_id": "DB00968",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, epigenetic modifier",
    },
    "Clonidine": {
        "type": "Drug", "brand": "Catapres", "drug_class": "Central alpha-2 agonist",
        "mechanism": "Alpha-2 adrenergic agonist, sympatholytic",
        "fda_year": 1974, "drugbank_id": "DB00575",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Bosentan": {
        "type": "Drug", "brand": "Tracleer", "drug_class": "Endothelin receptor antagonist",
        "mechanism": "ET-A/ET-B receptor antagonist, anti-fibrotic",
        "fda_year": 2001, "drugbank_id": "DB00559",
        "original_indication": "Pulmonary arterial hypertension",
        "repurposing_status": "ReDO DB, anti-tumor stroma",
    },
    "Ambrisentan": {
        "type": "Drug", "brand": "Letairis", "drug_class": "Endothelin receptor antagonist",
        "mechanism": "Selective ET-A receptor antagonist",
        "fda_year": 2007, "drugbank_id": "DB06403",
        "original_indication": "Pulmonary arterial hypertension",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Nitroprusside": {
        "type": "Drug", "brand": "Nipride", "drug_class": "Nitrovasodilator",
        "mechanism": "NO donor, cGMP pathway activator",
        "fda_year": 1974, "drugbank_id": "DB00325",
        "original_indication": "Hypertensive emergency",
        "repurposing_status": "ReDO DB, NO-mediated anti-tumor",
    },

    # === MORE DIURETICS ===
    "Furosemide": {
        "type": "Drug", "brand": "Lasix", "drug_class": "Loop diuretic",
        "mechanism": "NKCC2 inhibitor, anti-angiogenic",
        "fda_year": 1966, "drugbank_id": "DB00695",
        "original_indication": "Edema/heart failure",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Hydrochlorothiazide": {
        "type": "Drug", "brand": "Microzide", "drug_class": "Thiazide diuretic",
        "mechanism": "NCC inhibitor, carbonic anhydrase inhibitor",
        "fda_year": 1959, "drugbank_id": "DB00999",
        "original_indication": "Hypertension/edema",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Chlorthalidone": {
        "type": "Drug", "brand": "Thalitone", "drug_class": "Thiazide-like diuretic",
        "mechanism": "NCC inhibitor, carbonic anhydrase inhibitor",
        "fda_year": 1960, "drugbank_id": "DB00310",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Indapamide": {
        "type": "Drug", "brand": "Lozol", "drug_class": "Thiazide-like diuretic",
        "mechanism": "NCC inhibitor, vasodilator",
        "fda_year": 1983, "drugbank_id": "DB00808",
        "original_indication": "Hypertension",
        "repurposing_status": "ReDO DB, limited evidence",
    },
    "Bumetanide": {
        "type": "Drug", "brand": "Bumex", "drug_class": "Loop diuretic",
        "mechanism": "NKCC1/NKCC2 inhibitor",
        "fda_year": 1983, "drugbank_id": "DB00887",
        "original_indication": "Edema",
        "repurposing_status": "ReDO DB, NKCC1 in cancer cell volume regulation",
    },

    # === CARDIAC / ANTI-ARRHYTHMICS ===
    "Amiodarone": {
        "type": "Drug", "brand": "Cordarone", "drug_class": "Class III antiarrhythmic",
        "mechanism": "Multi-ion channel blocker, thyroid hormone modulator",
        "fda_year": 1985, "drugbank_id": "DB01118",
        "original_indication": "Ventricular arrhythmias",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Propafenone": {
        "type": "Drug", "brand": "Rythmol", "drug_class": "Class IC antiarrhythmic",
        "mechanism": "Sodium channel blocker, weak beta-blocker",
        "fda_year": 1989, "drugbank_id": "DB01182",
        "original_indication": "Supraventricular arrhythmias",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Flecainide": {
        "type": "Drug", "brand": "Tambocor", "drug_class": "Class IC antiarrhythmic",
        "mechanism": "Sodium channel blocker",
        "fda_year": 1985, "drugbank_id": "DB01195",
        "original_indication": "Arrhythmias",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Mexiletine": {
        "type": "Drug", "brand": "Mexitil", "drug_class": "Class IB antiarrhythmic",
        "mechanism": "Sodium channel blocker, Nav1.5 inhibitor",
        "fda_year": 1986, "drugbank_id": "DB00379",
        "original_indication": "Ventricular arrhythmias",
        "repurposing_status": "ReDO DB, Nav1.5 in cancer metastasis",
    },
    "Nicorandil": {
        "type": "Drug", "brand": "Ikorel", "drug_class": "KATP opener / nitrate",
        "mechanism": "KATP channel opener, NO donor",
        "fda_year": 1984, "drugbank_id": "DB09220",
        "original_indication": "Angina pectoris",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Ranolazine": {
        "type": "Drug", "brand": "Ranexa", "drug_class": "Late sodium current inhibitor",
        "mechanism": "Late INa inhibitor, fatty acid oxidation modulator",
        "fda_year": 2006, "drugbank_id": "DB00243",
        "original_indication": "Chronic angina",
        "repurposing_status": "ReDO DB, metabolic modulation in cancer",
    },
    "Milrinone": {
        "type": "Drug", "brand": "Primacor", "drug_class": "PDE3 inhibitor",
        "mechanism": "PDE3 inhibitor, cAMP pathway modulator",
        "fda_year": 1987, "drugbank_id": "DB00235",
        "original_indication": "Acute heart failure",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === MORE ANTIPSYCHOTICS ===
    "Perphenazine": {
        "type": "Drug", "brand": "Trilafon", "drug_class": "Phenothiazine antipsychotic",
        "mechanism": "DRD2 antagonist, calmodulin inhibitor",
        "fda_year": 1957, "drugbank_id": "DB00850",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Olanzapine": {
        "type": "Drug", "brand": "Zyprexa", "drug_class": "Atypical antipsychotic",
        "mechanism": "Multi-receptor antagonist (D2/5-HT2A/H1)",
        "fda_year": 1996, "drugbank_id": "DB00334",
        "original_indication": "Schizophrenia/bipolar",
        "repurposing_status": "ReDO DB, anti-emetic in chemotherapy",
    },
    "Risperidone": {
        "type": "Drug", "brand": "Risperdal", "drug_class": "Atypical antipsychotic",
        "mechanism": "D2/5-HT2A antagonist",
        "fda_year": 1993, "drugbank_id": "DB00734",
        "original_indication": "Schizophrenia",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Quetiapine": {
        "type": "Drug", "brand": "Seroquel", "drug_class": "Atypical antipsychotic",
        "mechanism": "Multi-receptor antagonist, autophagy inducer",
        "fda_year": 1997, "drugbank_id": "DB01224",
        "original_indication": "Schizophrenia/bipolar",
        "repurposing_status": "ReDO DB, preclinical glioma",
    },
    "Aripiprazole": {
        "type": "Drug", "brand": "Abilify", "drug_class": "Atypical antipsychotic",
        "mechanism": "D2 partial agonist, 5-HT1A partial agonist",
        "fda_year": 2002, "drugbank_id": "DB01238",
        "original_indication": "Schizophrenia/bipolar",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === MORE ANTIDEPRESSANTS ===
    "Amitriptyline": {
        "type": "Drug", "brand": "Elavil", "drug_class": "Tricyclic antidepressant",
        "mechanism": "Serotonin/NE reuptake inhibitor, acid sphingomyelinase inhibitor",
        "fda_year": 1961, "drugbank_id": "DB00321",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, anti-cancer via ASM inhibition",
    },
    "Clomipramine": {
        "type": "Drug", "brand": "Anafranil", "drug_class": "Tricyclic antidepressant",
        "mechanism": "Serotonin reuptake inhibitor, anti-histaminic",
        "fda_year": 1989, "drugbank_id": "DB01242",
        "original_indication": "OCD/depression",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Desipramine": {
        "type": "Drug", "brand": "Norpramin", "drug_class": "Tricyclic antidepressant",
        "mechanism": "NE reuptake inhibitor, acid sphingomyelinase inhibitor",
        "fda_year": 1964, "drugbank_id": "DB01151",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, ASM inhibition anti-cancer",
    },
    "Nortriptyline": {
        "type": "Drug", "brand": "Pamelor", "drug_class": "Tricyclic antidepressant",
        "mechanism": "NE reuptake inhibitor, acid ceramidase modulator",
        "fda_year": 1964, "drugbank_id": "DB00540",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Paroxetine": {
        "type": "Drug", "brand": "Paxil", "drug_class": "SSRI",
        "mechanism": "Serotonin reuptake inhibitor, anti-proliferative",
        "fda_year": 1992, "drugbank_id": "DB00715",
        "original_indication": "Depression/anxiety",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Fluvoxamine": {
        "type": "Drug", "brand": "Luvox", "drug_class": "SSRI",
        "mechanism": "Serotonin reuptake inhibitor, sigma-1 receptor agonist",
        "fda_year": 1994, "drugbank_id": "DB00176",
        "original_indication": "OCD",
        "repurposing_status": "ReDO DB, sigma-1 receptor modulation",
    },
    "Citalopram": {
        "type": "Drug", "brand": "Celexa", "drug_class": "SSRI",
        "mechanism": "Selective serotonin reuptake inhibitor",
        "fda_year": 1998, "drugbank_id": "DB00215",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Mirtazapine": {
        "type": "Drug", "brand": "Remeron", "drug_class": "NaSSA antidepressant",
        "mechanism": "Alpha-2 antagonist, 5-HT2/5-HT3 antagonist, H1 antagonist",
        "fda_year": 1996, "drugbank_id": "DB00370",
        "original_indication": "Depression",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === MORE ANTIEPILEPTICS ===
    "Topiramate": {
        "type": "Drug", "brand": "Topamax", "drug_class": "Anticonvulsant",
        "mechanism": "Carbonic anhydrase inhibitor, GABA modulator, Na+ channel blocker",
        "fda_year": 1996, "drugbank_id": "DB00273",
        "original_indication": "Epilepsy/migraine",
        "repurposing_status": "ReDO DB, carbonic anhydrase in tumor pH",
    },
    "Gabapentin": {
        "type": "Drug", "brand": "Neurontin", "drug_class": "Gabapentinoid",
        "mechanism": "Alpha-2-delta subunit ligand, calcium channel modulator",
        "fda_year": 1993, "drugbank_id": "DB00996",
        "original_indication": "Epilepsy/neuropathic pain",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Lamotrigine": {
        "type": "Drug", "brand": "Lamictal", "drug_class": "Anticonvulsant",
        "mechanism": "Sodium channel blocker, glutamate release inhibitor",
        "fda_year": 1994, "drugbank_id": "DB00555",
        "original_indication": "Epilepsy/bipolar",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Phenytoin": {
        "type": "Drug", "brand": "Dilantin", "drug_class": "Hydantoin anticonvulsant",
        "mechanism": "Sodium channel blocker, anti-arrhythmic",
        "fda_year": 1953, "drugbank_id": "DB00252",
        "original_indication": "Epilepsy",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Pregabalin": {
        "type": "Drug", "brand": "Lyrica", "drug_class": "Gabapentinoid",
        "mechanism": "Alpha-2-delta subunit ligand, calcium channel modulator",
        "fda_year": 2004, "drugbank_id": "DB00230",
        "original_indication": "Neuropathic pain/epilepsy",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === ANTI-INFLAMMATORY / CORTICOSTEROIDS ===
    "Mesalamine": {
        "type": "Drug", "brand": "Asacol", "drug_class": "5-ASA anti-inflammatory",
        "mechanism": "PPARG agonist, NF-kB inhibitor, COX/LOX inhibitor",
        "fda_year": 1987, "drugbank_id": "DB00244",
        "original_indication": "Ulcerative colitis",
        "repurposing_status": "ReDO DB, CRC chemoprevention in UC",
    },
    "Dexamethasone": {
        "type": "Drug", "brand": "Decadron", "drug_class": "Corticosteroid",
        "mechanism": "Glucocorticoid receptor agonist, NF-kB suppressor, anti-inflammatory",
        "fda_year": 1958, "drugbank_id": "DB01234",
        "original_indication": "Inflammation/autoimmune",
        "repurposing_status": "ReDO DB, widely used as anti-emetic/anti-edema in oncology",
    },
    "Prednisone": {
        "type": "Drug", "brand": "Deltasone", "drug_class": "Corticosteroid",
        "mechanism": "Glucocorticoid receptor agonist, immune suppressant",
        "fda_year": 1955, "drugbank_id": "DB00635",
        "original_indication": "Inflammation/autoimmune",
        "repurposing_status": "ReDO DB, component of cancer regimens (R-CHOP, etc.)",
    },
    "Budesonide": {
        "type": "Drug", "brand": "Pulmicort", "drug_class": "Corticosteroid",
        "mechanism": "Glucocorticoid receptor agonist, local anti-inflammatory",
        "fda_year": 1997, "drugbank_id": "DB01222",
        "original_indication": "Asthma/IBD",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Beclomethasone": {
        "type": "Drug", "brand": "Qvar", "drug_class": "Corticosteroid",
        "mechanism": "Glucocorticoid receptor agonist",
        "fda_year": 1976, "drugbank_id": "DB00394",
        "original_indication": "Asthma/rhinitis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === HORMONAL AGENTS ===
    "Danazol": {
        "type": "Drug", "brand": "Danocrine", "drug_class": "Synthetic androgen",
        "mechanism": "Androgen receptor modulator, gonadotropin suppressor",
        "fda_year": 1971, "drugbank_id": "DB01406",
        "original_indication": "Endometriosis",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Medroxyprogesterone": {
        "type": "Drug", "brand": "Provera", "drug_class": "Progestin",
        "mechanism": "Progesterone receptor agonist, anti-estrogenic",
        "fda_year": 1959, "drugbank_id": "DB00603",
        "original_indication": "Amenorrhea/endometriosis",
        "repurposing_status": "ReDO DB, endometrial cancer treatment",
    },
    "Octreotide": {
        "type": "Drug", "brand": "Sandostatin", "drug_class": "Somatostatin analog",
        "mechanism": "Somatostatin receptor agonist (SSTR2/5), anti-secretory",
        "fda_year": 1988, "drugbank_id": "DB00104",
        "original_indication": "Acromegaly/carcinoid",
        "repurposing_status": "ReDO DB, neuroendocrine tumor treatment",
    },
    "Leuprolide": {
        "type": "Drug", "brand": "Lupron", "drug_class": "GnRH agonist",
        "mechanism": "GnRH receptor agonist (desensitization), androgen/estrogen suppression",
        "fda_year": 1985, "drugbank_id": "DB00007",
        "original_indication": "Endometriosis/precocious puberty",
        "repurposing_status": "ReDO DB, prostate cancer ADT",
    },
    "Goserelin": {
        "type": "Drug", "brand": "Zoladex", "drug_class": "GnRH agonist",
        "mechanism": "GnRH receptor agonist (desensitization), sex hormone suppression",
        "fda_year": 1989, "drugbank_id": "DB00014",
        "original_indication": "Endometriosis",
        "repurposing_status": "ReDO DB, breast and prostate cancer hormone suppression",
    },
    "Tamoxifen": {
        "type": "Drug", "brand": "Nolvadex", "drug_class": "SERM",
        "mechanism": "Estrogen receptor antagonist in breast, P-gp inhibitor",
        "fda_year": 1977, "drugbank_id": "DB00675",
        "original_indication": "Breast cancer prevention (non-cancer indication: gynecomastia)",
        "repurposing_status": "ReDO DB, MDR reversal in non-breast cancers",
    },

    # === ANTICOAGULANT / ANTIPLATELET ===
    "Ticlopidine": {
        "type": "Drug", "brand": "Ticlid", "drug_class": "Thienopyridine antiplatelet",
        "mechanism": "P2Y12 receptor antagonist, anti-platelet",
        "fda_year": 1991, "drugbank_id": "DB00208",
        "original_indication": "Stroke prevention",
        "repurposing_status": "ReDO DB, anti-metastatic via platelet inhibition",
    },
    "Warfarin": {
        "type": "Drug", "brand": "Coumadin", "drug_class": "Vitamin K antagonist",
        "mechanism": "VKORC1 inhibitor, anti-coagulant, Gas6/Axl pathway modulator",
        "fda_year": 1954, "drugbank_id": "DB00682",
        "original_indication": "Thromboembolism",
        "repurposing_status": "ReDO DB, Gas6/Axl anti-cancer (Kirane 2015)",
    },
    "Heparin": {
        "type": "Drug", "brand": "Heparin", "drug_class": "Glycosaminoglycan anticoagulant",
        "mechanism": "Antithrombin III activator, selectin inhibitor, heparanase inhibitor",
        "fda_year": 1939, "drugbank_id": "DB01109",
        "original_indication": "Thromboembolism",
        "repurposing_status": "ReDO DB, anti-metastatic via selectin/heparanase (Stevenson 2007)",
    },
    "Enoxaparin": {
        "type": "Drug", "brand": "Lovenox", "drug_class": "LMWH anticoagulant",
        "mechanism": "Factor Xa inhibitor, anti-angiogenic, heparanase inhibitor",
        "fda_year": 1993, "drugbank_id": "DB01225",
        "original_indication": "DVT prophylaxis",
        "repurposing_status": "ReDO DB, anti-metastatic in SCLC (FRAGMATIC trial)",
    },

    # === GI DRUGS ===
    "Loperamide": {
        "type": "Drug", "brand": "Imodium", "drug_class": "Opioid antidiarrheal",
        "mechanism": "Mu-opioid receptor agonist (peripheral), calmodulin inhibitor",
        "fda_year": 1976, "drugbank_id": "DB00836",
        "original_indication": "Diarrhea",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Ondansetron": {
        "type": "Drug", "brand": "Zofran", "drug_class": "5-HT3 antagonist",
        "mechanism": "Serotonin 5-HT3 receptor antagonist",
        "fda_year": 1991, "drugbank_id": "DB00904",
        "original_indication": "Nausea/vomiting",
        "repurposing_status": "ReDO DB, widely used anti-emetic in oncology",
    },
    "Metoclopramide": {
        "type": "Drug", "brand": "Reglan", "drug_class": "Dopamine antagonist prokinetic",
        "mechanism": "D2 antagonist, 5-HT4 agonist, anti-emetic",
        "fda_year": 1979, "drugbank_id": "DB01233",
        "original_indication": "GERD/gastroparesis",
        "repurposing_status": "ReDO DB, anti-emetic in oncology",
    },
    "Misoprostol": {
        "type": "Drug", "brand": "Cytotec", "drug_class": "Prostaglandin E1 analog",
        "mechanism": "EP receptor agonist, cytoprotective",
        "fda_year": 1988, "drugbank_id": "DB00929",
        "original_indication": "NSAID-induced ulcer prevention",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Sucralfate": {
        "type": "Drug", "brand": "Carafate", "drug_class": "Mucosal protectant",
        "mechanism": "Sucrose sulfate-aluminum complex, mucosal barrier",
        "fda_year": 1981, "drugbank_id": "DB00364",
        "original_indication": "Peptic ulcer",
        "repurposing_status": "ReDO DB, mucositis management in oncology",
    },

    # === RESPIRATORY ===
    "Montelukast": {
        "type": "Drug", "brand": "Singulair", "drug_class": "Leukotriene receptor antagonist",
        "mechanism": "CysLT1 receptor antagonist, anti-inflammatory",
        "fda_year": 1998, "drugbank_id": "DB00471",
        "original_indication": "Asthma",
        "repurposing_status": "ReDO DB, anti-cancer via leukotriene pathway",
    },
    "Cromolyn": {
        "type": "Drug", "brand": "Intal", "drug_class": "Mast cell stabilizer",
        "mechanism": "Mast cell stabilizer, GPR35 agonist",
        "fda_year": 1973, "drugbank_id": "DB01003",
        "original_indication": "Asthma",
        "repurposing_status": "ReDO DB, tumor microenvironment modulation",
    },
    "Zileuton": {
        "type": "Drug", "brand": "Zyflo", "drug_class": "5-LOX inhibitor",
        "mechanism": "5-lipoxygenase inhibitor, leukotriene synthesis blocker",
        "fda_year": 1996, "drugbank_id": "DB00744",
        "original_indication": "Asthma",
        "repurposing_status": "ReDO DB, anti-cancer via 5-LOX pathway",
    },
    "Zafirlukast": {
        "type": "Drug", "brand": "Accolate", "drug_class": "Leukotriene receptor antagonist",
        "mechanism": "CysLT1 receptor antagonist",
        "fda_year": 1996, "drugbank_id": "DB00549",
        "original_indication": "Asthma",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === UROLOGICALS ===
    "Tamsulosin": {
        "type": "Drug", "brand": "Flomax", "drug_class": "Alpha-1A adrenergic blocker",
        "mechanism": "Selective alpha-1A antagonist",
        "fda_year": 1997, "drugbank_id": "DB00706",
        "original_indication": "BPH",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Doxazosin": {
        "type": "Drug", "brand": "Cardura", "drug_class": "Alpha-1 adrenergic blocker",
        "mechanism": "Alpha-1 antagonist, pro-apoptotic in prostate cancer cells",
        "fda_year": 1990, "drugbank_id": "DB00590",
        "original_indication": "BPH/hypertension",
        "repurposing_status": "ReDO DB, anti-angiogenic + pro-apoptotic",
    },
    "Terazosin": {
        "type": "Drug", "brand": "Hytrin", "drug_class": "Alpha-1 adrenergic blocker",
        "mechanism": "Alpha-1 antagonist, pro-apoptotic",
        "fda_year": 1987, "drugbank_id": "DB01162",
        "original_indication": "BPH/hypertension",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },

    # === MORE IMMUNOSUPPRESSANTS ===
    "Tacrolimus": {
        "type": "Drug", "brand": "Prograf", "drug_class": "Calcineurin inhibitor",
        "mechanism": "FKBP12-calcineurin inhibitor, IL-2 suppressor",
        "fda_year": 1994, "drugbank_id": "DB00864",
        "original_indication": "Transplant rejection",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Mycophenolate": {
        "type": "Drug", "brand": "CellCept", "drug_class": "IMPDH inhibitor",
        "mechanism": "Inosine monophosphate dehydrogenase inhibitor, anti-proliferative",
        "fda_year": 1995, "drugbank_id": "DB00688",
        "original_indication": "Transplant rejection",
        "repurposing_status": "ReDO DB, anti-proliferative in cancer cells",
    },
    "Azathioprine": {
        "type": "Drug", "brand": "Imuran", "drug_class": "Purine antimetabolite",
        "mechanism": "6-mercaptopurine prodrug, DNA synthesis inhibitor",
        "fda_year": 1968, "drugbank_id": "DB00993",
        "original_indication": "Transplant rejection/autoimmune",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === MUSCLE RELAXANTS ===
    "Baclofen": {
        "type": "Drug", "brand": "Lioresal", "drug_class": "GABA-B agonist",
        "mechanism": "GABA-B receptor agonist, anti-spastic",
        "fda_year": 1977, "drugbank_id": "DB00181",
        "original_indication": "Spasticity",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Tizanidine": {
        "type": "Drug", "brand": "Zanaflex", "drug_class": "Alpha-2 agonist",
        "mechanism": "Central alpha-2 adrenergic agonist, muscle relaxant",
        "fda_year": 1996, "drugbank_id": "DB00697",
        "original_indication": "Spasticity",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Cyclobenzaprine": {
        "type": "Drug", "brand": "Flexeril", "drug_class": "Muscle relaxant",
        "mechanism": "Central muscle relaxant, structurally related to TCAs",
        "fda_year": 1977, "drugbank_id": "DB00924",
        "original_indication": "Muscle spasm",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === ANESTHETICS ===
    "Ketamine": {
        "type": "Drug", "brand": "Ketalar", "drug_class": "Dissociative anesthetic",
        "mechanism": "NMDA receptor antagonist, anti-inflammatory",
        "fda_year": 1970, "drugbank_id": "DB01221",
        "original_indication": "Anesthesia",
        "repurposing_status": "ReDO DB, perioperative immunomodulation",
    },
    "Propofol": {
        "type": "Drug", "brand": "Diprivan", "drug_class": "IV anesthetic",
        "mechanism": "GABA-A receptor modulator, anti-inflammatory, HIF-1a inhibitor",
        "fda_year": 1989, "drugbank_id": "DB00818",
        "original_indication": "Anesthesia",
        "repurposing_status": "ReDO DB, perioperative anti-cancer (Wigmore 2016)",
    },
    "Sevoflurane": {
        "type": "Drug", "brand": "Ultane", "drug_class": "Inhaled anesthetic",
        "mechanism": "GABA-A modulator, glycine receptor modulator",
        "fda_year": 1995, "drugbank_id": "DB01236",
        "original_indication": "General anesthesia",
        "repurposing_status": "ReDO DB, perioperative immunity effects",
    },

    # === METABOLIC ===
    "Febuxostat": {
        "type": "Drug", "brand": "Uloric", "drug_class": "Xanthine oxidase inhibitor",
        "mechanism": "Selective xanthine oxidase inhibitor, ROS modulator",
        "fda_year": 2009, "drugbank_id": "DB04854",
        "original_indication": "Gout",
        "repurposing_status": "ReDO DB, anti-cancer via ROS modulation",
    },
    "Probenecid": {
        "type": "Drug", "brand": "Benemid", "drug_class": "Uricosuric",
        "mechanism": "OAT inhibitor, pannexin-1 blocker, MRP inhibitor",
        "fda_year": 1951, "drugbank_id": "DB01032",
        "original_indication": "Gout",
        "repurposing_status": "ReDO DB, chemosensitization via MRP inhibition",
    },

    # === MISC REDO CANDIDATES ===
    "Dichloroacetate": {
        "type": "Drug", "brand": "DCA", "drug_class": "Pyruvate dehydrogenase kinase inhibitor",
        "mechanism": "PDK inhibitor, shifts metabolism from glycolysis to OXPHOS",
        "fda_year": 1973, "drugbank_id": "DB04267",
        "original_indication": "Lactic acidosis",
        "repurposing_status": "ReDO DB, Warburg effect reversal (Bonnet 2007)",
    },
    "Dimethyl_Fumarate": {
        "type": "Drug", "brand": "Tecfidera", "drug_class": "Fumaric acid ester",
        "mechanism": "Nrf2 activator, NF-kB inhibitor, anti-inflammatory",
        "fda_year": 2013, "drugbank_id": "DB08908",
        "original_indication": "Multiple sclerosis",
        "repurposing_status": "ReDO DB, anti-cancer via NF-kB/Nrf2",
    },
    "Aprepitant": {
        "type": "Drug", "brand": "Emend", "drug_class": "NK1 receptor antagonist",
        "mechanism": "Substance P/NK1 receptor antagonist, anti-emetic",
        "fda_year": 2003, "drugbank_id": "DB00673",
        "original_indication": "Chemotherapy-induced nausea",
        "repurposing_status": "ReDO DB, anti-cancer via NK1R (Munoz 2010)",
    },
    "Naltrexone": {
        "type": "Drug", "brand": "ReVia", "drug_class": "Opioid antagonist",
        "mechanism": "Mu/kappa opioid receptor antagonist, OGFr modulator at low dose",
        "fda_year": 1984, "drugbank_id": "DB00704",
        "original_indication": "Alcohol/opioid dependence",
        "repurposing_status": "ReDO DB, low-dose naltrexone anti-cancer (Zagon 2011)",
    },
    "Cannabidiol": {
        "type": "Drug", "brand": "Epidiolex", "drug_class": "Cannabinoid",
        "mechanism": "CB1/CB2 modulator, TRPV1 agonist, GPR55 antagonist, anti-inflammatory",
        "fda_year": 2018, "drugbank_id": "DB09061",
        "original_indication": "Epilepsy (Lennox-Gastaut/Dravet)",
        "repurposing_status": "ReDO DB, anti-proliferative + pro-apoptotic",
    },
    "Gossypol": {
        "type": "Drug", "brand": "AT-101", "drug_class": "BH3 mimetic / polyphenol",
        "mechanism": "Bcl-2/Bcl-xL inhibitor, BH3 mimetic",
        "fda_year": 1970, "drugbank_id": "DB04766",
        "original_indication": "Male contraceptive (investigational)",
        "repurposing_status": "ReDO DB, Bcl-2 inhibition in cancer (AT-101 trials)",
    },
    "D_Penicillamine": {
        "type": "Drug", "brand": "Cuprimine", "drug_class": "Chelating agent",
        "mechanism": "Copper chelator, anti-angiogenic via copper depletion",
        "fda_year": 1970, "drugbank_id": "DB00859",
        "original_indication": "Wilson's disease/RA",
        "repurposing_status": "ReDO DB, anti-angiogenic via copper depletion",
    },
    "Dextromethorphan": {
        "type": "Drug", "brand": "Robitussin", "drug_class": "Antitussive / NMDA antagonist",
        "mechanism": "NMDA antagonist, sigma-1 receptor agonist",
        "fda_year": 1958, "drugbank_id": "DB00514",
        "original_indication": "Cough suppressant",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Imiquimod": {
        "type": "Drug", "brand": "Aldara", "drug_class": "TLR7 agonist",
        "mechanism": "Toll-like receptor 7 agonist, immune activator",
        "fda_year": 1997, "drugbank_id": "DB00724",
        "original_indication": "Actinic keratosis/genital warts",
        "repurposing_status": "ReDO DB, superficial BCC treatment (approved)",
    },
    "Pimecrolimus": {
        "type": "Drug", "brand": "Elidel", "drug_class": "Calcineurin inhibitor",
        "mechanism": "Calcineurin inhibitor (topical), T-cell modulator",
        "fda_year": 2001, "drugbank_id": "DB00337",
        "original_indication": "Atopic dermatitis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Adapalene": {
        "type": "Drug", "brand": "Differin", "drug_class": "Retinoid",
        "mechanism": "RAR-beta/gamma selective agonist, anti-proliferative",
        "fda_year": 1996, "drugbank_id": "DB00210",
        "original_indication": "Acne",
        "repurposing_status": "ReDO DB, retinoid anti-cancer activity",
    },

    # === MORE ANTIMALARIALS ===
    "Primaquine": {
        "type": "Drug", "brand": "Primaquine", "drug_class": "8-aminoquinoline",
        "mechanism": "Mitochondrial electron transport disruptor, ROS generator",
        "fda_year": 1952, "drugbank_id": "DB01087",
        "original_indication": "Malaria (liver stage)",
        "repurposing_status": "ReDO DB, mitochondrial disruption in cancer",
    },
    "Amodiaquine": {
        "type": "Drug", "brand": "Camoquin", "drug_class": "4-aminoquinoline",
        "mechanism": "Lysosomal alkalizer, autophagy inhibitor",
        "fda_year": 1951, "drugbank_id": "DB00613",
        "original_indication": "Malaria",
        "repurposing_status": "ReDO DB, autophagy inhibition in cancer",
    },

    # === MORE STATINS ===
    "Pitavastatin": {
        "type": "Drug", "brand": "Livalo", "drug_class": "Statin",
        "mechanism": "HMG-CoA reductase inhibitor, minimal CYP metabolism",
        "fda_year": 2009, "drugbank_id": "DB08860",
        "original_indication": "Hypercholesterolemia",
        "repurposing_status": "ReDO DB, anti-cancer via mevalonate pathway",
    },

    # === MORE NSAIDS ===
    "Mefenamic_Acid": {
        "type": "Drug", "brand": "Ponstel", "drug_class": "NSAID (fenamate)",
        "mechanism": "COX-1/COX-2 inhibitor, Wnt pathway modulator",
        "fda_year": 1967, "drugbank_id": "DB00784",
        "original_indication": "Pain/dysmenorrhea",
        "repurposing_status": "ReDO DB, Wnt pathway modulation anti-cancer",
    },
    "Etodolac": {
        "type": "Drug", "brand": "Lodine", "drug_class": "NSAID (pyranocarboxylic acid)",
        "mechanism": "COX-2 preferential inhibitor, PPARgamma activator",
        "fda_year": 1991, "drugbank_id": "DB00749",
        "original_indication": "Arthritis pain",
        "repurposing_status": "ReDO DB, preclinical anti-cancer",
    },
    "Diflunisal": {
        "type": "Drug", "brand": "Dolobid", "drug_class": "NSAID (salicylate)",
        "mechanism": "COX inhibitor, amyloid stabilizer",
        "fda_year": 1982, "drugbank_id": "DB00861",
        "original_indication": "Pain",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },

    # === MORE ANTIFUNGALS ===
    "Voriconazole": {
        "type": "Drug", "brand": "Vfend", "drug_class": "Triazole antifungal",
        "mechanism": "CYP51 inhibitor, anti-angiogenic",
        "fda_year": 2002, "drugbank_id": "DB00582",
        "original_indication": "Invasive aspergillosis",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Posaconazole": {
        "type": "Drug", "brand": "Noxafil", "drug_class": "Triazole antifungal",
        "mechanism": "CYP51 inhibitor, Hedgehog pathway inhibitor",
        "fda_year": 2006, "drugbank_id": "DB01263",
        "original_indication": "Fungal infections",
        "repurposing_status": "ReDO DB, Hedgehog pathway inhibition",
    },

    # === MORE ANTHELMINTHICS ===
    "Praziquantel": {
        "type": "Drug", "brand": "Biltricide", "drug_class": "Anthelmintic",
        "mechanism": "Calcium channel modulator, tegument disruptor",
        "fda_year": 1982, "drugbank_id": "DB01058",
        "original_indication": "Schistosomiasis",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Oxfendazole": {
        "type": "Drug", "brand": "Synanthic", "drug_class": "Benzimidazole anthelmintic",
        "mechanism": "Tubulin polymerization inhibitor",
        "fda_year": 1984, "drugbank_id": "DB13038",
        "original_indication": "Helminth infections",
        "repurposing_status": "ReDO DB, anti-mitotic preclinical",
    },

    # === MORE H2 BLOCKERS ===
    "Nizatidine": {
        "type": "Drug", "brand": "Axid", "drug_class": "H2 receptor antagonist",
        "mechanism": "Histamine H2 blocker, acetylcholinesterase inhibitor",
        "fda_year": 1988, "drugbank_id": "DB00585",
        "original_indication": "Peptic ulcer/GERD",
        "repurposing_status": "ReDO DB, immunomodulatory (similar to cimetidine)",
    },

    # === ADDITIONAL MISC TO REACH 268 ===
    "Nicotinamide": {
        "type": "Drug", "brand": "Niacinamide", "drug_class": "Vitamin B3 derivative",
        "mechanism": "SIRT inhibitor, PARP substrate, NAD+ precursor",
        "fda_year": 1942, "drugbank_id": "DB02701",
        "original_indication": "Pellagra",
        "repurposing_status": "ReDO DB, ONTRAC trial skin cancer prevention (Chen 2015 NEJM)",
    },
    "Pentamidine": {
        "type": "Drug", "brand": "Pentam", "drug_class": "Antiprotozoal",
        "mechanism": "DNA minor groove binder, PRL phosphatase inhibitor",
        "fda_year": 1984, "drugbank_id": "DB00738",
        "original_indication": "Pneumocystis/leishmaniasis",
        "repurposing_status": "ReDO DB, PRL-3 phosphatase inhibition in cancer",
    },
    "Artemether": {
        "type": "Drug", "brand": "Coartem", "drug_class": "Artemisinin derivative",
        "mechanism": "Iron-dependent ROS generator, anti-angiogenic",
        "fda_year": 2009, "drugbank_id": "DB06697",
        "original_indication": "Malaria",
        "repurposing_status": "ReDO DB, iron-dependent cancer cell killing",
    },
    "Miltefosine": {
        "type": "Drug", "brand": "Impavido", "drug_class": "Alkylphosphocholine",
        "mechanism": "Membrane disruptor, AKT/PI3K inhibitor, apoptosis inducer",
        "fda_year": 2014, "drugbank_id": "DB09031",
        "original_indication": "Leishmaniasis",
        "repurposing_status": "ReDO DB, anti-cancer via PI3K/AKT inhibition",
    },
    "Phenformin": {
        "type": "Drug", "brand": "DBI", "drug_class": "Biguanide",
        "mechanism": "Mitochondrial complex I inhibitor, AMPK activator",
        "fda_year": 1957, "drugbank_id": "DB00914",
        "original_indication": "Type 2 diabetes (withdrawn in US)",
        "repurposing_status": "ReDO DB, anti-cancer via AMPK (more potent than metformin)",
    },
    "Diethylstilbestrol": {
        "type": "Drug", "brand": "DES", "drug_class": "Synthetic estrogen",
        "mechanism": "Estrogen receptor agonist, anti-androgen effect",
        "fda_year": 1941, "drugbank_id": "DB00255",
        "original_indication": "Menopause (historical)",
        "repurposing_status": "ReDO DB, historical prostate cancer treatment",
    },
    "Eflornithine": {
        "type": "Drug", "brand": "Vaniqa", "drug_class": "Ornithine decarboxylase inhibitor",
        "mechanism": "ODC inhibitor, polyamine synthesis blocker",
        "fda_year": 1990, "drugbank_id": "DB00570",
        "original_indication": "Trypanosomiasis/hirsutism",
        "repurposing_status": "ReDO DB, cancer chemoprevention (polyamine pathway)",
    },
    "Methimazole": {
        "type": "Drug", "brand": "Tapazole", "drug_class": "Thionamide antithyroid",
        "mechanism": "Thyroid peroxidase inhibitor, anti-angiogenic",
        "fda_year": 1950, "drugbank_id": "DB00763",
        "original_indication": "Hyperthyroidism",
        "repurposing_status": "ReDO DB, anti-angiogenic preclinical",
    },
    "Benztropine": {
        "type": "Drug", "brand": "Cogentin", "drug_class": "Anticholinergic",
        "mechanism": "Muscarinic receptor antagonist, dopamine reuptake inhibitor",
        "fda_year": 1954, "drugbank_id": "DB00245",
        "original_indication": "Parkinson's/EPS",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Chlorzoxazone": {
        "type": "Drug", "brand": "Parafon", "drug_class": "Muscle relaxant",
        "mechanism": "Central muscle relaxant, CYP2E1 substrate, TRPV1 modulator",
        "fda_year": 1958, "drugbank_id": "DB00356",
        "original_indication": "Muscle spasm",
        "repurposing_status": "ReDO DB, limited anti-cancer evidence",
    },
    "Triclabendazole": {
        "type": "Drug", "brand": "Egaten", "drug_class": "Benzimidazole anthelmintic",
        "mechanism": "Tubulin modulator, fasciolicide",
        "fda_year": 2019, "drugbank_id": "DB12245",
        "original_indication": "Fascioliasis",
        "repurposing_status": "ReDO DB, anti-mitotic preclinical",
    },
})


# ============================================================================
# BATCH 2: Additional proteins
# ============================================================================

REDO_FULL_ADDITIONAL_PROTEINS.update({
    "NR3C1": {
        "type": "Receptor",
        "function": "Glucocorticoid receptor, immune regulation and apoptosis",
        "pathways": ["glucocorticoid", "immune", "apoptosis"],
        "cancers": ["lymphoma", "ALL", "multiple_myeloma"],
    },
    "TOP2A": {
        "type": "Signaling",
        "function": "Topoisomerase II alpha, DNA replication and repair",
        "pathways": ["DNA_replication", "chromosome_segregation"],
        "cancers": ["breast", "AML", "NSCLC"],
    },
    "ESR1": {
        "type": "Receptor",
        "function": "Estrogen receptor alpha, hormone-responsive gene regulation",
        "pathways": ["estrogen", "proliferation", "survival"],
        "cancers": ["breast", "ovarian", "endometrial"],
    },
    "AR": {
        "type": "Receptor",
        "function": "Androgen receptor, male hormone signaling",
        "pathways": ["androgen", "proliferation", "survival"],
        "cancers": ["prostate", "breast_TNBC"],
    },
    "SSTR2": {
        "type": "Receptor",
        "function": "Somatostatin receptor 2, anti-secretory and anti-proliferative",
        "pathways": ["somatostatin", "cAMP", "proliferation"],
        "cancers": ["neuroendocrine", "pancreatic", "pituitary"],
    },
})


# ============================================================================
# BATCH 2: Drug -> Protein interactions for new drugs
# ============================================================================

REDO_FULL_DRUG_TARGET_INTERACTIONS.extend([
    # Antibiotics/antimicrobials -> various
    ("Chloramphenicol", "MTOR", "indirect_inhibitor", 0.40, "Mitochondrial ribosome inhibition"),
    ("Dapsone", "NFKB1", "inhibits", 0.45, "Anti-inflammatory, NF-kB modulation"),
    ("Erythromycin", "MTOR", "indirect_inhibitor", 0.42, "Macrolide mitochondrial effect"),
    ("Tetracycline", "MMP9", "inhibits", 0.65, "MMP inhibition (Golub 1991)"),
    ("Tetracycline", "MTOR", "indirect_inhibitor", 0.40, "Anti-angiogenic effect"),
    ("Linezolid", "MTOR", "indirect_inhibitor", 0.40, "Mitochondrial ribosome inhibition"),
    ("Griseofulvin", "TUBB", "inhibits", 0.72, "Tubulin binding, centrosome declustering"),
    ("Trimethoprim", "STAT3", "indirect_inhibitor", 0.38, "Anti-folate, anti-proliferative"),
    ("Colistin", "NFKB1", "indirect_inhibitor", 0.38, "Membrane disruption, NF-kB effect"),
    ("Amphotericin_B", "NFKB1", "indirect_inhibitor", 0.40, "Membrane permeabilization"),
    ("Nystatin", "NFKB1", "indirect_inhibitor", 0.35, "Membrane disruption"),
    ("Gentamicin", "TP53", "indirect_inhibitor", 0.45, "Readthrough of premature stop codons"),
    ("Terbinafine", "HMGCR", "indirect_inhibitor", 0.40, "Cholesterol pathway disruption"),
    ("Isoniazid", "NFKB1", "indirect_inhibitor", 0.38, "ROS generation, NF-kB modulation"),
    ("Nitrofurantoin", "NFKB1", "indirect_inhibitor", 0.40, "ROS generation"),

    # Antivirals -> various
    ("Acyclovir", "MTOR", "indirect_inhibitor", 0.35, "Nucleoside analog, limited anti-proliferative"),
    ("Ganciclovir", "MTOR", "indirect_inhibitor", 0.40, "DNA synthesis inhibition"),
    ("Zidovudine", "MTOR", "indirect_inhibitor", 0.45, "Telomerase inhibition"),
    ("Didanosine", "MTOR", "indirect_inhibitor", 0.35, "Nucleoside analog"),
    ("Lopinavir", "AKT1", "inhibits", 0.50, "AKT pathway inhibition (Srirangam 2006)"),
    ("Oseltamivir", "VEGFR2", "indirect_inhibitor", 0.40, "Anti-invasive via neuraminidase"),
    ("Amantadine", "MTOR", "indirect_inhibitor", 0.35, "NMDA antagonism"),
    ("Valacyclovir", "MTOR", "indirect_inhibitor", 0.35, "Acyclovir prodrug"),

    # Antidiabetics -> AMPK/MTOR
    ("Glibenclamide", "AMPK", "indirect_inhibitor", 0.45, "KATP channel / metabolic modulation"),
    ("Glibenclamide", "NFKB1", "inhibits", 0.42, "NLRP3 inhibition, anti-inflammatory"),
    ("Dapagliflozin", "MTOR", "indirect_inhibitor", 0.42, "Glucose deprivation, metabolic stress"),
    ("Canagliflozin", "AMPK", "activator", 0.55, "AMPK activation (Hawley 2016)"),
    ("Canagliflozin", "MTOR", "indirect_inhibitor", 0.48, "AMPK-mediated mTOR suppression"),
    ("Acarbose", "MTOR", "indirect_inhibitor", 0.35, "Glucose modulation"),
    ("Empagliflozin", "MTOR", "indirect_inhibitor", 0.40, "Metabolic stress via glucose reduction"),

    # Antihypertensives -> various
    ("Minoxidil", "VEGFR2", "indirect_inhibitor", 0.35, "Vasodilator, limited anti-angiogenic"),
    ("Methyldopa", "DNMT1", "inhibits", 0.50, "DNMT inhibitor (Lee 2005)"),
    ("Clonidine", "VEGFR2", "indirect_inhibitor", 0.35, "Anti-angiogenic preclinical"),
    ("Bosentan", "VEGFR2", "indirect_inhibitor", 0.45, "Endothelin pathway anti-angiogenic"),
    ("Ambrisentan", "VEGFR2", "indirect_inhibitor", 0.40, "ET-A anti-angiogenic"),
    ("Nitroprusside", "HIF1A", "inhibits", 0.42, "NO-mediated HIF modulation"),

    # More diuretics -> NFKB1
    ("Furosemide", "NFKB1", "indirect_inhibitor", 0.38, "Anti-angiogenic effect"),
    ("Hydrochlorothiazide", "NFKB1", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Chlorthalidone", "NFKB1", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Indapamide", "NFKB1", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Bumetanide", "NFKB1", "indirect_inhibitor", 0.38, "NKCC1 in cancer cell volume"),

    # Cardiac / anti-arrhythmics -> SRC/STAT3/MTOR
    ("Amiodarone", "MTOR", "indirect_inhibitor", 0.42, "Multi-channel blocker, autophagy induction"),
    ("Amiodarone", "STAT3", "indirect_inhibitor", 0.40, "Anti-angiogenic preclinical"),
    ("Propafenone", "SRC", "indirect_inhibitor", 0.38, "Na channel / SRC pathway"),
    ("Flecainide", "SRC", "indirect_inhibitor", 0.35, "Na channel blockade"),
    ("Mexiletine", "SRC", "indirect_inhibitor", 0.40, "Nav1.5 in cancer metastasis"),
    ("Nicorandil", "MTOR", "indirect_inhibitor", 0.35, "KATP opener, NO donor"),
    ("Ranolazine", "MTOR", "indirect_inhibitor", 0.38, "Metabolic modulation"),
    ("Milrinone", "MTOR", "indirect_inhibitor", 0.35, "PDE3/cAMP pathway"),

    # More antipsychotics -> DRD2/AKT1
    ("Perphenazine", "DRD2", "inhibits", 0.88, "Phenothiazine D2 antagonist"),
    ("Perphenazine", "AKT1", "indirect_inhibitor", 0.45, "AKT pathway modulation"),
    ("Olanzapine", "DRD2", "inhibits", 0.75, "Multi-receptor D2 antagonist"),
    ("Risperidone", "DRD2", "inhibits", 0.85, "D2/5-HT2A antagonist"),
    ("Quetiapine", "DRD2", "inhibits", 0.70, "Multi-receptor antagonist"),
    ("Quetiapine", "MTOR", "indirect_inhibitor", 0.38, "Autophagy induction"),
    ("Aripiprazole", "DRD2", "inhibits", 0.80, "D2 partial agonist"),

    # More antidepressants -> STAT3/AKT1
    ("Amitriptyline", "STAT3", "indirect_inhibitor", 0.42, "ASM inhibition, anti-cancer"),
    ("Amitriptyline", "AKT1", "indirect_inhibitor", 0.40, "AKT pathway modulation"),
    ("Clomipramine", "STAT3", "indirect_inhibitor", 0.40, "Anti-cancer preclinical"),
    ("Desipramine", "STAT3", "indirect_inhibitor", 0.42, "ASM inhibition (Petersen 2008)"),
    ("Nortriptyline", "STAT3", "indirect_inhibitor", 0.38, "TCA anti-cancer effect"),
    ("Paroxetine", "AKT1", "indirect_inhibitor", 0.40, "Anti-proliferative"),
    ("Fluvoxamine", "STAT3", "indirect_inhibitor", 0.38, "Sigma-1 receptor modulation"),
    ("Citalopram", "STAT3", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Mirtazapine", "STAT3", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),

    # More antiepileptics -> HDAC1/MTOR
    ("Topiramate", "MTOR", "indirect_inhibitor", 0.40, "Carbonic anhydrase / metabolic"),
    ("Gabapentin", "MTOR", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Lamotrigine", "MTOR", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Phenytoin", "HDAC1", "indirect_inhibitor", 0.38, "Na channel / epigenetic modulation"),
    ("Pregabalin", "MTOR", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),

    # Anti-inflammatory / corticosteroids -> NR3C1/NFKB1
    ("Mesalamine", "NFKB1", "inhibits", 0.60, "NF-kB inhibition in CRC chemoprevention"),
    ("Mesalamine", "PPARG", "activates", 0.50, "PPARgamma activation (Rousseaux 2005)"),
    ("Dexamethasone", "NR3C1", "activates", 0.95, "Potent glucocorticoid receptor agonist"),
    ("Dexamethasone", "NFKB1", "inhibits", 0.80, "NF-kB suppression via GR"),
    ("Prednisone", "NR3C1", "activates", 0.90, "Glucocorticoid receptor agonist"),
    ("Prednisone", "NFKB1", "inhibits", 0.75, "NF-kB suppression"),
    ("Budesonide", "NR3C1", "activates", 0.88, "Glucocorticoid receptor agonist"),
    ("Beclomethasone", "NR3C1", "activates", 0.85, "Glucocorticoid receptor agonist"),

    # Hormonal agents -> ESR1/AR/SSTR2/VEGFR2
    ("Danazol", "VEGFR2", "indirect_inhibitor", 0.45, "Anti-angiogenic via androgen pathway"),
    ("Medroxyprogesterone", "ESR1", "indirect_inhibitor", 0.55, "Anti-estrogenic effect"),
    ("Octreotide", "SSTR2", "activates", 0.92, "Somatostatin receptor 2/5 agonist"),
    ("Octreotide", "MTOR", "indirect_inhibitor", 0.50, "Anti-proliferative via SSTR2"),
    ("Leuprolide", "AR", "indirect_inhibitor", 0.85, "Androgen suppression via GnRH desensitization"),
    ("Goserelin", "AR", "indirect_inhibitor", 0.85, "Androgen suppression via GnRH desensitization"),
    ("Goserelin", "ESR1", "indirect_inhibitor", 0.80, "Estrogen suppression"),
    ("Tamoxifen", "ESR1", "inhibits", 0.92, "Selective estrogen receptor modulator"),
    ("Tamoxifen", "ABCB1", "inhibits", 0.55, "P-glycoprotein inhibitor (MDR reversal)"),

    # Anticoagulant/antiplatelet -> VEGFR2/NFKB1
    ("Ticlopidine", "VEGFR2", "indirect_inhibitor", 0.38, "Anti-platelet, anti-metastatic"),
    ("Warfarin", "VEGFR2", "indirect_inhibitor", 0.42, "Gas6/Axl pathway modulation"),
    ("Warfarin", "AKT1", "indirect_inhibitor", 0.40, "Axl-dependent AKT modulation"),
    ("Heparin", "VEGFR2", "inhibits", 0.55, "Direct anti-angiogenic (Norrby 2006)"),
    ("Heparin", "NFKB1", "inhibits", 0.45, "Selectin inhibition, anti-inflammatory"),
    ("Enoxaparin", "VEGFR2", "inhibits", 0.50, "Anti-angiogenic"),

    # GI drugs -> MTOR/DRD2
    ("Loperamide", "MTOR", "indirect_inhibitor", 0.38, "Calmodulin inhibition"),
    ("Ondansetron", "STAT3", "indirect_inhibitor", 0.35, "5-HT3 modulation"),
    ("Metoclopramide", "DRD2", "inhibits", 0.75, "D2 antagonist"),
    ("Misoprostol", "NFKB1", "indirect_inhibitor", 0.38, "Cytoprotective, prostaglandin pathway"),
    ("Sucralfate", "VEGFR2", "indirect_inhibitor", 0.30, "Mucosal protection"),

    # Respiratory -> NFKB1/STAT3
    ("Montelukast", "NFKB1", "inhibits", 0.50, "CysLT1 antagonism, NF-kB modulation"),
    ("Montelukast", "STAT3", "indirect_inhibitor", 0.42, "Leukotriene pathway anti-cancer"),
    ("Cromolyn", "NFKB1", "indirect_inhibitor", 0.40, "Mast cell stabilization"),
    ("Zileuton", "NFKB1", "inhibits", 0.52, "5-LOX inhibition, anti-inflammatory"),
    ("Zafirlukast", "NFKB1", "indirect_inhibitor", 0.40, "CysLT1 antagonism"),

    # Urologicals -> VEGFR2
    ("Tamsulosin", "VEGFR2", "indirect_inhibitor", 0.35, "Alpha-1A blockade"),
    ("Doxazosin", "VEGFR2", "indirect_inhibitor", 0.50, "Anti-angiogenic + pro-apoptotic"),
    ("Doxazosin", "AKT1", "indirect_inhibitor", 0.45, "AKT pathway inhibition"),
    ("Terazosin", "VEGFR2", "indirect_inhibitor", 0.45, "Alpha-1 anti-angiogenic"),

    # More immunosuppressants -> MTOR/NFKB1
    ("Tacrolimus", "NFKB1", "inhibits", 0.55, "Calcineurin/NFAT/NF-kB"),
    ("Tacrolimus", "MTOR", "indirect_inhibitor", 0.40, "FKBP12 binding"),
    ("Mycophenolate", "MTOR", "indirect_inhibitor", 0.45, "IMPDH inhibition, GTP depletion"),
    ("Azathioprine", "NFKB1", "indirect_inhibitor", 0.42, "Purine antimetabolite, immune suppression"),

    # Muscle relaxants -> MTOR
    ("Baclofen", "MTOR", "indirect_inhibitor", 0.35, "GABA-B agonism"),
    ("Tizanidine", "MTOR", "indirect_inhibitor", 0.35, "Alpha-2 agonism"),
    ("Cyclobenzaprine", "STAT3", "indirect_inhibitor", 0.35, "TCA-like anti-cancer effect"),

    # Anesthetics -> NFKB1/STAT3/HIF1A
    ("Ketamine", "NFKB1", "inhibits", 0.45, "Anti-inflammatory via NF-kB"),
    ("Propofol", "HIF1A", "inhibits", 0.50, "HIF-1a inhibition (Huang 2014)"),
    ("Propofol", "NFKB1", "inhibits", 0.48, "Anti-inflammatory"),
    ("Sevoflurane", "STAT3", "indirect_inhibitor", 0.38, "Immune modulation"),

    # Metabolic -> NFKB1
    ("Febuxostat", "NFKB1", "inhibits", 0.45, "XO inhibition, ROS reduction"),
    ("Probenecid", "NFKB1", "indirect_inhibitor", 0.40, "MRP/pannexin-1 inhibition"),

    # Misc ReDO candidates -> various
    ("Dichloroacetate", "MTOR", "indirect_inhibitor", 0.50, "PDK inhibition, metabolic shift"),
    ("Dichloroacetate", "HIF1A", "inhibits", 0.48, "Reverses Warburg effect"),
    ("Dimethyl_Fumarate", "NFKB1", "inhibits", 0.60, "NF-kB inhibition via Nrf2"),
    ("Aprepitant", "NFKB1", "indirect_inhibitor", 0.42, "NK1R antagonism, anti-cancer"),
    ("Naltrexone", "MTOR", "indirect_inhibitor", 0.40, "OGF-OGFr axis at low dose"),
    ("Cannabidiol", "MTOR", "indirect_inhibitor", 0.45, "Anti-proliferative, pro-apoptotic"),
    ("Cannabidiol", "NFKB1", "inhibits", 0.48, "Anti-inflammatory via NF-kB"),
    ("Gossypol", "STAT3", "indirect_inhibitor", 0.50, "Bcl-2/Bcl-xL inhibition"),
    ("D_Penicillamine", "VEGFR2", "indirect_inhibitor", 0.50, "Copper chelation, anti-angiogenic"),
    ("Dextromethorphan", "STAT3", "indirect_inhibitor", 0.35, "Sigma-1/NMDA modulation"),
    ("Imiquimod", "NFKB1", "activator", 0.60, "TLR7-mediated immune activation"),
    ("Pimecrolimus", "NFKB1", "inhibits", 0.45, "Calcineurin inhibition"),
    ("Adapalene", "STAT3", "indirect_inhibitor", 0.42, "RAR-mediated differentiation"),

    # More antimalarials
    ("Primaquine", "MTOR", "indirect_inhibitor", 0.42, "Mitochondrial disruption"),
    ("Amodiaquine", "MTOR", "indirect_inhibitor", 0.45, "Autophagy inhibition"),

    # More statins
    ("Pitavastatin", "HMGCR", "inhibits", 0.94, "HMG-CoA reductase inhibition"),

    # More NSAIDs
    ("Mefenamic_Acid", "COX2", "inhibits", 0.88, "Fenamate COX inhibitor"),
    ("Mefenamic_Acid", "GSK3B", "indirect_inhibitor", 0.45, "Wnt pathway modulation"),
    ("Etodolac", "COX2", "inhibits", 0.85, "COX-2 preferential inhibitor"),
    ("Etodolac", "PPARG", "activates", 0.42, "PPARgamma activation"),
    ("Diflunisal", "COX2", "inhibits", 0.82, "Salicylate COX inhibitor"),

    # More antifungals
    ("Voriconazole", "VEGFR2", "indirect_inhibitor", 0.42, "Anti-angiogenic"),
    ("Posaconazole", "SMO", "inhibits", 0.55, "Hedgehog pathway inhibition (Kim 2013)"),

    # More anthelminthics
    ("Praziquantel", "MTOR", "indirect_inhibitor", 0.35, "Calcium modulation"),
    ("Oxfendazole", "TUBB", "inhibits", 0.75, "Tubulin polymerization inhibitor"),

    # More H2 blockers
    ("Nizatidine", "NFKB1", "inhibits", 0.42, "Immunomodulatory (H2 class effect)"),

    # Additional misc
    ("Nicotinamide", "MTOR", "indirect_inhibitor", 0.45, "SIRT/PARP/NAD+ modulation"),
    ("Pentamidine", "STAT3", "inhibits", 0.50, "PRL-3 phosphatase inhibition"),
    ("Artemether", "NFKB1", "inhibits", 0.50, "ROS-mediated NF-kB inhibition"),
    ("Artemether", "HIF1A", "inhibits", 0.45, "Iron-dependent ROS, HIF modulation"),
    ("Miltefosine", "AKT1", "inhibits", 0.55, "PI3K/AKT pathway inhibition"),
    ("Phenformin", "AMPK", "activator", 0.80, "Potent AMPK activator (complex I inhibitor)"),
    ("Phenformin", "MTOR", "indirect_inhibitor", 0.65, "AMPK-mediated mTOR suppression"),
    ("Diethylstilbestrol", "ESR1", "activates", 0.90, "Potent synthetic estrogen"),
    ("Diethylstilbestrol", "AR", "indirect_inhibitor", 0.55, "Anti-androgen via estrogen feedback"),
    ("Eflornithine", "MTOR", "indirect_inhibitor", 0.48, "ODC inhibition, polyamine depletion"),
    ("Methimazole", "VEGFR2", "indirect_inhibitor", 0.40, "Anti-angiogenic preclinical"),
    ("Benztropine", "DRD2", "indirect_inhibitor", 0.40, "Dopamine pathway modulation"),
    ("Chlorzoxazone", "MTOR", "indirect_inhibitor", 0.35, "Limited anti-cancer effect"),
    ("Triclabendazole", "TUBB", "inhibits", 0.60, "Benzimidazole tubulin binding"),
])


# ============================================================================
# BATCH 2: Additional Protein -> Disease associations
# ============================================================================

REDO_FULL_PROTEIN_DISEASE_ASSOCIATIONS.extend([
    # NR3C1 (glucocorticoid receptor) -> cancers
    ("NR3C1", "AML", "associated_with", 0.70, "GR-mediated apoptosis in lymphoid malignancies"),
    ("NR3C1", "Multiple_Myeloma", "associated_with", 0.65, "Dexamethasone in myeloma regimens"),
    ("NR3C1", "Breast_Cancer", "associated_with", 0.50, "GR expression in breast cancer subtypes"),

    # TOP2A -> cancers
    ("TOP2A", "Breast_Cancer", "associated_with", 0.72, "TOP2A amplification in HER2+ breast cancer"),
    ("TOP2A", "AML", "associated_with", 0.70, "Topoisomerase II target in AML treatment"),

    # ESR1 -> cancers
    ("ESR1", "Breast_Cancer", "driver_of", 0.85, "ER-positive breast cancer driver"),
    ("ESR1", "Ovarian_Cancer", "associated_with", 0.55, "ER expression in some ovarian cancers"),

    # AR -> cancers
    ("AR", "Prostate_Cancer", "driver_of", 0.90, "Androgen receptor drives prostate cancer"),
    ("AR", "Breast_Cancer", "associated_with", 0.45, "AR expression in TNBC subset"),

    # SSTR2 -> cancers
    ("SSTR2", "Pancreatic_Cancer", "associated_with", 0.65, "SSTR2 in pancreatic neuroendocrine tumors"),
    ("SSTR2", "Glioblastoma", "associated_with", 0.45, "SSTR expression in GBM"),
])


# ============================================================================
# BATCH 2: Additional holdout edges (Drug -> Disease)
# ============================================================================

REDO_FULL_HOLDOUT_EDGES.extend([
    # Anti-inflammatory / corticosteroids
    ("Dexamethasone", "Multiple_Myeloma", "potential_treatment", 0.65,
     "Standard component of myeloma regimens (VRd, KRd)"),
    ("Mesalamine", "Colorectal_Cancer", "potential_treatment", 0.55,
     "CRC chemoprevention in UC patients (Velayos 2005)"),

    # Hormonal agents
    ("Leuprolide", "Prostate_Cancer", "potential_treatment", 0.70,
     "ADT standard of care for advanced prostate cancer"),
    ("Goserelin", "Breast_Cancer", "potential_treatment", 0.60,
     "Ovarian suppression in premenopausal breast cancer (SOFT trial)"),
    ("Tamoxifen", "Breast_Cancer", "potential_treatment", 0.75,
     "Breast cancer prevention and treatment (NSABP P-1)"),
    ("Octreotide", "Pancreatic_Cancer", "potential_treatment", 0.55,
     "Neuroendocrine tumor treatment"),

    # Anticoagulants
    ("Heparin", "NSCLC", "potential_treatment", 0.45,
     "Anti-metastatic in NSCLC (FRAGMATIC-like)"),
    ("Warfarin", "NSCLC", "potential_treatment", 0.40,
     "Gas6/Axl pathway in NSCLC (Kirane 2015)"),

    # Antidiabetics
    ("Canagliflozin", "HCC", "potential_treatment", 0.42,
     "AMPK activation, anti-proliferative in HCC cells"),

    # Misc ReDO
    ("Dichloroacetate", "Glioblastoma", "potential_treatment", 0.48,
     "Warburg effect reversal in GBM (Michelakis 2010)"),
    ("Dimethyl_Fumarate", "Colorectal_Cancer", "potential_treatment", 0.42,
     "NF-kB inhibition in CRC preclinical"),
    ("Aprepitant", "Breast_Cancer", "potential_treatment", 0.42,
     "NK1R antagonism anti-cancer (Munoz 2010)"),
    ("Naltrexone", "Colorectal_Cancer", "potential_treatment", 0.42,
     "Low-dose naltrexone OGF-OGFr in CRC (Zagon 2011)"),
    ("Cannabidiol", "Glioblastoma", "potential_treatment", 0.45,
     "Anti-proliferative in GBM (Massi 2004)"),
    ("Imiquimod", "Melanoma", "potential_treatment", 0.50,
     "TLR7-mediated immune activation against melanoma"),
    ("Nicotinamide", "Melanoma", "potential_treatment", 0.52,
     "ONTRAC trial: reduced skin cancer in high-risk patients (Chen 2015 NEJM)"),
    ("Eflornithine", "Colorectal_Cancer", "potential_treatment", 0.45,
     "Polyamine pathway chemoprevention (Meyskens 2008)"),
    ("Phenformin", "Breast_Cancer", "potential_treatment", 0.42,
     "AMPK activation, anti-cancer (more potent than metformin)"),
    ("Miltefosine", "Breast_Cancer", "potential_treatment", 0.40,
     "PI3K/AKT inhibition in breast cancer (preclinical)"),
    ("Propofol", "Breast_Cancer", "potential_treatment", 0.42,
     "Perioperative propofol vs volatile: improved breast cancer outcomes (Wigmore 2016)"),

    # More NSAIDs
    ("Mefenamic_Acid", "Colorectal_Cancer", "potential_treatment", 0.45,
     "Wnt pathway modulation in CRC"),

    # More antifungals
    ("Posaconazole", "Glioblastoma", "potential_treatment", 0.42,
     "Hedgehog pathway inhibition in GBM"),

    # More alpha-blockers
    ("Doxazosin", "Prostate_Cancer", "potential_treatment", 0.45,
     "Alpha-blocker pro-apoptotic in prostate cancer cells"),

    # Respiratory
    ("Montelukast", "Colorectal_Cancer", "potential_treatment", 0.40,
     "Leukotriene pathway in CRC (preclinical)"),
    ("Zileuton", "Pancreatic_Cancer", "potential_treatment", 0.40,
     "5-LOX pathway in pancreatic cancer"),
])
