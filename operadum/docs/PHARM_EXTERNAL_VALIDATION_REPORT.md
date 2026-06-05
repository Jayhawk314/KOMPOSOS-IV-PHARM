# PHARM External Validation Report

Date: 2026-06-05

This report checks the PHARM findings against external public research,
regulatory, and clinical-trial sources. It is a supplement to:

- `docs/PHARM_FINDINGS_REPORT.md`
- `docs/PHARM_RESEARCH_LEADS.md`
- `docs/PHARM_LEAD_AUDIT_TRAIL_SUPPLEMENT.md`

Boundary: this is validation/curation analysis, not medical advice or a clinical
recommendation.

## Data Trail By System

### OPERADUM

OPERADUM is the orchestration and delivery layer for this pass. It did not make
the biomedical evidence claim by itself. In this PHARM run, OPERADUM's role was
to organize candidates, connect the adapter loop, and package readable reports:

```text
Candidate -> KOMPOSOS-IV-PHARM evidence -> PRONOIA score/report -> docs
```

### KOMPOSOS-IV-PHARM

KOMPOSOS-IV-PHARM supplied the local typed graph, drug/disease universe, hidden
label benchmark, graph paths, morphism confidences, and local morphism
provenance. The important protocol was:

```text
remove_direct_labels
```

That means direct Drug->Disease treatment labels were hidden from PRONOIA. The
system had to infer candidates from mechanism/path evidence such as:

```text
Drug -[inhibits]-> Target
Target -[driver_of]-> Disease
```

The local PHARM database contains PMID/FDA/mechanism provenance on morphism rows.
Those local PMIDs are part of the KOMPOSOS audit trail. The external web check
below separately asks whether the surfaced candidate is supported by public
research, trials, or approvals.

### PRONOIA

PRONOIA supplied the ranking and audit metrics. PHARM score v2 uses:

```text
score = structured path/mechanism strength
        - grounding penalty
        - contradiction penalty placeholder
```

Raw zlib-MDL gain is retained as a transparency metric, but it is not the
primary PHARM ranker.

### External Web Validation

The external check used public sources such as FDA pages, NCI clinical trial
pages, PubMed, PMC, and journal pages. This check is not allowed to replace the
system trail. It only classifies whether the system's surfaced pair is:

- externally validated / likely local label-table curation issue
- supported by active research or trials
- mechanism-supported but clinically mixed
- weak or not validated

## Summary Verdict

The strongest result is that several PRONOIA "label-negative" findings are
externally supported by clinical trials, FDA approvals, or major published
studies. That means some of the top "false positives" are likely not simple
errors. They are often local benchmark label-table gaps, underrepresented labels,
or cases where the graph found a real mechanism before the benchmark treated the
pair as positive.

| Candidate | PRONOIA score | Local PHARM route | External validation verdict |
|---|---:|---|---|
| Sotorasib -> Pancreatic_Cancer | 97.0 | Sotorasib -> KRAS -> Pancreatic_Cancer | Supported by published pancreatic KRAS G12C work and active NCI trial |
| Adagrasib -> Pancreatic_Cancer | 97.0 | Adagrasib -> KRAS -> Pancreatic_Cancer | Supported by active NCI trial |
| Adagrasib -> Colorectal_Cancer | 93.4 | Adagrasib -> KRAS -> Colorectal_Cancer | Strongly externally validated; FDA-approved with cetuximab |
| Sotorasib -> Colorectal_Cancer | 93.4 | Sotorasib -> KRAS -> Colorectal_Cancer | Strongly externally validated; FDA-approved with panitumumab |
| Trastuzumab_deruxtecan -> Breast_Cancer | 96.5 | T-DXd -> ERBB2 -> Breast_Cancer | Strongly externally validated; likely local label curation issue |
| Lorlatinib -> NSCLC | 95.4 | Lorlatinib -> ALK/ROS1 -> NSCLC | Strongly externally validated; likely local label curation issue |
| Brigatinib -> NSCLC | 95.0 | Brigatinib -> ALK -> NSCLC | Strongly externally validated; likely local label curation issue |
| Afatinib -> Breast_Cancer | 95.0 | Afatinib -> ERBB2/EGFR -> Breast_Cancer | Mechanism supported, clinically mixed/unfavorable; v3 calibration case |
| Cetuximab -> NSCLC | 95.0 | Cetuximab -> EGFR -> NSCLC | Mechanism supported, not enough as standalone treatment claim; v3 calibration case |
| Lapatinib -> NSCLC | 94.5 | Lapatinib -> EGFR/ERBB2 -> NSCLC | Mechanism supported, weak/older clinical signal; v3 calibration case |

