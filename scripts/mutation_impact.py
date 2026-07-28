# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins
#!/usr/bin/env python3

"""
Mutation Impact Analysis Pipeline
===================================
From a protein sequence and mutation -> drug recommendations.

Pipeline:
  1. Apply mutation to sequence
  2. ESM-2 contact prediction (wild-type vs mutant)
  3. Contact map differencing (gained/lost contacts)
  4. Chemistry validation (energy delta, H-bonds, clashes)
  5. Ricci curvature analysis (binding region disruption)
  6. Persistent homology (pocket/cavity changes)
  7. Drug recommendations from curated network

Why this matters:
  Oncologists face this exact problem daily. Patient's tumor has a specific
  mutation. Which drug still works? This gives a physics-grounded answer
  from just the mutant sequence in under 2 minutes on a laptop.

Usage:
    python mutation_impact.py --protein EGFR --mutation L858R
    python mutation_impact.py --protein BRAF --mutation V600E
    python mutation_impact.py --protein EGFR --mutation T790M
    python mutation_impact.py --sequence MKLVS... --mutation L100G --protein Custom
"""

import sys
import time
import json
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent))


# ============================================================================
# CLINICALLY IMPORTANT MUTATIONS (with sequences)
# These are the most common actionable oncology mutations.
# Sequences are the kinase domain or functional domain (UniProt).
# ============================================================================

# EGFR kinase domain (UniProt P00533, residues 696-1022)
# Position numbering matches clinical convention (L858R = position 163 in this fragment)
EGFR_KINASE_DOMAIN = (
    "FKKIKVLGSGAFGTVYKGLWIPEGEKVKIPVAIKELREATSPKANKEILDEAYVMASVDNPHVCRLLGI"
    "CLTSTVQLITQLMPFGCLLDYVREHKDNIGSQYLLNWCVQIAKGMNYLEDRRLVHRDLAARNVLVKTPQ"
    "HVKITDFGLAKLLGAEEKEYHAEGGKVPIKWMALESILHRIYTHQSDVWSYGVTVWELMTFGSKPYDGIP"
    "ASEISSILEKGERLPQPPICTIDVYMIMVKCWMIDADSRPKFRELIIEFSKMARDPQRYLVIQGDERMHL"
    "PSPTDSNFYRALMDEEDMDDVVDADEYLIPQQGFFSSPSTSRTPLLSSLSATSNNSTVACIDR"
)

# BRAF kinase domain (UniProt P15056, residues 457-717)
BRAF_KINASE_DOMAIN = (
    "IGDFGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNIN"
    "NRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHERPI"
    "FHAVYVNQEEQKISGPDSGFASSGLDRKLEHAKPIQSMCVIGSWSGPQVHIATLQSNQELQQKVSDQKE"
    "QISFLNKIQKTQKFALKTIKNAQESEQKLISEEDLLRKRREQLKHKLEQYTSQIAQLREQFQQ"
)

# KRAS (UniProt P01116, full length 189 aa)
KRAS_FULL = (
    "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY"
    "RKQVVIDGETCLLDILDTAGQEEYSAMRDQYMRTGEGFLCV"
    "FAINNTKSFEDIHHQRQYTKEVDLMRQLLSNSSAKRRLTQE"
    "SPITSIETKLSQHNIALLKEIGRIYEPDCPPTFINQITCEI"
    "LNYHIDMTSASPYIPMEIDQIRDLKRELK"
)

# TP53 DNA-binding domain (UniProt P04637, residues 94-292)
# Contains all 3 Li-Fraumeni Syndrome hotspot mutations: R175H, R248W, R273H
TP53_DNA_BINDING_DOMAIN = (
    "SSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPP"
    "GTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFR"
    "HSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVR"
    "VCACPGRDRRTEEENLRKK"
)

# VEGFR2 kinase domain (UniProt P35968, residues 834-1200)
# Extended to include Y1175 autophosphorylation site at fragment position 341
VEGFR2_KINASE_DOMAIN = (
    "LKLGKPLGRGAFGQVIEADAFGIDKTATCRTVAVKMLKEGATHSEHRALMSELKILIHIG"
    "HHLNVVNLLGACTKPGGPLMVIVEFCKFGNLSTYLRSKRNEFVPYKTKGARFRQGKDYVG"
    "AIPVDLKRRLDSITSSQSSASSGFVEEKSLSDVEEEEAPEDLYKDFLTLEHLICYSFQVA"
    "KGMEFLASRKCIHRDLAARNILLSEKNVVKICDFGLARDIYKDPDYVRKGDARLPLKWMA"
    "PETIFDRVYTIQSDVWSFGVLLWEIFSLGASPYPGVKIDEEFCRRLKEGTRMRAPDYTTP"
    "EMYQTMLDCWHGEPSQRPTFSELVEHLGNLLQANAQQDGKDYIVLPISETLSMEEDSGLS"
    "LPTSPVS"
)

# JAK2 pseudokinase domain (UniProt O60674, residues 536-812)
# V617F is in JH2 (pseudokinase), NOT the kinase domain (JH1)
# V617F at fragment position 81
JAK2_PSEUDOKINASE_DOMAIN = (
    "VFHKIRNEDLIFNESLGQGTFTKIFKGVRREVGDYGQLHETEVLLKVLDKAHRNYSESFF"
    "EAASMMSKLSHKHLVLNYGVCVCGDENILVQEFVKFGSLDTYLKKNKNCINILWKLEVAK"
    "QLAWAMHFLEENTLIHGNVCAKNILLIREEDRKTGNPPFIKLSDPGISITVLPKDILQER"
    "IPWVPPECIENPKNLNLATDKWSFGTTLWEICSGGDKPLSALDSQRKLQFYEDRHQLPAP"
    "KWAELANLINNCMDYEPDFRPSFRAIIRDLNSLFTPD"
)

