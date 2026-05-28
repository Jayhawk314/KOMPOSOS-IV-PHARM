# Getting Started with KOMPOSOS-IV-PHARM

This guide will have you running drug repurposing candidate triage within 5 minutes.

**Audience**: First-time users (practitioners, researchers, developers)
**Time**: ~5 minutes for setup + first triage

---

## Prerequisites

- **Python 3.10+** (check: `python --version`)
- **SQLite** (built into Python, no separate install needed)
- **pip** (check: `pip --version`)
- *Optional*: **Git** (to clone the repo)
- *Optional*: **Streamlit** (for web UI)

---

## 1. Install

### Option A: Clone from GitHub

```bash
git clone https://github.com/your-repo/KOMPOSOS-IV-PHARM.git
cd KOMPOSOS-IV-PHARM
pip install -r requirements.txt
```

### Option B: Install from directory

```bash
cd /path/to/KOMPOSOS-IV-PHARM
pip install -e .
```

---

## 2. Verify Installation

Check that the database and validation tools are present:

```bash
# Should exist: data/drugs/tier1.db (3.67 MB)
ls data/drugs/tier1.db

# Should exist: validation/triage.py
ls validation/triage.py
```

Test the triage tool:

```bash
python validation/triage.py --help
```

Expected output: Help text with usage modes (disease-first, drug-first, pair detail).

---

## 3. Run Your First Triage

### Example 1: Rank drugs for a disease (disease-first)

```bash
python validation/triage.py Melanoma --top 10
```

**Expected output** (example):
```
====== TRIAGE: Melanoma ======
Source: data/drugs/tier1.db | View: full_typed | Strategy votes: 9

Self-check: 44/44 FDA-approved pairs recovered ✓

Top 10 candidates for Melanoma:
==========================================================

1. Sorafenib [APPROVED 2008]
   Score: 0.910
   Votes: Mechanistic Path(0.81) Binding Evidence(0.87) Drug Analogy(0.90)
   Evidence:
   - Sorafenib --inhibits--> BRAF [IC50=25.8 nM, PMID:12829955]
   - Sorafenib --inhibits--> VEGFR2 [PMID:18241329]
   - BRAF, VEGFR2 --regulate--> Melanoma proliferation [PMID:16116430]
   Top evidence: PMID:18241329 (FDA approval), PMID:12829955 (binding)

2. Vemurafenib [APPROVED 2011]
   Score: 0.905
   Votes: Mechanistic Path(0.81) Binding Evidence(0.88) Structural Similarity(0.79)
   Evidence:
   - Vemurafenib --inhibits--> BRAF [IC50=13.1 nM, PMID:21346200]
   - BRAF --mutation--> Melanoma [Mutation freq=70.0%, PMID:15184864]
   Top evidence: PMID:21346200, PMID:15184864

... (continuing with remaining top candidates)
```

### Example 2: Rank diseases for a drug (drug-first)

```bash
python validation/triage.py --drug Sorafenib --top 5
```

**Expected output**:
```
====== TRIAGE: Sorafenib (drug-first) ======

Top 5 diseases for Sorafenib:
==========================================================

1. Melanoma [APPROVED]
   Score: 0.910
   ...

2. Renal Cell Carcinoma [APPROVED]
   Score: 0.887
   ...

3. Hepatocellular Carcinoma [APPROVED]
   ...
```

### Example 3: Deep dive on a specific pair (pair detail)

```bash
python validation/triage.py Melanoma --drug Vemurafenib
```

