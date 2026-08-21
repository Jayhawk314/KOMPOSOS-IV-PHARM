# Public release readiness — 2026-08-21

Written before offering this repository and its Streamlit app free to
researchers. Every count below was measured against the current tree, not
recalled.

**Verdict: two items need your decision, six were mechanical and are fixed in
the same commit as this document. Nothing found is a correctness problem with
the science.**

The most likely failure mode of a public release here is not "the code is
wrong." It is a stranger forming a bad first impression from an unmarked file or
an unattributed data source, and never reaching the work that is actually good.

---

## 1. Needs your decision — not mine to make

### 1a. COSMIC and KEGG redistribution in the shipped graph

`data/drugs/tier1.db` is committed to the repository and contains 2,462 edges.
Measured provenance:

| Source | Edges | Redistribution posture |
|---|---:|---|
| ChEMBL | 881 | CC BY-SA 3.0 — permissive, attribution required |
| PubMed / PMID-derived | 433 | Identifiers and facts, not article text |
| ESMC (computed here) | 422 | Ours; excluded from scoring anyway |
| curated cancer-protein lists | 393 | Ours |
| **KEGG** | **72** | **Restrictive.** Bulk redistribution is licensed; academic web use is free |
| literature (unverified) | 64 | Ours |
| FDA labels | 61 | U.S. Government work, public domain |
| PPI (unattributed) | 22 | Source not recorded on the edge — see 2a |
| **COSMIC Cancer Gene Census** | **18** | **Restrictive.** Free for academic use; commercial and redistribution terms apply |
| ABPP | 15 | Ours |
| DepMap | 9 | CC BY 4.0 — permissive |
| WHO Classification | 3 | Publication-derived facts |

**Why the 18 COSMIC edges matter more than their count suggests.** All 18 are
`driver_of` relations — they are **18 of the 60 directed terminal
Protein→Disease edges, 30% of the hop that every candidate in this system
descends from.** Removing them is not cosmetic; it would materially change the
graph and every number computed on it.

The honest reading is that 90 edges out of 2,462 (3.7%) are thin, attributed,
factual extractions — "gene X is a Tier 1 driver of disease Y", "protein A
phosphorylates protein B in pathway hsa04014" — rather than a redistribution of
either database. Facts are not copyrightable in the US; the EU sui generis
database right is a separate question and KEGG in particular is known to
enforce its terms.

**I am not qualified to clear this and neither is a confident-sounding
paragraph.** Your options, roughly in order of cost:

1. **Attribute and ship.** Extend `NOTICE` with the inventory above (done in
   this commit) and state the extraction is factual and attributed. Lowest cost,
   non-zero residual risk, and the most common practice in the field.
2. **Ask.** Email COSMIC (Sanger) and KEGG (Kanehisa Labs) describing exactly
   what is extracted. A written yes removes the question permanently. Slow but
   definitive, and academic requests of this size are routinely granted.
3. **Ship the code without the database.** Provide a rebuild script and let each
   user fetch from source under their own terms. Safest legally, but it breaks
   the thing that makes this repo pleasant — that it runs immediately from a
   clone — and it would make the benchmark unreproducible for anyone who does
   not complete the fetch.

**Recommendation: option 1 now, option 2 in parallel.** Ship with accurate
attribution and write the two emails the same week. Do not choose option 3
unless one of them objects — losing one-clone reproducibility costs more than
the risk it removes.

### 1b. Eleven unpushed commits

`master` is 11 commits ahead of `origin/master`. None of the PRISM adjudication,
the geometry fix, or these release changes are visible to anyone yet. Nothing to
decide except when.

---

## 2. Fixed in this commit

### 2a. `CLAUDE.md` listed a data source the graph does not contain

`CLAUDE.md` named **STRING** among the graph's sources. Measured: **0 edges**
reference STRING in `provenance`, and 0 in `metadata`. The 22 edges labelled
`PPI` record no source at all. CosMx is 2 edges, not a layer.

An orientation file that overstates its own inputs is exactly the kind of thing
a careful reader checks first. Corrected to the measured inventory, with the 22
unattributed `PPI` edges named as an open provenance gap rather than quietly
folded into a source that is not there.

### 2b. NCBI E-utilities calls identified no client

`validation/nonobvious.py` and `validation/audit_terminal_pmids.py` call
E-utilities with no `tool`, no `email`, and no `api_key`. NCBI asks for the
first two and rate-limits anonymous clients to 3 requests/second, with the
documented remedy for abuse being an IP block.

For a repository run by a handful of people this is untidy. **For a live public
Streamlit deployment it is a real operational risk**: every user's searches
arrive from one server IP, and getting that IP blocked takes down the feature
for everyone. Now sends `tool` and `email`, and uses `NCBI_API_KEY` from the
environment when present (raising the ceiling to 10 req/s). No key is committed.

### 2c. The "not clinical" disclaimer was reachable but not prominent

The strongest statement lived at `app.py:2917`, inside a tab a first-time
visitor may never open. Given this is a public, live app about cancer drugs,
that is the wrong placement. A persistent caption now renders under the title on
every mode, not once in one tab.

Verified separately: the **no dosing language** hard rule holds. The sweep's
apparent hits were `BID` the apoptosis gene and `broad_id` variables, not
dosing.

### 2d. README understated what the project now has

Evidence-layer counts were stale (141 outcomes; actually 160) and there was no
mention of the PRISM adjudication or the trial recovery. More importantly the
README led with the ranker, which is the least defensible thing here.

Restructured to lead with what a researcher would actually want — **four
measured negative controls and a pre-registered external adjudication** — and
corrected the counts. The AUROC section is unchanged; it was already careful.

### 2e. No machine-readable citation

