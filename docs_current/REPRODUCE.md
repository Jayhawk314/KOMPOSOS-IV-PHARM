# Reproduce — Current Numbers (2026-06-02)

Every figure in `VALIDATION.md` and `DATA.md` comes from these commands on
`data/drugs/tier1.db`. PowerShell syntax.

## Primary strict benchmark (AUROC 0.970549, with CIs + baselines)

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --ci --baselines
```

## Holdouts

```powershell
python validation\repurposing_benchmark.py --view full_typed --protocol loocv   # LOOCV 0.967431
python validation\temporal_holdout.py                                           # temporal 0.970646
python validation\external_validation.py                                        # Hetionet 0.643615
python validation\disease_holdout.py --min-positives 2                          # disease mean 0.937795
```

## Database facts

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/drugs/tier1.db').cursor(); print('morphisms', c.execute('SELECT COUNT(*) FROM morphisms').fetchone()[0]); print('RELATION-VERIFIED', c.execute(\"SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%RELATION-VERIFIED%'\").fetchone()[0]); print('LEXICAL', c.execute(\"SELECT COUNT(*) FROM morphisms WHERE provenance LIKE '%LEXICAL-COOCCURRENCE%'\").fetchone()[0])"
```

## Candidate triage (with evidence chains + PMIDs)

```powershell
python validation\triage.py Melanoma
python validation\triage.py --drug Sorafenib
```

## Tests

```powershell
pytest tests\test_repurposing_benchmark.py -q
```

## Notes

- 44 positives = FDA `treats` indications only (the harness filters to `mor.name == "treats"`).
- `remove_direct_labels` is the headline protocol; `as_loaded` is a dataset artifact, not recommended.
- DB SHA256 `09F849850C0E97051F9F2D0A2247FF24CDCC9D25A93BC0453C3C0B89DC32F6D3` pins this snapshot.