## Candidate Checks

### Sotorasib -> Pancreatic_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied the hidden-label
PHARM graph route `Sotorasib -[inhibits]-> KRAS; KRAS -[driver_of]->
Pancreatic_Cancer`; PRONOIA scored it `97.0` with grounding `0.783`. The local
PHARM morphism provenance includes `FDA:NDA214665,
mechanism:KRAS_G12C_inhibitor; PMID:42144204; [RELATION-VERIFIED]` for
Sotorasib->KRAS and `PMID:42092950; [RELATION-VERIFIED]` for
KRAS->Pancreatic_Cancer.

External validation: public sources support this as a real research target, not
just a graph artifact. A PMC/NEJM report studied sotorasib in KRAS p.G12C-mutated
advanced pancreatic cancer, and an NCI trial studies sotorasib combined with
chemotherapy in KRAS G12C pancreatic cancer.

Verdict: supported research lead. This is not established from PRONOIA alone,
but the external literature validates that the PRONOIA/KOMPOSOS mechanism is
research-relevant.

Sources:

- [PMC: Sotorasib in KRAS p.G12C-mutated advanced pancreatic cancer](https://pmc.ncbi.nlm.nih.gov/articles/PMC10506456/)
- [NCI-2022-06901: Sotorasib with chemotherapy in KRAS G12C pancreatic cancer](https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2022-06901)

### Adagrasib -> Pancreatic_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Adagrasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Pancreatic_Cancer`;
PRONOIA scored it `97.0` with grounding `0.783`. The local PHARM morphism
provenance includes `FDA:NDA216340, mechanism:KRAS_G12C_inhibitor;
PMID:42122163; [RELATION-VERIFIED]` for Adagrasib->KRAS and
`PMID:42092950; [RELATION-VERIFIED]` for KRAS->Pancreatic_Cancer.

External validation: an NCI-listed trial directly tests adagrasib in
unresectable or metastatic pancreatic cancer with KRAS G12C mutation and names
objective response as a target outcome.

Verdict: supported active-trial lead. This is stronger than a speculative graph
hit, but it should still be framed as trial/research support rather than a
general treatment recommendation.

Source:

- [NCI-2022-10011: Adagrasib for metastatic pancreatic cancer with KRAS G12C mutation](https://www.cancer.gov/clinicaltrials/NCI-2022-10011)

### Adagrasib -> Colorectal_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Adagrasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Colorectal_Cancer`;
PRONOIA scored it `93.4345` with grounding `0.741`. The local PHARM trail also
found secondary KRAS->BRAF and KRAS->TP53 colorectal paths. Local provenance
includes `FDA:NDA216340, mechanism:KRAS_G12C_inhibitor; PMID:42122163;
[RELATION-VERIFIED]` for Adagrasib->KRAS and `PMID:18316791` for
KRAS->Colorectal_Cancer.

External validation: this is strongly validated externally. The FDA granted
accelerated approval for adagrasib with cetuximab in previously treated KRAS
G12C-mutated locally advanced or metastatic colorectal cancer. Published
KRYSTAL-1 evidence also supports the adagrasib+cetuximab colorectal cancer
combination.

Verdict: likely local PHARM label-table curation issue, not a true negative.
This is one of the best first outreach packets because PRONOIA found a
label-negative pair that external sources already support.

Sources:

- [FDA: Adagrasib with cetuximab for KRAS G12C-mutated colorectal cancer](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-adagrasib-cetuximab-kras-g12c-mutated-colorectal-cancer)
- [PMC: Adagrasib with or without cetuximab in KRAS G12C colorectal cancer](https://pmc.ncbi.nlm.nih.gov/articles/PMC9908297/)
- [PubMed: Adagrasib plus cetuximab in KRAS G12C-mutated metastatic CRC, PMID 38587856](https://pubmed.ncbi.nlm.nih.gov/38587856/)

### Sotorasib -> Colorectal_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Sotorasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Colorectal_Cancer`;
PRONOIA scored it `93.4345` with grounding `0.741`. The local graph also
provided KRAS->BRAF and KRAS->TP53 colorectal support paths. Local provenance
includes `FDA:NDA214665, mechanism:KRAS_G12C_inhibitor; PMID:42144204;
[RELATION-VERIFIED]` for Sotorasib->KRAS and `PMID:18316791` for
KRAS->Colorectal_Cancer.

External validation: this is strongly validated externally. The FDA approved
sotorasib with panitumumab for previously treated KRAS G12C-mutated metastatic
colorectal cancer. CodeBreaK 300 evaluated sotorasib plus panitumumab in this
setting.

Verdict: likely local PHARM label-table curation issue, not a true negative.
This is another high-quality validation packet.

Sources:

- [FDA: Sotorasib with panitumumab for KRAS G12C-mutated colorectal cancer](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-sotorasib-panitumumab-kras-g12c-mutated-colorectal-cancer)
- [NEJM: Sotorasib plus panitumumab in refractory KRAS G12C colorectal cancer](https://www.nejm.org/doi/full/10.1056/NEJMoa2308795)
- [PubMed: CodeBreaK 300 overall survival analysis, PMID 40215429](https://pubmed.ncbi.nlm.nih.gov/40215429/)

### Trastuzumab_deruxtecan -> Breast_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Trastuzumab_deruxtecan -[inhibits]-> ERBB2; ERBB2 -[driver_of]->
Breast_Cancer`; PRONOIA scored it `96.4883` with grounding `0.794`. Local PHARM
provenance includes `FDA:BLA761139, mechanism:HER2_ADC` for
T-DXd->ERBB2 and `PMID:41554087; [RELATION-VERIFIED]` for
ERBB2->Breast_Cancer.

External validation: this is strongly validated externally. DESTINY-Breast04 and
FDA/NCI materials support trastuzumab deruxtecan as a HER2-targeted breast cancer
therapy, including HER2-low metastatic breast cancer settings.

Verdict: very likely local label-table curation issue. This is not a speculative
repurposing lead; it is a strong validation case showing that the local benchmark
can treat an externally supported pair as label-negative.

Sources:

- [PubMed: DESTINY-Breast04, PMID 35665782](https://pubmed.ncbi.nlm.nih.gov/35665782/)
- [NCI: Trastuzumab deruxtecan for HER2-low metastatic breast cancer](https://www.cancer.gov/news-events/cancer-currents-blog/2022/enhertu-her2-low-breast-cancer)
- [FDA: Enhertu HER2-low / ultralow breast cancer approval](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-fam-trastuzumab-deruxtecan-nxki-unresectable-or-metastatic-hr-positive-her2-low-or-her2)

### Lorlatinib -> NSCLC

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied two convergent
routes: `Lorlatinib -[inhibits]-> ALK; ALK -[driver_of]-> NSCLC` and
`Lorlatinib -[inhibits]-> ROS1; ROS1 -[driver_of]-> NSCLC`; PRONOIA scored it
`95.4358` with grounding `0.562`. Local PHARM provenance includes
`FDA:NDA210868, mechanism:3rd_gen_ALK_TKI; PMID:42170281;
[RELATION-VERIFIED]` for Lorlatinib->ALK, `PMID:42187575;
[LEXICAL-COOCCURRENCE]` for ALK->NSCLC, `FDA:NDA210868,
mechanism:ALK_ROS1_TKI; PMID:41704605; [RELATION-VERIFIED]` for
Lorlatinib->ROS1, and `PMID:42075590; [RELATION-VERIFIED]` for ROS1->NSCLC.

External validation: strongly validated. The CROWN study and other published
work support lorlatinib in ALK-positive NSCLC, and phase 1/2 work supports
lorlatinib activity in ALK/ROS1-rearranged NSCLC contexts.

Verdict: likely local label-table curation issue or underrepresented indication
context. This is a strong validation case.

Sources:

- [PubMed: First-line lorlatinib or crizotinib in ALK-positive lung cancer, PMID 33207094](https://pubmed.ncbi.nlm.nih.gov/33207094/)
- [PMC: Lorlatinib 5-year CROWN outcomes](https://pmc.ncbi.nlm.nih.gov/articles/PMC11458101/)
- [PMC: Lorlatinib in ALK- or ROS1-rearranged NSCLC, PMID 29074098](https://pmc.ncbi.nlm.nih.gov/articles/PMC5777233/)

### Brigatinib -> NSCLC

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Brigatinib -[inhibits]-> ALK; ALK -[driver_of]-> NSCLC`, with secondary EGFR
routes; PRONOIA scored it `94.9526` with grounding `0.562`. Local provenance
includes `FDA:NDA208772, mechanism:ALK_TKI; PMID:42136297;
[RELATION-VERIFIED]` for Brigatinib->ALK and `PMID:42187575;
[LEXICAL-COOCCURRENCE]` for ALK->NSCLC. Secondary EGFR route provenance is more
lexical, so it should be treated as support rather than the main basis.

External validation: strongly validated. ALTA-1L published results support
brigatinib in ALK-positive NSCLC, including superiority versus crizotinib in
ALK inhibitor-naive advanced ALK-positive NSCLC.

Verdict: likely local label-table curation issue or underrepresented indication
context. The ALK route is the clean external validation route; the EGFR route is
more useful as secondary support.

Sources:

- [PubMed: ALTA-1L final results, PMID 34537440](https://pubmed.ncbi.nlm.nih.gov/34537440/)
- [PMC: ALTA-1L second interim analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC7605398/)
- [PMC: Brigatinib long-term ALTA results](https://pmc.ncbi.nlm.nih.gov/articles/PMC9440305/)

### Afatinib -> Breast_Cancer

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Afatinib -[inhibits]-> ERBB2; ERBB2 -[driver_of]-> Breast_Cancer` and
`Afatinib -[inhibits]-> EGFR; EGFR -[associated_with]-> Breast_Cancer`;
PRONOIA scored it `95.0` with grounding `0.700`. Local provenance includes
`FDA:NDA201292, mechanism:pan-HER_TKI; PMID:40612504; [RELATION-VERIFIED]` for
Afatinib->ERBB2, `PMID:41554087; [RELATION-VERIFIED]` for
ERBB2->Breast_Cancer, `FDA:NDA201292, mechanism:irreversible_EGFR_TKI;
PMID:42151084; [RELATION-VERIFIED]` for Afatinib->EGFR, and
`ABPP; PMID:16618952` for EGFR->Breast_Cancer.

External validation: mixed. External breast cancer trials show that afatinib has
biological HER2/EGFR relevance, but LUX-Breast results were not cleanly positive
as an actionable breast cancer treatment strategy. Published summaries describe
similar PFS/response in some comparisons but shorter overall survival and poorer
tolerability versus comparator regimens.

Verdict: not a strong outreach result as a treatment claim. It is a strong v3
calibration case because it proves that mechanism strength alone can over-rank a
clinically weak or unfavorable indication.

Sources:

- [PubMed: LUX-Breast 1, PMID 26822398](https://pubmed.ncbi.nlm.nih.gov/26822398/)
- [PMC: LUX-Breast 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8960620/)
- [PMC: Afatinib +/- vinorelbine inflammatory breast cancer trial](https://pmc.ncbi.nlm.nih.gov/articles/PMC5140058/)

### Cetuximab -> NSCLC

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Cetuximab -[inhibits]-> EGFR; EGFR -[driver_of]-> NSCLC`, plus downstream
EGFR->KRAS and EGFR->KRAS->TP53 paths; PRONOIA scored it `95.0` with grounding
`0.533`. Local provenance includes `PMID:15269313` for Cetuximab->EGFR,
`PMID:42182703; [LEXICAL-COOCCURRENCE]` for EGFR->NSCLC,
`PMID:42075590; [RELATION-VERIFIED]` for KRAS->NSCLC, and `PMID:37683526` for
TP53->NSCLC.

External validation: partial and cautionary. The EGFR/NSCLC biology is real, and
SWOG S1403 studied afatinib plus cetuximab versus afatinib alone in EGFR-mutant
NSCLC. But the external evidence does not validate `Cetuximab -> NSCLC` as a
standalone broad treatment claim.

Verdict: v3 calibration case. The graph sees real EGFR biology, but external
research says indication, mutation class, combination context, and resistance
matter.

Sources:

- [PubMed: SWOG S1403, PMID 33021871](https://pubmed.ncbi.nlm.nih.gov/33021871/)
- [SWOG S1403 trial page](https://www.swog.org/clinical-trials/s1403)

### Lapatinib -> NSCLC

System trail: OPERADUM packaged the candidate; KOMPOSOS supplied
`Lapatinib -[inhibits]-> EGFR; EGFR -[driver_of]-> NSCLC` and
`Lapatinib -[inhibits]-> ERBB2; ERBB2 -[associated_with]-> NSCLC`; PRONOIA
scored it `94.4987` with grounding `0.533`. Local provenance includes
`FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI; PMID:42089475;
[RELATION-VERIFIED]` for Lapatinib->EGFR, `PMID:42182703;
[LEXICAL-COOCCURRENCE]` for EGFR->NSCLC, `FDA:NDA022059,
mechanism:dual_EGFR_HER2_TKI` for Lapatinib->ERBB2, and `ABPP; PMID:41982617;
[RELATION-VERIFIED]` for ERBB2->NSCLC.

External validation: weak/cautionary. A randomized phase II lapatinib NSCLC
study exists, which confirms that this axis has been clinically explored, but it
does not make the pair a strong current positive. This is a good negative-control
style case.

Verdict: v3 calibration case. The external web check weakens the treatment-claim
interpretation while validating that the mechanism route is not random.

Source:

- [PubMed: randomized phase II lapatinib NSCLC study, PMID 20215545](https://pubmed.ncbi.nlm.nih.gov/20215545/)

## Overall Interpretation

The external public-source check changes the interpretation of the PHARM
results:

1. Several top "false positives" are probably not false in the ordinary sense.
   They are externally supported relationships missing from, or underrepresented
   by, the local PHARM benchmark label table.

2. The best immediate use of the system is curation and expert review:

```text
Trastuzumab_deruxtecan -> Breast_Cancer
Lorlatinib -> NSCLC
Brigatinib -> NSCLC
Adagrasib -> Colorectal_Cancer
Sotorasib -> Colorectal_Cancer
```

3. The best research-hypothesis leads are the KRAS pancreatic findings:

```text
Sotorasib -> Pancreatic_Cancer
Adagrasib -> Pancreatic_Cancer
```

They are externally supported by pancreatic KRAS G12C research/trials, but they
should be framed as research/trial-context findings, not general treatment
claims.

4. The best v3 calibration cases are:

```text
Afatinib -> Breast_Cancer
Cetuximab -> NSCLC
Lapatinib -> NSCLC
```

These show exactly why PRONOIA needs contradiction/residual/indication-context
penalties. The graph mechanism is real, but mechanism alone is not enough.

## Recommendation

Create two outward-facing packets:

1. **Validation/curation packet**

Use externally supported label-negative pairs to show that the PRONOIA/KOMPOSOS
loop can detect benchmark gaps:

```text
T-DXd -> Breast_Cancer
Lorlatinib -> NSCLC
Brigatinib -> NSCLC
Adagrasib -> CRC
Sotorasib -> CRC
```

2. **Research-review packet**

Use KRAS pancreatic results to ask domain experts what v3 should penalize:

```text
Sotorasib -> Pancreatic_Cancer
Adagrasib -> Pancreatic_Cancer
```

The outreach should not claim discovery. It should say:

```text
Our hidden-label graph engine independently surfaced mechanism-backed pairs.
Several are externally supported, which suggests the local benchmark needs
curation and the scoring trace may be useful for expert review.
```

## Implementation Status

The PHARM adapter now carries local KOMPOSOS-IV-PHARM morphism provenance
directly inside `EvidenceItem.metadata` when the local SQLite database is
available:

```text
PMID/FDA provenance
evidence_tier
confidence interval fields
quantitative fields
raw morphism id
parsed PMID list
raw_morphism record
```

Mechanism evidence items include enriched first/second morphism records. Path
evidence items include enriched records for each path morphism, plus path-level
PMID, provenance, and evidence-tier summaries. A future external validation
packet can now be generated from one `PredictionReport` without separately
querying the PHARM SQLite database.
