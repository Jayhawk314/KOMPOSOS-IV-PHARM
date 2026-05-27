# Troubleshooting and FAQ

**Purpose**: Common issues, error messages, and frequently asked questions.

**Audience**: All users

---

## Installation Issues

### "Python version error" or "Python 3.10+ required"

**Error**: `SyntaxError` or `TypeError` mentioning type hints

**Cause**: Using Python < 3.10. Type hints with `|` (union syntax) require 3.10+.

**Fix**:
```bash
python --version  # Check current version
python3.10 --version  # Check if 3.10 is available

# Install Python 3.10+ or use virtual environment
python3.10 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

### "ModuleNotFoundError: No module named 'core'"

**Error**: `from core.category import Category` fails

**Cause**: Package not installed, or running from wrong directory

**Fix**:
```bash
# From repo root, install in development mode
pip install -e .

# Or add repo to Python path
export PYTHONPATH=/path/to/KOMPOSOS-IV-PHARM:$PYTHONPATH
```

---

### "SQLite3 not found"

**Unlikely**: SQLite3 ships with Python.

**If it happens**:
```bash
# Reinstall Python
# Or on Linux: apt-get install sqlite3 libsqlite3-dev
```

---

## Data Loading Issues

### "Database not found: data/drugs/tier1.db"

**Cause**: Database file missing or deleted

**Fix**:
```bash
# Rebuild database from manifest
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json

# Verify
ls -la data/drugs/tier1.db
```

---

### "Database corrupted" or "Database disk image is malformed"

**Cause**: Interrupted write or file corruption

**Fix**:
```bash
# Delete corrupted DB
rm data/drugs/tier1.db

# Rebuild
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

---

### "Object not found: Melanoma" or similar

**Cause**: Disease/drug name misspelled or not in database

**Fix**:
```bash
# List available diseases
python -c "
from data.store import KomposOSStore
store = KomposOSStore('data/drugs/tier1.db')
diseases = [obj.name for obj in store.list_objects(limit=None) if obj.type_name == 'Disease']
print('Available diseases:', sorted(diseases))
"

# Expected output includes: Melanoma, Non-Small-Cell Lung Cancer, ...
```

**Common names**:
- Melanoma ✓
- Renal Cell Carcinoma ✓
- Non-Small-Cell Lung Cancer ✓
- Hepatocellular Carcinoma ✓
- Ovarian Cancer ✓
- Prostate Cancer ✓
- Colorectal Cancer ✓

---

## Triage CLI Issues

### "No candidates found" or empty output

**Cause**: Database not loaded, or no paths from drugs to disease

**Fix**:
```bash
# Verify database exists
ls data/drugs/tier1.db

# Check disease name (exact match required)
python validation/triage.py Melanoma --help

# If still empty, try verbose mode
python validation/triage.py Melanoma --all
```

---

### "Slow performance" or timeout

**Cause**: Path finding is expensive (first run); database indexes missing

**Fix**:
```bash
# First run will be slow (2–5 sec); subsequent runs cached
# Try again

# If still slow, rebuild with indexes
python data/drugs/build_tier1.py --manifest data/drugs/tier1_manifest.json
```

---

### "Strange rankings" or unexpected candidates

**This is expected!** The system scores based on:
1. Mechanistic paths (Drug → Protein → Disease)
2. Quantitative evidence (IC50, mutation freq)
3. Structural similarity
4. Logical consistency

**It does NOT consider**:
- Clinical trial status (ClinicalTrials.gov)
- Regulatory approval timeline
- Manufacturing feasibility
- Patient stratification (genetics, demographics)

**Action**: Check mechanistic justification:
```bash
python validation/trace_prediction.py Melanoma CandidateDrug
```

---

## Benchmark Issues

### "AUROC not 0.965" or metrics diverge

**Cause**: Different view/protocol; stale database; code changes

