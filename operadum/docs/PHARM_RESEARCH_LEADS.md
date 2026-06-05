# PHARM Research Leads

Date: 2026-06-05

Purpose: identify real researchers, groups, and trial networks whose current work
lines up with the PHARM findings report. The goal is not to sell the system. The
goal is to find people who may care about the results now because PRONOIA
independently surfaced mechanism-backed pairs that overlap their research.

Boundary: these are outreach/review leads, not clinical recommendations.

For the system-provided audit trail behind each lead, see
`docs/PHARM_LEAD_AUDIT_TRAIL_SUPPLEMENT.md`.

For the public-source validation check of the system findings, see
`docs/PHARM_EXTERNAL_VALIDATION_REPORT.md`.

## What To Send

Send a short result packet, not the whole codebase:

1. The PHARM finding: top ranked drug/disease pair, score, grounding, and hidden-label protocol.
2. The evidence path PRONOIA used.
3. The benchmark caveat: direct treatment labels were hidden; label-negative means absent from the local benchmark label table, not clinically false.
4. The ask: "Would this be useful as an independent graph-based curation or hypothesis screen for your work?"

Example packet:

```text
PRONOIA PHARM result
Protocol: remove_direct_labels
Pair: Sotorasib -> Pancreatic_Cancer
Score: 97.0
Grounding: 0.783
Evidence: Sotorasib inhibits KRAS; KRAS driver_of Pancreatic_Cancer
Interpretation: high-signal mechanism-backed pair absent from local PHARM treats-label set.
```

## Highest-Priority Leads

These are the best matches because their active or recent work directly overlaps
PRONOIA's highest-signal label-negative findings.

