# Pocket Recovery Benchmark — Summary (Validation Ladder Level 2-3)

Updated: 2026-05-29
Harness: `scripts/benchmark_pocket_recovery.py`
Manifest: `data/benchmarks/cocrystal_small.json` (10 co-crystals)
Raw report: `reports/pocket_recovery_benchmark.json`
Radius: 10 Angstrom. Contact distance: 4.0 Angstrom.

## Question

Does the engine's grid pocket detector find the real ligand-binding pocket, on
structures where the bound cognate drug defines the ground truth?

## Result: the rewritten detector passes the gate

After replacing the pocket selector with a **largest-connected-cavity** method
(see "The fix" below), the grid detector now beats the protein-centroid baseline.

| Mode | Median centroid error (A) | Within 4A | Within 6A | Mean contact recall | Mean contact precision |
|------|--------------------------:|----------:|----------:|--------------------:|-----------------------:|
| grid (current) | **5.6** | **40%** | **50%** | **0.697** | 0.276 |
| centroid (baseline) | 11.9 | 0% | 0% | 0.428 | 0.128 |
| ligand (oracle ceiling) | 0.0 | 100% | 100% | 0.986 | 0.376 |

Grid vs centroid: **+6.3 A** median error reduction, **+0.27** contact recall.

(Cofactors such as HEM/FAD/NAD(P) are blocklisted so the cognate ligand is the
drug, not a cofactor. 1CX2 ground truth is now the inhibitor S58, not heme.)

## Generalization: held-out set (frozen thresholds)

The thresholds above were tuned on the 10 training co-crystals. To test whether
they generalize, the same frozen detector was run on a **held-out set of 10 new
co-crystals across 9 new target families** (`data/benchmarks/cocrystal_holdout.json`,
report `reports/pocket_recovery_holdout.json`): ABL1, PDE5, HSP90, ERa, GR, HIV-1
protease, carbonic anhydrase II, DHFR, PPARg, AChE.

| Mode | Median error (A) | Within 4A | Within 6A | Mean contact recall |
|------|-----------------:|----------:|----------:|--------------------:|
| grid | **5.4** | **40%** | **50%** | **0.81** |
| centroid | 12.2 | 0% | 10% | 0.48 |

Grid beats centroid by **6.9 A** median and **+0.33** recall, and wins on **10/10**
held-out structures (recall is even higher than on the training set). The detector
generalizes to targets and families it was not tuned on. Sub-2 A on AChE (0.7),
HSP90 (1.5), HIV protease (1.5); weakest on PPARg (12.9) and GR (12.5), both large
multi-lobed nuclear-receptor pockets.

Held-out per-structure (grid / centroid centroid error, A):
1IEP 8.6/30.9 | 1UDT 4.1/14.7 | 1YET 1.5/8.6 | 3ERT 8.6/12.1 | 1M2Z 12.5/18.9 |
1HXW 1.5/5.9 | 1AZM 2.0/6.6 | 4DFR 6.6/10.1 | 2PRG 12.9/20.4 | 1EVE 0.7/12.3

For reference, the previous detector (single-max-buriedness, since replaced)
scored 22.2 A median / 0% within 6 A / 0.151 recall — worse than centroid.

## Per-structure centroid error (Angstrom)

| PDB | Target | cognate | grid | centroid | grid recall | grid better? |
|-----|--------|---------|-----:|---------:|------------:|:------------:|
| 1M17 | EGFR  | AQ4 |  2.3 | 11.8 | 1.00 | yes |
| 1XKK | EGFR  | FMM |  0.7 |  9.1 | 0.96 | yes |
| 3OG7 | BRAF  | 032 | 28.2 | 13.7 | 0.00 | **no** |
| 2XP2 | ALK   | VGH |  7.0 | 11.9 | 0.80 | yes |
| 2WGJ | MET   | VGH |  2.6 | 11.0 | 1.00 | yes |
| 5L2I | CDK6  | LQQ | 13.6 | 13.4 | 0.45 | tie/no |
| 3KRR | JAK2  | DQX |  4.3 | 11.4 | 0.95 | yes |
| 1CX2 | PTGS2 | S58 | 24.3 | 29.3 | 0.06 | marginal |
| 6O0K | BCL2  | LBM |  8.1 | 11.9 | 0.81 | yes |
| 6OIM | KRAS  | MOV |  2.4 | 13.1 | 0.94 | yes |

Grid beats centroid on 7-8/10. Failures: 3OG7 (BRAF) — the largest cavity is not
the ATP site; 5L2I (CDK6) — a wash; 1CX2 (COX-2) — the inhibitor sits in a long
hydrophobic channel, not the largest enclosed cavity, so both methods miss.
Shallow/allosteric, channel-like, or multi-cavity targets remain the hard cases.

## The fix

Old (failing): "where is the single most buried void?" -> the fully-enclosed
protein core (buriedness ~1.0), ~22 A from the ligand.

New (passing): "where is the largest connected concave cavity?"
- candidate void points: min-atom-distance in [3.0, 5.5] A AND >=12 atoms within 9 A
- buriedness filter: keep ray-cast buriedness >= 0.78 (64 probe directions)
- cluster kept points (connected if within 3.2 A); return the largest cluster's centroid

The real ATP pocket has buriedness ~0.91 (concave but solvent-accessible), so it
loses a single-point max-buriedness contest to the core but wins on cavity volume.

## Honesty caveats

- The thresholds (buriedness >= 0.78, clearance 3.0-5.5 A, link 3.2 A) were tuned
  on these same 10 structures. The 22 -> 5.6 A improvement is far beyond tuning
  noise, but generalization to unseen targets is not yet demonstrated. A held-out
  co-crystal set is the next step before claiming general pocket-finding.
- This measures **geometry recovery only**. It does not measure binding,
  affinity, or ranking of actives vs decoys (Validation Ladder Level 4 — not
  yet built).
- For targets where the binding site is not the largest cavity (e.g. some
  allosteric/shallow sites, BRAF here), still supply the pocket via
  `--center`/`--residue`. This benchmark is the regression gate for any future
  detector change.
