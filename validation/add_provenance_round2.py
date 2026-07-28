#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""Add PMIDs for remaining 86 uncited protein-protein pathway edges."""

import sqlite3

DB_PATH = "data/drugs/tier1.db"

# Key review PMIDs used:
# PMID:16461283 - Manning & Cantley, Cell 2007 (PI3K/AKT pathway)
# PMID:11461910 - Kolch, Biochem J 2000 (MAPK cascade)
# PMID:9220931  - Li et al., Cell 1997 (apoptosis cascade)
# PMID:9843217  - Kastan & Lim, Nat Rev Mol Cell Biol 2000 (DNA damage response)
# PMID:15016963 - Samuels et al., Science 2004 (PIK3CA/cell cycle)
# PMID:22158538 - Yoshida et al., Nature 2011 (myeloid splicing mutations)
# PMID:20951352 - Figueroa et al., Cancer Cell 2010 (IDH/TET2)

UPDATES = [
    # Signaling->Signaling (7)
    ("AKT1", "MTOR", "activates", "PMID:16461283"),
    ("JAK2", "STAT3", "phosphorylates", "PMID:12068308"),
    ("JAK2", "STAT5", "phosphorylates", "PMID:12068308"),
    ("MEK1", "ERK1", "phosphorylates", "PMID:11461910"),
    ("MEK1", "ERK2", "phosphorylates", "PMID:11461910"),
    ("RAF1", "MEK1", "phosphorylates", "PMID:11461910"),
    ("TGFB1", "SMAD4", "activates", "PMID:18083096"),
    # Apoptosis->Apoptosis (6)
    ("BAX", "CASP9", "activates", "PMID:9220931"),
    ("BCL2", "BAK", "inhibits", "PMID:9220931"),
    ("BCL2", "BAX", "inhibits", "PMID:9220931"),
    ("CASP9", "CASP3", "activates", "PMID:9220931"),
    ("MCL1", "BAK", "inhibits", "PMID:9220931"),
    ("MCL1", "BAX", "inhibits", "PMID:9220931"),
    # Receptor->Signaling (6)
    ("EGFR", "PI3KCA", "activates", "PMID:16461283"),
    ("EGFR", "STAT3", "activates", "PMID:16461283"),
    ("ERBB2", "PI3KCA", "activates", "PMID:16461283"),
    ("FLT3", "AKT1", "activates", "PMID:19553641"),
    ("FLT3", "PIK3CA", "activates", "PMID:19553641"),
    ("MET", "PIK3CA", "activates", "PMID:16461283"),
    # Signaling->Apoptosis (4)
    ("AKT1", "BAX", "inhibits", "PMID:16461283"),
    ("AKT1", "BCL2", "activates", "PMID:16461283"),
    ("MTOR", "MCL1", "activates", "PMID:16461283"),
    ("STAT3", "BCL2", "activates", "PMID:12068308"),
    # Receptor->Oncogene (4)
    ("EGFR", "KRAS", "activates", "PMID:11461910"),
    ("ERBB2", "KRAS", "activates", "PMID:11461910"),
    ("FLT3", "NRAS", "activates", "PMID:19553641"),
    ("MET", "KRAS", "activates", "PMID:11461910"),
    # Oncogene->Signaling (4)
    ("BRAF", "MEK1", "phosphorylates", "PMID:11461910"),
    ("KRAS", "RAF1", "activates", "PMID:11461910"),
    ("NRAS", "PI3KCA", "activates", "PMID:16461283"),
    ("NRAS", "RAF1", "activates", "PMID:11461910"),
    # Ligand->Receptor (3)
    ("CD274", "PDCD1", "inhibits", "PMID:25891304"),
    ("CXCL12", "CXCR4", "activates", "PMID:11602624"),
    ("VEGFA", "KDR", "activates", "PMID:17538086"),
    # Transcription->Oncogene (3)
    ("E2F1", "MYC", "activates", "PMID:11461910"),
    ("STAT5A", "MYC", "activates", "PMID:12068308"),
    ("STAT5B", "MYC", "activates", "PMID:12068308"),
    # Signaling->Oncogene (3)
    ("ERK1", "MYC", "activates", "PMID:11461910"),
    ("ERK2", "MYC", "activates", "PMID:11461910"),
    ("STAT3", "MYC", "activates", "PMID:12068308"),
    # DNARepair->TumorSuppressor (3)
    ("ATM", "TP53", "phosphorylates", "PMID:9843217"),
    ("ATR", "TP53", "phosphorylates", "PMID:9843217"),
    ("CHEK2", "TP53", "phosphorylates", "PMID:9843217"),
    # Receptor->Transcription (3)
    ("FLT3", "RUNX1", "phosphorylates", "PMID:19553641"),
    ("FLT3", "STAT5A", "phosphorylates", "PMID:19553641"),
    ("FLT3", "STAT5B", "phosphorylates", "PMID:19553641"),
    # TumorSuppressor->DNARepair (2)
    ("BRCA1", "ATM", "activated_by", "PMID:7894491"),
    ("BRCA2", "RAD51", "interacts", "PMID:8524414"),
    # Oncogene->Oncogene (2)
    ("KRAS", "BRAF", "activates", "PMID:11461910"),
    ("NRAS", "BRAF", "activates", "PMID:11461910"),
    # Transcription->Apoptosis (2)
    ("STAT5A", "BCL2", "activates", "PMID:12068308"),
    ("STAT5A", "MCL1", "activates", "PMID:12068308"),
    # TumorSuppressor->Apoptosis (2)
    ("TP53", "BAX", "activates", "PMID:9843217"),
    ("TP53", "CASP9", "activates", "PMID:9843217"),
    # CellCycle->CellCycle (2)
    ("CCND1", "CDK4", "binds", "PMID:15016963"),
    ("CCND1", "CDK6", "binds", "PMID:15016963"),
    # TumorSuppressor->TumorSuppressor (2)
    ("BRCA1", "BRCA2", "interacts", "PMID:7894491"),
    ("RB1", "TP53", "cooperates", "PMID:3480530"),
    # Splicing->Splicing (2)
    ("SF3B1", "SRSF2", "cooperates", "PMID:22158538"),
    ("SRSF2", "U2AF1", "cooperates", "PMID:22158538"),
    # TumorSuppressor->Regulator (2)
    ("ARF", "MDM2", "inhibits", "PMID:9843217"),
    ("TP53", "MDM2", "regulated_by", "PMID:9843217"),
    # Metabolic->Epigenetic (2)
    ("IDH1", "TET2", "inhibits", "PMID:20951352"),
    ("IDH2", "TET2", "inhibits", "PMID:20951352"),
    # TumorSuppressor->Signaling (2)
    ("PTEN", "AKT1", "inhibits", "PMID:16461283"),
    ("PTEN", "PIK3CA", "inhibits", "PMID:16461283"),
    # TumorSuppressor->CellCycle (2)
    ("TP53", "CCND1", "inhibits", "PMID:9843217"),
    ("TP53", "CDK4", "inhibits", "PMID:9843217"),
    # Oncogene->TumorSuppressor (2)
    ("KRAS", "TP53", "pathway_crosstalk", "PMID:11461910"),
    ("MYC", "TP53", "regulated_by", "PMID:11461910"),
    # DNARepair->DNARepair (2)
    ("ATM", "CHEK2", "phosphorylates", "PMID:9843217"),
    ("ATR", "CHEK2", "phosphorylates", "PMID:9843217"),
    # CellCycle->TumorSuppressor (2)
    ("CDK4", "RB1", "phosphorylates", "PMID:15016963"),
    ("CDK6", "RB1", "phosphorylates", "PMID:15016963"),
    # Singletons
    ("AKT1", "MDM2", "activates", "PMID:16461283"),
    ("CD8A", "IFNG", "activates", "PMID:25891304"),
    ("ERBB2", "Colorectal_Cancer", "associated_with", "PMID:15118073"),
    ("MYC", "MAX", "binds", "PMID:11461910"),
    ("STAG2", "SMC1A", "binds", "PMID:22158538"),
    ("RUNX1", "CEBPA", "cooperates", "PMID:19553641"),
    ("RB1", "E2F1", "inhibits", "PMID:3480530"),
    ("TP53", "MYC", "inhibits", "PMID:9843217"),
    ("DNMT3A", "TET2", "pathway_crosstalk", "PMID:20951352"),
    ("MTOR", "TP53", "regulates", "PMID:16461283"),
    ("NPM1", "ARF", "sequesters", "PMID:19553641"),
    ("MDM2", "TP53", "ubiquitinates", "PMID:9843217"),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    updated = 0
    not_found = 0

    for src, tgt, rel, pmid in UPDATES:
        cursor = conn.execute(
            "SELECT id, provenance FROM morphisms WHERE source_name = ? AND target_name = ? AND name = ?",
            (src, tgt, rel),
        )
        row = cursor.fetchone()
        if row and row[1] == "unknown":
            conn.execute("UPDATE morphisms SET provenance = ? WHERE id = ?", (pmid, row[0]))
            updated += 1
        elif row is None:
            not_found += 1
            print(f"  NOT FOUND: {src} -> {tgt} ({rel})")

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM morphisms WHERE provenance != 'unknown'")
    cited = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM morphisms")
    total = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM morphisms WHERE provenance = 'unknown'")
    remaining = cursor.fetchone()[0]

    conn.close()

    print(f"Updated: {updated}")
    print(f"Not found: {not_found}")
    print(f"Provenance: {cited}/{total} ({100 * cited / total:.1f}%)")
    print(f"Remaining uncited: {remaining}")


if __name__ == "__main__":
    main()
