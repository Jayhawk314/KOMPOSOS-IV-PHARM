# Local completion, external validation, and outreach plan

Status: recommended project pause and next-step plan, 2026-08-01.

## Decision

The local engineering phase is complete enough to stop.

This is not a claim that KOMPOSOS has solved oncology repurposing. It means the
repository now answers the questions that software development alone can
answer, and the remaining uncertainty requires researchers outside the project.

The next milestone is not another model, graph database, benchmark, or UI page.
It is evidence that a real researcher can use the existing free application to
complete a real repurposing-triage task better than with their normal workflow.

Until that evidence exists, the correct project state is **maintained pause**:
keep the application available, fix serious defects, answer interested users,
and do not expand the architecture speculatively.

## What is complete

The repository now contains:

- a reproducible scored drug-target-disease graph;
- disease-first, drug-first, and pair-inspection workflows;
- mechanistic paths and source provenance;
- direction checking and explicit abstention;
- a separate contextual evidence layer for claims, studies, roles, outcomes,
  reviews, and receipts;
- distinctions between tested-with-signal, tested-inactive, recruiting,
  category error, and unknown;
- a deterministic SQLite evidence build and local FTS5 retrieval;
- a free Streamlit interface;
- regression tests, benchmark reproduction, and honest limitation documents;
- an architectural boundary preventing retrieved literature or human review
  from silently changing scores.

The system can generate a mechanism-first reading queue. It cannot establish
that a candidate is clinically effective or genuinely novel.

## Why this is the local stopping point

### 1. The remaining question is behavioral

The unanswered question is:

> When a cancer researcher begins with a disease rather than a selected drug,
> does KOMPOSOS save time, prevent an evidence mistake, or surface something
> useful they would otherwise miss?

No local test can answer that. More unit tests can show that the software
behaves as designed; they cannot show that the design fits a researcher's work.

### 2. The primary constraint is evidence, not computation

The scored graph is small and fast. Its most important limitation is the sparse
and uneven protein-disease layer, especially the difference between directed
`driver_of` edges and undirected `associated_with` co-occurrence. Moving the
same data to a faster graph engine does not strengthen the biology.

### 3. The evidence layer has reached a useful vertical slice

The 60 reviewed candidates are sufficient to demonstrate the intended
semantics:

- positive and mixed human signals;
- completed inactive trials;
- published negative results;
- recruiting trials without results;
- biomarker restrictions;
- category errors;
- missing evidence;
- unresolved citations.

Expanding from 60 to hundreds of reviewed pairs would be expensive and still
would not prove that anyone needs the workflow.

### 4. More ranking metrics will not establish usefulness

The current benchmark measures recovery of sparse local labels. It is useful
for regression protection, but it does not measure researcher time, missed
evidence, false-lead burden, or willingness to reuse the application.

### 5. The project now needs independent judgment

The developer is no longer the right person to decide whether the workflow is
intuitive or valuable. Familiarity with the graph makes it impossible to
experience the application like a new oncology researcher.

This is the normal boundary between building a tool and validating a tool.

## Work that should remain paused

Do not start these projects without evidence from users that they solve a
specific observed problem:

- migrating SQLite to Neo4j, Rocketgraph, or another graph engine;
- adding vector retrieval before it beats the FTS5 baseline on a frozen task;
- adding more mathematical scoring strategies;
- optimizing AUROC or producing new headline benchmark figures;
- bulk-adding diseases, drugs, or co-occurrence edges;
- expanding all 60 reviews into a large literature-curation program;
- building patient-specific or treatment-recommendation features;
- adding generative summaries that can change evidence standing;
- polishing unused pages merely because they exist.

Infrastructure work may feel productive while leaving the usefulness question
untouched.

## The next falsifiable hypothesis

Use one project hypothesis:

> For a cancer selected by an external researcher, KOMPOSOS helps construct a
> defensible shortlist of approved-drug hypotheses and inspect their human
> evidence with less time or fewer classification mistakes than the
> researcher's normal initial triage process.

This hypothesis can fail. A failure is informative and is a valid reason to
archive the project.

## Who should test it

The first round needs only three to five people. Seek different roles because
they notice different failures:

1. A translational oncology researcher who evaluates mechanisms and candidate
   interventions.
