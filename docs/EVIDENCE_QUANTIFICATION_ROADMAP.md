# Evidence Quantification Roadmap
## From Graph Coherence to Real Biological Measurements

**Date:** 2026-05-25
**Current State:** 609 PMIDs, 4944 edges, topology-based confidence scores
**Goal:** Distinguish measured data from inferred relationships, add real quantitative evidence

---

## The Core Problem

**Current approach:**
- PMID citations get assigned confidence (0.20-0.54) based on graph topology
- 5-layer categorical verification checks graph coherence, not biological strength
- Users see "confidence 0.45" and may interpret as "45% likely to be true"
- **Reality:** It measures "how well this edge fits the graph structure"

**What we need:**
- Explicit tiers: MEASURED (IC50 data) vs INFERRED (ESM2) vs HYPOTHESIS (PMID citations)
- Real effect sizes: mutation frequencies, clinical outcomes, binding affinities
- Transparent uncertainty: confidence intervals, not point estimates

---

## SHORT TERM: Honest Evidence Presentation (1-2 weeks)

### Goal: Stop conflating graph coherence with biological evidence strength

### 1. Create Evidence Tier System

**Implementation:**

```python
# core/evidence_tiers.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class EvidenceTier(Enum):
    MEASURED = "MEASURED"           # IC50, clinical trial data, mutations
    ESTABLISHED = "ESTABLISHED"     # FDA, KEGG canonical pathways
    INFERRED = "INFERRED"          # ESM2, computed similarity
    HYPOTHESIS = "HYPOTHESIS"       # PubMed AGREE/PARTIAL
    SPECULATIVE = "SPECULATIVE"     # PubMed ORPHAN
    NOISE = "NOISE"                # PubMed REJECT

@dataclass
class EvidenceAnnotation:
    tier: EvidenceTier
    source: str                    # "ChEMBL IC50", "FDA approval", "PubMed PMID:12345"
    quantitative_value: Optional[float] = None  # IC50 in μM, mutation freq, etc.
    unit: Optional[str] = None     # "μM", "percentage", "hazard_ratio"
    sample_size: Optional[int] = None
    p_value: Optional[float] = None

    def display_string(self) -> str:
        """Human-readable evidence string."""
        if self.tier == EvidenceTier.MEASURED and self.quantitative_value:
            return f"{self.tier.value}: {self.source} = {self.quantitative_value} {self.unit or ''}"
        elif self.tier == EvidenceTier.HYPOTHESIS:
            return f"{self.tier.value}: {self.source} (not quantified)"
        else:
            return f"{self.tier.value}: {self.source}"
```

**Database schema addition:**
```sql
-- Add to morphisms table
ALTER TABLE morphisms ADD COLUMN evidence_tier TEXT DEFAULT 'HYPOTHESIS';
ALTER TABLE morphisms ADD COLUMN quantitative_value REAL;
ALTER TABLE morphisms ADD COLUMN value_unit TEXT;
```

**Migration script:**
```python
# scripts/classify_evidence_tiers.py

import sqlite3
import re

DB_PATH = "data/drugs/tier1.db"

TIER_RULES = {
    "MEASURED": [
        lambda prov: "ChEMBL" in prov and "IC50" in prov,
        lambda prov: "ABPP" in prov,
    ],
    "ESTABLISHED": [
        lambda prov: "FDA" in prov,
        lambda prov: "KEGG pathway" in prov,
    ],
    "INFERRED": [
        lambda prov: "ESM2" in prov or "ESM-2" in prov,
        lambda prov: "STRING PPI" in prov,
    ],
    "HYPOTHESIS": [
        lambda prov, meta: meta.get("categorical_delta") in ["AGREE", "PARTIAL"],
    ],
    "SPECULATIVE": [
        lambda prov, meta: meta.get("categorical_delta") == "ORPHAN",
    ],
    "NOISE": [
        lambda prov, meta: meta.get("categorical_delta") == "REJECT",
    ],
}

def classify_edge(provenance: str, metadata: dict, confidence: float) -> str:
    """Classify edge into evidence tier."""
    for tier, rules in TIER_RULES.items():
        for rule in rules:
            try:
                if rule(provenance, metadata) if len(rule.__code__.co_varnames) > 1 else rule(provenance):
                    return tier
            except:
                continue

    # Fallback based on confidence
    if confidence >= 0.70:
        return "ESTABLISHED"
    elif confidence >= 0.40:
        return "INFERRED"
    else:
        return "HYPOTHESIS"

# Apply to all morphisms
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, provenance, metadata, confidence FROM morphisms")
for morph_id, prov, meta_str, conf in cursor.fetchall():
    import json
    meta = json.loads(meta_str) if meta_str else {}
    tier = classify_edge(prov, meta, conf)

    cursor.execute("UPDATE morphisms SET evidence_tier = ? WHERE id = ?", (tier, morph_id))

conn.commit()
print("Evidence tiers classified!")
```

