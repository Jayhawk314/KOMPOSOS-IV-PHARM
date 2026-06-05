# PHARM Lead Audit Trail Supplement

Date: 2026-06-05

This supplements `docs/PHARM_RESEARCH_LEADS.md`.

This document uses the system's own audit trail:

- PRONOIA `PredictionReport` score, grounding, raw MDL gain, and evidence count.
- PRONOIA evidence packet paths from `KompososPharmEvidenceProvider`.
- PHARM database morphism provenance from
  `C:\Users\JAMES\github\KOMPOSOS-IV-PHARM\data\drugs\tier1.db`.

No outside web search is used for the audit trail below. The local PHARM database
contains PMID/FDA/mechanism provenance on the raw morphism rows. It did not
contain figure-level metadata for the morphism rows inspected here.

## How To Read The Trail

All lead candidates below were scored under:

```text
protocol = remove_direct_labels
quality = all
min_grounding = 0.2
```

The direct Drug->Disease treatment labels were hidden from PRONOIA. The system
therefore reached each conclusion from mechanism/path evidence, usually:

```text
Drug -[inhibits]-> Target
Target -[driver_of or associated_with]-> Disease
```

PHARM score v2 is:

```text
score = 100 * max(mechanism_strength, non_direct_path_strength)
        - grounding_penalty
        - contradiction_penalty
```

For all pairs below, grounding cleared the 0.2 gate. The contradiction penalty is
currently a placeholder at zero. Raw MDL gain is recorded for audit, but it is
not the primary PHARM score.

## Highest-Priority Lead Audit Trails

### 1. Devalingam Mahalingam / NCI-Hoosier Trial

The relevant PRONOIA candidate is `Sotorasib -> Pancreatic_Cancer`. PRONOIA
scored it `97.0` with grounding `0.783`, raw MDL gain `64.0` bits, and `9`
evidence items. The score came from a top mechanism item:
`Sotorasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Pancreatic_Cancer`.
The mechanism strength is `sqrt(0.97 * 0.97) = 0.970`, and the matching path
score is `0.9409` for
`inhibits:Sotorasib->KRAS; driver_of:KRAS->Pancreatic_Cancer`. PHARM provenance
for `Sotorasib -> KRAS` is `FDA:NDA214665, mechanism:KRAS_G12C_inhibitor;
PMID:42144204; [RELATION-VERIFIED]`. PHARM provenance for
`KRAS -> Pancreatic_Cancer` is `PMID:42092950; [RELATION-VERIFIED]`. The audit
conclusion is that the system did not infer this from a treatment label; it
reconstructed the candidate from a high-confidence KRAS G12C inhibition edge and
a high-confidence KRAS pancreatic cancer driver edge.

### 2. John H. Strickler / David S. Hong / CodeBreaK Pancreatic Work

The same system audit trail applies to `Sotorasib -> Pancreatic_Cancer`: score
`97.0`, grounding `0.783`, raw MDL gain `64.0` bits, and `9` evidence items.
The strongest evidence is the two-edge mechanism
`Sotorasib inhibits KRAS; KRAS driver_of Pancreatic_Cancer`, with mechanism
strength `0.970` and direct path-search strength `0.9409`. The local PHARM
provenance attached to those morphisms is `FDA:NDA214665,
mechanism:KRAS_G12C_inhibitor; PMID:42144204; [RELATION-VERIFIED]` and
`PMID:42092950; [RELATION-VERIFIED]`. This lead is interested because the
system independently ranks the same pancreatic KRAS G12C axis as one of its top
hidden-label findings.

### 3. Dan Zhao / MD Anderson And Kimberly Perez / Dana-Farber

The relevant PRONOIA candidate is `Adagrasib -> Pancreatic_Cancer`. PRONOIA
scored it `97.0` with grounding `0.783`, raw MDL gain `80.0` bits, and `9`
evidence items. The top mechanism item is
`Adagrasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Pancreatic_Cancer`.
The mechanism strength is `sqrt(0.97 * 0.97) = 0.970`, while the matching
two-edge path has score `0.9409`. PHARM provenance for `Adagrasib -> KRAS` is
`FDA:NDA216340, mechanism:KRAS_G12C_inhibitor; PMID:42122163;
[RELATION-VERIFIED]`. PHARM provenance for `KRAS -> Pancreatic_Cancer` is
`PMID:42092950; [RELATION-VERIFIED]`. The audit conclusion is that PRONOIA
surfaced adagrasib pancreatic cancer by the same KRAS G12C driver route as
sotorasib, with equally strong local graph confidence.

