# Phase 1: PHARM Standing Predictor Loop

This phase makes the consolidated architecture executable on a real vertical
slice. It does not merge the engines. It wires them through `domain_core`.

## Flow

```text
domain_core.Candidate
  -> KompososPharmEvidenceProvider
  -> domain_core.EvidencePacket
  -> PronoiaPredictor
  -> domain_core.PredictionReport
```

## Files

- `domain_core/__init__.py`: shared contracts (`Candidate`, `EvidencePacket`,
  `PredictionReport`, provider/predictor protocols).
- `operadum/integrations/komposos_pharm_evidence.py`: read-only adapter over the
  external `KOMPOSOS-IV-PHARM` checkout.
- `operadum/integrations/pronoia_pharm_loop.py`: candidate slate -> ranked PRONOIA
  reports.
- `examples/pronoia/pharm_prediction_loop_demo.py`: live NSCLC demo.
- `tests/pronoia/test_komposos_pharm_evidence.py`: deterministic fake-category
  adapter tests.
- `tests/pronoia/test_pharm_prediction_loop.py`: deterministic loop tests.

## Run

```powershell
python -m examples.pronoia.pharm_prediction_loop_demo
python -m pytest tests/pronoia -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
```

## Current Behavior

The demo reads real KOMPOSOS-IV-PHARM graph evidence when the checkout exists at
`C:\Users\JAMES\github\KOMPOSOS-IV-PHARM`. It emits one `PredictionReport` per
candidate with PHARM score v2, raw MDL gain, grounding, abstain/pass status,
trace, and the evidence packet used for the decision.

The current live NSCLC demo ranks Osimertinib first, with Erlotinib and
Sotorasib also backed. Aspirin abstains because the evidence strength/grounding
gate is insufficient.

PHARM score v2 is the current primary PHARM ranker:

```text
score =
    strongest structured path/mechanism evidence
    - grounding penalty
    - contradiction penalty placeholder
```

Raw zlib-MDL gain remains in `PredictionReport.metrics` for transparency, but it
is not the primary PHARM score.

## Next Work

1. Use the benchmark harness in `operadum.validation.pronoia_pharm_benchmark`
   to track AUROC/AUPRC/Hits@K after every scoring change. See
   `docs/PHARM_BENCHMARK_EXPLORATION.md` for the first full run.
2. Integrate the sheaf contradiction signal as a bits penalty in the PRONOIA
   report.
3. Add a domain-aware structured evidence codebook so MDL measures graph support,
   not compressed text length.
4. Add a second domain using the same contracts, probably materials/MOF, before
   expanding `domain_core` further.