# Known mutation data: (clinical_name, domain_position, wt_aa, mut_aa, clinical_significance)
KNOWN_MUTATIONS = {
    "EGFR": {
        "L858R": {
            "domain_pos": 146,  # 858-712 = position in kinase domain (starts at 712)
            "wt_aa": "L",
            "mut_aa": "R",
            "clinical": "Most common activating EGFR mutation in NSCLC (40-45% of EGFR mutations). "
                        "Sensitizes to erlotinib, gefitinib, afatinib. Increases kinase activity 50-fold.",
            "drug_response": {
                "Erlotinib": "sensitive",
                "Gefitinib": "sensitive",
                "Cetuximab": "sensitive",
                "Lapatinib": "sensitive",
            },
        },
        "T790M": {
            "domain_pos": 78,  # 790-712
            "wt_aa": "T",
            "mut_aa": "M",
            "clinical": "Gatekeeper mutation causing resistance to first-gen TKIs. "
                        "Found in 50-60% of patients who progress on erlotinib/gefitinib. "
                        "Responds to osimertinib (3rd gen).",
            "drug_response": {
                "Erlotinib": "resistant",
                "Gefitinib": "resistant",
                "Cetuximab": "variable",
                "Lapatinib": "resistant",
            },
        },
        "C797S": {
            "domain_pos": 85,  # 797-712
            "wt_aa": "C",
            "mut_aa": "S",
            "clinical": "Resistance mutation to osimertinib. Eliminates covalent binding site. "
                        "No approved targeted therapy.",
            "drug_response": {
                "Erlotinib": "resistant",
                "Gefitinib": "resistant",
            },
        },
    },
    "BRAF": {
        "V600E": {
            "domain_pos": 143,  # 600-457
            "wt_aa": "V",
            "mut_aa": "E",
            "clinical": "Most common BRAF mutation (>90% of BRAF-mutant melanoma). "
                        "Constitutively activates kinase. Responds to vemurafenib, dabrafenib.",
            "drug_response": {
                "Vemurafenib": "sensitive",
                "Dabrafenib": "sensitive",
                "Sorafenib": "partial",
                "Trametinib": "sensitive (downstream MEK)",
            },
        },
    },
    "KRAS": {
        "G12C": {
            "domain_pos": 12,
            "wt_aa": "G",
            "mut_aa": "C",
            "clinical": "Found in 13% of NSCLC. First directly targetable KRAS mutation. "
                        "Sotorasib (FDA 2021) and adagrasib target this specific mutation.",
            "drug_response": {},
        },
        "G12D": {
            "domain_pos": 12,
            "wt_aa": "G",
            "mut_aa": "D",
            "clinical": "Most common KRAS mutation in pancreatic cancer (30-40%). "
                        "Currently undruggable with approved agents.",
            "drug_response": {},
        },
    },
    "TP53": {
        "R175H": {
            "domain_pos": 81,  # 175-94 = position in DNA-binding domain fragment
            "wt_aa": "R",
            "mut_aa": "H",
            "clinical": "Most common TP53 hotspot mutation. Structural mutant that destabilizes "
                        "the DNA-binding domain. Found in Li-Fraumeni syndrome (germline) and "
                        "~6% of all somatic TP53 mutations across cancers (COSMIC).",
            "drug_response": {
                "Disulfiram": "may_benefit (p53 stabilization)",
                "Mebendazole": "may_benefit (p53/p21 induction)",
            },
        },
        "R248W": {
            "domain_pos": 154,  # 248-94
            "wt_aa": "R",
            "mut_aa": "W",
            "clinical": "Contact mutant — directly disrupts DNA binding without fully unfolding "
                        "the domain. Li-Fraumeni hotspot. Largest structural disruption of "
                        "the LFS hotspots. ~5% of somatic TP53 mutations (COSMIC).",
            "drug_response": {},
        },
        "R273H": {
            "domain_pos": 179,  # 273-94
            "wt_aa": "R",
            "mut_aa": "H",
            "clinical": "Contact mutant — disrupts DNA contact but maintains overall protein fold. "
                        "Li-Fraumeni hotspot. Least structurally disruptive of the LFS hotspots. "
                        "~5% of somatic TP53 mutations (COSMIC).",
            "drug_response": {},
        },
    },
    "VEGFR2": {
        "Y1175F": {
            "domain_pos": 341,  # 1175-834 = position in kinase domain fragment
            "wt_aa": "Y",
            "mut_aa": "F",
            "clinical": "Autophosphorylation site mutation. Abolishes VEGFR2 signaling. "
                        "Y1175 is critical for PLCgamma binding and downstream angiogenesis.",
            "drug_response": {
                "Sorafenib": "variable",
                "Sunitinib": "variable",
                "Bevacizumab": "likely_preserved (targets ligand, not receptor)",
            },
        },
    },
    "JAK2": {
        "V617F": {
            "domain_pos": 81,  # 617-536 = position in pseudokinase domain fragment
            "wt_aa": "V",
            "mut_aa": "F",
            "clinical": "Most common JAK2 mutation. Found in 95% of polycythemia vera, "
                        "60% of myelofibrosis, 50% of essential thrombocythemia. "
                        "Constitutively activates JAK-STAT signaling.",
            "drug_response": {
                "Ruxolitinib": "sensitive",
            },
        },
    },
}

# Map protein names to their domain sequences
PROTEIN_SEQUENCES = {
    "EGFR": EGFR_KINASE_DOMAIN,
    "BRAF": BRAF_KINASE_DOMAIN,
    "KRAS": KRAS_FULL,
    "TP53": TP53_DNA_BINDING_DOMAIN,
    "VEGFR2": VEGFR2_KINASE_DOMAIN,
    "JAK2": JAK2_PSEUDOKINASE_DOMAIN,
}


# ============================================================================
# MUTATION APPLICATION
# ============================================================================

def parse_mutation(mutation_str: str) -> Tuple[str, int, str]:
    """
    Parse mutation notation like L858R.

    Returns: (wt_aa, position, mut_aa)
    Position is 1-indexed as in clinical notation.
    """
    mutation_str = mutation_str.strip()
    wt_aa = mutation_str[0]
    mut_aa = mutation_str[-1]
    position = int(mutation_str[1:-1])
    return wt_aa, position, mut_aa


def apply_mutation(sequence: str, position: int, new_aa: str) -> str:
    """Apply single point mutation. Position is 0-indexed into the sequence."""
    seq_list = list(sequence)
    seq_list[position] = new_aa
    return ''.join(seq_list)


# ============================================================================
# PIPELINE STAGES
# ============================================================================

def stage_1_contacts(wt_seq: str, mut_seq: str, mutation_pos: int):
    """
    Stage 1: ESM-2 contact prediction for WT and mutant.

    Returns dict with contact maps, confidence scores, and diff analysis.
    """
    print("\n  [Stage 1] ESM-2 Contact Prediction")
    print("  " + "-" * 50)

    try:
        from geometry.esm2_contact_predictor import ESM2ContactPredictor
        predictor = ESM2ContactPredictor()
    except Exception as e:
        print(f"  [WARN] ESM-2 not available: {e}")
        print("  Using fallback distance-based contact prediction...")
        return _fallback_contacts(wt_seq, mut_seq, mutation_pos)

    t0 = time.time()

    # Use top-L contacts (standard in contact prediction literature)
    # This gives ~L contacts per protein instead of sparse threshold-based prediction
    L = len(wt_seq)

    # Predict WT contacts
    print(f"  Predicting wild-type contacts ({L} residues, top-L={L})...")
    wt_contacts, wt_confidence = predictor.predict_contacts_top_L(wt_seq, top_L=L)

    # Predict mutant contacts
    print(f"  Predicting mutant contacts ({L} residues, top-L={L})...")
    mut_contacts, mut_confidence = predictor.predict_contacts_top_L(mut_seq, top_L=L)

    elapsed = time.time() - t0
    print(f"  ESM-2 inference: {elapsed:.1f}s")

    # Contact map differencing
    contact_diff = mut_contacts.astype(float) - wt_contacts.astype(float)
    conf_diff = mut_confidence - wt_confidence

    # Identify gained and lost contacts
    gained = []
    lost = []
    N = len(wt_seq)
    for i in range(N):
        for j in range(i + 5, N):
            if contact_diff[i, j] > 0:
                gained.append((i, j, float(mut_confidence[i, j])))
            elif contact_diff[i, j] < 0:
                lost.append((i, j, float(wt_confidence[i, j])))

    # Contacts involving the mutation site
    mutation_contacts_wt = [(j, float(wt_confidence[mutation_pos, j]))
                            for j in range(N) if abs(j - mutation_pos) >= 5
                            and wt_contacts[mutation_pos, j] == 1]
    mutation_contacts_mut = [(j, float(mut_confidence[mutation_pos, j]))
                             for j in range(N) if abs(j - mutation_pos) >= 5
                             and mut_contacts[mutation_pos, j] == 1]

    n_wt = int(np.sum(wt_contacts) / 2)
    n_mut = int(np.sum(mut_contacts) / 2)

    print(f"  WT contacts:     {n_wt}")
    print(f"  Mutant contacts: {n_mut} (delta: {n_mut - n_wt:+d})")
    print(f"  Gained: {len(gained)}  Lost: {len(lost)}")
    print(f"  Mutation site contacts: {len(mutation_contacts_wt)} (WT) -> {len(mutation_contacts_mut)} (mut)")

    return {
        "wt_contacts": wt_contacts,
        "mut_contacts": mut_contacts,
        "wt_confidence": wt_confidence,
        "mut_confidence": mut_confidence,
        "contact_diff": contact_diff,
        "conf_diff": conf_diff,
        "gained": gained,
        "lost": lost,
        "n_wt_contacts": n_wt,
        "n_mut_contacts": n_mut,
        "mutation_contacts_wt": mutation_contacts_wt,
        "mutation_contacts_mut": mutation_contacts_mut,
        "method": "ESM-2",
        "elapsed": elapsed,
    }