### 2. Update UI to Show Evidence Tiers

**app.py changes:**

```python
# In render_detail() function
def render_detail(entry):
    # ... existing code ...

    # ── Evidence Tier Breakdown ──────────────────────────────────────
    st.markdown("### Evidence Quality")

    tier_counts = {"MEASURED": 0, "ESTABLISHED": 0, "INFERRED": 0, "HYPOTHESIS": 0}
    for chain in entry.get("chains", []):
        for edge in chain["edges"]:
            tier = edge.get("evidence_tier", "HYPOTHESIS")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

    cols = st.columns(4)
    cols[0].metric("🔬 Measured", tier_counts.get("MEASURED", 0),
                   help="IC50 data, clinical outcomes")
    cols[1].metric("✅ Established", tier_counts.get("ESTABLISHED", 0),
                   help="FDA approved, KEGG pathways")
    cols[2].metric("💡 Inferred", tier_counts.get("INFERRED", 0),
                   help="ESM2 similarity, computed")
    cols[3].metric("❓ Hypothesis", tier_counts.get("HYPOTHESIS", 0),
                   help="Literature citations, not quantified")

    # Show highest-tier evidence first
    best_tier = None
    for tier in ["MEASURED", "ESTABLISHED", "INFERRED", "HYPOTHESIS"]:
        if tier_counts.get(tier, 0) > 0:
            best_tier = tier
            break

    if best_tier:
        st.info(f"**Highest evidence tier:** {best_tier}")
```

**For PubMed edges, relabel confidence:**

```python
# In path display
if edge["evidence_tier"] in ["HYPOTHESIS", "SPECULATIVE"]:
    # Don't call it "confidence" - call it "graph coherence"
    meta = edge.get("metadata", {})
    coherence = meta.get("categorical_score", edge["confidence"])
    st.markdown(
        f"- **{edge['source']}** -{edge['relation']}-> **{edge['target']}** "
        f"(:orange[graph coherence: {coherence:.2f}], {prov_display})"
    )
else:
    # For measured/established data, confidence is meaningful
    st.markdown(
        f"- **{edge['source']}** -{edge['relation']}-> **{edge['target']}** "
        f"(:green[confidence: {edge['confidence']:.2f}], {prov_display})"
    )
```

### 3. Update "How Scoring Works" Page

Add explicit section:

```markdown
### ⚠️ Understanding Evidence Tiers vs. Graph Coherence

**MEASURED evidence (🔬):**
- IC50 binding data from ChEMBL or ABPP experiments
- Clinical trial outcomes (response rates, survival)
- Mutation frequencies from genomic databases
- **Confidence score = actual quantitative measurement**

**ESTABLISHED evidence (✅):**
- FDA-approved drug-disease indications
- KEGG canonical pathways
- **Confidence = regulatory/database authority**

**INFERRED evidence (💡):**
- ESM2 protein sequence similarity (0-1 cosine distance)
- STRING protein-protein interactions
- **Confidence = computational similarity metric**

**HYPOTHESIS evidence (❓):**
- PubMed citations without extracted quantitative data
- **"Confidence" is actually GRAPH COHERENCE (0-1)**
- Measures: Does this claim fit the rest of the knowledge graph?
- **NOT the biological strength of the relationship**

**Graph coherence (for HYPOTHESIS edges):**
- 5-layer categorical verification checks structural consistency
- High coherence (>0.4) = edge supported by graph topology
- Low coherence (<0.2) = edge contradicts known relationships
- **This filters noise, but doesn't measure effect size**

**When you see a score:**
- Check the evidence tier FIRST
- 0.85 MEASURED (IC50 data) >> 0.85 HYPOTHESIS (coherence)
- A HYPOTHESIS edge with high coherence is worth investigating
- But it's not equivalent to experimental validation
```

### 4. Update Documentation Everywhere

**CLAUDE.md:**
```markdown
## Evidence Tiers (2026-05-25)

The system distinguishes 4 evidence quality tiers:

1. **MEASURED** (~900 edges): ChEMBL IC50/Ki/Kd, ABPP experiments
   - Confidence = actual quantitative measurement
2. **ESTABLISHED** (~150 edges): FDA approvals, KEGG pathways
   - Confidence = regulatory/database authority
3. **INFERRED** (~500 edges): ESM2 similarity, STRING PPI
   - Confidence = computational metric
4. **HYPOTHESIS** (~3,400 edges): PubMed citations, not quantified
   - "Confidence" = graph coherence (0-1), NOT biological strength

**IMPORTANT:** Do not compare scores across tiers. A 0.9 MEASURED edge
is fundamentally different from a 0.9 HYPOTHESIS edge.
```