### 4. Rona Yaeger / Tanios Bekaii-Saab / KRYSTAL CRC Work

The relevant PRONOIA candidate is `Adagrasib -> Colorectal_Cancer`. PRONOIA
scored it `93.4345` with grounding `0.741`, raw MDL gain `88.0` bits, and `9`
evidence items. The top mechanism item is
`Adagrasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Colorectal_Cancer`.
The mechanism strength is `sqrt(0.97 * 0.90) = 0.9343446901`, and the matching
path score is `0.873`. Additional paths go through KRAS->BRAF and KRAS->TP53:
`Adagrasib -> KRAS -> BRAF -> Colorectal_Cancer` scored `0.705675`, and
`Adagrasib -> KRAS -> TP53 -> Colorectal_Cancer` scored `0.699952`. PHARM
provenance for `Adagrasib -> KRAS` is `FDA:NDA216340,
mechanism:KRAS_G12C_inhibitor; PMID:42122163; [RELATION-VERIFIED]`.
Provenance for `KRAS -> Colorectal_Cancer` is `PMID:18316791`. BRAF and TP53
support edges include `PMID:42200009; [RELATION-VERIFIED]` and `PMID:36768460`.
The audit conclusion is that the system ranks this label-negative pair because
multiple local paths converge on KRAS-driven colorectal cancer biology, not
because of a visible treatment edge.

### 5. Marwan Fakih / CodeBreaK 300 CRC Work

The relevant PRONOIA candidate is `Sotorasib -> Colorectal_Cancer`. PRONOIA
scored it `93.4345` with grounding `0.741`, raw MDL gain `80.0` bits, and `9`
evidence items. The primary mechanism is
`Sotorasib -[inhibits]-> KRAS; KRAS -[driver_of]-> Colorectal_Cancer`, with
mechanism strength `sqrt(0.97 * 0.90) = 0.9343446901` and matching path score
`0.873`. Secondary paths include `Sotorasib -> KRAS -> BRAF ->
Colorectal_Cancer` at `0.705675` and `Sotorasib -> KRAS -> TP53 ->
Colorectal_Cancer` at `0.699952`. PHARM provenance for `Sotorasib -> KRAS` is
`FDA:NDA214665, mechanism:KRAS_G12C_inhibitor; PMID:42144204;
[RELATION-VERIFIED]`; provenance for `KRAS -> Colorectal_Cancer` is
`PMID:18316791`. The audit conclusion is that PRONOIA surfaced the CRC pair from
the same KRAS driver edge family that explains the pancreatic finding, with
slightly lower disease-driver confidence than pancreatic cancer.

### 6. Christine Parseghian / MD Anderson CRC Trial

The relevant PRONOIA candidate is again `Adagrasib -> Colorectal_Cancer`. The
audit trail is score `93.4345`, grounding `0.741`, raw MDL gain `88.0` bits, and
`9` evidence items. The score is dominated by the two-edge path
`Adagrasib inhibits KRAS; KRAS driver_of Colorectal_Cancer`, with mechanism
strength `0.9343446901` and path strength `0.873`. PHARM provenance is
`FDA:NDA216340, mechanism:KRAS_G12C_inhibitor; PMID:42122163;
[RELATION-VERIFIED]` for the drug-target edge and `PMID:18316791` for the
KRAS-colorectal driver edge. The reason this is a separate lead is not a
different computation; it is that this same audit packet is specifically useful
for a colorectal KRAS G12C trial context.

### 7. Shanu Modi / MSK DESTINY-Breast Work