def _fallback_contacts(wt_seq, mut_seq, mutation_pos):
    """Fallback contact prediction when ESM-2 is not available."""
    N = len(wt_seq)
    # Simple statistical contact prediction based on sequence separation + hydrophobicity
    hydrophobic = set("AILMFVPW")
    wt_contacts = np.zeros((N, N), dtype=int)
    mut_contacts = np.zeros((N, N), dtype=int)
    wt_conf = np.zeros((N, N))
    mut_conf = np.zeros((N, N))

    for i in range(N):
        for j in range(i + 5, N):
            # Simple heuristic: hydrophobic residues in range tend to contact
            sep = abs(j - i)
            if sep < 8:
                base_prob = 0.3
            elif sep < 20:
                base_prob = 0.15
            else:
                base_prob = 0.05
            if wt_seq[i] in hydrophobic and wt_seq[j] in hydrophobic:
                base_prob *= 2
            if base_prob > 0.2:
                wt_contacts[i, j] = wt_contacts[j, i] = 1
                wt_conf[i, j] = wt_conf[j, i] = base_prob

            # Repeat for mutant
            if mut_seq[i] in hydrophobic and mut_seq[j] in hydrophobic:
                base_prob_m = base_prob * 2
            else:
                base_prob_m = base_prob
            if base_prob_m > 0.2:
                mut_contacts[i, j] = mut_contacts[j, i] = 1
                mut_conf[i, j] = mut_conf[j, i] = base_prob_m

    contact_diff = mut_contacts.astype(float) - wt_contacts.astype(float)
    gained = [(i, j, float(mut_conf[i, j])) for i in range(N) for j in range(i+5, N) if contact_diff[i, j] > 0]
    lost = [(i, j, float(wt_conf[i, j])) for i in range(N) for j in range(i+5, N) if contact_diff[i, j] < 0]

    print(f"  [FALLBACK] Using heuristic contacts (ESM-2 recommended for accuracy)")
    print(f"  WT contacts: {int(np.sum(wt_contacts)/2)}, Mutant: {int(np.sum(mut_contacts)/2)}")

    return {
        "wt_contacts": wt_contacts,
        "mut_contacts": mut_contacts,
        "wt_confidence": wt_conf,
        "mut_confidence": mut_conf,
        "contact_diff": contact_diff,
        "conf_diff": mut_conf - wt_conf,
        "gained": gained,
        "lost": lost,
        "n_wt_contacts": int(np.sum(wt_contacts) / 2),
        "n_mut_contacts": int(np.sum(mut_contacts) / 2),
        "mutation_contacts_wt": [],
        "mutation_contacts_mut": [],
        "method": "heuristic_fallback",
        "elapsed": 0.0,
    }


def stage_2_chemistry(wt_seq: str, mut_seq: str, wt_contacts, mut_contacts):
    """
    Stage 2: Chemistry validation — energy, H-bonds, clashes.

    Computes energy breakdown for both WT and mutant using the
    Rosetta-style energy function from the Physical-Chemical Bridge.
    """
    print("\n  [Stage 2] Physical-Chemical Validation")
    print("  " + "-" * 50)

    try:
        from chemistry import (
            EnergyFunction,
            HydrogenBondValidator,
            VanDerWaalsConstraints,
            ElectrostaticConstraints,
            HydrophobicConstraints,
        )
    except ImportError as e:
        print(f"  [WARN] Chemistry module not available: {e}")
        return {"error": str(e)}

    N = len(wt_seq)

    # Generate pseudo-coordinates from contact maps for chemistry scoring
    # Use distance geometry: contacts at ~6A, non-contacts at ~12A
    wt_coords = _contacts_to_coords(wt_contacts, N)
    mut_coords = _contacts_to_coords(mut_contacts, N)

    # Energy function
    energy_func = EnergyFunction()

    # Extract contact lists
    wt_contact_list = [(i, j) for i in range(N) for j in range(i+5, N) if wt_contacts[i, j] == 1]
    mut_contact_list = [(i, j) for i in range(N) for j in range(i+5, N) if mut_contacts[i, j] == 1]

    # WT energy
    wt_energy = energy_func.compute_total_energy({
        'coords': wt_coords,
        'sequence': wt_seq,
        'contacts': wt_contact_list,
    })

    # Mutant energy
    mut_energy = energy_func.compute_total_energy({
        'coords': mut_coords,
        'sequence': mut_seq,
        'contacts': mut_contact_list,
    })

    delta_energy = mut_energy.total - wt_energy.total

    print(f"  WT total energy:     {wt_energy.total:8.2f} kcal/mol")
    print(f"  Mutant total energy: {mut_energy.total:8.2f} kcal/mol")
    print(f"  Delta energy:        {delta_energy:+8.2f} kcal/mol")
    print()
    print(f"  Energy breakdown (WT -> Mut):")
    print(f"    vdW:           {wt_energy.vdw:8.2f} -> {mut_energy.vdw:8.2f}  ({mut_energy.vdw - wt_energy.vdw:+.2f})")
    print(f"    Electrostatic: {wt_energy.electrostatic:8.2f} -> {mut_energy.electrostatic:8.2f}  ({mut_energy.electrostatic - wt_energy.electrostatic:+.2f})")
    print(f"    H-bond:        {wt_energy.hbond:8.2f} -> {mut_energy.hbond:8.2f}  ({mut_energy.hbond - wt_energy.hbond:+.2f})")
    print(f"    Solvation:     {wt_energy.solvation:8.2f} -> {mut_energy.solvation:8.2f}  ({mut_energy.solvation - wt_energy.solvation:+.2f})")
    print(f"    Pair:          {wt_energy.pair:8.2f} -> {mut_energy.pair:8.2f}  ({mut_energy.pair - wt_energy.pair:+.2f})")

    # Stability assessment
    if delta_energy < -2.0:
        stability = "STABILIZING - Mutation lowers energy (likely activating)"
    elif delta_energy > 2.0:
        stability = "DESTABILIZING - Mutation raises energy (may impair function)"
    else:
        stability = "NEUTRAL - Minimal energy change"

    print(f"\n  Assessment: {stability}")

    # H-bond analysis
    hbond_validator = HydrogenBondValidator()
    wt_hbonds = hbond_validator.predict_hbonds(wt_coords, wt_seq)
    mut_hbonds = hbond_validator.predict_hbonds(mut_coords, mut_seq)

    print(f"\n  H-bonds: {len(wt_hbonds)} (WT) -> {len(mut_hbonds)} (mut) (delta: {len(mut_hbonds)-len(wt_hbonds):+d})")

    # Clash analysis
    vdw = VanDerWaalsConstraints()
    wt_clashes = vdw.check_clashes(wt_coords)
    mut_clashes = vdw.check_clashes(mut_coords)

    print(f"  Clashes: {len(wt_clashes)} (WT) -> {len(mut_clashes)} (mut) (delta: {len(mut_clashes)-len(wt_clashes):+d})")

    # ZFC chemistry constraints (optional)
    zfc_constraints = []
    try:
        from chemistry.zfc_constraints import ChemZFCBridge
        chem_zfc = ChemZFCBridge()
        if chem_zfc.is_available:
            zfc_constraints = chem_zfc.mutation_impact_constraints(
                protein=wt_seq[:10],
                mutation="mutation",
                delta_energy=delta_energy,
                lost_contacts=max(0, len(wt_contact_list) - len(mut_contact_list)),
                gained_contacts=max(0, len(mut_contact_list) - len(wt_contact_list)),
                stability=stability,
            )
            if zfc_constraints:
                print(f"\n  ZFC constraints: {len(zfc_constraints)} generated")
                for c in zfc_constraints:
                    print(f"    - {c.strategy}: conf={c.confidence:.2f}")
    except Exception:
        pass

    return {
        "wt_energy": wt_energy.to_dict(),
        "mut_energy": mut_energy.to_dict(),
        "delta_energy": round(delta_energy, 3),
        "stability": stability,
        "wt_hbonds": len(wt_hbonds),
        "mut_hbonds": len(mut_hbonds),
        "delta_hbonds": len(mut_hbonds) - len(wt_hbonds),
        "wt_clashes": len(wt_clashes),
        "mut_clashes": len(mut_clashes),
        "zfc_constraints": len(zfc_constraints),
    }