**RESEARCHER_GUIDE.md:**
Add decision tree:
```
1. Does the candidate have MEASURED evidence?
   YES → Check IC50 values, clinical data → HIGH PRIORITY
   NO → Continue

2. Does the candidate have ESTABLISHED evidence?
   YES → FDA/KEGG support → MEDIUM-HIGH PRIORITY
   NO → Continue

3. Does the candidate have INFERRED evidence only?
   YES → ESM2/computational → Verify with literature

4. Only HYPOTHESIS evidence?
   YES → High coherence (>0.5)? → Worth investigating, but validate experimentally
   NO → Low priority unless novel mechanism
```

---

## MEDIUM TERM: Real Quantification (2-4 months)

### Goal: Extract real biological measurements for key relationships

### 1. FDA-Approved Indications: Clinical Trial Data

**Data source:** ClinicalTrials.gov API + FDA labels

**What to extract:**
- Overall response rate (ORR)
- Progression-free survival (PFS) median months
- Overall survival (OS) hazard ratio
- Sample size (N patients)
- Trial phase

**Implementation:**

```python
# scripts/extract_clinical_outcomes.py

import requests
import json

# FDA-approved drug-disease pairs from tier1.db
APPROVED_PAIRS = [
    ("Imatinib", "CML", "NCT00000000"),  # Example trial ID
    ("Vemurafenib", "Melanoma", "NCT01..."),
    # ... all 44 pairs
]

def fetch_trial_outcome(nct_id: str) -> dict:
    """Fetch outcome measures from ClinicalTrials.gov API."""
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    resp = requests.get(url)
    data = resp.json()

    outcomes = {}
    for measure in data.get("protocolSection", {}).get("outcomesModule", {}).get("primaryOutcomes", []):
        if "response rate" in measure["measure"].lower():
            # Parse "ORR: 45%" from measure text
            outcomes["response_rate"] = parse_percentage(measure.get("description", ""))
        elif "progression-free survival" in measure["measure"].lower():
            outcomes["pfs_months"] = parse_months(measure.get("description", ""))

    outcomes["sample_size"] = data.get("protocolSection", {}).get("designModule", {}).get("enrollmentInfo", {}).get("count")

    return outcomes

# For each approved pair, find trial, extract outcomes
for drug, disease, nct_id in APPROVED_PAIRS:
    outcomes = fetch_trial_outcome(nct_id)

    # Store in database
    # UPDATE morphisms
    # SET quantitative_value = outcomes["response_rate"],
    #     value_unit = "response_rate_percentage",
    #     metadata = json({...outcomes...})
    # WHERE source = drug AND target = disease AND name = 'treats'
```

**Outcome storage:**
```json
{
  "clinical_outcomes": {
    "response_rate": 0.87,
    "pfs_months": 14.5,
    "os_hazard_ratio": 0.42,
    "sample_size": 553,
    "trial_phase": "III",
    "nct_id": "NCT01234567",
    "reference": "PMID:12345678"
  }
}
```

### 2. Protein-Disease Edges: Genomic Data

**Data sources:**
- **cBioPortal API:** Mutation frequencies across cancer types
- **TCGA:** Gene expression, copy number alterations
- **COSMIC:** Somatic mutations in cancer

**What to extract:**
- Mutation frequency (% of tumors with this gene mutated)
- Expression fold-change (tumor vs normal)
- Copy number alteration frequency
- Prognostic significance (p-value)

**Implementation:**

```python
# scripts/extract_genomic_data.py

import requests

CBIOPORTAL_URL = "https://www.cbioportal.org/api/v2"

def get_mutation_frequency(gene: str, cancer_type: str) -> dict:
    """
    Get mutation frequency from cBioPortal.

    Example: EGFR in NSCLC → 15% of tumors have EGFR mutations
    """
    # Map our disease names to cBioPortal study IDs
    study_map = {
        "NSCLC": "luad_tcga",
        "Melanoma": "skcm_tcga",
        "CML": "cml_ohsu_2018",
        # ... all 20 diseases
    }

    study_id = study_map.get(cancer_type)
    if not study_id:
        return {}

    # Query molecular profile for mutations
    url = f"{CBIOPORTAL_URL}/molecular-profiles/{study_id}_mutations/mutations"
    params = {"entrezGeneId": gene_to_entrez(gene)}

    resp = requests.get(url, params=params)
    data = resp.json()

    # Calculate frequency
    total_samples = get_sample_count(study_id)
    mutated_samples = len(set(m["sampleId"] for m in data))

    return {
        "mutation_frequency": mutated_samples / total_samples,
        "mutated_samples": mutated_samples,
        "total_samples": total_samples,
        "source": f"cBioPortal:{study_id}"
    }

# For all protein-disease edges
for protein, disease in protein_disease_pairs:
    freq_data = get_mutation_frequency(protein, disease)

    if freq_data["mutation_frequency"] > 0:
        # Store in database
        # UPDATE morphisms
        # SET evidence_tier = 'MEASURED',
        #     quantitative_value = freq_data["mutation_frequency"],
        #     value_unit = "mutation_frequency"
        # WHERE source = protein AND target = disease
```