The relevant PRONOIA candidate is
`Trastuzumab_deruxtecan -> Breast_Cancer`. PRONOIA scored it `96.4883` with
grounding `0.794`, raw MDL gain `128.0` bits, and `7` evidence items. The top
mechanism item is `Trastuzumab_deruxtecan -[inhibits]-> ERBB2; ERBB2
-[driver_of]-> Breast_Cancer`. The mechanism strength is
`sqrt(0.98 * 0.95) = 0.9648834126`, and the matching path score is `0.931`.
Secondary paths connect ERBB2 through KRAS/TP53, KRAS/BRAF, and KRAS/RAF1 into
breast cancer-associated nodes. PHARM provenance for
`Trastuzumab_deruxtecan -> ERBB2` is `FDA:BLA761139, mechanism:HER2_ADC`;
provenance for `ERBB2 -> Breast_Cancer` is `PMID:41554087;
[RELATION-VERIFIED]`. The audit conclusion is that the local benchmark marked
this pair label-negative, but PRONOIA found a direct, high-confidence HER2/ERBB2
driver trail that makes it a strong curation-review candidate.

### 8. Nancy Lin / Dana-Farber DESTINY-Breast12

The relevant PRONOIA candidate is also
`Trastuzumab_deruxtecan -> Breast_Cancer`. The audit trail is score `96.4883`,
grounding `0.794`, raw MDL gain `128.0` bits, and `7` evidence items. The score
comes from the ERBB2 mechanism:
`Trastuzumab_deruxtecan inhibits ERBB2; ERBB2 driver_of Breast_Cancer`, with
mechanism strength `0.9648834126` and path strength `0.931`. The PHARM database
provenance is `FDA:BLA761139, mechanism:HER2_ADC` for the T-DXd->ERBB2 edge and
`PMID:41554087; [RELATION-VERIFIED]` for the ERBB2->Breast_Cancer edge. This is
mainly a curation/validation lead: the system's local graph trail strongly
supports a pair that should be reviewed against the benchmark label table.

### 9. Alice Shaw / Benjamin Solomon / Lorlatinib ALK-ROS1 NSCLC Work

The relevant PRONOIA candidate is `Lorlatinib -> NSCLC`. PRONOIA scored it
`95.4358` with grounding `0.562`, raw MDL gain `32.0` bits, and `4` evidence
items. The primary mechanism is `Lorlatinib -[inhibits]-> ALK; ALK
-[driver_of]-> NSCLC`, with strength `sqrt(0.99 * 0.92) = 0.9543584232` and
path score `0.9108`. A second independent mechanism is
`Lorlatinib -[inhibits]-> ROS1; ROS1 -[driver_of]-> NSCLC`, with strength
`sqrt(0.95 * 0.85) = 0.8986100378` and path score `0.8075`. PHARM provenance is
`FDA:NDA210868, mechanism:3rd_gen_ALK_TKI; PMID:42170281;
[RELATION-VERIFIED]` for Lorlatinib->ALK, `PMID:42187575;
[LEXICAL-COOCCURRENCE]` for ALK->NSCLC, `FDA:NDA210868,
mechanism:ALK_ROS1_TKI; PMID:41704605; [RELATION-VERIFIED]` for
Lorlatinib->ROS1, and `PMID:42075590; [RELATION-VERIFIED]` for ROS1->NSCLC.
The audit conclusion is that PRONOIA did not rely on one fragile edge; it found
two convergent ALK/ROS1 NSCLC routes.

### 10. D. Ross Camidge / Scott Gettinger / Brigatinib ALK NSCLC Work

The relevant PRONOIA candidate is `Brigatinib -> NSCLC`. PRONOIA scored it
`94.9526` with grounding `0.562`, raw MDL gain `32.0` bits, and `10` evidence
items. The primary mechanism is `Brigatinib -[inhibits]-> ALK; ALK
-[driver_of]-> NSCLC`, with strength `sqrt(0.98 * 0.92) = 0.9495261976` and
path score `0.9016`. A secondary route is `Brigatinib -[inhibits]-> EGFR; EGFR
-[driver_of]-> NSCLC`, with mechanism strength `sqrt(0.75 * 0.95) =
0.8440971508` and path score `0.7125`; another path runs
`Brigatinib -> EGFR -> KRAS -> NSCLC` at `0.6270`. PHARM provenance is
`FDA:NDA208772, mechanism:ALK_TKI; PMID:42136297; [RELATION-VERIFIED]` for
Brigatinib->ALK, `PMID:42187575; [LEXICAL-COOCCURRENCE]` for ALK->NSCLC,
`FDA:NDA208772, mechanism:ALK_EGFR_TKI; PMID:41611070;
[LEXICAL-COOCCURRENCE]` for Brigatinib->EGFR, and `PMID:42182703;
[LEXICAL-COOCCURRENCE]` for EGFR->NSCLC. The audit conclusion is that the ALK
route is strong enough to explain the high score, while the EGFR route should be
treated as supporting but less clean because some provenance is lexical.