Added `CITATION.cff`. Researchers cite what is easy to cite, and GitHub renders
this as a "Cite this repository" button.

### 2f. 145 markdown files with no stated status

`docs/` holds 73 and `truedocs/` 19, much of it aged and contradicting current
numbers. `CLAUDE.md` tells *you* to trust the code and `HONEST_VALUE.md`; a
stranger has no such instruction and will quote a stale number in good faith.

Rewrote `docs/README.md` to mark which documents are current, which are
historical records that should not be quoted for numbers, and which are
superseded.

**The old version of that file was itself the problem, and pointed the wrong
way.** It carried a 2026-05-27 notice declaring `docs/` a historical archive and
naming `truedocs/` as the current source of truth. That has since reversed:
`docs/` now holds the newest plans and results while `truedocs/` has not been
touched since. The old notice also quoted AUROC 0.974694, AUPRC 0.551698, a
Hetionet external AUROC of 0.634479, and a 5,382-morphism graph — all retired,
against a graph that now has 2,462 edges. Anyone following that pointer in good
faith would have landed in aged material and quoted a dead number. The reversal
is recorded at the top of the new file rather than silently dropped.

---

## 3. Checked and found genuinely fine

Worth recording, because I expected some of these to be problems.

- **The quarantined modules are already marked, and well.** I expected this to
  be the top finding and asserted it as one before looking, which was wrong.
  All five carry a loud module-level `QUARANTINED 2026-07-31 — NON-PRODUCT,
  EXCLUDED FROM VALIDATION` header naming the specific defect: the fabricated
  distance matrix behind `mutation_impact.py`'s kcal/mol, the circular-by-
  construction synthetic generator, the hardcoded placeholder metrics, the
  structurally-zero Dempster conflict, and the hand-set coefficients. A stranger
  browsing the tree cannot miss them. Nothing to do.
  (The files are also clean UTF-8 with real em-dashes — the mojibake I thought I
  saw was a PowerShell console rendering artifact, not file corruption. Worth
  recording so nobody later "repairs" encoding that is already correct.)
- **`LICENSE` and `NOTICE` both exist.** The NOTICE is unusually thoughtful
  about DrugBank's non-commercial terms. Its only defect is scope — see 1a.
- **A clean clone works.** Verified this session: `git clone` → `python -m
  evidence.build` → `pytest` gives 249 passed, 1 skipped, with no manual steps
  and no network. That was *not* true a week ago.
- **The benchmark reproduces bit-identically.** AUROC 0.976306, AUPRC 0.592023,
  margin +0.2280 over common-neighbour.
- **The scored path is clean.** Nothing in `oracle/`, `core/`, `validation/`,
  `data/` or `komposos_kg/` imports the evidence layer or PRISM, and a test
  enforces it.
- **No dosing language anywhere.** See 2c.
- **The README already named cohort and protocol with every AUROC**, already
  pointed at `HONEST_VALUE.md` first, and already called the project a research
  prototype. My initial assessment that it needed rewriting was wrong.

---

## 4. What to actually offer, and to whom

This matters more than any item above, because it determines whether the release
lands at all.

**Do not offer this as a drug repurposing engine.** Anyone who evaluates it as
one will find the 60-candidate audit — 1 lead, 12 structurally invalid, 16
already clinically tested, 17 with nothing findable — and the PRISM null, and
leave. Those results are honest and they are not a product.

**Offer it as a methods artifact.** The contribution is a repurposing system
that measured itself four times and reported four negatives:

1. **ESMC ablation** — an embedding layer that made the model *worse*
   (0.9691 → 0.9784 on removal).
2. **Grounding permutation control** — post-hoc PubMed citation measures corpus
   density, not biology; real 12.5% vs scrambled 7.5%, Fisher p=0.28.
3. **Horn composition** — categorical machinery adding nothing over ordinary
   pairwise comparison.
4. **PRISM pre-registered adjudication** — frozen and committed before the
   scoring code existed; zero lineage-selective hits, zero of 60 standings
   changed.

Plus the **trial-graveyard finding**: 75% of tracked trials never posted
results, every recorded stop reason was operational or financial rather than
efficacy or safety, and 13 trials have posted results with no publication of any
kind — invisible to any literature search. That one matters well beyond this
project, because it means a novelty signal built on literature absence cannot
distinguish "unexplored" from "quietly abandoned."

**Who wants this**

- **Meta-research and research-integrity groups** — the trial recovery sits
  directly in the AllTrials / RIAT / Cochrane literature and has receipts.
- **People building knowledge-graph or ML repurposing systems** — as a
  validation template. The pre-registration-before-scoring pattern and the
  written disease correspondence, which forces every identification to be stated
  and reviewable rather than joined on a string, solve problems many people have
  and quietly get wrong.
- **Anyone teaching how computational biology claims fail.** The 60-candidate
  audit is an unusually good teaching artifact.

The Streamlit app's audience is narrower but real: it demonstrates a glass-box UI
that abstains, shows receipts and evidence tiers, and renders "not found" as
unresolved rather than as a pass. Interesting to decision-support builders; less
so to bench biologists.

**A paper should lead.** A repository alone gets starred and forgotten; a
repository attached to "here are four negative controls that killed our own
methods" gets cited. Phase 3 of the GRAND_PLAN is most of the way written
already.

Suggested one-line framing:

> A glass-box drug-repurposing triage tool that knows its limits — shipped with
> the four negative controls that define them.

---

## 5. Remaining before you send the first email

- [ ] Decide 1a (attribute / ask / unbundle). Recommendation: attribute now, ask in parallel.
- [ ] Push the 11 commits.
- [ ] Set `NCBI_API_KEY` and a contact email in the live deployment's environment.
- [ ] Re-read the new README top section once as a stranger would.