**Fix**:
```bash
# Use canonical harness with exact flags
python validation/repurposing_benchmark.py \
  --view full_typed \
  --protocol remove_direct_labels

# Expected: AUROC 0.965 ± 0.020
```

**Check**:
- Correct view: `full_typed` (not `legacy`)
- Correct protocol: `remove_direct_labels` (not `as_loaded`)
- Fresh database: `python data/drugs/build_tier1.py ...`

---

### "Baseline comparison fails" or baseline scores are weird

**Cause**: Baseline implementation uses different path finding

**Fix**: Baselines are separate implementations; minor divergence expected.

---

## Common Questions

### Q: Can I use this for my disease (not oncology)?

**A**: Use at your own risk. System is trained on oncology (20 diseases, 78 drugs). Applicability to other domains untested.

**Recommendation**:
1. Test on known drug-disease pairs in your domain
2. Check if mechanistic paths make sense (use `trace_prediction.py`)
3. Validate externally (literature, clinical trials)

---

### Q: Why is [my drug] ranked low?

**A**: Check:
1. **Is it in the database?**
   ```bash
   python -c "
   from data.store import KomposOSStore
   store = KomposOSStore('data/drugs/tier1.db')
   print(store.get_object('YourDrug'))
   "
   ```

2. **Does it have targets?**
   ```bash
   python validation/triage.py --drug YourDrug
   ```

3. **Are those targets connected to the disease?**
   ```bash
   python validation/trace_prediction.py YourDisease YourDrug
   ```

If no targets or no paths, add them to the database.

---

### Q: Can I export candidates as CSV?

**A**: Use JSON output and convert:
```bash
python validation/triage.py Melanoma --json > candidates.json

# Convert JSON to CSV
python -c "
import json, csv
with open('candidates.json') as f:
    data = json.load(f)
with open('candidates.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['drug', 'score', 'status'])
    writer.writeheader()
    for item in data['candidates']:
        writer.writerow({'drug': item['name'], 'score': item['score'], 'status': item['status']})
"
```

---

### Q: How often is the database updated?

**A**: Currently static (2026-05-26 snapshot). Updates require:
1. Modify manifest
2. Rebuild: `python data/drugs/build_tier1.py ...`
3. Benchmark to verify AUROC

**Frequency**: No automatic updates (user-driven).

---

### Q: Why AUROC 0.965? Is it overfit?

**A**: No, not overfit. Evidence:
- **LOOCV AUROC**: 0.945 (leave-one-out cross-validation, gold standard)
- **External (Hetionet)**: 0.744 (different database)
- **Temporal (post-2013)**: 0.959 (true future data)
- **Disease-level holdout**: 0.877 (per-disease average)

0.965 is on self-validation with label removal; 0.945 is LOOCV (more honest).

---

### Q: Can I reproduce AUROC 0.965 exactly?

**A**: Yes, if you:
1. Use exact same database (tier1.db)
2. Use exact same protocol (remove_direct_labels)
3. Use exact same view (full_typed)
4. Same random seed (if applicable)

Small variations (±0.01) are expected due to:
- Bootstrap resampling
- Random negative sampling
- Python version differences

---

### Q: What about female/male or racial stratification?

**A**: Database doesn't include patient demographics. Would require:
1. Clinical trial data with patient breakdowns
2. Patient subtype classification
3. New morphisms: Patient_subtype → Treatment_response

Current system is disease-agnostic (not patient-specific).

---

### Q: How do I add my own data?

**A**: See [DATA_AND_DATABASE.md](DATA_AND_DATABASE.md) and [DATA_EXPANSION_GUIDE.md](../DATA_EXPANSION_GUIDE.md).

Steps:
1. Create importer: `data/drugs/importers/my_source.py`
2. Update manifest: `tier1_manifest.json`
3. Modify build script: `data/drugs/build_tier1.py`
4. Rebuild: `python data/drugs/build_tier1.py --manifest tier1_manifest.json`
5. Validate: `python validation/audit_provenance.py`
6. Benchmark: `python validation/repurposing_benchmark.py ...`