## Additional Calibration Lead Audit Trails

### KRAS G12C Landscape, Resistance, Advocacy, And Pancreatic Trial-Matching Leads

The relevant packet for these groups is not one candidate but the repeated KRAS
G12C pattern. PRONOIA ranked four label-negative KRAS findings highly:
`Sotorasib -> Pancreatic_Cancer` at `97.0`, `Adagrasib ->
Pancreatic_Cancer` at `97.0`, `Sotorasib -> Colorectal_Cancer` at `93.4345`,
and `Adagrasib -> Colorectal_Cancer` at `93.4345`. In all four cases the audit
trail is the same shape: a high-confidence `inhibits` edge from the drug to KRAS
plus a disease driver edge from KRAS into pancreatic or colorectal cancer. The
PHARM provenance includes `PMID:42144204` for Sotorasib->KRAS,
`PMID:42122163` for Adagrasib->KRAS, `PMID:42092950` for
KRAS->Pancreatic_Cancer, and `PMID:18316791` for KRAS->Colorectal_Cancer. This
is the strongest system-generated package for KRAS researchers because it shows
the same mechanism emerging across two drugs and two diseases with direct
treatment labels hidden.

### Andreas Saltos / Sotorasib Plus T-DXd KRAS-ERBB Biology Lead

This is a weaker, cross-axis lead rather than a direct combination candidate.
PRONOIA did not score a `Sotorasib + Trastuzumab_deruxtecan` combination
candidate. What the system did show is that separate high-scoring axes exist in
the same PHARM graph: KRAS G12C inhibitor paths such as `Sotorasib -> KRAS ->
Pancreatic_Cancer/Colorectal_Cancer/NSCLC`, and ERBB2/HER2 ADC paths such as
`Trastuzumab_deruxtecan -> ERBB2 -> Breast_Cancer`. The local audit evidence
includes Sotorasib->KRAS provenance `FDA:NDA214665,
mechanism:KRAS_G12C_inhibitor; PMID:42144204; [RELATION-VERIFIED]`,
KRAS->NSCLC provenance `PMID:42075590; [RELATION-VERIFIED]`,
T-DXd->ERBB2 provenance `FDA:BLA761139, mechanism:HER2_ADC`, and
ERBB2->Breast_Cancer provenance `PMID:41554087; [RELATION-VERIFIED]`. This
should be presented as a graph-axis observation, not as a scored combination
prediction.

### Javier Cortes / Ian Krop / Additional T-DXd Breast Validation Leads

The relevant candidate is `Trastuzumab_deruxtecan -> Breast_Cancer`, with score
`96.4883`, grounding `0.794`, raw MDL gain `128.0` bits, and `7` evidence
items. The audit trail is the high-confidence HER2/ERBB2 route:
`Trastuzumab_deruxtecan inhibits ERBB2; ERBB2 driver_of Breast_Cancer`.
The mechanism score is `0.9648834126`; the path score is `0.931`. PHARM
provenance is `FDA:BLA761139, mechanism:HER2_ADC` and `PMID:41554087;
[RELATION-VERIFIED]`. This is not framed as a new discovery; it is a strong
validation and benchmark-curation case because the local label table treated the
pair as label-negative while the mechanism trail is direct.

### Afatinib -> Breast_Cancer Calibration Lead

