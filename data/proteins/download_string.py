# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Download and process STRING database for cancer proteins.

STRING DB: https://string-db.org/
Focus: Human cancer-related proteins from multiple pathways
"""

import requests
import gzip
import io
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

# Cancer-related gene lists from major databases
CANCER_GENE_LISTS = {
    # Oncogenes and tumor suppressors from COSMIC
    'cosmic_census': [
        'TP53', 'KRAS', 'NRAS', 'HRAS', 'BRAF', 'PIK3CA', 'PTEN', 'AKT1', 'AKT2', 'AKT3',
        'EGFR', 'ERBB2', 'ERBB3', 'ERBB4', 'MET', 'ALK', 'RET', 'ROS1', 'FGFR1', 'FGFR2',
        'FGFR3', 'FGFR4', 'MYC', 'MYCN', 'MYCL', 'MDM2', 'MDM4', 'CDKN2A', 'CDKN2B', 'CDK4',
        'CDK6', 'CCND1', 'CCND2', 'CCND3', 'RB1', 'E2F1', 'E2F2', 'E2F3', 'BRCA1', 'BRCA2',
        'ATM', 'ATR', 'CHEK1', 'CHEK2', 'RAD51', 'RAD52', 'XRCC1', 'XRCC2', 'PALB2', 'FANCA',
        'FANCD2', 'MLH1', 'MSH2', 'MSH6', 'PMS2', 'POLE', 'POLD1', 'VHL', 'HIF1A', 'EPAS1',
        'VEGFA', 'VEGFR1', 'VEGFR2', 'VEGFR3', 'PDGFRA', 'PDGFRB', 'KIT', 'FLT3', 'JAK1',
        'JAK2', 'JAK3', 'STAT3', 'STAT5A', 'STAT5B', 'NOTCH1', 'NOTCH2', 'NOTCH3', 'NOTCH4',
        'WNT1', 'WNT2', 'WNT3', 'CTNNB1', 'APC', 'AXIN1', 'AXIN2', 'TCF7L2', 'SMAD2', 'SMAD3',
        'SMAD4', 'TGFBR1', 'TGFBR2', 'MTOR', 'TSC1', 'TSC2', 'STK11', 'NF1', 'NF2', 'PTCH1',
        'SMO', 'GLI1', 'GLI2', 'BCL2', 'BCL2L1', 'BCL2L2', 'MCL1', 'BAX', 'BAK1', 'BAD',
        'BID', 'BIM', 'CASP3', 'CASP8', 'CASP9', 'APAF1', 'CYCS', 'FAS', 'FASLG', 'TNFRSF1A',
        'IDH1', 'IDH2', 'ARID1A', 'ARID1B', 'ARID2', 'SMARCA4', 'SMARCB1', 'KMT2A', 'KMT2C',
        'KMT2D', 'SETD2', 'DNMT1', 'DNMT3A', 'DNMT3B', 'TET1', 'TET2', 'CREBBP', 'EP300',
        'MEN1', 'GATA3', 'FOXA1', 'ESR1', 'AR', 'SPOP', 'FOXA2', 'MAX', 'SRC', 'ABL1',
        'LCK', 'FYN', 'LYN', 'YES1', 'FGR', 'HCK', 'BLK', 'MAPK1', 'MAPK3', 'MAP2K1',
        'MAP2K2', 'RAF1', 'ARAF', 'MAP3K1', 'MAP3K7', 'RHOA', 'RAC1', 'CDC42', 'RALA',
        'RALB', 'RRAS', 'RRAS2', 'MRAS', 'GRB2', 'SOS1', 'SOS2', 'GAB1', 'GAB2', 'IRS1',
        'IRS2', 'INSR', 'IGF1R', 'IGF2R', 'FANCL', 'FANCM', 'ERCC1', 'ERCC2', 'ERCC3',
        'ERCC4', 'ERCC5', 'XPA', 'XPC', 'DDB2', 'KEAP1', 'NFE2L2', 'CUL3', 'RBX1',
        'SKP1', 'SKP2', 'FBXW7', 'MDM4', 'USP7', 'USP9X', 'SIAH1', 'SIAH2', 'CBL',
        'CBLB', 'CBLC', 'TRAF1', 'TRAF2', 'TRAF3', 'TRAF4', 'TRAF5', 'TRAF6', 'BIRC2',
        'BIRC3', 'BIRC5', 'XIAP', 'IKBKA', 'IKBKB', 'IKBKG', 'NFKB1', 'NFKB2', 'RELA',
        'RELB', 'REL', 'CHUK', 'BCR', 'ABL2', 'PDCD1', 'CD274', 'PDCD1LG2', 'CTLA4',
        'CD80', 'CD86', 'CD28', 'ICOS', 'ICOSLG', 'LAG3', 'HAVCR2', 'TIGIT', 'BTLA',
        'VISTA', 'TNFRSF4', 'TNFSF4', 'TNFRSF9', 'TNFSF9', 'TNFRSF18', 'TNFSF18'
    ]
}

# STRING API endpoints
STRING_API = "https://string-db.org/api"
STRING_SPECIES = "9606"  # Human

def download_string_interactions(proteins: List[str],
                                 score_threshold: int = 400,
                                 limit: int = 10000) -> List[Tuple[str, str, float]]:
    """
    Download protein-protein interactions from STRING database.

    Args:
        proteins: List of gene names
        score_threshold: Minimum combined score (0-1000), 400 = medium confidence
        limit: Maximum number of interactions per protein

    Returns:
        List of (protein1, protein2, confidence) tuples
    """
    print(f"[STRING] Downloading interactions for {len(proteins)} proteins...")
    print(f"[STRING] Score threshold: {score_threshold}/1000")

    # Build identifiers query
    identifiers = "%0d".join(proteins)

    # Network endpoint
    url = f"{STRING_API}/tsv/network"
    params = {
        'identifiers': identifiers,
        'species': STRING_SPECIES,
        'required_score': score_threshold,
        'limit': limit,
        'network_type': 'functional'  # functional includes physical + pathway
    }

    print(f"[STRING] Fetching from API...")
    response = requests.get(url, params=params, timeout=300)
    response.raise_for_status()

    # Parse TSV
    lines = response.text.strip().split('\n')
    header = lines[0].split('\t')

    # Find column indices
    try:
        prot1_idx = header.index('preferredName_A')
        prot2_idx = header.index('preferredName_B')
        score_idx = header.index('score')
    except ValueError:
        # Fallback: assume columns are stringId_A, stringId_B, preferredName_A, preferredName_B, score
        print(f"[STRING] Header: {header}")
        prot1_idx = 2  # preferredName_A
        prot2_idx = 3  # preferredName_B
        score_idx = 5  # score

    interactions = []
    seen_pairs = set()

    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) < max(prot1_idx, prot2_idx, score_idx) + 1:
            continue

        protein1 = parts[prot1_idx]
        protein2 = parts[prot2_idx]

        try:
            score = float(parts[score_idx])
        except (ValueError, IndexError):
            continue

        # Normalize score to 0-1
        if score > 1.0:
            score = score / 1000.0

        # Deduplicate (A-B same as B-A)
        pair = tuple(sorted([protein1, protein2]))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            interactions.append((protein1, protein2, score))

    print(f"[STRING] Downloaded {len(interactions)} interactions")
    return interactions


def get_protein_annotations(proteins: List[str]) -> Dict[str, Dict]:
    """
    Get protein annotations from STRING.

    Returns:
        Dict mapping protein name to metadata (GO terms, pathways, etc.)
    """
    print(f"[STRING] Fetching annotations for {len(proteins)} proteins...")

    identifiers = "%0d".join(proteins)

    url = f"{STRING_API}/json/enrichment"
    params = {
        'identifiers': identifiers,
        'species': STRING_SPECIES
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    enrichment = response.json()

    # Parse annotations
    annotations = {}
    for protein in proteins:
        annotations[protein] = {
            'pathways': [],
            'go_terms': [],
            'diseases': []
        }

    # Extract pathway information
    for item in enrichment:
        category = item.get('category', '')
        term = item.get('term', '')

        if 'KEGG' in category or 'Reactome' in category:
            # Pathway annotation
            for protein in proteins:
                if protein in item.get('preferredNames', ''):
                    annotations[protein]['pathways'].append(term)

    print(f"[STRING] Annotated {len(annotations)} proteins")
    return annotations


def build_cancer_protein_dataset(max_proteins: int = 5000) -> Tuple[Dict, List]:
    """
    Build large-scale cancer protein interaction dataset.

    Args:
        max_proteins: Maximum number of proteins to include

    Returns:
        (proteins_dict, interactions_list)
    """
    print("=" * 80)
    print("STRING Cancer Protein Dataset Builder")
    print("=" * 80)
    print()

    # Start with core cancer genes
    core_genes = CANCER_GENE_LISTS['cosmic_census'][:max_proteins]

    print(f"[1/4] Core cancer genes: {len(core_genes)}")

    # Download interactions
    interactions = download_string_interactions(
        core_genes,
        score_threshold=400,  # Medium confidence
        limit=20  # Top 20 per protein
    )

    # Get all unique proteins from interactions
    all_proteins = set(core_genes)
    for p1, p2, score in interactions:
        # Extract gene names from STRING format
        # STRING returns "9606.ENSP00000269305" format
        # We need to map back to gene names
        all_proteins.add(p1)
        all_proteins.add(p2)

    print(f"[2/4] Total proteins after expansion: {len(all_proteins)}")

    # Get annotations
    annotations = get_protein_annotations(list(all_proteins)[:max_proteins])

    # Build protein metadata
    proteins_dict = {}
    for protein in all_proteins:
        if len(proteins_dict) >= max_proteins:
            break

        # Infer type from known lists
        ptype = "Protein"
        if protein in core_genes[:50]:
            ptype = "Oncogene"
        elif protein in core_genes[50:100]:
            ptype = "TumorSuppressor"

        proteins_dict[protein] = {
            'type': ptype,
            'pathways': annotations.get(protein, {}).get('pathways', ['unknown'])[:3],
            'source': 'STRING'
        }

    print(f"[3/4] Built metadata for {len(proteins_dict)} proteins")

    # Filter interactions to only included proteins
    filtered_interactions = []
    for p1, p2, score in interactions:
        if p1 in proteins_dict and p2 in proteins_dict:
            filtered_interactions.append((p1, p2, score))

    print(f"[4/4] Filtered to {len(filtered_interactions)} interactions")
    print()
    print("=" * 80)
    print(f"Dataset ready: {len(proteins_dict)} proteins, {len(filtered_interactions)} interactions")
    print("=" * 80)

    return proteins_dict, filtered_interactions


def save_dataset(proteins: Dict, interactions: List, output_dir: str = "data/proteins"):
    """Save dataset to JSON for loading."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    dataset = {
        'proteins': proteins,
        'interactions': [
            {
                'source': p1,
                'target': p2,
                'confidence': score
            }
            for p1, p2, score in interactions
        ]
    }

    output_file = output_path / "string_cancer_large.json"
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"Saved dataset to: {output_file}")
    return output_file


if __name__ == "__main__":
    # Build dataset
    proteins, interactions = build_cancer_protein_dataset(max_proteins=5000)

    # Save
    save_dataset(proteins, interactions)
