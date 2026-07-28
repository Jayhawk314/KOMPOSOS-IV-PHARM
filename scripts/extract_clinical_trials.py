#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

"""
Extract clinical trial outcomes for FDA-approved drug-disease pairs.

Uses ClinicalTrials.gov API to get response rates, survival data, sample sizes.
"""

import requests
import json
import sqlite3
import re
from typing import Optional, Dict
import time

DB_PATH = "data/drugs/tier1.db"
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"


# Manual mapping of FDA-approved pairs to their pivotal trial NCT IDs
# This would ideally come from FDA approval documents
FDA_TRIAL_MAP = {
    ("Imatinib", "CML"): "NCT00000445",  # Example - needs real NCT IDs
    ("Dasatinib", "CML"): "NCT00123474",
    ("Vemurafenib", "Melanoma"): "NCT01006980",  # BRAF V600E trial
    ("Dabrafenib", "Melanoma"): "NCT01227889",
    ("Sunit

inib", "RCC"): "NCT00083889",
    ("Sorafenib", "RCC"): "NCT00073307",  # TARGET trial
    ("Pazopanib", "RCC"): "NCT00334282",
    # ... Add all 44 FDA-approved pairs
}


def get_approved_pairs() -> list:
    """Get all FDA-approved drug-disease pairs from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT source_name, target_name
        FROM morphisms
        WHERE name = 'treats'
        AND evidence_tier = 'ESTABLISHED'
        AND provenance LIKE '%FDA%'
    """)

    pairs = cursor.fetchall()
    conn.close()
    return pairs


def fetch_trial_data(nct_id: str) -> Optional[Dict]:
    """
    Fetch trial data from ClinicalTrials.gov API v2.

    Args:
        nct_id: NCT identifier (e.g., "NCT00073307")

    Returns:
        Dict with trial outcomes or None if not found
    """
    url = f"{CLINICALTRIALS_API}/{nct_id}"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"  [WARN] NCT {nct_id} not found (status {resp.status_code})")
            return None

        data = resp.json()
        return parse_trial_outcomes(data)

    except Exception as e:
        print(f"  [ERROR] Failed to fetch {nct_id}: {e}")
        return None


def parse_trial_outcomes(trial_data: dict) -> dict:
    """
    Parse relevant outcomes from ClinicalTrials.gov JSON response.

    Extracts:
    - Overall response rate (ORR)
    - Progression-free survival (PFS)
    - Overall survival (OS)
    - Sample size
    - Trial phase
    """
    outcomes = {}

    try:
        protocol = trial_data.get("protocolSection", {})

        # Sample size
        design = protocol.get("designModule", {})
        enrollment = design.get("enrollmentInfo", {})
        outcomes["sample_size"] = enrollment.get("count")

        # Trial phase
        phases = design.get("phases", [])
        outcomes["trial_phase"] = phases[0] if phases else "Unknown"

        # Primary outcomes
        outcomes_module = protocol.get("outcomesModule", {})
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])

        for outcome in primary_outcomes:
            measure = outcome.get("measure", "").lower()
            description = outcome.get("description", "")

            # Response rate
            if "response rate" in measure or "orr" in measure:
                rate = extract_percentage(description)
                if rate is not None:
                    outcomes["response_rate"] = rate

            # Progression-free survival
            if "progression-free survival" in measure or "pfs" in measure:
                months = extract_months(description)
                if months is not None:
                    outcomes["pfs_months"] = months

            # Overall survival
            if "overall survival" in measure or "os" in measure:
                months = extract_months(description)
                if months is not None:
                    outcomes["os_months"] = months

                # Hazard ratio
                hr = extract_hazard_ratio(description)
                if hr is not None:
                    outcomes["os_hazard_ratio"] = hr

    except Exception as e:
        print(f"  [ERROR] Failed to parse trial outcomes: {e}")

    return outcomes


def extract_percentage(text: str) -> Optional[float]:
    """Extract percentage from text (e.g., '45%' -> 0.45)."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if match:
        return float(match.group(1)) / 100.0
    return None


def extract_months(text: str) -> Optional[float]:
    """Extract months from text (e.g., '14.5 months')."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*months?', text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def extract_hazard_ratio(text: str) -> Optional[float]:
    """Extract hazard ratio from text (e.g., 'HR=0.42')."""
    match = re.search(r'(?:HR|hazard ratio)[:\s=]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def update_database(drug: str, disease: str, outcomes: dict):
    """Update morphism with clinical trial outcomes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find the morphism
    cursor.execute("""
        SELECT id, metadata FROM morphisms
        WHERE source_name = ? AND target_name = ? AND name = 'treats'
    """, (drug, disease))

    result = cursor.fetchone()
    if not result:
        print(f"  [WARN] No treats edge found for {drug} -> {disease}")
        conn.close()
        return

    morph_id, metadata_str = result

    # Parse existing metadata
    try:
        metadata = json.loads(metadata_str) if metadata_str else {}
    except:
        metadata = {}

    # Add clinical outcomes
    metadata["clinical_outcomes"] = outcomes

    # Update database
    cursor.execute("""
        UPDATE morphisms
        SET metadata = ?,
            quantitative_value = ?,
            value_unit = 'response_rate',
            sample_size = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        json.dumps(metadata),
        outcomes.get("response_rate"),
        outcomes.get("sample_size"),
        morph_id
    ))

    conn.commit()
    conn.close()

    print(f"  [OK] Updated {drug} -> {disease} with clinical outcomes")


def main():
    print("="*70)
    print("CLINICAL TRIAL OUTCOME EXTRACTION")
    print("="*70)

    # Get approved pairs
    pairs = get_approved_pairs()
    print(f"\nFound {len(pairs)} FDA-approved drug-disease pairs")

    # Extract outcomes for each
    success_count = 0
    for drug, disease in pairs:
        print(f"\n{drug} -> {disease}:")

        # Get NCT ID from manual mapping
        nct_id = FDA_TRIAL_MAP.get((drug, disease))

        if not nct_id:
            print(f"  [SKIP] No NCT ID mapped (needs manual curation)")
            continue

        # Fetch trial data
        outcomes = fetch_trial_data(nct_id)

        if outcomes and len(outcomes) > 0:
            print(f"  Outcomes: {outcomes}")
            update_database(drug, disease, outcomes)
            success_count += 1
        else:
            print(f"  [WARN] No outcomes extracted")

        # Rate limiting
        time.sleep(0.5)

    print(f"\n{'='*70}")
    print(f"Extraction complete: {success_count}/{len(pairs)} pairs updated")
    print(f"{'='*70}")

    print("\nNote: This script requires manual NCT ID mapping for all 44 pairs.")
    print("See FDA drug labels or approval documents for pivotal trial IDs.")


if __name__ == "__main__":
    main()