def _contacts_to_coords(contacts, N, dim=3):
    """
    Generate approximate 3D coordinates from a contact map using
    multi-dimensional scaling (MDS) with proper spacing.

    Ensures minimum pairwise distance of 3.5A to prevent vdW explosion.
    """
    # Build distance matrix from contacts
    # Contact => ~7 Angstroms, no contact => ~15 Angstroms
    distances = np.full((N, N), 15.0)
    for i in range(N):
        distances[i, i] = 0.0
        # Sequential neighbors at 3.8A (CA-CA bond distance)
        if i + 1 < N:
            distances[i, i+1] = 3.8
            distances[i+1, i] = 3.8
        if i + 2 < N:
            distances[i, i+2] = 6.0
            distances[i+2, i] = 6.0
        # Contacts at ~7A (typical CA-CA contact distance)
        for j in range(N):
            if contacts[i, j] == 1 and abs(i - j) >= 5:
                distances[i, j] = 7.0
                distances[j, i] = 7.0

    # Simple MDS: embed using eigendecomposition of centered distance matrix
    H = np.eye(N) - np.ones((N, N)) / N
    B = -0.5 * H @ (distances ** 2) @ H

    try:
        eigenvalues, eigenvectors = np.linalg.eigh(B)
        # Take top 3 positive eigenvalues
        idx = np.argsort(eigenvalues)[::-1][:dim]
        coords = eigenvectors[:, idx] * np.sqrt(np.maximum(eigenvalues[idx], 0))
    except np.linalg.LinAlgError:
        coords = np.random.randn(N, dim) * 5.0

    # Enforce minimum pairwise distance of 3.5A to prevent vdW artifacts
    for iteration in range(50):
        moved = False
        for i in range(N):
            for j in range(i + 1, min(i + 20, N)):  # Check nearby residues
                diff = coords[j] - coords[i]
                dist = np.linalg.norm(diff)
                if dist < 3.5 and dist > 0.01:
                    # Push apart
                    push = (3.5 - dist) / 2.0 * (diff / dist)
                    coords[i] -= push
                    coords[j] += push
                    moved = True
        if not moved:
            break

    return coords


def stage_3_curvature(wt_contacts, mut_contacts, wt_seq, mut_seq, mutation_pos):
    """
    Stage 3: Ollivier-Ricci curvature analysis.

    Identifies binding regions as spherical (clustered) geometry,
    and detects if the mutation disrupts these regions.
    """
    print("\n  [Stage 3] Ricci Curvature Analysis")
    print("  " + "-" * 50)

    try:
        from geometry.ricci import OllivierRicciCurvature
        from data import KomposOSStore, StoredObject, StoredMorphism
    except ImportError as e:
        print(f"  [WARN] Ricci curvature not available: {e}")
        return {"error": str(e)}

    N = len(wt_seq)

    def _build_contact_store(contacts, seq, label):
        """Build a minimal store from a contact map for Ricci computation."""
        store = KomposOSStore(":memory:")
        for i in range(N):
            store.add_object(StoredObject(
                name=f"R{i}_{seq[i]}",
                type_name="Residue",
                metadata={"position": i, "aa": seq[i]},
            ))
        n_edges = 0
        for i in range(N):
            for j in range(i + 5, N):
                if contacts[i, j] == 1:
                    store.add_morphism(StoredMorphism(
                        source_name=f"R{i}_{seq[i]}",
                        target_name=f"R{j}_{seq[j]}",
                        name="contact",
                        confidence=0.8,
                    ))
                    n_edges += 1
        return store, n_edges

    # Build stores
    wt_store, wt_edges = _build_contact_store(wt_contacts, wt_seq, "WT")
    mut_store, mut_edges = _build_contact_store(mut_contacts, mut_seq, "MUT")

    if wt_edges == 0 or mut_edges == 0:
        print("  [WARN] Too few contacts for curvature analysis")
        return {"error": "insufficient_contacts"}

    # Compute curvatures
    print(f"  Computing WT curvature ({wt_edges} edges)...")
    wt_ricci = OllivierRicciCurvature(wt_store, alpha=0.5)
    wt_result = wt_ricci.compute_all_curvatures()

    print(f"  Computing mutant curvature ({mut_edges} edges)...")
    mut_ricci = OllivierRicciCurvature(mut_store, alpha=0.5)
    mut_result = mut_ricci.compute_all_curvatures()

    # Mutation site curvature
    mut_node = f"R{mutation_pos}_{mut_seq[mutation_pos]}"
    wt_node = f"R{mutation_pos}_{wt_seq[mutation_pos]}"

    wt_mut_curv = wt_result.node_curvatures.get(wt_node, 0.0)
    mut_mut_curv = mut_result.node_curvatures.get(mut_node, 0.0)

    # Identify binding regions (high positive curvature = clusters)
    wt_spherical = [name for name, curv in wt_result.node_curvatures.items()
                    if curv > 0.1]
    mut_spherical = [name for name, curv in mut_result.node_curvatures.items()
                     if curv > 0.1]

    # Regions disrupted by mutation
    wt_spherical_set = set(wt_spherical)
    mut_spherical_set = set(mut_spherical)

    # Find positions that lost cluster geometry
    disrupted_positions = []
    for name in wt_spherical:
        pos = int(name.split("_")[0][1:])
        wt_name = name
        mut_name = f"R{pos}_{mut_seq[pos]}"
        if mut_name not in mut_spherical_set:
            disrupted_positions.append(pos)

    print(f"\n  WT curvature stats:")
    print(f"    Mean: {wt_result.statistics.get('mean', 0):.4f}")
    print(f"    Spherical regions: {wt_result.num_spherical} edges")
    print(f"    Hyperbolic regions: {wt_result.num_hyperbolic} edges")

    print(f"\n  Mutant curvature stats:")
    print(f"    Mean: {mut_result.statistics.get('mean', 0):.4f}")
    print(f"    Spherical regions: {mut_result.num_spherical} edges")
    print(f"    Hyperbolic regions: {mut_result.num_hyperbolic} edges")

    print(f"\n  Mutation site curvature: {wt_mut_curv:.4f} (WT) -> {mut_mut_curv:.4f} (mut)")

    if len(disrupted_positions) > 0:
        print(f"  Disrupted binding regions: {len(disrupted_positions)} positions")
        # Show first 10
        for pos in disrupted_positions[:10]:
            print(f"    Position {pos} ({wt_seq[pos]}): lost cluster geometry")
    else:
        print("  No binding regions disrupted")

    return {
        "wt_mean_curvature": round(wt_result.statistics.get('mean', 0), 4),
        "mut_mean_curvature": round(mut_result.statistics.get('mean', 0), 4),
        "wt_spherical": wt_result.num_spherical,
        "mut_spherical": mut_result.num_spherical,
        "wt_hyperbolic": wt_result.num_hyperbolic,
        "mut_hyperbolic": mut_result.num_hyperbolic,
        "mutation_site_curvature_wt": round(wt_mut_curv, 4),
        "mutation_site_curvature_mut": round(mut_mut_curv, 4),
        "disrupted_positions": disrupted_positions[:20],
    }


