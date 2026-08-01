# KOMPOSOS-IV-PHARM: AI x Bio Event Readiness

Prepared July 31, 2026, for **AI x Bio Demo Night with NVIDIA and the Allen Institute for AI**, August 11, 2026.

## Bottom line

Go if the registration is accepted. Bring the laptop, but go primarily to learn and meet people, not to convince the room that KOMPOSOS is a finished drug-discovery platform.

KOMPOSOS-IV-PHARM has a credible narrow story:

> It is an inspectable drug-repurposing search accelerator over a curated oncology graph. It ranks known drug-target-disease relationships, shows the evidence paths that caused the ranking, and exposes where its evidence is weak.

That story fits a technical AI-and-biology gathering. The larger stories—patient-specific healing, de-novo drug design, genomic collapse, clinical decisions, or a universal categorical intelligence system—do not yet have enough validation to survive expert questions.

Do strengthen PHARM before the event, but strengthen the **demonstration and evidence boundary**, not its breadth.

## What is verified about the event

The public AI Tinkerers event index confirms the title, date, Seattle location, 6–9 PM time, NVIDIA and Ai2 support, and a focus on builders and researchers demonstrating AI applications in biology through live code and tools. The registration email provides the specific address and says the application is still pending. A pending application is not a confirmed seat.

AI Tinkerers Seattle describes itself as a screened, hands-on builder meetup centered on working prototypes, technical discussion, failures, and practical demos rather than sales presentations. Its previous event instructions consistently call for roughly five-minute, code-first demonstrations with technical Q&A and no pitches or slide decks.

The event banner emphasizes protein-model sequence, confidence, structure, and quality. That suggests protein modeling may be visible in the room, but it is not a published agenda and should not be treated as one.

NVIDIA's current BioNeMo materials cover biological foundation-model workflows including protein and genomic sequence models, single-cell models, molecular generation, representation learning, and model training or fine-tuning. PHARM does not compete with that infrastructure. Its plausible relationship is downstream: a model or database produces evidence, while PHARM helps organize, rank, inspect, and refuse to overinterpret the resulting drug-disease hypotheses.

Sources:

- [AI x Bio event listing](https://aitinkerers.org/events)
- [Direct Seattle event page](https://seattle.aitinkerers.org/p/ai-x-bio-demo-night-w-nvidia-allen-institute-for-ai)
- [AI Tinkerers Seattle format and audience](https://seattle.aitinkerers.org/?tab=home)
- [Example Seattle demo instructions](https://seattle.aitinkerers.org/p/ai-tinkerers-seattle-september-meetup-september-30-2025)
- [NVIDIA BioNeMo overview](https://docs.nvidia.com/bionemo-framework/2.0/user-guide/index.html)
- [Current BioNeMo model and training recipes](https://docs.nvidia.com/bionemo-framework/latest/main/recipes/index.html)

## What PHARM can honestly demonstrate now

The following was checked locally on July 31 against commit `2d0db01`:

- The complete local test suite passed: **166 passed, 1 skipped**.
- The focused repurposing tests passed: **4 passed, 1 skipped**.
- The current strict core-cohort benchmark reproduced with 78 drugs, 20 diseases, 44 known positive indications, and 1,516 unlabeled pairs.
- Under `full_typed / remove_direct_labels`, it produced AUROC **0.97845**, AUPRC **0.61278**, and Hits@20 **0.70**.
- The strongest included simple graph baseline was common-neighbor AUROC **0.7429**, a margin of approximately **+0.24**.
- The benchmark scored 957 of 1,560 pairs; 603 received no score. That abstention/coverage fact belongs beside the performance number.
- A pair-level run for Sorafenib and melanoma completed and exposed the score, component strategies, evidence tiers, and paths.

These are real engineering results, but their meaning is narrow. The high internal score is recovery of known labels from a small curated graph after removing direct labels. It is not a prospective drug-discovery hit rate. The repository's carried-forward Hetionet result—AUROC about 0.644 and AUPRC about 0.010—is the important warning that external top-of-list precision is weak. That external result was not rerun during this review.

The repository deserves credit for publishing its negative results. Its ESMC similarity-transfer edges hurt rather than helped. Its post-hoc PubMed grounding control did not show statistically reliable signal over scrambled pairs. Those failures make a better technical conversation than a grand claim would.

## Is category theory load-bearing?

There are two different answers.

### In the implementation

Graph composition is load-bearing. The ranker depends heavily on composing drug-to-protein and protein-to-disease paths, carrying confidence and provenance through those paths, and comparing structured neighborhoods. Category theory is a coherent language for that work.

### In the scientific value claim

Category theory has not been shown to be uniquely necessary. The repository's own ablation says that confidence-weighted mechanistic path composition retains most of the headline performance. In the stored ablation, composition alone reached AUROC about 0.969, removing composition caused the largest drop, Yoneda alone was near chance, and removing several higher strategies changed almost nothing. The later ESMC ablation showed that the embedding-similarity transfer layer slightly reduced every main metric.

There is also no matched experiment yet showing that the categorical implementation beats a well-built classical knowledge-graph model because of its categorical properties. Common-neighbor and path-count baselines are useful, but they do not settle that question.

Therefore:

- Keep category theory as an internal design language and a source of testable ideas.
- Describe the working mechanism in ordinary terms first: typed evidence graph, path composition, provenance, abstention, and auditable ranking.
- Do not put “categorical AI” in the opening sentence at this event.
- If someone asks, explain that the categorical framing motivated compositional structure, but the current evidence attributes most predictive value to classical mechanistic path scoring.
- A future claim that category theory adds value should require a current, pre-specified ablation against a matched non-categorical implementation.

This does not make KOMPOSOS pointless. It separates the part people can use from the intellectual framework that inspired it.

## Who might need the current system?

The first plausible user is not a patient, clinician, or pharma procurement team. It is a computational biologist, translational researcher, or scientific ML builder who already has too many candidate relationships to inspect and wants a shorter list with visible reasons.

The concrete job is:

> Reduce a candidate set to a reviewable shortlist while preserving the source, relation type, confidence, and limitations of every path.

That user may value PHARM even if category theory is completely hidden. They will care about:

- whether the data sources are legitimate and current;
- whether labels or indication-derived edges leaked into evaluation;
- whether results beat reasonable baselines;
- whether the ranking transfers to a different dataset or future time period;
- whether weak association and directed mechanism are clearly distinguished;
- whether a candidate can be rejected or marked unassessed;
- whether they can run it on their own graph or data.

The event is useful because it may contain people who can tell James which of those requirements actually blocks use. One precise rejection from a biologist is more valuable than another speculative module.

## The smallest credible preparation

### 1. Freeze the product claim

Use one sentence consistently:

> KOMPOSOS-IV-PHARM is a research prototype that prioritizes oncology drug-repurposing hypotheses from a curated evidence graph and shows why each result was ranked; it is not a clinical or efficacy predictor.

Do not add patient-specific, multi-omic, inflammation, safety, or de-novo design claims before August 11.

### 2. Make one four-minute demonstration

The current pair-level output is too long. The Sorafenib–melanoma run emitted 86 chains, many of them weak multi-hop disease-association paths. A useful event demo should show only:

1. the question being asked;
2. the score and its non-probabilistic meaning;
3. the three strongest evidence paths;
4. the evidence tier on each edge;
5. what evidence is missing;
6. the system's final status: supported for review, weak, or not assessed.

Use two cases:

- one held-out known indication to show recovery under label removal;
- one plausible but unapproved or failed case to show why mechanistic plausibility is not clinical efficacy.

Sorafenib–melanoma may be more valuable as the second case than as a success story. It lets the system say, “The BRAF path makes this rank highly, but this graph cannot establish patient benefit, safety, or trial success.” That is memorable and honest.

### 3. Run a current, matched ablation only if there is time

The highest-value technical strengthening would be a small experiment on the exact current benchmark:

- full current scorer;
- confidence-weighted mechanistic composition only;
- a matched classical weighted-path scorer;
- common-neighbor/path-count baselines;
- the same core cohort, removed labels, and fixed metrics.

Do not tune the methods after seeing the answer. Record the design first. If the categorical version does not win, publish that result and lead with the simpler method. If time is short, do not build this merely for the event; the existing honest ablation is enough for a conversation.

### 4. Verify a clean run and prepare a backup

Before leaving:

- clone the public repository into a fresh directory;
- create a fresh environment from documented dependencies;
- run the focused tests and exact benchmark command;
- run the four-minute demo without network access;
- record a short local screen capture in case venue Wi-Fi or dependencies fail;
- use large terminal text;
- fully charge the laptop and bring its charger.

The laptop should stay in the bag until someone asks or a demo opportunity appears. It is evidence, not a social shield.

### 5. Clean the communication surface

The root `README.md`, `HONEST_VALUE.md`, and `CLAUDE.md` contain the current July figures. `docs_current/` still presents the older June benchmark and calls itself current, so a visitor can encounter conflicting numbers. Resolve or clearly archive that drift before directing experts to the repository.

The pair demo should also suppress long, weak path chains by default. “320/320 edges cited” is not the same as “320 relationships verified,” especially because the repository's own negative control showed that post-hoc citation retrieval added little discriminating signal.

## What not to build before August 11

Do not add a chromosomal-collapse module, patient genome, inflammation layer, cancer multi-omics layer, or “patient healing system” for this event.

Those ideas could become separate research questions, but each requires cohort definitions, data governance, variant interpretation, outcome labels, privacy controls, biological baselines, and external review. Adding them now would expand the claim surface much faster than the evidence surface. It would make PHARM less credible in precisely the room where credibility matters.

Do not integrate BioNeMo merely because NVIDIA is a supporter. Only use an NVIDIA model if it answers a pre-existing, measurable PHARM question and can be compared with the current method. Logo-driven integration is not validation.

## How James should introduce it

Twenty-second version:

> I built an evidence-bound drug-repurposing ranker over a small oncology graph. It is very good at recovering known relationships inside that graph, but external precision is still weak. What I care about is that every ranking shows the paths behind it and admits what it cannot establish. I am here to find out whether that kind of auditable triage would help real biological work.

Do not lead with being a vibe coder or apologize for not having a CS degree. Also do not present yourself as a computational biologist. The accurate identity is **independent systems builder investigating evidence-bound scientific reasoning**. Then let the running system and the quality of the questions carry the conversation.

## Three useful conversations

Ask a computational biologist:

> If a tool reduced 1,500 candidate pairs to 100 inspectable paths, what evidence would have to be present before you would spend an afternoon reviewing them?

Ask a scientific ML builder:

> What baseline or holdout would convince you that structured path composition adds value beyond degree and common-neighbor effects?

Ask someone working with biomolecular foundation models:

> After a model generates an embedding, structure, or candidate, where does your workflow preserve—or lose—the evidence for why anyone should act on it?

The goal is not to collect compliments. It is to leave with one person willing to inspect a result, one concrete dataset or benchmark PHARM should face, and one follow-up conversation.

## Schedule through August 11

- **July 31–August 2:** freeze the claim; select the two demo cases; remove conflicting “current” documentation from the visitor path.
- **August 3–5:** create the compact evidence-gated demo; run it from a clean clone; keep the existing full output available only for inspection.
- **August 6–7:** run the matched ablation if it can be done without rushing or tuning; otherwise document it as future work.
- **August 8:** ask one technically literate person to interrupt the demo with skeptical questions.
- **August 9:** make the offline recording and freeze code.
- **August 10:** rehearse a four-minute version and a twenty-second version; prepare the three questions above.
- **August 11:** attend if accepted, listen first, and aim for one real follow-up rather than broad attention.

## Readiness verdict

PHARM is ready to be **shown as a bounded research prototype and discussed as an experiment**. It is not ready to be offered as a patient-level system, clinical tool, validated discovery engine, or categorical breakthrough.

The most distinctive thing James can bring is not category theory by itself and not a larger feature list. It is a working system that shows its reasoning, publishes its failed ablations, and can say: “This is why the candidate ranked; this is where the evidence weakens; this is what I still do not know.”