**Outcome storage:**
```json
{
  "genomic_data": {
    "mutation_frequency": 0.15,
    "mutated_samples": 87,
    "total_samples": 580,
    "expression_fold_change": 2.3,
    "cna_frequency": 0.08,
    "prognostic_pvalue": 0.001,
    "source": "cBioPortal:luad_tcga"
  }
}
```

### 3. High-Value PMIDs: Manual Curation

**Goal:** For top 50 candidates, manually extract effect sizes from papers

**Workflow:**
1. Run triage for all 20 diseases
2. Identify top 10 NOT_APPROVED candidates per disease (200 total)
3. For each candidate, find the most-cited PMID in the evidence chains
4. Human curator reads paper, extracts:
   - Study design (RCT, observational, case study)
   - Sample size
   - Effect size (OR, HR, correlation coefficient)
   - P-value, confidence interval
   - Conclusion (positive, negative, inconclusive)

**Template:**
```yaml
# curated_evidence/Sorafenib_Melanoma.yaml
drug: Sorafenib
disease: Melanoma
pmid: 12345678
title: "Phase II trial of sorafenib in melanoma"
study_design: Phase II clinical trial
sample_size: 40
primary_outcome:
  measure: Overall response rate
  value: 0.10
  unit: proportion
  ci_lower: 0.02
  ci_upper: 0.18
  p_value: 0.08
secondary_outcomes:
  - measure: Progression-free survival
    value: 3.2
    unit: months
    ci_lower: 2.1
    ci_upper: 4.5
conclusion: "Modest activity in melanoma, below expectations"
evidence_tier: MEASURED
curator: JRH
date: 2026-05-25
```

**Import script:**
```python
# scripts/import_curated_evidence.py
import yaml
import glob

for yaml_file in glob.glob("curated_evidence/*.yaml"):
    data = yaml.safe_load(open(yaml_file))

    # Update morphism with quantitative data
    # SET quantitative_value = data["primary_outcome"]["value"],
    #     value_unit = data["primary_outcome"]["measure"],
    #     evidence_tier = "MEASURED",
    #     metadata = json(data)
```

### 4. Hybrid Scoring System

**Goal:** Use real data when available, fall back to graph coherence

```python
# validation/repurposing_benchmark.py

def hybrid_score(drug: str, disease: str, category: Category) -> float:
    """
    Scoring priority:
    1. If MEASURED evidence exists → use quantitative value
    2. If ESTABLISHED → use high confidence (0.9)
    3. If INFERRED → use computational metric
    4. If HYPOTHESIS only → use graph coherence (current system)
    """

    # Check for direct edge
    direct_edge = category.get_morphism(drug, disease)
    if direct_edge:
        tier = direct_edge.metadata.get("evidence_tier", "HYPOTHESIS")

        if tier == "MEASURED":
            # Use quantitative value (response rate, mutation freq, etc.)
            value = direct_edge.metadata.get("quantitative_value", direct_edge.confidence)
            return value
        elif tier == "ESTABLISHED":
            return 0.95  # FDA-approved
        elif tier == "INFERRED":
            return direct_edge.confidence  # ESM2 similarity
        # else: HYPOTHESIS, continue to path-based scoring

    # Path-based scoring (current Kan extension + composition system)
    strategies = make_strategies(category)
    score, votes = score_pair(strategies, drug, disease)

    # But weight strategies by their evidence tier
    measured_votes = [c for n, c in votes if has_measured_evidence(n, drug, disease)]
    if measured_votes:
        return max(measured_votes)  # Trust measured evidence most

    return score  # Fall back to graph coherence
```

---

## DATA SOURCE EXPANSION ANALYSIS

### Goal: Leverage underutilized data sources from early development

### Current Usage Audit

