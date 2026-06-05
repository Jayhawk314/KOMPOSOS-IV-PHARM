# KOMPOSOS-IV-PHARM — YouTube teaching assets

Factual teaching slides + script for the drug-repurposing system.

## Files
| File | What it's for |
|---|---|
| `how_it_works_deck.html` | The main deck: what it is → core idea → strict results → honesty → scope → run it. |
| `SCRIPT.md` | Talking points for the videos (not a teleprompter). |

**Driving a deck:** open the `.html` in a browser → press `F` (fullscreen) → record
with OBS → arrow keys advance, bullets reveal one click at a time → talk over it.

**Math deck reuse:** the categorical math is the *same kernel* as the chemistry
project. Reuse `KOMPOSOS-IV-CHEM/YOUTUBE/math_visuals.html` and just relabel the
objects as drugs/proteins/diseases — no need to rebuild it here.

## Honesty rules (don't break)
- Always state the **view + protocol** with any AUROC. The current strict number is
  **`full_typed / remove_direct_labels` = 0.949**.
- **Do NOT** advertise the retired **0.969** AUROC — it had label leakage.
- It's a **research prototype, not clinical validation.** Candidates are leads, not recommendations.
- Provenance is tiered (594 verified / 215 co-occurrence): **presence ≠ verification.**
- **Track A (repurposing)** is the validated track. **Track B (drug design)** is a goal,
  not validated — never use Track A's AUROC to claim Track B.

## Reproduce the numbers
```
python validation/repurposing_benchmark.py --view full_typed --protocol remove_direct_labels --baselines --ci
```
