# HANDOFF — AlphaFold Structural Coherence and Conformational-State Atlas

Written 2026-08-12 for the next Claude/Codex session. Read this before changing
the structural work. Executable code and dated result files are the source of
truth.

## 0. The honest goal

The AlphaFold experiment has **not** produced a novel biological finding or a
confirmed AlphaFold error. It has produced a functioning, receipt-carrying
auditor that detects relative domain-pose differences and distinguishes them
from AlphaFold uncertainty and experimental conformational variation.

The scientifically worthwhile next question is:

> Can recurring domain movements across related proteins be organized into
> reproducible conformational states, and are those states associated with
> ligands, drugs, mutations, binding partners, activation or resistance?

Do not turn geometric inconsistency alone into a biological claim. Category
theory may organize state transitions and contextual relationships; statistics
and biological metadata must establish significance.

This work is separate from the oncology drug-repurposing candidate graph. Do
not let it modify drug candidate scores unless an independently validated
structural result later justifies that integration.

## 1. Repository state

- Repository: `C:\Users\JAMES\github-clean\komposos-iv-pharm`
- Branch: `master`
- HEAD at handoff: `c37d204`
- The structural implementation and result are currently **uncommitted**.
- Full test suite: `212 passed, 1 skipped` on 2026-08-12.

Important: the working tree also contains `README.md` changes and
`docs/LOCAL_COMPLETION_AND_EXTERNAL_VALIDATION.md`. Treat all existing changes
as user work. Inspect the diff before committing and do not discard or overwrite
anything.

Verify first:

```powershell
python -m pytest tests\ -q
python validation\build_alphafold_coherence_cohort.py --max-experimental 3
```

The second command is cached and resumable. The final run completed 34 proteins
in about 35 seconds with the cache present.

## 2. What was implemented

### Structural kernel

`geometry/alphafold_coherence.py`

- Loads PDB/mmCIF coordinates and AlphaFold PAE.
- Maps partial experimental constructs onto the reference sequence.
- Fits domain-specific rigid transforms with Kabsch alignment.
- Measures relative domain-pose disagreement:
  - arrangement RMSD;
  - independently fitted mobile-domain RMSD;
  - excess arrangement RMSD;
  - rotation disagreement;
  - centroid displacement.
- Composes SE(3) maps around A-to-B-to-C triangles as the concrete horn test.
- Preserves `CONSISTENT`, `INCONSISTENT` and `QUARANTINE` rather than converting
  missing or uncertain evidence into a weak score.

### Oracle specialization

`oracle/structural_coherence.py`

- Family-level structural Oracle, intentionally separate from the oncology
  `CategoricalOracle.predict(source, target)` interface.
- Enumerates pairwise domain arrangements and compositional triangles.
- Ranks conflicts, retains quarantined checks and attaches coordinate receipts.

Runner: `scripts/run_structural_coherence_oracle.py`.

### Public-data cohort builder

`validation/build_alphafold_coherence_cohort.py`

The builder acquires and caches:

- AlphaFold DB model and PAE;
- InterPro domain annotations;
- PDBe experimental mappings;
- RCSB mmCIF coordinates;
- SIFTS observed-residue segments.

It records URLs, timestamps and SHA-256 checksums. Large downloaded data live
under `data/external/alphafold_coherence_2026-08-12/` and are ignored by Git.
The dated summaries and interpretation live under
`reports/alphafold_coherence_2026-08-12/`.

Documentation:

- `docs/ALPHAFOLD_COHERENCE_AUDITOR.md`
- `docs/STRUCTURAL_COHERENCE_ORACLE.md`
- `reports/alphafold_coherence_2026-08-12/README.md`

Tests:

- `tests/test_alphafold_coherence.py`
- `tests/test_structural_oracle.py`
- `tests/test_build_alphafold_coherence_cohort.py`

## 3. The completed 34-protein feasibility result

The accession set came from the older KOMPOSOS structural workspace and is
cancer-related, not a calibrated AlphaFold benchmark.

| Outcome | Count |
|---|---:|
| No AlphaFold conflict | 12 |
| AlphaFold quarantine because cross-domain PAE was too high | 5 |
| AlphaFold and experimental structures conflict, but experiments also conflict | 3 |
| Experimental conformational variation without AlphaFold conflict | 1 |
| Structurally ineligible | 13 |
| Processing errors | 0 |

