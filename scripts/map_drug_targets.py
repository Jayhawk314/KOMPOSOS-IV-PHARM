# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Map novel predictions to FDA-approved drugs and therapeutic opportunities.
"""
import csv
from pathlib import Path
from typing import List, Dict, Tuple

# Hardcoded drug database for 36 cancer proteins
DRUG_DATABASE = {
    # Kinases (highly druggable)
    "EGFR": {
        "druggable": True,
        "drug_class": "receptor_tyrosine_kinase",
        "fda_drugs": ["Erlotinib", "Gefitinib", "Afatinib", "Osimertinib", "Cetuximab"],
        "cancers": ["lung", "colorectal", "head_neck"]
    },
    "BRAF": {
        "druggable": True,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": ["Vemurafenib", "Dabrafenib", "Encorafenib"],
        "cancers": ["melanoma", "thyroid", "colorectal"]
    },
    "CDK4": {
        "druggable": True,
        "drug_class": "cyclin_dependent_kinase",
        "fda_drugs": ["Palbociclib", "Ribociclib", "Abemaciclib"],
        "cancers": ["breast", "liposarcoma"]
    },
    "CDK6": {
        "druggable": True,
        "drug_class": "cyclin_dependent_kinase",
        "fda_drugs": ["Palbociclib", "Ribociclib", "Abemaciclib"],
        "cancers": ["breast", "liposarcoma"]
    },
    "MTOR": {
        "druggable": True,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": ["Everolimus", "Temsirolimus"],
        "cancers": ["renal", "breast", "neuroendocrine"]
    },
    "PIK3CA": {
        "druggable": True,
        "drug_class": "lipid_kinase",
        "fda_drugs": ["Alpelisib"],
        "cancers": ["breast"]
    },
    "JAK2": {
        "druggable": True,
        "drug_class": "tyrosine_kinase",
        "fda_drugs": ["Ruxolitinib", "Fedratinib"],
        "cancers": ["myelofibrosis", "polycythemia"]
    },
    "ABL1": {
        "druggable": True,
        "drug_class": "tyrosine_kinase",
        "fda_drugs": ["Imatinib", "Dasatinib", "Nilotinib"],
        "cancers": ["CML", "ALL"]
    },
    "SRC": {
        "druggable": True,
        "drug_class": "tyrosine_kinase",
        "fda_drugs": ["Dasatinib"],
        "cancers": ["CML"]
    },
    "KDR": {  # VEGFR2
        "druggable": True,
        "drug_class": "receptor_tyrosine_kinase",
        "fda_drugs": ["Sorafenib", "Sunitinib", "Pazopanib", "Bevacizumab"],
        "cancers": ["renal", "hepatocellular", "colorectal"]
    },

    # RAS family (challenging but indirect targeting)
    "KRAS": {
        "druggable": True,
        "drug_class": "small_gtpase",
        "fda_drugs": ["Sotorasib", "Adagrasib"],  # G12C specific
        "cancers": ["lung", "colorectal"]
    },
    "NRAS": {
        "druggable": False,
        "drug_class": "small_gtpase",
        "fda_drugs": [],
        "indirect": ["MEK inhibitors (Trametinib)"]
    },
    "HRAS": {
        "druggable": False,
        "drug_class": "small_gtpase",
        "fda_drugs": [],
        "indirect": ["MEK inhibitors"]
    },

    # Tumor suppressors (challenging - loss of function)
    "TP53": {
        "druggable": False,
        "drug_class": "transcription_factor",
        "fda_drugs": [],
        "indirect": ["APR-246 (eprenetapopt) - clinical trials", "MDM2 inhibitors"]
    },
    "PTEN": {
        "druggable": False,
        "drug_class": "phosphatase",
        "fda_drugs": [],
        "indirect": ["PI3K inhibitors"]
    },
    "BRCA1": {
        "druggable": False,
        "drug_class": "dna_repair",
        "fda_drugs": [],
        "indirect": ["PARP inhibitors (Olaparib, Rucaparib)"]
    },
    "BRCA2": {
        "druggable": False,
        "drug_class": "dna_repair",
        "fda_drugs": [],
        "indirect": ["PARP inhibitors (Olaparib, Rucaparib)"]
    },
    "ATM": {
        "druggable": False,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": [],
        "indirect": ["ATR inhibitors - clinical trials"]
    },
    "CHEK2": {
        "druggable": False,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": [],
        "indirect": ["CHK1 inhibitors - clinical trials"]
    },

    # Oncogenes (transcription factors - challenging)
    "MYC": {
        "druggable": False,
        "drug_class": "transcription_factor",
        "fda_drugs": [],
        "indirect": ["BET inhibitors - clinical trials", "CDK7 inhibitors"]
    },

    # Signal transduction
    "AKT1": {
        "druggable": True,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": ["Capivasertib (Truqap)"],
        "cancers": ["breast"]
    },
    "STAT3": {
        "druggable": False,
        "drug_class": "transcription_factor",
        "fda_drugs": [],
        "indirect": ["JAK inhibitors"]
    },
    "STAT5": {
        "druggable": False,
        "drug_class": "transcription_factor",
        "fda_drugs": [],
        "indirect": ["JAK inhibitors"]
    },
    "RAF1": {
        "druggable": True,
        "drug_class": "serine_threonine_kinase",
        "fda_drugs": ["Sorafenib"],
        "cancers": ["renal", "hepatocellular"]
    },

    # Apoptosis
    "BCL2": {
        "druggable": True,
        "drug_class": "apoptosis_regulator",
        "fda_drugs": ["Venetoclax"],
        "cancers": ["CLL", "AML"]
    },
    "BAX": {
        "druggable": False,
        "drug_class": "apoptosis_regulator",
        "fda_drugs": [],
        "indirect": ["BCL2 inhibitors"]
    },
    "CASP3": {
        "druggable": False,
        "drug_class": "cysteine_protease",
        "fda_drugs": [],
        "indirect": ["IAP inhibitors"]
    },

    # Other
    "MDM2": {
        "druggable": False,
        "drug_class": "e3_ubiquitin_ligase",
        "fda_drugs": [],
        "indirect": ["MDM2 inhibitors - clinical trials"]
    },
    "RB1": {
        "druggable": False,
        "drug_class": "tumor_suppressor",
        "fda_drugs": [],
        "indirect": ["CDK4/6 inhibitors"]
    },
    "ERBB2": {  # HER2
        "druggable": True,
        "drug_class": "receptor_tyrosine_kinase",
        "fda_drugs": ["Trastuzumab", "Pertuzumab", "Ado-trastuzumab", "Lapatinib"],
        "cancers": ["breast", "gastric"]
    },
    "MET": {
        "druggable": True,
        "drug_class": "receptor_tyrosine_kinase",
        "fda_drugs": ["Capmatinib", "Tepotinib"],
        "cancers": ["lung"]
    },
    "FGFR2": {
        "druggable": True,
        "drug_class": "receptor_tyrosine_kinase",
        "fda_drugs": ["Pemigatinib", "Infigratinib"],
        "cancers": ["cholangiocarcinoma"]
    },
    "RAD51": {
        "druggable": False,
        "drug_class": "dna_repair",
        "fda_drugs": [],
        "indirect": ["PARP inhibitors"]
    },
    "NOTCH1": {
        "druggable": False,
        "drug_class": "transmembrane_receptor",
        "fda_drugs": [],
        "indirect": ["Gamma-secretase inhibitors - clinical trials"]
    },
    "CTNNB1": {  # Beta-catenin
        "druggable": False,
        "drug_class": "transcription_coactivator",
        "fda_drugs": [],
        "indirect": ["Wnt pathway inhibitors - clinical trials"]
    },
}


def load_novelty_results(csv_path: Path) -> List[Dict]:
    """Load predictions with novelty labels."""
    predictions = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions.append({
                'rank': int(row['rank']),
                'source': row['source'],
                'target': row['target'],
                'confidence': float(row['confidence']),
                'system': row['system'],
                'novelty': row['novelty']
            })
    return predictions


def compute_therapeutic_score(pred: Dict, db: Dict) -> Tuple[float, int, str, str]:
    """
    Compute therapeutic potential score.

    Returns: (score, tier, source_drugs, target_drugs)
    """
    source = pred['source']
    target = pred['target']
    confidence = pred['confidence']
    novelty = 1.0 if pred['novelty'] == 'NOVEL' else 0.5

    # Get druggability
    source_info = db.get(source, {})
    target_info = db.get(target, {})

    source_druggable = source_info.get('druggable', False)
    target_druggable = target_info.get('druggable', False)

    source_drugs = ", ".join(source_info.get('fda_drugs', [])) if source_druggable else "None"
    target_drugs = ", ".join(target_info.get('fda_drugs', [])) if target_druggable else "None"

    # Add indirect drugs if direct not available
    if not source_druggable and 'indirect' in source_info:
        source_drugs = f"Indirect: {', '.join(source_info['indirect'])}"
    if not target_druggable and 'indirect' in target_info:
        target_drugs = f"Indirect: {', '.join(target_info['indirect'])}"

    # Druggability score
    if source_druggable and target_druggable:
        druggability = 1.0
        tier = 1
    elif source_druggable or target_druggable:
        druggability = 0.5
        tier = 2
    else:
        druggability = 0.1
        tier = 3

    score = druggability * confidence * novelty

    return score, tier, source_drugs, target_drugs


def main():
    print("=" * 80)
    print("PHASE 3: DRUG TARGET MAPPING")
    print("=" * 80)
    print()

    # Load novelty results
    novelty_file = Path('reports/predictions_with_novelty.csv')
    if not novelty_file.exists():
        print(f"ERROR: {novelty_file} not found")
        print("Run check_novelty_comprehensive.py first")
        return

    predictions = load_novelty_results(novelty_file)
    novel_predictions = [p for p in predictions if p['novelty'] == 'NOVEL']

    print(f"Total predictions: {len(predictions)}")
    print(f"Novel predictions: {len(novel_predictions)} ({len(novel_predictions)/len(predictions)*100:.1f}%)")
    print()

    # Score all predictions
    scored = []
    for pred in novel_predictions:
        score, tier, source_drugs, target_drugs = compute_therapeutic_score(pred, DRUG_DATABASE)
        scored.append({
            **pred,
            'therapeutic_score': score,
            'tier': tier,
            'source_drugs': source_drugs,
            'target_drugs': target_drugs
        })

    # Sort by score
    scored.sort(key=lambda x: x['therapeutic_score'], reverse=True)

    # Count by tier
    tier1 = [s for s in scored if s['tier'] == 1]
    tier2 = [s for s in scored if s['tier'] == 2]
    tier3 = [s for s in scored if s['tier'] == 3]

    print("THERAPEUTIC OPPORTUNITY SUMMARY")
    print("=" * 80)
    print()
    print(f"Total novel predictions: {len(novel_predictions)}")
    print(f"Tier 1 (Both druggable): {len(tier1)} predictions")
    print(f"Tier 2 (One druggable): {len(tier2)} predictions")
    print(f"Tier 3 (Research only): {len(tier3)} predictions")
    print()

    # Export full results
    output_file = Path('reports/therapeutic_opportunities.csv')
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['tier', 'rank', 'source', 'target', 'confidence', 'novelty',
                     'therapeutic_score', 'source_drugs', 'target_drugs', 'system']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, s in enumerate(scored, 1):
            writer.writerow({
                'tier': s['tier'],
                'rank': i,
                'source': s['source'],
                'target': s['target'],
                'confidence': s['confidence'],
                'novelty': s['novelty'],
                'therapeutic_score': f"{s['therapeutic_score']:.4f}",
                'source_drugs': s['source_drugs'],
                'target_drugs': s['target_drugs'],
                'system': s['system']
            })

    print(f"Saved: {output_file}")
    print()

    # Print top opportunities by tier
    print("=" * 80)
    print("TIER 1: IMMEDIATE DRUG OPPORTUNITIES (Both Proteins Druggable)")
    print("=" * 80)
    print()

    if tier1:
        for i, opp in enumerate(tier1[:10], 1):
            print(f"{i}. {opp['source']} -> {opp['target']} | Score: {opp['therapeutic_score']:.4f} | {opp['system']}")
            print(f"   Source drugs: {opp['source_drugs']}")
            print(f"   Target drugs: {opp['target_drugs']}")
            print()
    else:
        print("No Tier 1 opportunities found")
        print()

    print("=" * 80)
    print("TIER 2: SINGLE-TARGET OPPORTUNITIES (One Protein Druggable)")
    print("=" * 80)
    print()

    if tier2:
        for i, opp in enumerate(tier2[:10], 1):
            print(f"{i}. {opp['source']} -> {opp['target']} | Score: {opp['therapeutic_score']:.4f} | {opp['system']}")
            if opp['source_drugs'] != "None":
                print(f"   Druggable: {opp['source']} ({opp['source_drugs']})")
            if opp['target_drugs'] != "None":
                print(f"   Druggable: {opp['target']} ({opp['target_drugs']})")
            print()
    else:
        print("No Tier 2 opportunities found")
        print()

    # Generate summary statistics
    print("=" * 80)
    print("KEY STATISTICS FOR GOOGLE/DEEPMIND")
    print("=" * 80)
    print()
    print(f"Novel predictions discovered: {len(novel_predictions)}")
    print(f"Druggable opportunities (Tier 1+2): {len(tier1) + len(tier2)}")
    print(f"Immediate combination therapies (Tier 1): {len(tier1)}")
    print(f"Single-agent opportunities (Tier 2): {len(tier2)}")
    print()

    # Count biological vs text
    bio_tier1 = len([t for t in tier1 if t['system'] == 'Biological'])
    text_tier1 = len([t for t in tier1 if t['system'] == 'Text'])

    print(f"Tier 1 by system:")
    print(f"  Biological (ESM-2): {bio_tier1}")
    print(f"  Text (MPNet): {text_tier1}")
    print()


if __name__ == "__main__":
    main()