def stage_4_topology(wt_contacts, mut_contacts, wt_seq):
    """
    Stage 4: Persistent homology — detect pocket/cavity changes.

    Uses contact confidence matrices as point cloud embeddings.
    Compares topological features (H0=domains, H1=loops, H2=cavities).
    """
    print("\n  [Stage 4] Persistent Homology (TDA)")
    print("  " + "-" * 50)

    try:
        from topology.persistence import PersistentHomologyAnalyzer
    except ImportError as e:
        print(f"  [WARN] Topology module not available: {e}")
        return {"error": str(e)}

    N = len(wt_seq)

    # Convert contact matrices to distance matrices for TDA
    # Use contact map rows as feature vectors (each residue is a point in N-dim space)
    # This captures the contact neighborhood of each residue
    wt_features = wt_contacts.astype(float)
    mut_features = mut_contacts.astype(float)

    try:
        # WT topology
        print("  Computing WT persistent homology...")
        wt_analyzer = PersistentHomologyAnalyzer(
            point_cloud=wt_features,
            variable_names=[f"R{i}" for i in range(N)]
        )
        wt_diagrams = wt_analyzer.compute_persistence(maxdim=1)
        wt_h0 = len(wt_analyzer.features.get(0, []))
        wt_h1 = len(wt_analyzer.features.get(1, []))

        # Mutant topology
        print("  Computing mutant persistent homology...")
        mut_analyzer = PersistentHomologyAnalyzer(
            point_cloud=mut_features,
            variable_names=[f"R{i}" for i in range(N)]
        )
        mut_diagrams = mut_analyzer.compute_persistence(maxdim=1)
        mut_h0 = len(mut_analyzer.features.get(0, []))
        mut_h1 = len(mut_analyzer.features.get(1, []))

        print(f"\n  Topological features:")
        print(f"    H0 (domains):  {wt_h0} (WT) -> {mut_h0} (mut)")
        print(f"    H1 (loops):    {wt_h1} (WT) -> {mut_h1} (mut)")

        # Significant loops (high persistence)
        wt_strong_loops = [f for f in wt_analyzer.features.get(1, []) if f.persistence > 0.5]
        mut_strong_loops = [f for f in mut_analyzer.features.get(1, []) if f.persistence > 0.5]

        print(f"    Strong loops (persistence > 0.5): {len(wt_strong_loops)} (WT) -> {len(mut_strong_loops)} (mut)")

        if len(mut_strong_loops) != len(wt_strong_loops):
            if len(mut_strong_loops) > len(wt_strong_loops):
                print("    -> Mutation CREATES new topological features (potential new binding pocket)")
            else:
                print("    -> Mutation DESTROYS topological features (pocket collapse)")

        return {
            "wt_h0": wt_h0,
            "mut_h0": mut_h0,
            "wt_h1": wt_h1,
            "mut_h1": mut_h1,
            "wt_strong_loops": len(wt_strong_loops),
            "mut_strong_loops": len(mut_strong_loops),
            "topology_change": "new_features" if mut_h1 > wt_h1 else
                               "lost_features" if mut_h1 < wt_h1 else "stable",
        }

    except Exception as e:
        print(f"  [WARN] TDA computation failed: {e}")
        print("  (This may require 'pip install ripser')")
        return {"error": str(e)}


def stage_5_drug_recommendations(protein_name: str, mutation_str: str,
                                  contact_result: dict, chemistry_result: dict,
                                  curvature_result: dict, mutation_pos: int,
                                  wt_seq: str):
    """
    Stage 5: Drug recommendations based on structural impact.

    Cross-references mutation impact with known drug-target interactions.
    """
    print("\n  [Stage 5] Drug Recommendations")
    print("  " + "-" * 50)

    from data.drugs.drug_network import (
        DRUG_TARGET_INTERACTIONS,
        PROTEIN_DISEASE_ASSOCIATIONS,
        DRUGS,
    )

    # Merge with ReDO expansion interactions if available
    all_drug_target_interactions = list(DRUG_TARGET_INTERACTIONS)
    all_protein_disease_assoc = list(PROTEIN_DISEASE_ASSOCIATIONS)
    all_drugs_dict = dict(DRUGS)
    try:
        from data.drugs.redo_expansion import (
            REDO_DRUG_TARGET_INTERACTIONS,
            REDO_PROTEIN_DISEASE_ASSOCIATIONS,
            REDO_DRUGS,
        )
        all_drug_target_interactions.extend(REDO_DRUG_TARGET_INTERACTIONS)
        all_protein_disease_assoc.extend(REDO_PROTEIN_DISEASE_ASSOCIATIONS)
        all_drugs_dict.update(REDO_DRUGS)
    except ImportError:
        pass

    # Find all drugs targeting this protein
    targeting_drugs = [
        (drug, rel, conf, ev)
        for drug, target, rel, conf, ev in all_drug_target_interactions
        if target == protein_name
    ]

    if not targeting_drugs:
        print(f"  No drugs in database targeting {protein_name}")
        all_targets = set(t for _, t, _, _, _ in all_drug_target_interactions)
        print(f"  Available targets: {', '.join(sorted(all_targets))}")
        return {"drugs": [], "note": f"No drugs targeting {protein_name} in curated network"}

    # Find diseases this protein drives
    protein_diseases = [
        (dis, rel, conf, ev)
        for prot, dis, rel, conf, ev in all_protein_disease_assoc
        if prot == protein_name
    ]

    print(f"  Drugs targeting {protein_name}: {len(targeting_drugs)}")
    print(f"  Diseases linked to {protein_name}: {len(protein_diseases)}")

    # Get known mutation response if available
    known_mut_data = KNOWN_MUTATIONS.get(protein_name, {}).get(mutation_str, {})
    known_responses = known_mut_data.get("drug_response", {})

    # Assess each drug
    recommendations = []
    print(f"\n  {'Drug':15s}  {'Conf':>5s}  {'Relation':15s}  {'Prediction':15s}  Known Response")
    print(f"  {'-'*15}  {'-'*5}  {'-'*15}  {'-'*15}  {'-'*20}")

    for drug, rel, conf, ev in sorted(targeting_drugs, key=lambda x: -x[2]):
        drug_info = all_drugs_dict.get(drug, {})

        # Predict impact based on structural analysis
        prediction = _predict_drug_impact(
            drug, rel, conf, mutation_pos,
            contact_result, chemistry_result, curvature_result
        )

        known = known_responses.get(drug, "unknown")

        print(f"  {drug:15s}  {conf:5.2f}  {rel:15s}  {prediction:15s}  {known}")

        recommendations.append({
            "drug": drug,
            "drug_class": drug_info.get("drug_class", ""),
            "brand": drug_info.get("brand", ""),
            "binding_confidence": round(conf, 3),
            "relation": rel,
            "structural_prediction": prediction,
            "known_clinical_response": known,
            "evidence": ev,
        })

    # Show linked diseases
    print(f"\n  Relevant diseases for {protein_name}:")
    for dis, rel, conf, ev in sorted(protein_diseases, key=lambda x: -x[2]):
        print(f"    {dis:20s}  ({rel}, conf={conf:.2f})")

    # Clinical interpretation
    print(f"\n  Clinical Interpretation:")
    known_clinical = known_mut_data.get("clinical", "")
    if known_clinical:
        print(f"    Known: {known_clinical}")

    delta_e = chemistry_result.get("delta_energy", 0)
    if delta_e < -2.0:
        print(f"    Energy: Mutation is STABILIZING ({delta_e:+.2f} kcal/mol)")
        print(f"           -> Likely gain-of-function (constitutive activation)")
        print(f"           -> Kinase inhibitors targeting active conformation may work")
    elif delta_e > 2.0:
        print(f"    Energy: Mutation is DESTABILIZING ({delta_e:+.2f} kcal/mol)")
        print(f"           -> May impair protein folding or drug binding")
    else:
        print(f"    Energy: Minimal change ({delta_e:+.2f} kcal/mol)")

    return {
        "protein": protein_name,
        "mutation": mutation_str,
        "targeting_drugs": len(targeting_drugs),
        "linked_diseases": [(d, r) for d, r, c, e in protein_diseases],
        "recommendations": recommendations,
        "clinical_note": known_clinical,
    }