Twenty-one of 34 proteins were geometrically analyzable. There was **no
AlphaFold-specific contradiction**.

Three of the four anomalous cases reveal a repeatable shape: the mobile domain
remains internally similar (internal RMSD below 1 A) while its relative
rigid-body orientation changes. **EGFR is not one of them** — see the table.

| Protein | Observed pattern | Current interpretation |
|---|---|---|
| EGFR (`P00533`) | `1MOX` differs by about 3.5–4.2 A centroid displacement and 11.6–14.5 degrees from AlphaFold and two other experiments, but the mobile domain's own internal RMSD is 3.4–3.9 A — as large as the displacement | **Not a clean rigid-body pose difference**: the furin-like domain itself differs in `1MOX`, so construct/mapping and local deformation are live explanations before conformational state |
| MET (`P08581`) | `4K3J` differs by about 6–9 A and 58–73 degrees; mobile-domain internal RMSD remains about 0.7 A | Strong rigid-body domain-state difference; not AlphaFold-specific |
| RAD51 (`Q06609`) | `9SVY` differs by about 40 A and 168 degrees while internal RMSD remains below 1 A | Near-flipped experimental pose or context/mapping issue; not AlphaFold-specific |
| VEGFR2 (`P35968`) | Experimental structures differ by about 4–7 A; AlphaFold does not exceed thresholds | Experimental conformational variation |

For EGFR, MET and RAD51 the recurring topology is approximately:

```text
AlphaFold + two experimental structures agree
                    |
       one experimental structure differs
```

This is biologically interesting but not yet biologically significant. The
differences have not been connected to activation, ligand binding, drug state,
mutation, complex formation or disease outcome.

**Where these numbers live.** The committed report files (`SUMMARY.csv`,
`COHORT.json`) carry only per-accession counts, standings and classifications.
Every per-pair geometric figure quoted above — centroid displacement, rotation
disagreement, excess arrangement RMSD, mobile-domain internal RMSD — comes from
`data/external/alphafold_coherence_2026-08-12/<accession>/oracle_report.json`,
which is inside the ~205 MB gitignored cache. If the cache is cleared, these
figures are not checkable from the repository until the builder re-runs.

## 4. Errors found and repaired

Two real pipeline errors were exposed by the cohort:

1. PDBe construct/SEQRES coverage was initially treated as observed structural
   coverage. The final builder uses SIFTS observed-residue segments, so a domain
   must actually have coordinates.
2. Global alignment traceback could select an equally scoring wrong placement
   around long construct deletions. The final mapper first anchors exact
   same-protein sequence blocks and retains the global fallback for divergent
   homologs.

Tests cover both cases. Do not remove the observed-residue filter or replace the
mapping with a naive sequence-span check.

## 5. What category theory did and did not add

The structural category is concrete:

- objects: structures or conformational states;
- morphisms: fitted SE(3) domain transforms;
- composition: multiplication of fitted transforms;
- horn defect: disagreement between a composed path and a directly measured
  transform.

However, every anomaly in this cohort was already found by ordinary pairwise
domain-arrangement comparison. There were no horn-only inconsistent findings.
Therefore horn composition has **not demonstrated incremental biological or
detection value** here.

Do not claim category theory discovered the conformational differences. Its
possible future value is a shared language for contextual state transitions and
cross-protein mappings, which must be tested against simpler baselines.

## 6. Formal model for the next phase

### Per-protein conformation category

For one protein or homologous family:

- objects: empirically supported conformational-state clusters;
- observations: individual PDB chains and AlphaFold models;
- morphisms: normalized domain-pose transformations between states;
- context labels: ligand, drug, mutation, binding partner, oligomeric state,
  experimental method and biochemical state;
- composition: candidate transition paths between conformational states.

Do not assume every pairwise comparison is a biological transition. A morphism
initially means a measured geometric relationship; transition semantics require
external evidence.

### Shared conformational-signature space

Raw coordinates cannot be compared across unrelated proteins. Map each
observation to invariant or normalized features:

- rotation angle and axis relative to a defined anchor domain;
- translation normalized by domain radius or inter-domain distance;
- inferred hinge location;
- mobile-domain internal RMSD;
- interface/contact change;
- PAE and pLDDT;
- sequence/domain-family identity.

A functor from each protein-specific category into a shared signature category
is a testable way to compare analogous movements across homologs. It is useful
only if those mapped signatures predict biological context better than ordinary
feature clustering.

### Contextual hypergraph

Do not reduce a structural observation to a binary edge. The natural evidence
record is n-ary:

```text
(protein, structure, pose state, domain pair, ligand/drug, mutation,
 binding partner, assay/condition, publication)
```

Implement this with `Claim`, `Study`, `Intervention`, `Outcome` and structural
observation records in SQLite, then expose it as a hypergraph. Vectors may help
retrieve literature but must not silently change a claim's standing without a
receipt and review.

## 7. Next executable experiment

Do not scale immediately to all of AlphaFold DB. Start with one coherent,
data-rich homologous family, preferably receptor tyrosine kinases.

### Phase A — freeze the question and cohort

1. Choose a comparable domain pair or interface across the family.
2. Collect roughly 100–300 experimental structures.
3. Record ligand/drug, apo/bound status, mutation, partner, chain, construct,
   oligomeric context, method and PMID/DOI receipts.
4. Separately curate a small literature-backed set of known AlphaFold
   domain-orientation/interface errors and known alternative conformations.
5. Freeze inclusion rules before examining associations.

### Phase B — construct the state atlas

Suggested new files:

- `geometry/conformational_states.py`: normalized SE(3) features and clustering;
- `validation/build_conformational_state_atlas.py`: metadata/data acquisition;
- `validation/evaluate_conformational_states.py`: blinded tests and baselines;
- `reports/conformational_state_atlas_<date>/`: frozen cohort and receipts.

Cluster transformations within homologous domain pairs using ordinary methods
first: SE(3)-aware distance, mixture models or hierarchical clustering. Test
cluster stability under structure resampling and alternative thresholds.

### Phase C — ask biological questions

Test, with held-out structures and permutation controls:

1. Are pose clusters reproducible rather than continuous crystallographic
   scatter?
2. Are clusters associated with apo/ligand/drug state?
3. Are activating or resistance mutations enriched in particular states or
   transition/interface residues?
4. Does PAE track experimentally observed state diversity?
5. Can context predict the state of an unseen structure?
6. Do categorical composition or hypergraph context improve held-out prediction
   beyond pairwise RMSD, PAE, sequence identity and the same numeric features?

Correct for repeated PDB structures from the same publication/construct and for
protein identity. Do not treat thousands of near-duplicate structures as
independent biological evidence.

## 8. Go/no-go criterion

Continue scaling only if at least one of these survives held-out testing:

- a reproducible state association with ligand, mutation, activation or
  resistance;
- detection of known AlphaFold errors beyond PAE and ordinary alignment;
- incremental predictive value from categorical composition or hypergraph
  context beyond the same non-categorical features.

If the analysis only redescribes pairwise RMSD clusters, keep the useful
structural auditor but stop claiming a special KOMPOSOS/category-theory result.

## 9. Hard interpretation rules

- `INCONSISTENT` is a review target, not proof that AlphaFold is wrong.
- High PAE means quarantine, not failure and not a weak pass.
- Experimental disagreement must be checked before assigning an AlphaFold
  conflict.
- Alternative conformations, construct differences, crystal contacts,
  oligomeric context and sequence mapping are competing explanations.
- Compare homologous domains or normalized invariants; never cluster raw RMSD
  across unrelated domain pairs.
- Preserve accession, PDB chain, source URL, checksum and publication receipt
  for every observation.
- Report null results. The current result is a valid null feasibility result.
- Do not claim biological significance until geometry is associated with a
  biological context or outcome under a controlled analysis.

## 10. Immediate handoff action

First inspect and commit the existing structural work as a coherent unit if the
user authorizes it. Then begin only Phase A: define the receptor-kinase question,
schema and frozen inclusion rules. Do not spend the next session downloading a
large unfocused cohort before those decisions are written.
