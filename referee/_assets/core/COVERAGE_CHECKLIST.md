# Coverage Checklist: What Experienced Referees Check

Use as a prompt for your own thinking, not a list to paste. For each item decide: applies / does not apply / cannot tell. Raise a concern only if it applies AND you can anchor it to an exact quote or a clearly absent element. Origin: recurring requests in a published Nature-family review file (a methods/systems paper), plus standard methodological practice. It has been checked against one paper only; extend it with experience.

## Any empirical paper
- **Sample and uncertainty:** is n large enough for the claim? Intervals or tests reported? One run reported for a stochastic process?
- **Survivorship:** are failures, exclusions and dropped items counted (attempted vs retained)?
- **Train/test overlap:** was the system built or tuned on the same material it is tested on? Are "new" test cases truly different in kind, or parameter variations?
- **Baselines:** strongest current baseline? Given equal information and effort? Stale model or version?
- **Ground truth:** how was it set, by whom, how many raters, what agreement, what rubric?
- **Claims vs evidence:** "discovered/identified" vs "prioritised hypothesis"; "validated" vs secondary analysis of existing data; any human choice hidden inside "autonomous" results?
- **Generality:** one domain, one tool, one model, one dataset? Say what is untested.
- **Failure modes:** out-of-scope, ambiguous or adversarial inputs; how often does it wrongly claim capability? Error rate stated near the headline result?
- **Cost and maintenance:** time, money, hardware, who keeps it working as dependencies change?

## Systems, software and AI-method papers (also)
- **Ablations:** is each component shown to matter? Is a simpler alternative (a monolith, a plain document, a script) compared fairly?
- **Closest existing systems:** named, compared in a table, difference stated (use retrieval; do not rely on memory).
- **Inherited errors:** if built on prior code or data, do their bugs propagate? Can validation detect them or only confirm consistency with them?
- **Adaptation:** does it adjust parameters to the data, or follow a fixed template that happens to work on the tested cases? Can it train as well as run?
- **Security and misuse:** threat model, data and credential handling, malicious inputs, attribution and IP.
- **Reproducibility of the system itself:** key algorithms in the paper (pseudocode), not only in a repository; versioned release; what cannot be frozen.
- **Definitions:** what exactly counts as a pass, a novel query, a success?

## Clinical, epidemiological and social-science papers (also)
- Confounding and identification strategy; pre-registration; multiple comparisons; missing data; measurement validity; selection and generalisability; effect sizes with intervals; reporting-guideline adherence (CONSORT, STROBE, PRISMA).

## Presentation
- Abstract matches the evidence; figures legible with stated units, n and error bars; inputs and outputs of each pipeline step clear; code and data availability stated.