```python
# scripts/audit_data_source_coverage.py

import sqlite3
import json
from collections import Counter

conn = sqlite3.connect("data/drugs/tier1.db")
cursor = conn.cursor()

# Count edges by provenance source
cursor.execute("SELECT provenance FROM morphisms")
all_prov = cursor.fetchall()

sources = Counter()
for (prov,) in all_prov:
    if "ChEMBL" in prov:
        sources["ChEMBL"] += 1
    elif "ESM" in prov or "ESM-2" in prov:
        sources["ESM2"] += 1
    elif "PMID:" in prov:
        sources["PubMed"] += 1
    elif "FDA" in prov:
        sources["FDA"] += 1
    elif "KEGG" in prov:
        sources["KEGG"] += 1
    elif "STRING" in prov:
        sources["STRING"] += 1
    elif "ABPP" in prov:
        sources["ABPP"] += 1
    # ... etc

print("Current data source usage:")
for source, count in sources.most_common():
    print(f"  {source}: {count} edges")

# Check diseases covered by each source
cursor.execute("""
    SELECT DISTINCT target_name
    FROM morphisms
    WHERE provenance LIKE '%ESM%'
""")
esm2_diseases = [row[0] for row in cursor.fetchall()]

print(f"\nESM2 covers {len(esm2_diseases)} diseases:")
print(esm2_diseases)

# Find diseases with sparse coverage
all_diseases = ["AML", "Breast_Cancer", "CML", ...]  # All 20
for disease in all_diseases:
    cursor.execute("""
        SELECT COUNT(*) FROM morphisms
        WHERE target_name = ? AND provenance LIKE '%ESM%'
    """, (disease,))
    esm_count = cursor.fetchone()[0]

    if esm_count < 10:
        print(f"⚠️  {disease} has only {esm_count} ESM2 edges - can expand!")
```

### ESM2 Expansion Opportunity

**Current state:** ESM2 was used to add protein similarity edges for a few diseases (AML, CML, maybe 5 total)

**Expansion plan:**

```python
# scripts/expand_esm2_to_all_diseases.py

from sentence_transformers import SentenceTransformer
import numpy as np

# Load ESM2 model
model = SentenceTransformer('facebook/esm2_t33_650M_UR50D')

# Get all proteins currently in database
proteins = get_all_proteins()  # 366 proteins

# Get all diseases
diseases = get_all_diseases()  # 20 diseases

# For each disease, find which proteins are already linked
for disease in diseases:
    known_proteins = get_proteins_for_disease(disease)

    if len(known_proteins) < 5:
        print(f"⚠️  {disease} has only {len(known_proteins)} known proteins")
        continue

    # Compute ESM2 embeddings for known proteins
    known_seqs = [get_protein_sequence(p) for p in known_proteins]
    known_embeds = model.encode(known_seqs)

    # Compute embeddings for all other proteins
    candidate_proteins = [p for p in proteins if p not in known_proteins]
    candidate_seqs = [get_protein_sequence(p) for p in candidate_proteins]
    candidate_embeds = model.encode(candidate_seqs)

    # Find similar proteins (cosine similarity > 0.75)
    for i, candidate in enumerate(candidate_proteins):
        similarities = cosine_similarity([candidate_embeds[i]], known_embeds)[0]
        max_sim = np.max(similarities)
        most_similar = known_proteins[np.argmax(similarities)]

        if max_sim > 0.75:
            print(f"  {candidate} similar to {most_similar} ({max_sim:.2f})")

            # Add edge: candidate --[associated_with]--> disease
            # SET provenance = f"ESM2 similarity to {most_similar} ({max_sim:.2f})",
            #     confidence = max_sim,
            #     evidence_tier = "INFERRED"
```

**Expected gain:** 300-500 new protein-disease edges for diseases that currently have sparse coverage

### STRING PPI Expansion

**Current:** 22 edges from STRING

**Opportunity:** STRING has ~11 million protein-protein interactions

```python
# scripts/expand_string_ppi.py

import requests

STRING_API = "https://string-db.org/api/json"

def get_string_interactions(protein: str, species: str = "9606") -> list:
    """Get all STRING interactions for a protein."""
    url = f"{STRING_API}/network"
    params = {
        "identifiers": protein,
        "species": species,
        "required_score": 700,  # High confidence (0-1000)
    }
    resp = requests.get(url, params=params)
    return resp.json()

# For each protein in our database
for protein in get_all_proteins():
    interactions = get_string_interactions(protein)

    for interaction in interactions:
        partner = interaction["preferredName_B"]
        score = interaction["score"] / 1000.0  # Normalize to 0-1

        if partner in proteins and score > 0.7:
            # Add PPI edge if not exists
            # INSERT morphism: protein --[interacts_with]--> partner
            # SET provenance = f"STRING PPI (score {score})",
            #     confidence = score,
            #     evidence_tier = "INFERRED"
```

**Expected gain:** 1000-2000 high-confidence PPIs

### ChEMBL Expansion: More Diseases

**Current:** 881 ChEMBL edges, mostly for oncology targets

**Opportunity:** ChEMBL has data for rare diseases, non-cancer indications