def _build_evidence_chains(drug, disease):
    """
    Find Drug -> Protein -> Disease composition chains in the curated data.

    Returns list of chain dicts with intermediate protein and relationship info.
    Searches both base network and ReDO expansion interactions.
    """
    from data.drugs.drug_network import (
        DRUG_TARGET_INTERACTIONS,
        PROTEIN_DISEASE_ASSOCIATIONS,
    )

    # Merge with ReDO expansion interactions if available
    all_drug_targets = list(DRUG_TARGET_INTERACTIONS)
    all_protein_disease = list(PROTEIN_DISEASE_ASSOCIATIONS)
    try:
        from data.drugs.redo_expansion import (
            REDO_DRUG_TARGET_INTERACTIONS,
            REDO_PROTEIN_DISEASE_ASSOCIATIONS,
        )
        all_drug_targets.extend(REDO_DRUG_TARGET_INTERACTIONS)
        all_protein_disease.extend(REDO_PROTEIN_DISEASE_ASSOCIATIONS)
    except ImportError:
        pass

    chains = []
    # Find all proteins this drug targets
    drug_targets = [
        (prot, rel, conf, ev)
        for d, prot, rel, conf, ev in all_drug_targets
        if d == drug
    ]

    # For each target, check if it links to the target disease
    for prot, drug_rel, drug_conf, drug_ev in drug_targets:
        disease_links = [
            (dis_rel, dis_conf, dis_ev)
            for p, dis, dis_rel, dis_conf, dis_ev in all_protein_disease
            if p == prot and dis == disease
        ]
        for dis_rel, dis_conf, dis_ev in disease_links:
            chains.append({
                "protein": prot,
                "drug_rel": drug_rel,
                "disease_rel": dis_rel,
                "chain_conf": round(drug_conf * dis_conf, 3),
            })

    return sorted(chains, key=lambda x: -x["chain_conf"])