2. An oncology pharmacist or pharmacologist who can identify direction,
   exposure, interaction, and feasibility problems.
3. A cancer evidence-synthesis researcher or medical librarian who searches
   trials and literature professionally.
4. A computational oncology researcher who can assess graph provenance without
   being impressed by graph terminology.
5. Optionally, a clinician-scientist who runs early-stage or investigator-led
   trials.

Do not begin with patients seeking treatment advice. The application is a
research-triage prototype and must not be presented as clinical guidance.

## The first researcher session

Run a 30-45 minute observed session. Do not give a long presentation first.

### Before opening KOMPOSOS

Ask:

- What cancer or subtype are you currently familiar with?
- How would you normally look for inexpensive approved drugs worth reviewing?
- Which databases and search terms would you use?
- What information makes you discard a candidate immediately?
- How do you record negative or inconclusive evidence?

Use a disease the researcher chooses. Do not choose a pair that makes the
application look good.

### During the session

Ask the researcher to:

1. Start from their disease.
2. Inspect a short, direction-checked candidate set.
3. Explain why one candidate is worth opening.
4. Open Pair detail and interpret the mechanism separately from the clinical
   evidence.
5. Follow at least one primary receipt.
6. Identify one candidate they would keep, reject, or quarantine.
7. Say what they would do next outside the application.

Observe silently when possible. A feature that requires the developer to
explain it has not yet succeeded.

Never present a candidate list externally without the direction filter. Do not
interpret an unreviewed pair as novel, untested, or supported.

### After the session

Ask:

- What task did this make faster?
- What was confusing or untrustworthy?
- Which evidence was missing?
- Which page or field did you ignore?
- Did any false lead cost more time than the tool saved?
- Would you use this again for a specific future task?
- If yes, what exact task and when?

The last question is more informative than general praise.

## What to measure

| Measure | How to record it |
|---|---|
| Time to first defensible candidate | Minutes from disease selection to a candidate the researcher can explain |
| Time to disposition | Minutes to keep, reject, or quarantine a pair |
| Critical evidence missed | Important trial, negative result, biomarker restriction, or category error absent from the workflow |
| Irrelevant records opened | Count of receipts or candidates that consumed time without helping |
| Standing mistakes | Positive, negative, active, and unknown states interpreted incorrectly |
| Mechanism mistakes | Direction, target role, disease category, or combination context interpreted incorrectly |
| Useful surprise | Candidate or evidence item the researcher says they would not have searched initially |
| Reuse intent | A named future task for which the researcher asks to use the application again |
| Requested change | Concrete blocker tied to an observed task, not a speculative feature request |

Store observations without patient information. A simple dated Markdown or CSV
record under `reports/researcher_validation/` is sufficient.

## Continue, narrow, or stop

Use a small project decision rule after three to five sessions.

### Continue

Continue only when at least two independent researchers:

- identify a concrete task the application helped with;
- can interpret mechanism and evidence standing without developer correction;
- ask to reuse it or share it with a relevant colleague;
- and do not encounter a safety-critical misunderstanding.

The requested next feature should be common across users or clearly unblock a
high-value task.

### Narrow

Narrow the project when researchers value only one part, for example:

- evidence-state tracking but not ranking;
- disease-first candidate enumeration but not categorical explanations;
- trial and receipt organization but not graph visualization.

Keeping one useful workflow is a success. The unused pages do not need to be
defended.

### Stop or archive

Archive the project when:

- targeted researchers cannot identify when they would use it;
- false leads consistently take more time than the shortlist saves;
- the same work is already done better by a tool they use;
- useful operation requires a corpus or clinical curation effort the project
  cannot sustain;
- or nobody agrees to test it after a reasonable, targeted outreach effort.

A reasonable first outreach limit is ten personalized contacts, not hundreds
of generic messages. Silence after careful outreach is evidence about fit.

## Outreach order

### 1. Warm and local contacts

Start with people one connection away:

- university cancer biology laboratories;
- oncology pharmacy faculty;
- clinical-trials units;
- medical librarians supporting oncology;
- computational biology groups;
- hospital innovation or evidence-synthesis teams.