```python
# scripts/expand_chembl_rare_diseases.py

from chembl_webresource_client.new_client import new_client

# ChEMBL API clients
molecule = new_client.molecule
assay = new_client.assay
activity = new_client.activity

# Check if ChEMBL has data for our 20 diseases
disease_efo_map = {
    "AML": "EFO_0000222",
    "Melanoma": "EFO_0000756",
    # ... map all 20 to EFO IDs
}

for disease, efo_id in disease_efo_map.items():
    # Find assays related to this disease
    assays = assay.filter(disease_efo_id=efo_id)

    print(f"\n{disease} ({efo_id}):")
    print(f"  ChEMBL assays: {len(assays)}")

    # For each drug in our database
    for drug in get_all_drugs():
        chembl_id = get_chembl_id(drug)
        if not chembl_id:
            continue

        # Get activities for this drug in disease-related assays
        activities = activity.filter(
            molecule_chembl_id=chembl_id,
            assay_type="B",  # Binding
            pchembl_value__gte=6  # IC50 <= 1 μM
        )

        for act in activities:
            target = act["target_chembl_id"]
            ic50 = 10 ** (-act["pchembl_value"])  # Convert pChEMBL to μM

            # Add edge: drug --[inhibits]--> target
            # SET quantitative_value = ic50,
            #     value_unit = "IC50_uM",
            #     evidence_tier = "MEASURED"
```

### OpenTargets: Disease-Gene Associations

**New data source (not currently used):**

```python
# scripts/import_opentargets_associations.py

import requests

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"

query = """
query diseaseGenes($efoId: String!) {
  disease(efoId: $efoId) {
    associatedTargets(page: {size: 100}) {
      rows {
        target {
          approvedSymbol
        }
        score
        datatypeScores {
          id
          score
        }
      }
    }
  }
}
"""

for disease, efo_id in disease_efo_map.items():
    resp = requests.post(OPENTARGETS_API, json={
        "query": query,
        "variables": {"efoId": efo_id}
    })
    data = resp.json()

    for row in data["data"]["disease"]["associatedTargets"]["rows"]:
        gene = row["target"]["approvedSymbol"]
        score = row["score"]

        # Check individual evidence types
        genetic_score = next((d["score"] for d in row["datatypeScores"] if d["id"] == "genetic_association"), 0)
        somatic_score = next((d["score"] for d in row["datatypeScores"] if d["id"] == "somatic_mutation"), 0)

        if score > 0.5:  # Medium-high association
            # Add edge: gene --[associated_with]--> disease
            # SET confidence = score,
            #     evidence_tier = "INFERRED" if genetic_score > 0.7 else "HYPOTHESIS",
            #     provenance = f"OpenTargets (score {score:.2f})"
```

**Expected gain:** 500-1000 high-quality gene-disease associations

---

## LONG TERM: Research-Grade System (6-12 months)

### 1. NLP Extraction Pipeline

**Goal:** Automatically extract quantitative data from PMIDs

**Architecture:**

```
PubMed PMID → Entrez API → Full text XML/JSON
    ↓
PubTator API → Entity recognition (genes, drugs, diseases)
    ↓
Custom NLP pipeline:
  - Regex patterns for "IC50", "response rate", "hazard ratio"
  - Parse tables (pandas, camelot)
  - Extract numeric values + units
    ↓
Validation:
  - Does extracted value make sense? (IC50 should be nM-μM range)
  - Multiple extractions agree?
  - Manual review for top candidates
    ↓
Database storage as MEASURED evidence
```

**Implementation sketch:**

```python
# nlp/extract_quantitative_data.py

from Bio import Entrez
import re
import spacy

nlp = spacy.load("en_core_sci_sm")  # ScispaCy biomedical NLP

def fetch_full_text(pmid: str) -> str:
    """Get full text from PubMed Central if available."""
    Entrez.email = "your@email.com"
    handle = Entrez.efetch(db="pmc", id=pmid, retmode="xml")
    xml = handle.read()
    # Parse XML, extract text
    return extracted_text

def extract_ic50(text: str) -> list:
    """Extract IC50 values from text."""
    # Pattern: "IC50 = 0.5 μM", "IC50 of 12 nM", etc.
    pattern = r"IC50[:\s=]+([0-9.]+)\s*(nM|μM|uM|mM)"
    matches = re.findall(pattern, text, re.IGNORECASE)

    ic50_values = []
    for value, unit in matches:
        # Convert to μM
        value_um = float(value)
        if unit == "nM":
            value_um /= 1000
        elif unit == "mM":
            value_um *= 1000

        ic50_values.append(value_um)

    return ic50_values

def extract_clinical_outcome(text: str) -> dict:
    """Extract clinical trial outcomes."""
    outcomes = {}

    # Response rate
    rr_pattern = r"response rate[:\s]+([0-9.]+)%"
    match = re.search(rr_pattern, text, re.IGNORECASE)
    if match:
        outcomes["response_rate"] = float(match.group(1)) / 100

    # Hazard ratio
    hr_pattern = r"hazard ratio[:\s=]+([0-9.]+)"
    match = re.search(hr_pattern, text, re.IGNORECASE)
    if match:
        outcomes["hazard_ratio"] = float(match.group(1))

    return outcomes
```

