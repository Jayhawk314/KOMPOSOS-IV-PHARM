# OPERADUM + PRONOIA Bundle

KOMPOSOS-IV-PHARM now carries a bundled copy of the OPERADUM/PRONOIA stack at:

```text
KOMPOSOS-IV-PHARM/vendor/operadum/
```

This makes the PHARM app self-contained for delivery and GitHub pushes. The
standalone sibling repo can still exist at:

```text
C:/Users/JAMES/github/operadum/
```

Use the standalone copy as the universal workbench/source when building adapters
for other KOMPOSOS domains. Use the bundled copy for this PHARM app so the UI,
reports, and audit stack travel together.

## Import Rule

`app.py` loads stacks in this order:

1. `KOMPOSOS-IV-PHARM/vendor/operadum` if it contains `pronoia/`
2. `../operadum` as the standalone sibling fallback
3. the older bundled OPERADUM-only folder if PRONOIA is not present

That means a pushed PHARM repo uses its own bundled stack first and does not
depend on a local sibling checkout.

## Layer Roles

```text
KOMPOSOS-IV-PHARM
  owns the graph, Streamlit UI, PHARM database, benchmark labels,
  provenance, PMIDs, and report download UX

OPERADUM
  owns candidate packaging and decision/prioritization reports

PRONOIA
  owns prediction audit reports: grounding, abstain/pass, PHARM v2 score,
  raw MDL transparency, and evidence trail formatting

domain_core
  owns shared contracts so the engines do not import each other's internals
```

No Orion dependency is required or intended.

## Sync Rule

When the standalone universal stack changes and you want PHARM to carry that
work, run from the KOMPOSOS-IV-PHARM repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync_operadum_bundle.ps1
```

The sync script backs up the current bundled folder, copies the standalone stack
into `KOMPOSOS-IV-PHARM/vendor/operadum`, and excludes caches/compiled files. It does
not delete extra files from the bundle.

## Verification

After sync, run:

```powershell
python -c "compile(open('app.py','rb').read(), 'app.py', 'exec'); print('compile ok')"
python -c "import sys; sys.path.insert(0, 'vendor/operadum'); import domain_core, operadum, pronoia; print('bundle imports ok')"
```

For the deeper PRONOIA/PHARM audit, run the bundled tests from inside
`KOMPOSOS-IV-PHARM/vendor/operadum`:

```powershell
python -m pytest vendor/operadum/tests tests -q -p no:cacheprovider
```