---

### Q: What's the computational cost?

**A**:
- **First run** (path finding): 2–5 seconds (all diseases)
- **Subsequent runs**: < 1 second (cached paths)
- **Memory**: ~500 MB (full graph in memory)
- **Disk**: 3.67 MB (tier1.db)

---

### Q: Why is direct label removed during validation?

**A**: To prevent label leakage (cheating).

**Example leakage**: If we keep Drug→Disease label during scoring, composition will include that direct edge, and we're just looking up "is Sorafenib approved for Melanoma?" (trivial).

**Fair evaluation**: Remove Drug→Disease edges, force the system to find approval through mechanistic paths. This tests real prediction power.

---

### Q: Can I embed this as a service?

**A**: Partial. Currently:
- ✓ Core APIs stable (Category, scoring)
- ✓ CLI stable (triage.py)
- ✗ Web service not implemented (no Flask/FastAPI wrapper)

**To wrap as service**:
```python
from flask import Flask, request, jsonify
from validation.triage import run_triage

app = Flask(__name__)

@app.route('/triage', methods=['GET'])
def triage_api():
    disease = request.args.get('disease')
    top = request.args.get('top', 10, type=int)
    results = run_triage(disease, top=top, output_format='json')
    return jsonify(results)
```

---

### Q: What about Streamlit app?

**A**: `app.py` provides a basic Streamlit interface:

```bash
streamlit run app.py
```

Opens at http://localhost:8501

---

## Debugging

### Enable logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from core.category import Category
cat = Category('test')  # Shows debug info
```

### Run unit tests

```bash
pytest tests/test_repurposing_benchmark.py -v
pytest tests/test_oracle_strategies.py -v
pytest tests/ -v  # All tests
```

### Trace a specific pair

```bash
python validation/trace_prediction.py Melanoma Sorafenib --verbose
```

---

## Getting Help

### Check docs first

1. [TRACK_A_DRUG_REPURPOSING.md](TRACK_A_DRUG_REPURPOSING.md) — How it works
2. [GETTING_STARTED.md](GETTING_STARTED.md) — First-time setup
3. [VALIDATION_AND_BENCHMARKS.md](VALIDATION_AND_BENCHMARKS.md) — Metrics
4. [EVIDENCE_AND_PROVENANCE.md](EVIDENCE_AND_PROVENANCE.md) — Data sources
5. This file (you're reading it!)

### GitHub Issues

File an issue at https://github.com/your-repo/KOMPOSOS-IV-PHARM/issues

Include:
- Clear title: "[BUG] Triage fails on Melanoma"
- Reproducible example
- Environment (Python version, OS)
- Expected vs. actual output

### Code Review

Open a pull request at https://github.com/your-repo/KOMPOSOS-IV-PHARM/pulls

---

## Performance Tips

### For users (practitioners)

1. **Cache results**: First run caches paths, second run is faster
2. **Batch queries**: Triage a disease once, export results, don't re-run repeatedly
3. **Use JSON output**: Easier to parse and process than terminal

### For developers

1. **Profile before optimizing**: Use `cProfile`
2. **Index databases**: Add `CREATE INDEX` for common queries
3. **Parallelize**: Use `multiprocessing.Pool` for scoring all drugs
4. **Memoize**: Cache expensive function results (`@lru_cache`)

---

## Known Limitations

### Data

- **Oncology-only**: 20 diseases, 78 drugs (not generalizable to other domains)
- **Stale references**: Newest PMID from ~2015 (needs annual refresh)
- **Limited quantitative data**: Only 204/5382 edges have IC50 (3.8%)

### Methods

- **Heuristic binding**: Lipinski/Boltz2 (not crystal structure docking)
- **No off-target**: Doesn't predict side effects
- **No ADMET**: Doesn't predict pharmacokinetics
- **No patient context**: Doesn't account for tumor genetics or immune status

---

*Last updated: 2026-05-26*
