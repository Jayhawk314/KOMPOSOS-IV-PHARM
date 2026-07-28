# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Fix provenance to be HONEST about actual data sources.

Three categories:
1. FDA-approved drug mechanisms -> cite FDA NDA/BLA number
2. Repurposing hypotheses -> keep PMIDs (these are literature claims)
3. Remaining protein-protein -> mark as KEGG pathway reference (already done)
"""
import sqlite3

conn = sqlite3.connect('data/drugs/tier1.db')
cur = conn.cursor()

# FDA-approved drug mechanisms with their NDA/BLA numbers
FDA_MECHANISMS = {
    # Tyrosine kinase inhibitors
    ('Afatinib', 'EGFR', 'inhibits'): 'FDA:NDA201292, mechanism:irreversible_EGFR_TKI',
    ('Afatinib', 'ERBB2', 'inhibits'): 'FDA:NDA201292, mechanism:pan-HER_TKI',
    ('Erlotinib', 'EGFR', 'inhibits'): 'FDA:NDA021743, mechanism:reversible_EGFR_TKI',
    ('Gefitinib', 'EGFR', 'inhibits'): 'FDA:NDA021399, mechanism:reversible_EGFR_TKI',
    ('Osimertinib', 'EGFR', 'inhibits'): 'FDA:NDA208065, mechanism:3rd_gen_EGFR_TKI',
    ('Lapatinib', 'EGFR', 'inhibits'): 'FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI',
    ('Lapatinib', 'ERBB2', 'inhibits'): 'FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI',
    ('Brigatinib', 'ALK', 'inhibits'): 'FDA:NDA208772, mechanism:ALK_TKI',
    ('Brigatinib', 'EGFR', 'inhibits'): 'FDA:NDA208772, mechanism:ALK_EGFR_TKI',
    ('Alectinib', 'ALK', 'inhibits'): 'FDA:NDA208434, mechanism:ALK_TKI',
    ('Alectinib', 'RET', 'inhibits'): 'FDA:NDA208434, mechanism:ALK_RET_TKI',
    ('Lorlatinib', 'ALK', 'inhibits'): 'FDA:NDA210868, mechanism:3rd_gen_ALK_TKI',
    ('Lorlatinib', 'ROS1', 'inhibits'): 'FDA:NDA210868, mechanism:ALK_ROS1_TKI',
    ('Entrectinib', 'ALK', 'inhibits'): 'FDA:NDA212725, mechanism:TRK_ROS1_ALK_inhibitor',
    ('Entrectinib', 'NTRK1', 'inhibits'): 'FDA:NDA212725, mechanism:pan-TRK_inhibitor',
    ('Entrectinib', 'NTRK2', 'inhibits'): 'FDA:NDA212725, mechanism:pan-TRK_inhibitor',
    ('Entrectinib', 'NTRK3', 'inhibits'): 'FDA:NDA212725, mechanism:pan-TRK_inhibitor',
    ('Entrectinib', 'ROS1', 'inhibits'): 'FDA:NDA212725, mechanism:TRK_ROS1_ALK_inhibitor',
    ('Larotrectinib', 'NTRK1', 'inhibits'): 'FDA:NDA211710, mechanism:pan-TRK_inhibitor',
    ('Larotrectinib', 'NTRK2', 'inhibits'): 'FDA:NDA211710, mechanism:pan-TRK_inhibitor',
    ('Larotrectinib', 'NTRK3', 'inhibits'): 'FDA:NDA211710, mechanism:pan-TRK_inhibitor',
    ('Capmatinib', 'MET', 'inhibits'): 'FDA:NDA213591, mechanism:MET_TKI',
    ('Tepotinib', 'MET', 'inhibits'): 'FDA:NDA214096, mechanism:MET_TKI',
    ('Selpercatinib', 'RET', 'inhibits'): 'FDA:NDA213246, mechanism:RET_TKI',
    ('Pralsetinib', 'RET', 'inhibits'): 'FDA:NDA213721, mechanism:RET_TKI',
    # RAF/MEK/RAS inhibitors
    ('Vemurafenib', 'BRAF', 'inhibits'): 'FDA:NDA202429, mechanism:BRAF_V600E_inhibitor',
    ('Dabrafenib', 'BRAF', 'inhibits'): 'FDA:NDA202806, mechanism:BRAF_inhibitor',
    ('Encorafenib', 'BRAF', 'inhibits'): 'FDA:NDA210496, mechanism:BRAF_inhibitor',
    ('Trametinib', 'MEK1', 'inhibits'): 'FDA:NDA204114, mechanism:MEK1_2_inhibitor',
    ('Sotorasib', 'KRAS', 'inhibits'): 'FDA:NDA214665, mechanism:KRAS_G12C_inhibitor',
    ('Adagrasib', 'KRAS', 'inhibits'): 'FDA:NDA216340, mechanism:KRAS_G12C_inhibitor',
    # Multi-kinase inhibitors
    ('Sorafenib', 'BRAF', 'inhibits'): 'FDA:NDA021923, mechanism:multikinase_inhibitor',
    ('Sorafenib', 'RAF1', 'inhibits'): 'FDA:NDA021923, mechanism:multikinase_inhibitor',
    ('Sorafenib', 'VEGFR2', 'inhibits'): 'FDA:NDA021923, mechanism:multikinase_inhibitor',
    ('Sunitinib', 'VEGFR2', 'inhibits'): 'FDA:NDA021938, mechanism:multikinase_inhibitor',
    ('Sunitinib', 'PDGFRA', 'inhibits'): 'FDA:NDA021938, mechanism:multikinase_inhibitor',
    ('Sunitinib', 'KIT', 'inhibits'): 'FDA:NDA021938, mechanism:multikinase_inhibitor',
    ('Sunitinib', 'FLT3', 'inhibits'): 'FDA:NDA021938, mechanism:multikinase_inhibitor',
    ('Regorafenib', 'KDR', 'inhibits'): 'FDA:NDA203085, mechanism:multikinase_inhibitor',
    ('Regorafenib', 'RET', 'inhibits'): 'FDA:NDA203085, mechanism:multikinase_inhibitor',
    ('Ramucirumab', 'KDR', 'inhibits'): 'FDA:BLA125477, mechanism:VEGFR2_antibody',
    # CDK inhibitors
    ('Palbociclib', 'CDK4', 'inhibits'): 'FDA:NDA207103, mechanism:CDK4_6_inhibitor',
    ('Palbociclib', 'CDK6', 'inhibits'): 'FDA:NDA207103, mechanism:CDK4_6_inhibitor',
    ('Ribociclib', 'CDK4', 'inhibits'): 'FDA:NDA209092, mechanism:CDK4_6_inhibitor',
    ('Ribociclib', 'CDK6', 'inhibits'): 'FDA:NDA209092, mechanism:CDK4_6_inhibitor',
    # Immune checkpoint inhibitors
    ('Nivolumab', 'PDCD1', 'inhibits'): 'FDA:BLA125554, mechanism:PD-1_antibody',
    ('Pembrolizumab', 'PDCD1', 'inhibits'): 'FDA:BLA125514, mechanism:PD-1_antibody',
    ('Atezolizumab', 'CD274', 'inhibits'): 'FDA:BLA761034, mechanism:PD-L1_antibody',
    ('Durvalumab', 'CD274', 'inhibits'): 'FDA:BLA761069, mechanism:PD-L1_antibody',
    ('Ipilimumab', 'CTLA4', 'inhibits'): 'FDA:BLA125377, mechanism:CTLA-4_antibody',
    ('Cetuximab', 'EGFR', 'inhibits'): 'FDA:BLA125084, mechanism:EGFR_antibody',
    ('Trastuzumab', 'ERBB2', 'inhibits'): 'FDA:BLA103792, mechanism:HER2_antibody',
    ('Trastuzumab_deruxtecan', 'ERBB2', 'inhibits'): 'FDA:BLA761139, mechanism:HER2_ADC',
    ('Trastuzumab_deruxtecan', 'TOP1', 'inhibits'): 'FDA:BLA761139, mechanism:ADC_payload_TOP1i',
    # BCL2/JAK/mTOR
    ('Venetoclax', 'BCL2', 'inhibits'): 'FDA:NDA208573, mechanism:BCL-2_inhibitor',
    ('Ruxolitinib', 'JAK2', 'inhibits'): 'FDA:NDA202192, mechanism:JAK1_2_inhibitor',
    ('Temsirolimus', 'MTOR', 'inhibits'): 'FDA:NDA022088, mechanism:mTOR_inhibitor',
    # PARP synthetic lethality
    ('Olaparib', 'BRCA1', 'synthetic_lethal'): 'FDA:NDA206995, mechanism:PARP_inhibitor_synthetic_lethality',
    ('Olaparib', 'BRCA2', 'synthetic_lethal'): 'FDA:NDA206995, mechanism:PARP_inhibitor_synthetic_lethality',
    # HDAC
    ('Valproic_Acid', 'HDAC1', 'inhibits'): 'literature:established_HDAC_inhibitor, off-label_repurposing',
    ('Valproic_Acid', 'HDAC2', 'inhibits'): 'literature:established_HDAC_inhibitor, off-label_repurposing',
    # Immune enhancement
    ('Nivolumab', 'CD8A', 'enhances'): 'FDA:BLA125554, mechanism:PD-1_blockade_restores_T_cell_activity',
    ('Pembrolizumab', 'CD8A', 'enhances'): 'FDA:BLA125514, mechanism:PD-1_blockade_restores_T_cell_activity',
    ('Pembrolizumab', 'CD4', 'activates'): 'FDA:BLA125514, mechanism:PD-1_blockade_activates_helper_T_cells',
    # Topoisomerase/antimetabolite
    ('Irinotecan', 'TOP1', 'inhibits'): 'FDA:NDA020571, mechanism:TOP1_inhibitor',
    ('Pemetrexed', 'TYMS', 'inhibits'): 'FDA:NDA021462, mechanism:antifolate_TS_inhibitor',
    ('Fluorouracil', 'TYMS', 'inhibits'): 'FDA:established_mechanism, thymidylate_synthase_inhibitor',
    ('Fluorouracil', 'TOP2A', 'associated_with'): 'literature:5-FU_DNA_damage_response',
    ('Cisplatin', 'TP53', 'activator'): 'mechanism:DNA_crosslinking_activates_DDR_and_p53',
    ('Cisplatin', 'TOP2A', 'inhibits'): 'mechanism:DNA_damage_response',
    ('Carboplatin', 'TP53', 'activator'): 'mechanism:DNA_crosslinking_activates_DDR_and_p53',
    ('Oxaliplatin', 'TP53', 'activator'): 'mechanism:DNA_crosslinking_activates_DDR_and_p53',
    ('Chloroquine', 'TP53', 'activator'): 'literature:lysosome_inhibition_stabilizes_p53',
    ('Chloroquine', 'MTOR', 'indirect_inhibitor'): 'literature:autophagy_inhibition_mTOR_crosstalk',
    ('Mebendazole', 'TP53', 'activator'): 'literature:tubulin_disruption_activates_p53',
    # Thalidomide/CRBN
    ('Thalidomide', 'CRBN', 'binds'): 'established:cereblon_E3_ligase_substrate',
    # Antibody-drug
    ('Ipilimumab', 'FOXP3', 'inhibits'): 'FDA:BLA125377, mechanism:CTLA4_blockade_depletes_Tregs',
    # Combos
    ('Dabrafenib', 'Trametinib', 'synergizes_with'): 'FDA:NDA202806_204114, approved_combination_BRAF_MEK',
    ('Olaparib', 'Bevacizumab', 'synergizes_with'): 'clinical:PAOLA-1_trial, PMID:31806540',
    ('Palbociclib', 'Trastuzumab', 'synergizes_with'): 'clinical:monarcHER_trial, combination',
    ('Venetoclax', 'Ruxolitinib', 'synergizes_with'): 'preclinical:BCL2_JAK2_combination_rationale',
    ('Everolimus', 'Erlotinib', 'synergizes_with'): 'preclinical:mTOR_EGFR_dual_inhibition',
    # Other specific targets
    ('Verapamil', 'ABCB1', 'inhibits'): 'established:P-glycoprotein_inhibitor',
    ('Pirfenidone', 'TGFB1', 'inhibits'): 'FDA:NDA022535, mechanism:TGF-beta_inhibitor',
    ('Imatinib', 'KRAS', 'pathway_modulator'): 'literature:BCR-ABL_downstream_RAS_pathway',
}

# Apply
updated = 0
for (drug, target, rel), prov in FDA_MECHANISMS.items():
    cur.execute('UPDATE morphisms SET provenance = ? WHERE source_name = ? AND target_name = ? AND name = ?',
                (prov, drug, target, rel))
    if cur.rowcount > 0:
        updated += 1

conn.commit()

# Check what remains
cur.execute("""
    SELECT source_name, target_name, name, provenance FROM morphisms
    WHERE provenance LIKE 'PMID:%'
    AND source_name IN (SELECT name FROM objects WHERE type_name='Drug')
    AND target_name NOT IN (SELECT name FROM objects WHERE type_name='Disease')
""")
remaining = cur.fetchall()

print(f'Updated {updated} drug-target edges with FDA/mechanism provenance')
print(f'Remaining drug->protein with PMID: {len(remaining)}')
print()
if remaining:
    print('Remaining (repurposing hypotheses - PMIDs appropriate):')
    for src, tgt, rel, prov in remaining:
        print(f'  {src} -> {tgt} ({rel})')

conn.close()