PRONOIA scored `Afatinib -> Breast_Cancer` at `95.0` with grounding `0.700`,
raw MDL gain `56.0` bits, and `10` evidence items. The strongest mechanism is
`Afatinib -[inhibits]-> ERBB2; ERBB2 -[driver_of]-> Breast_Cancer`, with score
`sqrt(0.95 * 0.95) = 0.950` and path score `0.9025`. A secondary route is
`Afatinib -[inhibits]-> EGFR; EGFR -[associated_with]-> Breast_Cancer`, with
mechanism score `0.8809086218` and path score `0.776`. PHARM provenance is
`FDA:NDA201292, mechanism:pan-HER_TKI; PMID:40612504; [RELATION-VERIFIED]` for
Afatinib->ERBB2, `PMID:41554087; [RELATION-VERIFIED]` for
ERBB2->Breast_Cancer, `FDA:NDA201292, mechanism:irreversible_EGFR_TKI;
PMID:42151084; [RELATION-VERIFIED]` for Afatinib->EGFR, and
`ABPP; PMID:16618952` for EGFR->Breast_Cancer. This is a useful calibration case
because the graph mechanism is strong, but indication-specific context may still
make it a false positive or weak repurposing claim.

### Cetuximab -> NSCLC Calibration Lead

PRONOIA scored `Cetuximab -> NSCLC` at `95.0` with grounding `0.533`, raw MDL
gain `32.0` bits, and `9` evidence items. The top mechanism is
`Cetuximab -[inhibits]-> EGFR; EGFR -[driver_of]-> NSCLC`, with mechanism
strength `sqrt(0.95 * 0.95) = 0.950` and path strength `0.9025`. Additional
paths route through `EGFR -> KRAS -> NSCLC` at `0.7942` and
`EGFR -> KRAS -> TP53 -> NSCLC` at `0.666045`. PHARM provenance is
`PMID:15269313` for Cetuximab->EGFR, `PMID:42182703; [LEXICAL-COOCCURRENCE]`
for EGFR->NSCLC, `PMID:42075590; [RELATION-VERIFIED]` for KRAS->NSCLC, and
`PMID:37683526` for TP53->NSCLC. This is a valuable negative-control style lead:
the system sees real EGFR/NSCLC graph support, but v3 should learn when target
presence is not enough for an actionable indication.

### Lapatinib -> NSCLC Calibration Lead

PRONOIA scored `Lapatinib -> NSCLC` at `94.4987` with grounding `0.533`, raw
MDL gain `24.0` bits, and `10` evidence items. The top mechanism is
`Lapatinib -[inhibits]-> EGFR; EGFR -[driver_of]-> NSCLC`, with mechanism
strength `sqrt(0.94 * 0.95) = 0.9449867724` and path score `0.893`. A secondary
mechanism is `Lapatinib -[inhibits]-> ERBB2; ERBB2 -[associated_with]-> NSCLC`,
with mechanism strength `0.8625543461` and path score `0.744`. PHARM provenance
is `FDA:NDA022059, mechanism:dual_EGFR_HER2_TKI; PMID:42089475;
[RELATION-VERIFIED]` for Lapatinib->EGFR, `PMID:42182703;
[LEXICAL-COOCCURRENCE]` for EGFR->NSCLC, `FDA:NDA022059,
mechanism:dual_EGFR_HER2_TKI` for Lapatinib->ERBB2, and `ABPP; PMID:41982617;
[RELATION-VERIFIED]` for ERBB2->NSCLC. This should be used as a v3 calibration
case, because it exposes the current scorer's tendency to reward plausible
EGFR/ERBB2 biology before checking indication-specific clinical fit.

## System Improvement Applied

The raw PHARM database contains useful morphism provenance, including PMID/FDA
strings and evidence tags. The PRONOIA PHARM adapter now carries that provenance
forward into `EvidenceItem.metadata` when the local KOMPOSOS-IV-PHARM SQLite
database is available.

Each enriched morphism now includes:

```text
raw morphism id
PMID/FDA provenance
evidence_tier
confidence interval fields
quantitative fields
parsed PMID list
raw_morphism record
```

Mechanism items carry the enriched first/second morphism records. Path items
carry enriched records for each `morphism_id`, plus path-level `pmids`,
`provenance`, and `evidence_tiers`. Future lead packets can now be generated
from the `PredictionReport` evidence packet without a separate manual SQLite
join.