def stage_6_oracle_discovery(protein_name: str, mutation_str: str,
                             stage5_result: dict):
    """
    Stage 6: Oracle-based drug repurposing discovery.

    Uses the full 9-strategy Categorical Oracle to find pre-approved drugs
    that could treat diseases driven by the mutated protein -- even if the
    drug was never designed for that protein. This is genuine drug discovery
    via compositional reasoning (Drug -> Protein -> Disease chains).

    This goes BEYOND Stage 5 (which only looks up known drug-protein pairs).
    """
    print("\n  [Stage 6] Oracle Drug Discovery (Compositional Reasoning)")
    print("  " + "-" * 50)

    from data.drugs.drug_network import (
        DRUGS,
        PROTEIN_DISEASE_ASSOCIATIONS,
        get_holdout_edges,
    )

    # Merge protein-disease associations from base + ReDO expansion
    all_protein_disease = list(PROTEIN_DISEASE_ASSOCIATIONS)
    try:
        from data.drugs.redo_expansion import REDO_PROTEIN_DISEASE_ASSOCIATIONS
        all_protein_disease.extend(REDO_PROTEIN_DISEASE_ASSOCIATIONS)
    except ImportError:
        pass

    # Merge drug lists from base + ReDO expansion
    all_drugs = dict(DRUGS)
    try:
        from data.drugs.redo_expansion import REDO_DRUGS
        all_drugs.update(REDO_DRUGS)
    except ImportError:
        pass

    HOLDOUT_EDGES = get_holdout_edges()

    # Get diseases linked to this protein
    protein_diseases = [
        (dis, rel, conf)
        for prot, dis, rel, conf, ev in all_protein_disease
        if prot == protein_name
    ]

    if not protein_diseases:
        print(f"  No diseases linked to {protein_name} in curated network.")
        print(f"  Oracle discovery requires protein-disease associations.")
        return {"discoveries": [], "note": "no linked diseases"}

    disease_names = list(set(d[0] for d in protein_diseases))
    print(f"  Diseases linked to {protein_name}: {', '.join(disease_names)}")

    # Drugs already found by Stage 5 (direct protein targets)
    known_drugs = set()
    if stage5_result and stage5_result.get("recommendations"):
        known_drugs = {r["drug"] for r in stage5_result["recommendations"]}
    print(f"  Known direct inhibitors (Stage 5): {', '.join(sorted(known_drugs)) if known_drugs else 'none'}")

    # Set up Oracle
    print(f"\n  Initializing Oracle (9 inference strategies)...")
    t0 = time.time()

    try:
        from data.drugs.loader import create_drug_store
        from data import EmbeddingsEngine, StoreEmbedder
        from oracle import CategoricalOracle

        store = create_drug_store(db_path=":memory:", include_proteins=True)
        engine = EmbeddingsEngine()
        embedder = StoreEmbedder(store, engine)
        embedder.embed_all_objects()
        oracle = CategoricalOracle(store, engine, min_confidence=0.40, max_predictions=20)
    except Exception as e:
        print(f"  [WARN] Oracle initialization failed: {e}")
        print(f"  Stage 6 skipped. Stage 5 results still valid.")
        return {"discoveries": [], "error": str(e)}

    print(f"  Oracle ready ({time.time() - t0:.1f}s)")

    # ZFC dual-engine verification (optional)
    zfc_bridge = None
    try:
        from oracle.zfc_verifier import OracleZFCBridge
        zfc_bridge = OracleZFCBridge(store, domain="drug_repurposing")
        if zfc_bridge.is_available:
            print(f"  ZFC dual-engine verification: ACTIVE")
        else:
            zfc_bridge = None
    except Exception:
        pass

    # Query Oracle: for each disease, score ALL drugs
    print(f"  Scoring {len(all_drugs)} drugs x {len(disease_names)} diseases...")
    t0 = time.time()

    discoveries = []
    drug_names = list(all_drugs.keys())

    for disease in disease_names:
        disease_rel = next((r for d, r, c in protein_diseases if d == disease), "associated_with")
        disease_conf = next((c for d, r, c in protein_diseases if d == disease), 0.5)

        for drug in drug_names:
            # Skip drugs already found by Stage 5 for THIS disease
            # (they're already known direct targets of this protein)
            if drug in known_drugs:
                continue

            try:
                result = oracle.predict(drug, disease)
                preds = result.predictions

                if preds:
                    best = preds[0]
                    if best.confidence >= 0.40:
                        discovery = {
                            "drug": drug,
                            "drug_class": all_drugs[drug].get("drug_class", ""),
                            "brand": all_drugs[drug].get("brand", ""),
                            "disease": disease,
                            "disease_link": f"{protein_name} {disease_rel} {disease}",
                            "confidence": round(best.confidence, 4),
                            "relation": best.predicted_relation,
                            "strategy": best.strategy_name,
                            "reasoning": best.reasoning,
                            "n_strategies": result.total_candidates,
                            "zfc_verified": False,
                            "delta_type": "UNKNOWN",
                            "zfc_confidence": 0.0,
                        }

                        # ZFC dual verification
                        if zfc_bridge is not None:
                            try:
                                dual_result = zfc_bridge.verify_predictions(
                                    drug, disease, preds, cat_result=result
                                )
                                if dual_result.predictions:
                                    dp = dual_result.predictions[0]
                                    discovery["zfc_verified"] = True
                                    discovery["delta_type"] = dp.delta_type.name
                                    discovery["zfc_confidence"] = round(dp.zfc_confidence, 4)
                            except Exception:
                                pass

                        discoveries.append(discovery)
            except Exception:
                pass

    elapsed = time.time() - t0
    print(f"  Oracle scoring complete ({elapsed:.1f}s)")

    # Build holdout lookup set: (drug, disease)
    holdout_set = {(d, dis) for d, dis, rel, conf, ev in HOLDOUT_EDGES}

    # Classify each discovery into tiers
    for d in discoveries:
        drug, disease = d["drug"], d["disease"]

        # Tier 1: matches a holdout edge (clinically validated, independently re-discovered)
        if (drug, disease) in holdout_set:
            d["tier"] = 1
            # Attach holdout evidence string
            d["holdout_evidence"] = next(
                (ev for hd, hdis, _, _, ev in HOLDOUT_EDGES
                 if hd == drug and hdis == disease), ""
            )
            d["chains"] = _build_evidence_chains(drug, disease)

        else:
            # Check for Drug->Protein->Disease composition chains
            chains = _build_evidence_chains(drug, disease)
            d["chains"] = chains

            if chains and d["confidence"] >= 0.60:
                # Tier 2: has a mechanistic chain AND strong confidence
                d["tier"] = 2
            else:
                # Tier 3: mathematical prediction only
                d["tier"] = 3

            # ZFC dual-engine boost: AGREE promotes Tier 3 -> Tier 2
            if d.get("delta_type") == "AGREE" and d["tier"] == 3:
                d["tier"] = 2
                d["reasoning"] = (d.get("reasoning", "") +
                                  " [ZFC-verified: both engines agree]")

    # Sort within tiers by confidence
    tier1 = sorted([d for d in discoveries if d["tier"] == 1], key=lambda x: -x["confidence"])
    tier2 = sorted([d for d in discoveries if d["tier"] == 2], key=lambda x: -x["confidence"])
    tier3 = sorted([d for d in discoveries if d["tier"] == 3], key=lambda x: -x["confidence"])

    # Print tiered results
    if discoveries:
        print(f"\n  NOVEL REPURPOSING CANDIDATES ({len(discoveries)} found)")
        print(f"  FDA-approved drugs that may treat {protein_name}-driven cancers")
        print(f"  via OTHER protein targets (not direct {protein_name} inhibition).")

        if tier1:
            print(f"\n  --- TIER 1: Clinically Validated ({len(tier1)}) ---")
            print(f"  (Oracle independently re-discovered these known treatments)")
            for i, d in enumerate(tier1, 1):
                print(f"  {i:3d}. {d['drug']:15s} -> {d['disease']:20s}  "
                      f"conf={d['confidence']:.4f}  [{d.get('holdout_evidence', '')}]")
                if d.get("chains"):
                    c = d["chains"][0]
                    print(f"       Chain: {d['drug']} --[{c['drug_rel']}]--> "
                          f"{c['protein']} --[{c['disease_rel']}]--> {d['disease']}")

        if tier2:
            print(f"\n  --- TIER 2: Strong Candidates ({len(tier2)}) ---")
            print(f"  (Mechanistic Drug->Protein->Disease chain exists in curated data)")
            for i, d in enumerate(tier2, 1):
                print(f"  {i:3d}. {d['drug']:15s} -> {d['disease']:20s}  "
                      f"conf={d['confidence']:.4f}  strategy={d['strategy']}")
                if d.get("chains"):
                    c = d["chains"][0]
                    print(f"       Chain: {d['drug']} --[{c['drug_rel']}]--> "
                          f"{c['protein']} --[{c['disease_rel']}]--> {d['disease']}")

        if tier3:
            print(f"\n  --- TIER 3: Exploratory ({len(tier3)}) ---")
            print(f"  (Mathematical prediction, no curated mechanistic chain)")
            for i, d in enumerate(tier3[:10], 1):
                print(f"  {i:3d}. {d['drug']:15s} -> {d['disease']:20s}  "
                      f"conf={d['confidence']:.4f}  strategy={d['strategy']}")
            if len(tier3) > 10:
                print(f"       ... and {len(tier3) - 10} more exploratory predictions")

        print(f"\n  Summary: {len(tier1)} validated, {len(tier2)} strong candidates, "
              f"{len(tier3)} exploratory")

        # ZFC dual-engine summary
        if zfc_bridge is not None:
            agree_count = sum(1 for d in discoveries if d.get("delta_type") == "AGREE")
            hollow_count = sum(1 for d in discoveries if d.get("delta_type") == "HOLLOW")
            orphan_count = sum(1 for d in discoveries if d.get("delta_type") == "ORPHAN")
            verified = sum(1 for d in discoveries if d.get("zfc_verified"))
            print(f"\n  ZFC Dual-Engine: {verified}/{len(discoveries)} verified  "
                  f"({agree_count} AGREE, {hollow_count} HOLLOW, {orphan_count} ORPHAN)")
    else:
        print(f"\n  No novel repurposing candidates found above confidence threshold.")

    return {
        "protein": protein_name,
        "mutation": mutation_str,
        "diseases_queried": disease_names,
        "known_direct_drugs": sorted(known_drugs),
        "discoveries": discoveries,
        "unique_drugs_discovered": sorted(set(d["drug"] for d in discoveries)),
        "tier_counts": {"tier1": len(tier1), "tier2": len(tier2), "tier3": len(tier3)},
        "oracle_time_seconds": round(elapsed, 1),
    }