**Expected output** (full detail mode):
```
====== PAIR DETAIL: Melanoma + Vemurafenib ======

Status: APPROVED (FDA 2011, PMID:21346200)

Score breakdown:
  Mechanistic Path:    0.81  (composition)
  Binding Evidence:    0.87  (IC50 + drug properties)
  Interaction Profile: 0.73  (yoneda_pattern)
  Structural Inference: 0.70 (fibration_lift)
  Evidence Integration: 0.81 (topos_logic)
  Drug Analogy:        0.90  (kan_extension)
  Structural Similarity: 0.32 (yoneda_distance, live only)

Final score: 0.905 (above decision threshold 0.50)

Mechanistic paths (confidence-weighted):
  Path 1: Vemurafenib --inhibits--> BRAF (0.95)
          BRAF --mutated-in--> Melanoma (0.91)
          Compound confidence: 0.95 × 0.91 = 0.865

  Path 2: Vemurafenib --inhibits--> VEGFR2 (0.85)
          VEGFR2 --promotes--> Angiogenesis (0.88)
          Angiogenesis --supports--> Melanoma (0.80)
          Compound confidence: 0.85 × 0.88 × 0.80 = 0.597

Evidence chain (with PMIDs):
  Vemurafenib IC50 for BRAF: 13.1 nM
  Evidence source: PMID:21346200 (Bollag et al., Cancer Res 2010)

  BRAF mutation in Melanoma: 70.0% of cases
  Evidence source: PMID:15184864 (Davies et al., Nature 2002)

Structural similarity (Yoneda presheaf):
  Most similar approved drug: Encorafenib (score 0.79)
  Reason: Both inhibit BRAF; targets=={BRAF, RafKinases}

Full evidence dump: (attach --dump-pmids to list all 15 cited papers)
```

---

## 4. Common Commands

```bash
# Show top 20 candidates (not default 10)
python validation/triage.py Melanoma --top 20

# Output as JSON (for scripting)
python validation/triage.py Melanoma --json

# Output as Markdown (for reports)
python validation/triage.py Melanoma --markdown > melanoma_candidates.md

# Show all candidates, not just top 10
python validation/triage.py Melanoma --all

# Use a different database
python validation/triage.py Melanoma --db /path/to/custom_tier1.db

# Suppress detail for top 5, show all candidates
python validation/triage.py Melanoma --top 5 --all --brief
```

---

## 5. What's Happening Behind the Scenes?

When you run `python validation/triage.py Melanoma`, the system:

1. **Loads the database** (`data/drugs/tier1.db`): 464 objects, 5382 morphisms
2. **Removes direct labels**: Melanoma → Drug edges temporarily removed (prevents leakage)
3. **Finds all paths**: Drug → Protein → Disease paths for each drug
4. **Scores each path**: Multiplies confidences along the path (e.g., 0.95 × 0.91 = 0.865)
5. **Runs the active strategy profile**: composition, binding evidence, graph/categorical structure modules, and conditional Yoneda distance when visible comparators exist
6. **Aggregates votes**: Combines active strategy scores into a ranking score
7. **Ranks drugs**: Highest score first
8. **Formats output**: Recovers FDA labels, formats evidence chains with PMIDs

---

## 6. Understanding the Output

### Score Range

- **0.0 – 0.50**: Not recommended (below decision threshold)
- **0.50 – 0.75**: Possible candidate (worth investigating)
- **0.75 – 1.00**: Strong candidate (mechanistically justified)

### Strategy Votes

Each strategy contributes a score 0.0–1.0. Examples:

- **Mechanistic Path**: 0.81 = high-confidence Drug→Protein→Disease paths
- **Binding Evidence**: 0.87 = good ABPP IC50 binding data
- **Structural Similarity**: 0.32 = live/as-loaded structural similarity to visible known treatments; absent in strict `remove_direct_labels`
- **Drug Analogy**: 0.90 = similarity to other drugs with similar targets

### Evidence Chains

Each candidate shows:
- **Targets**: What proteins does the drug hit?
- **Binding data**: IC50 values, engagement status (from ABPP)
- **Disease relevance**: How are targets connected to the disease?
- **PMID citations**: Where is the evidence from?

---

## 7. Next Steps

### Learn the science

- **How does repurposing work?** → Read [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md)
- **How is this validated?** → Read [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md)
- **Where does the data come from?** → Read [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md)

### Dive deeper

- **How do I triage my own drug/disease?** → Use the examples above
- **Can I validate a specific pair?** → Use `python validation/trace_prediction.py Disease Drug`
- **Can I run the full benchmark?** → Use `python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci`

### For developers

- **How does the code work?** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
- **How do I add a new strategy?** → Read [STRATEGIES_IN_DEPTH.md](STRATEGIES_IN_DEPTH.md) and [CONTRIBUTING.md](CONTRIBUTING.md)
- **What APIs are available?** → Read [API_REFERENCE.md](API_REFERENCE.md)

