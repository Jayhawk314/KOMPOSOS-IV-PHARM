# Data & Database — Current Facts (2026-06-02)

Source: `data/drugs/tier1.db`. Reproducible build: `data/drugs/build_tier1.py`.
DB SHA256: `09F849850C0E97051F9F2D0A2247FF24CDCC9D25A93BC0453C3C0B89DC32F6D3`.

## Graph

| Item | Count |
|---|---|
| Stored objects | 464 (1,146 runtime after expansion) |
| Drugs | 78 |
| Diseases | 20 (oncology + Type2_Diabetes) |
| Biological entities | 366 |
| Morphisms (edges) | 2,329 |
| Relation types | 23 |
| FDA `treats` positives | 44 (all with mechanistic Drug→Protein→Disease paths) |

## Evidence tiers

| Tier | Count |
|---|---|
| MEASURED | 1,014 |
| ESTABLISHED | 377 |
| INFERRED | 918 |
| HYPOTHESIS | 20 |

> Caveat: MEASURED is a tier label. The numeric values (IC50, HR, mutation freq,
> response rate) currently live inside provenance/metadata strings; the structured
> `quantitative_value` column is **unpopulated**. Extracting values into the column
> is an open task.

## Provenance

| Item | Count |
|---|---|
| Edges with a source/provenance string | 2,329 / 2,329 (100%) |
| Edges carrying a PMID | 1,035 |
| Distinct PMIDs | 955 |
| RELATION-VERIFIED (agent-confirmed directed/signed) | 745 |
| LEXICAL-COOCCURRENCE (co-occurrence + polarity screen only) | 215 |

Source-string coverage is **not** the same as edge-level citation validation.
RELATION-VERIFIED means an agent read the cited sentence and confirmed the directed,
signed relation; LEXICAL-COOCCURRENCE passed only an automated screen.

## Recent additions (this snapshot)

151 agent-adjudicated `associated_with` protein→disease links were integrated
(97 from the first discovery pass, 54 from a disease-synonym rerun), each grounded
in a cited PMID and read in-session. Tagged `discovery-grounded; agent-adjudicated;
[RELATION-VERIFIED]`, tier INFERRED, confidence 0.60. These add mechanistic coverage
(repurposing rationale), not benchmark accuracy.

## Data sources

PubMed, ChEMBL, FDA, KEGG, STRING PPI, protein similarity (ESMC-300M), cBioPortal
genomic, ABPP experimental IC50.
