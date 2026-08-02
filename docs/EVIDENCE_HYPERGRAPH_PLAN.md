# Contextual evidence hypergraph plan

Status: phases 1-5 implemented 2026-08-01; vector evaluation and external
researcher workflow testing remain gated work.

## Researcher question

The evidence layer exists to answer one question the scored graph cannot:

> For this drug-cancer pair, what human evidence exists, in what context, what
> happened, and which source records were actually checked?

It does not create efficacy claims, change the repurposing score, or treat a
failed search as support.

## Architecture

Keep `data/drugs/tier1.db` as the scored binary graph. It is rebuilt from a
manifest and must remain independent of changing clinical evidence and human
review. Store contextual records in `data/evidence/evidence.db`, built
deterministically from versioned review artifacts.

The evidence database uses reified n-ary records rather than pretending that a
study is one binary edge:

```text
Study
|- INTERVENTION -> drug(s)
|- DISEASE -> disease/subtype
|- BIOMARKER -> molecular restriction
|- COMBINATION_PARTNER -> other intervention(s)
|- OUTCOME -> result signal
`- RECEIPT -> PMID/NCT/source record
```

External literal terms may be stored without adding them to the scored graph.

## Delivery phases

1. Add the evidence schema, store, models, and deterministic builder.
2. Import the 60 candidate reviews, trial inventory, terminal-PMID audit, and
   manual PMID relevance review.
3. Add pair and disease query APIs with regression fixtures for cimetidine-RCC,
   suramin-RCC, dacomitinib-GBM, amivantamab-GBM, category errors, biomarker
   context, and the unresolved KDR-GIST PMID.
4. Add a read-only contextual evidence section to Pair detail. Keep scoring
   unchanged.
5. Add SQLite FTS5 over source titles, study titles, and review notes.
6. Test optional document embeddings only if FTS leaves measurable retrieval
   gaps. Vectors may retrieve documents; they may never assert graph edges or
   alter standing automatically.
7. Run a researcher workflow test measuring time to a defensible answer,
   critical evidence missed, irrelevant records opened, and willingness to
   reuse the tool. Do not substitute AUROC for this usability test.

Implemented in the first vertical slice:

- separate deterministic SQLite build;
- lossless import of all 60 reviews;
- 77 registry studies and 3,237 typed study roles;
- reviewed pair/outcome/receipt query API;
- Pair-detail evidence rendering;
- FTS5 retrieval baseline;
- regression fixtures for the decisive positive, negative, active, contextual,
  category-error, and invalid-receipt cases.

## Stop/go gates

- **Import gate:** all 60 rows round-trip with no loss of evidence state,
  testing status, result signal, candidate assessment, negative-evidence note,
  or receipt review.
- **Truth gate:** missing evidence remains unresolved; active trials remain
  distinct from negative results; category and sign errors remain visible.
- **UI gate:** a reviewer can distinguish the decisive cases above and open the
  underlying records from Pair detail.
- **Retrieval gate:** vector retrieval ships only if it improves a frozen
  receipt-retrieval task over FTS5.
- **Usefulness gate:** expand the corpus only if external researchers complete
  evidence questions faster or with fewer errors than their normal workflow.

## Public deployment

The free application reads a bundled, rebuildable SQLite artifact. Public
review is read-only initially. If annotations are added later, the UI should
export an append-only review file rather than pretending ephemeral hosting has
durable multi-user storage.

## Explicit non-goals for the first release

- No Neo4j or hosted vector service.
- No changes to graph scoring or benchmark labels.
- No automated outcome-polarity decision from trial status.
- No automatic promotion of retrieved text into evidence.
- No new drug or disease nodes in the scored graph.