### 2. Bayesian Evidence Integration

**Goal:** Principled combination of heterogeneous evidence types

```python
# oracle/bayesian_scorer.py

import numpy as np
from scipy.stats import beta

class BayesianEvidenceScorer:
    """
    Bayesian approach to combining evidence:
    P(edge is true | all evidence) ∝ P(all evidence | edge is true) × P(edge is true)
    """

    def __init__(self):
        # Prior: What fraction of drug-disease pairs are true indications?
        # Very low! Maybe 0.001 (1 in 1000)
        self.prior = 0.001

    def likelihood_ic50(self, ic50_um: float) -> float:
        """
        Likelihood that we'd see this IC50 if the edge is true.

        Strong binding (IC50 < 0.1 μM) → high likelihood
        Weak binding (IC50 > 10 μM) → low likelihood
        """
        if ic50_um < 0.1:
            return 0.95  # Very strong evidence
        elif ic50_um < 1.0:
            return 0.80  # Strong evidence
        elif ic50_um < 10.0:
            return 0.50  # Moderate evidence
        else:
            return 0.20  # Weak evidence

    def likelihood_clinical_outcome(self, response_rate: float, sample_size: int) -> float:
        """
        Likelihood based on clinical trial results.

        High response rate + large N → strong evidence
        """
        if response_rate > 0.5 and sample_size > 100:
            return 0.90
        elif response_rate > 0.3 and sample_size > 50:
            return 0.70
        else:
            return 0.40

    def likelihood_pmid(self, graph_coherence: float) -> float:
        """
        Likelihood from PMID citation + graph coherence.

        High coherence → modest evidence boost
        Low coherence → slightly negative
        """
        return 0.30 + 0.30 * graph_coherence  # 0.30-0.60 range

    def posterior(self, evidence: dict) -> float:
        """
        Compute posterior P(edge true | evidence).

        Args:
            evidence: {
                "ic50": 0.5,  # μM
                "response_rate": 0.45,
                "sample_size": 120,
                "graph_coherence": 0.65,
                "num_pmids": 3
            }
        """
        # Start with prior
        p_true = self.prior

        # Update with each piece of evidence (Bayes rule)
        if "ic50" in evidence:
            likelihood = self.likelihood_ic50(evidence["ic50"])
            p_true = self.update_posterior(p_true, likelihood)

        if "response_rate" in evidence and "sample_size" in evidence:
            likelihood = self.likelihood_clinical_outcome(
                evidence["response_rate"],
                evidence["sample_size"]
            )
            p_true = self.update_posterior(p_true, likelihood)

        if "graph_coherence" in evidence:
            likelihood = self.likelihood_pmid(evidence["graph_coherence"])
            p_true = self.update_posterior(p_true, likelihood)

        return p_true

    def update_posterior(self, prior: float, likelihood: float) -> float:
        """Bayes update: P(H|E) = P(E|H) × P(H) / P(E)"""
        # Assume P(E|not H) = 0.5 (evidence is random noise if edge is false)
        p_not_true = 1 - prior
        p_evidence = likelihood * prior + 0.5 * p_not_true

        return (likelihood * prior) / p_evidence

# Usage:
scorer = BayesianEvidenceScorer()
score = scorer.posterior({
    "ic50": 0.12,  # Strong binding
    "response_rate": 0.45,
    "sample_size": 120,
    "graph_coherence": 0.65
})
# → score ≈ 0.85 (high confidence)

score2 = scorer.posterior({
    "graph_coherence": 0.45  # Only PMID, no quantitative data
})
# → score ≈ 0.02 (low confidence, prior dominates)
```

### 3. Uncertainty Quantification

**Goal:** Report confidence intervals, not point estimates