Ask for workflow criticism, not endorsement, funding, or clinical adoption.
Warm contacts are more likely to spend 30 minutes showing how they actually
work.

### 2. Anticancer Fund / ReDO

The [Anticancer Fund Science Office](https://www.anticancerfund.org/en/clinical-research/science-office)
maintains repurposing resources including ReDO_DB and ReDO_Trials_DB. Its
current team lists [Pan Pantziarka as Director Drug Repurposing](https://www.anticancerfund.org/en/about-us/meet-team).
This is the closest oncology-specific fit.

Ask:

> Would someone from the drug-repurposing team spend 30 minutes testing whether
> the mechanism-plus-evidence workflow adds anything to an expert literature
> review?

Use the [Anticancer Fund contact route](https://www.anticancerfund.org/en/happy-hear-you).
Do not lead with AUROC. Lead with the distinction between mechanism,
human-testing state, result signal, and opened receipts.

### 3. Cures Within Reach

[Cures Within Reach](https://www.cureswithinreach.org/) has active oncology and
[AI Validation](https://www.cureswithinreach.org/programs/ai-validation/)
work focused on connecting computational drug-disease hypotheses with clinical
researchers and real validation. That makes it a strong source of translational
criticism, although KOMPOSOS is not ready to propose a trial.

Ask:

> What evidence and workflow standard would a computational repurposing tool
> need to meet before its candidates deserve translational review?

Use its [contact/get-involved page](https://www.cureswithinreach.org/about-us-repurposing-research-leader/contact-us-get-involved-in-repurposing-research/).
The immediate request is critique, not funding.

### 4. Every Cure

[Every Cure's MATRIX documentation](https://docs.dev.everycure.org/) describes
a much larger knowledge-graph and machine-learning pipeline whose candidates
are reviewed by physicians. KOMPOSOS should not claim comparable scale. The
useful question is whether its smaller, receipt-centered evidence semantics
solve a review problem that remains after ranking.

Their [contact page](https://everycure.org/contact/) explicitly offers routes
to share repurposing ideas, volunteer as an expert, and discuss partnerships.

Ask:

> Does the explicit separation of mechanism, trial state, outcome signal, and
> receipt validity address any review or audit gap in a mature repurposing
> pipeline?

Expect that the answer may be no. A technically informed comparison is still
valuable.

### 5. REMEDi4ALL

[REMEDi4ALL](https://remedi4all.org/) connects scientists, regulators,
funders, and patient organizations around drug repurposing. Its
[Drug Repurposing Concierge](https://remedi4all.org/repurposing-concierge/)
offers an initial consultation about scientific support, regulatory pathways,
advocacy, and funding.

Use this route after at least one external researcher has tested the
application. Ask how to frame the project and what evidence would be required
for a credible next stage.

### 6. GlobalCures

[GlobalCures](https://www.global-cures.org/copy-of-our-team) explicitly focuses
on scientifically promising, readily available, cost-effective treatments and
the "financial orphan" problem. This aligns closely with the project's
non-commercial purpose.

Ask for a research-workflow review, not evaluation of a specific treatment for
a patient.

## Outreach message for an individual researcher

Subject: 30-minute test of a free oncology repurposing research tool

> I built a free research prototype that starts with a cancer and generates
> approved-drug hypotheses through drug-target-disease mechanisms. It then
> keeps mechanism separate from human evidence: completed inactive trials,
> mixed signals, recruiting trials, category errors, unknowns, and the source
> records actually opened.
>
> It does not recommend treatment, and I am not asking you to validate a
> candidate. I need to learn whether the workflow saves a researcher any time
> compared with their normal PubMed and trial-search process, or whether it
> simply creates more work.
>
> Would you be willing to spend 30 minutes using it on a cancer you choose
> while I observe where it helps or fails? The project is open, free, and I am
> comfortable stopping development if it does not fit real work.
>
> App: [link]
> Architecture and limitations: [link]

Personalize the first sentence with the recipient's actual field. Do not send
the same message indiscriminately.

## Outreach message for an organization

Subject: Request for workflow critique, not funding - open oncology repurposing prototype

> KOMPOSOS-IV-PHARM is a free, open research prototype for mechanism-first
> oncology drug-repurposing triage. Its distinctive feature is not another
> prediction score: it separates the mechanism graph from a contextual
> evidence layer representing studies, interventions, biomarkers, outcomes,
> testing state, and source receipts.
>
> The software is now at a local stopping point. Before expanding it, I am
> seeking an expert workflow critique: can a researcher answer an initial
> repurposing question faster or with fewer evidence-state mistakes than with
> their normal process?
>
> I am asking for one 30-minute observed test or referral to someone who
> evaluates repurposing evidence. I am not requesting clinical endorsement or
> presenting a treatment recommendation.
>
> App: [link]
> Evidence architecture: [link]
> Honest limitations: [link]

## What to prepare before outreach

Prepare only four artifacts:

1. A stable public app link that opens without setup.
2. A 60-90 second silent screen recording:
   disease selection -> direction-aware shortlist -> Pair detail -> receipt.
3. A one-page explanation using the researcher question, not the mathematical
   architecture.
4. A short feedback form matching the measures above.

Do not prepare a long investor deck, commercial plan, or generalized claim that
the system discovers cures.

## A five-minute demonstration

If a contact asks for a demonstration:

1. State the boundary: "This creates a reading queue, not a treatment answer."
2. Start with the researcher's disease.
3. Show why one pair appeared.
4. Show the direction status.
5. Open contextual evidence and distinguish testing state from result signal.
6. Open a receipt.
7. Show an unknown or unresolved case.
8. Ask what their normal process would do next.

Do not spend the demonstration explaining Kan extensions, AUROC, or graph
engine technology unless the researcher specifically asks.

## Responding to feedback

Classify every requested change:

- **Truth defect:** wrong fact, state, direction, citation, or category. Fix it.
- **Workflow blocker:** prevents completion of an observed research task.
  Consider a bounded fix.
- **Usability friction:** confusing wording or navigation. Fix when small.
- **Corpus request:** requires sustained domain curation. Estimate ownership
  before accepting.
- **Infrastructure preference:** different database, model, or framework
  without a demonstrated workflow effect. Defer.
- **New product:** patient guidance, clinical decision support, or broad drug
  discovery. Decline unless the project is deliberately re-chartered.

After each meaningful change, repeat the same task with a researcher. Do not
infer usefulness from completing the feature.

## Maintenance during the pause

While paused:

- keep the public app and repository readable;
- fix broken deployment, security issues, invalid links, and factual errors;
- preserve deterministic builds and passing tests;
- record incoming feedback;
- avoid refreshing data silently;
- label the age of the graph and evidence corpus;
- do not advertise candidates as findings.

A monthly development cadence is unnecessary without users. Respond to real
events rather than manufacturing a roadmap.

## Thirty-day external-validation sequence

### Week 1

- Confirm the public app works in a clean browser.
- Record the short demonstration.
- Create the feedback form and observation template.
- Identify five warm contacts and five specialist-organization contacts.

### Week 2

- Send five personalized messages.
- Schedule any willing testers.
- Do not implement new features while waiting.

### Week 3

- Run the first sessions.
- Record exact confusion, missed evidence, and time costs.
- Fix only truth defects that would invalidate later sessions.

### Week 4

- Run remaining sessions.
- Apply the continue/narrow/archive decision.
- Write a short public result even if the outcome is negative.

If no one responds, send the remaining five messages once. After ten
well-targeted contacts, pause rather than converting outreach into spam.

## The legitimate finishing outcomes

All three outcomes are respectable:

1. **Continue:** researchers reuse the workflow and reveal a bounded next
   problem.
2. **Narrow:** one component, such as evidence-state tracking, is useful and the
   rest is retired.
3. **Archive:** the workflow does not beat normal research practice or cannot
   be maintained responsibly.

The project has already produced a reproducible account of what its graph can
and cannot do. External use determines whether it becomes a maintained tool.
Lack of adoption would not erase the engineering or the measurements; it would
answer the remaining question.

## Related documents

- `HONEST_VALUE.md` - measured value and limitations.
- `docs/EVIDENCE_GRAPH_ARCHITECTURE.md` - before/after graph architecture.
- `docs/EVIDENCE_HYPERGRAPH_PLAN.md` - implementation and stop/go gates.
- `CLAUDE.md` - current executable facts and reproduction commands.