def _predict_drug_impact(drug, relation, binding_conf, mutation_pos,
                          contact_result, chemistry_result, curvature_result):
    """
    Predict whether a mutation affects a drug's efficacy.

    Uses contact changes near the mutation site and energy impact.
    """
    # Check if mutation disrupts contacts near the binding site
    lost_contacts = contact_result.get("lost", [])
    gained_contacts = contact_result.get("gained", [])
    delta_energy = chemistry_result.get("delta_energy", 0)

    # Count disrupted contacts near mutation site (within 10 residues)
    nearby_lost = sum(1 for i, j, c in lost_contacts
                      if abs(i - mutation_pos) < 10 or abs(j - mutation_pos) < 10)
    nearby_gained = sum(1 for i, j, c in gained_contacts
                        if abs(i - mutation_pos) < 10 or abs(j - mutation_pos) < 10)

    # Curvature at mutation site
    curv_change = (curvature_result.get("mutation_site_curvature_mut", 0) -
                   curvature_result.get("mutation_site_curvature_wt", 0))

    # Decision logic
    if nearby_lost > 5 and delta_energy > 1.0:
        return "likely_resistant"
    elif nearby_lost > 3:
        return "may_reduce"
    elif nearby_gained > 3 and delta_energy < -1.0:
        return "may_sensitize"
    elif abs(curv_change) > 0.3:
        return "geometry_changed"
    else:
        return "likely_preserved"


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_mutation_impact(protein_name: str, mutation_str: str,
                        sequence: Optional[str] = None):
    """
    Run the complete mutation impact analysis pipeline.

    Args:
        protein_name: Protein name (e.g., "EGFR", "BRAF", "KRAS")
        mutation_str: Mutation in standard notation (e.g., "L858R", "V600E")
        sequence: Optional protein sequence. If None, uses built-in sequences.
    """
    print("=" * 70)
    print(f"  MUTATION IMPACT ANALYSIS: {protein_name} {mutation_str}")
    print(f"  KOMPOSOS-III Physical-Chemical Bridge")
    print("=" * 70)
    t_start = time.time()

    # Resolve sequence
    if sequence is None:
        if protein_name not in PROTEIN_SEQUENCES:
            print(f"\n  ERROR: No built-in sequence for {protein_name}")
            print(f"  Available: {', '.join(PROTEIN_SEQUENCES.keys())}")
            print(f"  Provide sequence with --sequence flag")
            return None
        sequence = PROTEIN_SEQUENCES[protein_name]

    # Parse mutation
    wt_aa, clinical_pos, mut_aa = parse_mutation(mutation_str)

    # Get domain position
    known_mut_data = KNOWN_MUTATIONS.get(protein_name, {}).get(mutation_str, {})
    if known_mut_data:
        domain_pos = known_mut_data["domain_pos"]
        expected_wt = known_mut_data["wt_aa"]
        if sequence[domain_pos] != expected_wt:
            print(f"  WARNING: Expected {expected_wt} at position {domain_pos}, "
                  f"found {sequence[domain_pos]}")
    else:
        # For unknown mutations, use clinical position directly
        # (assumes position is 0-indexed into the provided sequence)
        domain_pos = clinical_pos - 1  # Convert to 0-indexed
        if domain_pos >= len(sequence) or domain_pos < 0:
            print(f"  ERROR: Position {clinical_pos} out of range for sequence length {len(sequence)}")
            return None
        if sequence[domain_pos] != wt_aa:
            print(f"  WARNING: Expected {wt_aa} at position {domain_pos}, "
                  f"found {sequence[domain_pos]}")
            print(f"  Proceeding anyway (position numbering may differ from domain)")

    print(f"\n  Protein:    {protein_name}")
    print(f"  Mutation:   {mutation_str} (clinical position {clinical_pos})")
    print(f"  Domain pos: {domain_pos} (0-indexed in provided sequence)")
    print(f"  Sequence:   {len(sequence)} residues")
    print(f"  WT residue: {sequence[domain_pos]} -> {mut_aa}")

    if known_mut_data:
        print(f"  Clinical:   {known_mut_data.get('clinical', 'N/A')[:100]}")

    # Apply mutation
    wt_seq = sequence
    mut_seq = apply_mutation(sequence, domain_pos, mut_aa)

    # Run pipeline stages
    # Stage 1: ESM-2 contacts
    contact_result = stage_1_contacts(wt_seq, mut_seq, domain_pos)

    # Stage 2: Chemistry
    chemistry_result = stage_2_chemistry(
        wt_seq, mut_seq,
        contact_result["wt_contacts"],
        contact_result["mut_contacts"]
    )

    # Stage 3: Ricci curvature
    curvature_result = stage_3_curvature(
        contact_result["wt_contacts"],
        contact_result["mut_contacts"],
        wt_seq, mut_seq, domain_pos
    )

    # Stage 4: Persistent homology
    topology_result = stage_4_topology(
        contact_result["wt_contacts"],
        contact_result["mut_contacts"],
        wt_seq
    )

    # Stage 5: Drug recommendations (direct lookup)
    drug_result = stage_5_drug_recommendations(
        protein_name, mutation_str,
        contact_result, chemistry_result, curvature_result,
        domain_pos, wt_seq
    )

    # Stage 6: Oracle drug discovery (compositional reasoning)
    discovery_result = stage_6_oracle_discovery(
        protein_name, mutation_str,
        drug_result,
    )

    # Summary
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {protein_name} {mutation_str}")
    print(f"{'=' * 70}")

    print(f"\n  Contacts:    {contact_result['n_wt_contacts']} -> {contact_result['n_mut_contacts']} "
          f"(+{len(contact_result['gained'])} / -{len(contact_result['lost'])})")

    if "delta_energy" in chemistry_result:
        print(f"  Energy:      {chemistry_result['delta_energy']:+.2f} kcal/mol "
              f"({chemistry_result['stability']})")

    if "mutation_site_curvature_wt" in curvature_result:
        print(f"  Curvature:   {curvature_result['mutation_site_curvature_wt']:.4f} -> "
              f"{curvature_result['mutation_site_curvature_mut']:.4f}")

    if drug_result and drug_result.get("recommendations"):
        print(f"\n  Stage 5 - Known Drug Targets ({len(drug_result['recommendations'])} drugs):")
        for rec in drug_result["recommendations"]:
            icon = "[+]" if "preserved" in rec["structural_prediction"] or "sensitize" in rec["structural_prediction"] else "[-]" if "resistant" in rec["structural_prediction"] else "[?]"
            print(f"    {icon} {rec['drug']:15s}  {rec['structural_prediction']:15s}  "
                  f"(known: {rec['known_clinical_response']})")

    if discovery_result and discovery_result.get("discoveries"):
        tc = discovery_result.get("tier_counts", {})
        print(f"\n  Stage 6 - Novel Repurposing Discoveries:")
        print(f"    Tier 1 (clinically validated):  {tc.get('tier1', 0)}")
        print(f"    Tier 2 (strong candidates):     {tc.get('tier2', 0)}")
        print(f"    Tier 3 (exploratory):           {tc.get('tier3', 0)}")
        # Show top Tier 1 and Tier 2 in summary
        for d in discovery_result["discoveries"]:
            if d.get("tier") == 1:
                print(f"    [T1] {d['drug']:15s}  -> {d['disease']:20s}  conf={d['confidence']:.4f}")
        for d in discovery_result["discoveries"][:3]:
            if d.get("tier") == 2:
                print(f"    [T2] {d['drug']:15s}  -> {d['disease']:20s}  conf={d['confidence']:.4f}")

    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Method:     {contact_result.get('method', 'unknown')}")

    # Save results
    output = {
        "protein": protein_name,
        "mutation": mutation_str,
        "sequence_length": len(wt_seq),
        "timestamp": datetime.now().isoformat(),
        "total_time_seconds": round(elapsed, 1),
        "contacts": {
            "method": contact_result.get("method"),
            "wt_contacts": contact_result["n_wt_contacts"],
            "mut_contacts": contact_result["n_mut_contacts"],
            "gained": len(contact_result["gained"]),
            "lost": len(contact_result["lost"]),
        },
        "chemistry": {k: v for k, v in chemistry_result.items() if k != "error"},
        "curvature": {k: v for k, v in curvature_result.items() if k != "error"},
        "topology": {k: v for k, v in topology_result.items() if k != "error"},
        "drugs": drug_result,
        "discovery": {k: v for k, v in discovery_result.items() if k != "error"} if discovery_result else {},
    }

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"mutation_impact_{protein_name}_{mutation_str}_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved: {out_path}")
    print(f"{'=' * 70}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="KOMPOSOS-III Mutation Impact Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mutation_impact.py --protein EGFR --mutation L858R
  python mutation_impact.py --protein BRAF --mutation V600E
  python mutation_impact.py --protein KRAS --mutation G12C
  python mutation_impact.py --protein EGFR --mutation T790M
  python mutation_impact.py --sequence MKLV... --mutation L50R --protein Custom

Built-in proteins: EGFR (kinase domain), BRAF (kinase domain), KRAS (full)
        """
    )
    parser.add_argument("--protein", required=True, help="Protein name (e.g., EGFR, BRAF, KRAS)")
    parser.add_argument("--mutation", required=True, help="Mutation notation (e.g., L858R, V600E)")
    parser.add_argument("--sequence", default=None, help="Custom protein sequence (optional)")

    args = parser.parse_args()

    run_mutation_impact(
        protein_name=args.protein,
        mutation_str=args.mutation,
        sequence=args.sequence,
    )


if __name__ == "__main__":
    main()