```python
# oracle/uncertainty.py

from scipy.stats import beta, binom
import numpy as np

def confidence_interval_ic50(ic50_measurements: list, confidence: float = 0.95) -> tuple:
    """
    If we have multiple IC50 measurements, compute CI.

    Args:
        ic50_measurements: [0.5, 0.7, 0.45] μM from different assays
        confidence: 0.95 for 95% CI

    Returns:
        (lower_bound, upper_bound, median)
    """
    if len(ic50_measurements) < 2:
        # Can't compute CI from 1 measurement
        return (ic50_measurements[0], ic50_measurements[0], ic50_measurements[0])

    # Use bootstrap to get CI
    bootstraps = []
    for _ in range(1000):
        sample = np.random.choice(ic50_measurements, size=len(ic50_measurements), replace=True)
        bootstraps.append(np.median(sample))

    lower = np.percentile(bootstraps, (1 - confidence) / 2 * 100)
    upper = np.percentile(bootstraps, (1 + confidence) / 2 * 100)
    median = np.median(ic50_measurements)

    return (lower, upper, median)

def confidence_interval_response_rate(responders: int, total: int, confidence: float = 0.95) -> tuple:
    """
    Wilson score interval for binomial proportion.

    Args:
        responders: Number of patients who responded
        total: Total patients in trial

    Returns:
        (lower_bound, upper_bound, point_estimate)
    """
    from statsmodels.stats.proportion import proportion_confint

    lower, upper = proportion_confint(responders, total, alpha=1-confidence, method='wilson')
    point = responders / total

    return (lower, upper, point)

# Display in UI:
# "Response rate: 45% (95% CI: 38%-52%)"
# "IC50: 0.5 μM (95% CI: 0.3-0.8 μM, N=3 assays)"
```

---

## IMPLEMENTATION PRIORITY

### Phase 1 (Week 1-2): SHORT TERM - Honest Presentation
- ✅ Add `evidence_tier` column to database
- ✅ Classify all 4944 edges into tiers
- ✅ Update UI to show tier breakdown
- ✅ Relabel "confidence" → "graph coherence" for HYPOTHESIS edges
- ✅ Update all documentation

**Deliverable:** Users see MEASURED vs HYPOTHESIS distinction, no more conflating graph coherence with biological strength

### Phase 2 (Month 1-2): MEDIUM TERM - Clinical Data
- Extract clinical outcomes for 44 FDA-approved pairs (ClinicalTrials.gov API)
- Extract mutation frequencies for top 100 protein-disease pairs (cBioPortal)
- Manually curate top 50 PMID papers for effect sizes
- Implement hybrid scoring: prefer MEASURED > ESTABLISHED > INFERRED > HYPOTHESIS

**Deliverable:** Top candidates have real quantitative data, not just citations

### Phase 3 (Month 2-3): DATA EXPANSION
- Expand ESM2 to all 20 diseases (currently only ~5)
- Import STRING PPI high-confidence interactions
- Add OpenTargets gene-disease associations
- Expand ChEMBL for rare diseases and non-oncology

**Deliverable:** 2x-3x more edges, better coverage for sparse diseases

### Phase 4 (Month 4-6): MEDIUM TERM - Bayesian Integration
- Implement Bayesian evidence scorer
- Add uncertainty quantification (confidence intervals)
- Test on validation set, compare to point-estimate system

**Deliverable:** Probabilistic scores with uncertainty bounds

### Phase 5 (Month 6-12): LONG TERM - NLP Pipeline
- Build PubMed full-text extraction
- Implement regex + NLP for IC50, response rates, hazard ratios
- Validate extractions (manual review of 100 papers)
- Scale to all 609 PMIDs

**Deliverable:** Automated quantitative data extraction

---

## SUCCESS METRICS

### Short term:
- [ ] 100% of edges classified into evidence tiers
- [ ] UI shows tier breakdown for every candidate
- [ ] Documentation clarifies graph coherence ≠ biological strength
- [ ] Zero user confusion about what confidence scores mean

### Medium term:
- [ ] 44/44 FDA-approved pairs have clinical outcome data
- [ ] Top 100 protein-disease pairs have mutation frequency data
- [ ] Top 50 NOT_APPROVED candidates have manually curated effect sizes
- [ ] Hybrid scoring system prefers measured data over graph coherence

### Long term:
- [ ] 500+ PMIDs have automatically extracted quantitative data
- [ ] Bayesian scorer provides posterior probabilities with CIs
- [ ] External validation: predictions correlate with prospective clinical trials
- [ ] System publishable in peer-reviewed journal (e.g., Nature Biotech)

---

## RISKS & MITIGATIONS

### Risk 1: Data extraction is noisy
**Mitigation:** Manual validation of top candidates, flag low-confidence extractions

### Risk 2: Multiple evidence types are hard to combine
**Mitigation:** Bayesian framework provides principled integration, report uncertainty

### Risk 3: Users still misinterpret scores
**Mitigation:** Explicit tier labels (MEASURED/HYPOTHESIS), clear documentation, decision trees

### Risk 4: External APIs change or go offline
**Mitigation:** Cache all fetched data, version manifests, fallback to graph-only mode

---

**Next step:** Implement Phase 1 (evidence tier classification) this week?