| Priority | PHARM finding | Lead / group | Why they may care | Source |
|---:|---|---|---|---|
| 1 | Sotorasib -> Pancreatic_Cancer | Devalingam Mahalingam / NCI-Hoosier pancreatic sotorasib+chemotherapy trial | PRONOIA surfaced the exact KRAS G12C pancreatic mechanism; this trial explicitly studies sotorasib plus chemotherapy and tumor biomarkers in KRAS G12C pancreatic cancer. | [NCI-2022-06901](https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2022-06901) |
| 2 | Sotorasib -> Pancreatic_Cancer | John H. Strickler, David S. Hong, and CodeBreaK pancreatic investigators | Their NEJM/PMC study evaluated sotorasib in KRAS p.G12C advanced pancreatic cancer; PRONOIA independently ranks the same mechanism highly with direct labels hidden. | [PMC sotorasib pancreatic](https://pmc.ncbi.nlm.nih.gov/articles/PMC10506456/) |
| 3 | Adagrasib -> Pancreatic_Cancer | Dan Zhao / MD Anderson NCT05634525; Kimberly Perez / Dana-Farber site | The local benchmark did not mark this pair positive, but active/recent clinical work has directly tested adagrasib in KRAS G12C metastatic pancreatic cancer. | [ClinicalTrials NCT05634525](https://clinicaltrials.gov/study/NCT05634525), [Dana-Farber 23-630](https://www.dana-farber.org/clinical-trials/23-630) |
| 4 | Adagrasib -> Colorectal_Cancer | Rona Yaeger / MSK; Tanios Bekaii-Saab; KRYSTAL-1 CRC investigators | PRONOIA surfaced adagrasib+CRC as high mechanism support; KRYSTAL-1 and FDA approval show this is a likely label-set curation issue in the local PHARM benchmark. | [PMC adagrasib+cetuximab CRC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9908297/), [FDA approval](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-adagrasib-cetuximab-kras-g12c-mutated-colorectal-cancer) |
| 5 | Sotorasib -> Colorectal_Cancer | Marwan Fakih and CodeBreaK 300 investigators | PRONOIA surfaced sotorasib+CRC; CodeBreaK 300 tested sotorasib plus panitumumab in KRAS G12C refractory CRC. This is a strong validation/curation lead. | [NEJM CodeBreaK 300](https://www.nejm.org/doi/full/10.1056/NEJMoa2308795), [PMC CodeBreaK OS](https://pmc.ncbi.nlm.nih.gov/articles/PMC12199804/) |
| 6 | Adagrasib -> Colorectal_Cancer | Christine Parseghian / MD Anderson trial NCT06412198 | Recruiting trial combines adagrasib, cetuximab, and cemiplimab for metastatic CRC with KRAS G12C mutations; PRONOIA's top CRC mechanism is directly relevant. | [NCI-2024-04127](https://www.cancer.gov/about-cancer/treatment/clinical-trials/search/v?id=NCI-2024-04127), [ClinicalTrials NCT06412198](https://clinicaltrials.gov/study/NCT06412198) |
| 7 | Trastuzumab_deruxtecan -> Breast_Cancer | Shanu Modi / MSK DESTINY-Breast04 HER2-low work | PRONOIA flagged T-DXd -> Breast_Cancer as high-signal but label-negative; external work makes this look like a local benchmark curation issue. | [PMC DESTINY-Breast04](https://pmc.ncbi.nlm.nih.gov/articles/PMC10561652/), [MSK release](https://www.mskcc.org/news-releases/asco-2022-practice-changing-findings-identify-her2-low-targetable-subset-breast-cancer-redefining-treatment-more-60-percent-her2-negative-metastatic-breast-cancer-patients) |
| 8 | Trastuzumab_deruxtecan -> Breast_Cancer | Nancy Lin / Dana-Farber DESTINY-Breast12 | T-DXd breast cancer with brain metastasis is directly active in her trial area; PRONOIA's graph support may be useful as curation evidence and mechanism trace. | [Dana-Farber DESTINY-Breast12](https://www.dana-farber.org/clinical-trials/22-067) |
| 9 | Lorlatinib -> NSCLC | Alice Shaw / early ALK-ROS1 lorlatinib; Benjamin Solomon / CROWN | PRONOIA flagged lorlatinib -> NSCLC via ALK/ROS1 driver paths; this maps directly to lorlatinib ALK/ROS1 NSCLC research. | [PMC lorlatinib phase 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC5777233/), [NCI CROWN summary](https://www.cancer.gov/news-events/cancer-currents-blog/2024/lorlatinib-alk-positive-lung-cancer-initial-treatment) |
| 10 | Brigatinib -> NSCLC | D. Ross Camidge / ALTA-1L; Scott Gettinger / ALTA | PRONOIA flagged brigatinib -> NSCLC through ALK; this overlaps directly with ALTA/ALTA-1L brigatinib ALK+ NSCLC work. | [PMC ALTA-1L](https://pmc.ncbi.nlm.nih.gov/articles/PMC7605398/), [PMC ALTA final](https://pmc.ncbi.nlm.nih.gov/articles/PMC9440305/) |

## Additional Leads

These are still plausible, but they are less immediate than the top group because
the PHARM result is either older, broader, or needs more indication context.

| PHARM finding / theme | Lead / group | Why it may matter | Source |
|---|---|---|---|
| KRAS G12C pancreatic landscape | MSK + AACR Project GENIE pancreatic KRAS G12C landscape researchers | Their work characterizes clinicogenomic outcomes in KRAS G12C pancreatic cancer; PRONOIA provides an independent graph ranking lens. | [JNCI KRAS G12C pancreatic landscape](https://academic.oup.com/jnci/article/116/9/1429/7664169) |
| KRAS inhibitor resistance | Piro Lito Lab / MSK | Lab focuses on RAS signaling and resistance to KRAS G12C inhibition; PRONOIA's next v3 contradiction/residual penalty could be relevant. | [Piro Lito Lab](https://www.mskcc.org/research-areas/labs/piro-lito) |
| Broad KRAS patient/research translation | KRAS Kickers | Patient-led KRAS research advocacy group; may care about a readable list of KRAS G12C pancreatic/CRC/NSCLC trial-relevant signals. | [KRAS Kickers](https://www.kraskickers.org/) |
| Pancreatic trial matching / patient services | PanCAN Patient Services / PanCAN targeted therapy program | PanCAN explicitly points patients to personalized targeted-therapy clinical trial searches; PRONOIA's KRAS G12C pancreatic candidates match this need. | [PanCAN targeted therapy](https://pancan.org/facing-pancreatic-cancer/treatment/treatment-types/targeted-therapy/), [PanCAN contact HCP](https://pancan.org/for-healthcare-professionals/contact-us/) |
| Sotorasib + T-DXd / ERBB2 biology in KRAS NSCLC | Andreas Saltos / NCI-2025-03809 | Trial studies sotorasib + trastuzumab deruxtecan in KRAS G12C NSCLC and specifically measures ERBB2/ERBB3 expression. This connects the KRAS and ERBB2 graph signals. | [NCI-2025-03809](https://www.cancer.gov/clinicaltrials/NCI-2025-03809) |
| T-DXd HER2-positive / HER2-low breast | Javier Cortes / DESTINY-Breast03; Ian Krop / TBCRC | PRONOIA's T-DXd breast signal is not novel clinically, but it is a strong curation/validation case for the graph engine. | [PubMed DESTINY-Breast03](https://pubmed.ncbi.nlm.nih.gov/36495879/), [BCRF Ian Krop](https://www.bcrf.org/researchers/ian-krop/) |
| Afatinib -> Breast_Cancer | LUX-Breast / HER2-targeted breast investigators | PRONOIA flagged ERBB2-mediated support; past afatinib breast work can help validate whether this is weak support or outdated signal. | [PMC LUX-Breast 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC8960620/) |
| Cetuximab -> NSCLC | EGFR NSCLC combination investigators | PHARM sees EGFR mechanism support, but this is exactly where indication/resistance context matters; useful for v3 false-positive calibration. | [Dana-Farber cetuximab NSCLC trial](https://www.dana-farber.org/clinical-trials/06-026), [SWOG S1403 PubMed](https://pubmed.ncbi.nlm.nih.gov/33021871/) |
| Lapatinib -> NSCLC | EGFR/HER2 NSCLC biomarker investigators | Older lapatinib NSCLC studies are useful negative/weak-positive calibration for PRONOIA's mechanism-only overreach problem. | [PubMed lapatinib NSCLC](https://pubmed.ncbi.nlm.nih.gov/20215545/) |

## Practical Outreach Order

1. Start with the curation/validation cases, not speculative repurposing:

```text
Trastuzumab_deruxtecan -> Breast_Cancer
Lorlatinib -> NSCLC
Brigatinib -> NSCLC
Adagrasib -> Colorectal_Cancer
Sotorasib -> Colorectal_Cancer
```

These are easiest to explain because external research already supports them.
The ask is: "Our benchmark label table missed/underrepresented these; does this
graph trace help as a curation or validation artifact?"

2. Then send the hypothesis/review cases:

```text
Adagrasib -> Pancreatic_Cancer
Sotorasib -> Pancreatic_Cancer
Adagrasib -> Colorectal_Cancer
Sotorasib -> Colorectal_Cancer
```

These matter because people are actively working on KRAS G12C in pancreatic and
CRC settings. The ask is not "is this a treatment?" The ask is: "Does this
ranked mechanism trace match what your trial biology expects, and what
contradiction/resistance context should PRONOIA penalize next?"

3. Use the weaker/older findings as calibration cases:

```text
Afatinib -> Breast_Cancer
Cetuximab -> NSCLC
Lapatinib -> NSCLC
```

These are useful for hardening PRONOIA v3 because they test whether the system
can distinguish target presence from actionable clinical indication.

## Short Message Template

```text
Subject: Independent graph finding matching your KRAS/HER2/ALK work

I am validating a non-LLM graph prediction engine against a local PHARM
drug-disease benchmark. In a blinded setting where direct treatment labels were
removed, it surfaced [PAIR] with this evidence path:

[DRUG] -> [TARGET] -> [DISEASE]

This is not a clinical recommendation. I am looking for expert review of whether
the graph trace is useful as a curation signal, a hypothesis screen, or a
negative-control case for the next scoring layer.

Would a one-page findings packet be useful for your team?
```

## Bottom Line

There are real leads. The most credible route is not pitching "PRONOIA" first.
It is sending a concise PHARM findings packet to researchers already working on:

- KRAS G12C pancreatic cancer
- KRAS G12C colorectal cancer
- HER2/T-DXd breast cancer
- ALK/ROS1 NSCLC
- KRAS/ERBB resistance mechanisms

The best immediate angle is curation and independent validation, not claims of
new clinical discovery.
