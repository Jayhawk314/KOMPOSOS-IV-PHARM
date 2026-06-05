# KOMPOSOS-IV-PHARM — video scripts (talking points)

**How to use:** talking points, not a teleprompter. The slide is your outline;
advance one click per point and say it in your own words.

### Numbers you can say (verified, leak-corrected — always name the protocol)
- Strict: **`full_typed / remove_direct_labels` → AUROC 0.949** [0.91–0.97], Hits@5 = 1.00.
- **LOOCV 0.976**; temporal holdout (approvals >2013) **0.978**; disease-level holdout mean **0.950**.
- Strongest baseline ~**0.63** → the system is **+0.34** over baseline on the same graph.
- Graph: 78 drugs, 20 diseases, 366 biological entities, **44** FDA approved positives (all with Drug→Protein→Disease paths).
- Provenance: **594 relation-verified**, 215 co-occurrence-only.

### Never say
- ❌ The retired **0.969** AUROC — it had label leakage; only the corrected **0.949** is current.
- ❌ Any AUROC **without naming the view + protocol** (it changes the number).
- ❌ "Track B / drug design works" — it's a goal, not validated. Don't borrow Track A's number for it.
- ❌ "clinically validated" / "treats" — it's a **research prototype**; candidates are leads to investigate, not recommendations.

### Always say
- It's a **research prototype, not clinical validation.** Unlabeled pairs are *unknown*, not negative. Provenance *presence ≠ verification*.

---

## VIDEO 1 — What it is  ·  deck `how_it_works_deck.html`
- **Hook:** repurposing an *approved* drug skips years of safety work — if you can find the match and explain *why*.
- **One job:** rank existing drugs for a disease, each with a mechanism.
- **Core idea:** drugs/proteins/diseases are objects; known facts are arrows ("drug inhibits protein," "protein drives disease"); compose Drug→Protein→Disease to derive a candidate with its mechanism attached. Yoneda/Rezk find drug look-alikes (MEK, BRAF, platinum classes).
- **Run it:** the triage command — rank drugs for a disease, see the evidence chain.

## VIDEO 2 — Does it work, honestly  ·  deck `how_it_works_deck.html` (results + honesty slides)
- **The number, with the protocol named:** strict leak-controlled AUROC 0.949, Hits@5 1.00; LOOCV 0.976. Beating a 0.63 baseline by 0.34 on the same graph is the real signal.
- **The honesty story (this is the good part):** I *caught myself* — an earlier 0.969 looked great but had label leakage; I isolated the folds and it dropped to 0.949. That's the honest number. Show the catch, not just the result.
- **The limits, plainly:** small curated graph (78/20/44); external Hetionet is weaker (0.63); provenance is tiered (verified vs co-occurrence); research prototype, not clinical.
- **What you get:** ranked candidates + Drug→Protein→Disease evidence chain + ClinicalTrials.gov cross-check (~63% already in trials, 7% novel).

## VIDEO 3 — The math (shared kernel)  ·  reuse `../../KOMPOSOS-IV-CHEM/YOUTUBE/math_visuals.html`
- Same engine as the chemistry side — just relabel the objects: **objects = drugs/proteins/diseases**, **arrows = interactions**.
- Composition (Drug→Protein→Disease), Yoneda (a drug known by its relationships), Yoneda distance (similar target profiles), Rezk (interchangeable drug classes), typed morphisms, the dual-engine check.
- Point viewers to the chem math deck and say "same math, different domain — that's the whole idea."

## VIDEO 4 *(optional)* — Limits & how to check it yourself
- Validated vs not (the honesty slide). The reproduce command. Repo link. "Open it, break it, tell me where I'm wrong."

---
*Tone: explain it like you're showing a colleague. The leak-catch story is your most credible moment — lead with the honesty, not the hype.*