---

## 8. Troubleshooting

### "Module not found" or "import error"

```bash
# Reinstall with development mode
pip install -e .

# Verify Python 3.10+
python --version  # should be 3.10 or higher
```

### "Database not found" (tier1.db missing)

```bash
# Rebuild the database from manifest
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

### "No candidates found" or empty output

```bash
# Verify the disease name is in the database
python -c "
import data.store as store
s = store.KomposOSStore('data/drugs/tier1.db')
diseases = [obj.name for obj in s.list_objects(limit=None) if obj.type_name == 'Disease']
print('Available diseases:', diseases)
"
```

Common disease names:
- Melanoma
- Renal Cell Carcinoma
- Non-Small-Cell Lung Cancer
- Hepatocellular Carcinoma
- Ovarian Cancer
- Prostate Cancer
- Colorectal Cancer
- ...and 13 more (see above command)

### "Slow performance" or timeout

- First run loads all paths (2-5 sec on typical hardware)
- Subsequent runs are cached
- If timeout >10 sec, check disk space and available memory

### "Strange ranking" or unexpected candidates

This is likely correct! See:
- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) for validation protocols
- [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) for how scoring works
- [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md) for common misconceptions

---

## 9. Full CLI Help

```bash
python validation/triage.py --help
```

Output:
```
usage: triage.py [-h] [disease] [--drug DRUG] [--db DB] [--view VIEW]
                 [--top N] [--all] [--brief] [--json] [--markdown]
                 [--dump-pmids]

Triage drug candidates for disease (or vice versa)

positional arguments:
  disease               Disease name (e.g., 'Melanoma')

options:
  --drug DRUG           Drug name; if set, rank diseases for this drug instead
  --db DB               Path to tier1.db (default: data/drugs/tier1.db)
  --view VIEW           View type: 'legacy' or 'full_typed' (default: full_typed)
  --top N               Show top N candidates (default: 10)
  --all                 Show all candidates, not just top N
  --brief               Suppress detail; show only ranks and scores
  --json                Output as JSON (for scripting)
  --markdown            Output as Markdown (for reports)
  --dump-pmids          Include full PMID citation list
```

---

## 10. Common Questions

**Q: Can I use this on my own data?**
A: Yes, but Track A was trained/validated on oncology. Apply to other domains at your own risk. See [DATA_AND_DATABASE.md](DATA_AND_DATABASE.md) for data structure.

**Q: How often is the database updated?**
A: Currently static (2026-05-26 snapshot, 609 PMID identifiers). Updates require rebuilding from manifest. See [DATA_AND_DATABASE.md](DATA_AND_DATABASE.md).

**Q: Can I export candidates as a CSV?**
A: Use `--json` flag and parse with your tool. Markdown export is also available with `--markdown`.

**Q: What's the difference between APPROVED and NOT_APPROVED status?**
A: APPROVED = in our 44 FDA oncology indications. NOT_APPROVED = not in the DB but may already be in clinical trials. See [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md).

**Q: Why is [my drug] ranked low?**
A: Check:
1. Is it in the database? (`python validation/triage.py --drug YourDrug`)
2. Does it have targets? (`python validation/trace_prediction.py Disease YourDrug`)
3. Are those targets connected to the disease? (See evidence chain)

For more Q&A, see [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md).

---

## Next: Validate the System

Want to confirm AUROC 0.9747? Run:

```bash
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels
```

Expected output:
```
AUROC: 0.9747
AUPRC: 0.552
Hits@5: 1.00
Hits@10: 0.60
...
Self-check: 44/44 approved pairs recovered ✓
```

See [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) for full details.

---

**Ready to explore?** Start with `python validation/triage.py Melanoma` and check the output!

For deep dives, see the full documentation:
- [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) — How repurposing works
- [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Metrics & validation
- [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Data sources
- [TROUBLESHOOTING_AND_FAQ.md](TROUBLESHOOTING_AND_FAQ.md) — Common issues

*Last updated: 2026-05-26*
