# Defect Hunt: How to Find What Is Actually Wrong

A limitation ("sample is small") is not a defect. A defect is a mechanism by which the reported result could appear WITHOUT the claim being true. For every central claim, trace: **claim -> figure/table -> analysis -> code/data -> raw inputs**, and at each link ask how the number was produced and what could distort it. Prefer investigating over interpreting: check whether the analysis computes what the text says before discussing what the result means.

## Method
1. Write the headline number or inference in one line.
2. Find the exact analysis that produces it (methods text, then code if supplied). Read the functions that compute it.
3. Ask, in order: What data does this step see? In what order are alignment, cleaning, normalisation, splitting and fitting done? Is each unit independent? What would the result look like if the claim were false?
4. Where text and code could disagree, say exactly which line or sentence you would check.
5. State the failure mechanism, the consequence for the claim, and the smallest check that would settle it (a reanalysis, an alignment plot, a shuffled-label control, a leave-one-participant-out run).

## Defect classes to check (raise only what applies and can be anchored)
- **Alignment and timing:** lags, offsets or delays estimated once and applied to every participant, session or channel; off-by-one and sign errors; resampling or clock drift; label-to-data misalignment; epoch boundaries; edge effects from shifting or filtering.
- **Leakage:** normalisation, feature selection, imputation or tuning fitted on all data before the train/test split; the same participant, item or time window in both sets; target-derived features; temporal leakage.
- **Circularity (double dipping):** selecting regions, features, thresholds or groups using the same data and outcome later tested.
- **Non-independence:** pseudoreplication (trials or samples treated as participants), clustering by school, site, family or subject ignored, repeated measures analysed as independent.
- **Wrong or unmet test:** assumptions (normality, ceiling or floor effects, equal variance), paired vs unpaired mix-ups, correlations used where the claim is about a difference, significance of one effect treated as a difference between effects.
- **Researcher degrees of freedom:** many analyses or subgroups without correction, thresholds chosen after seeing data, selective exclusions or outcome switching, survivorship (failures not counted).
- **Measurement validity:** the proxy is not the construct, task type differs between conditions (recognition vs production), reliability unknown, ground truth set by one rater.
- **Baselines and controls:** weak, stale or information-starved baselines; missing negative controls; no shuffled or permuted null.
- **Text-code-data mismatch:** the paper describes one pipeline and the code or data show another; numbers in text, tables and figures disagree; sample sizes do not reconcile between sections.
- **Inference beyond data:** causal wording from correlational design, "discovered" for a prioritised hypothesis, generalisation beyond the sampled population.

## Rules for this phase
- Do not stop at the first problem on a claim; look for the one that would change the conclusion most.
- A concern needs an anchor (an exact quote or a clearly absent element) and a mechanism. If you can only say "this could be an issue", find out whether it is.
- Distinguish "not reported" from "reported and wrong". Ask for the information; do not assume failure.
- Do not worry about how many concerns you have found. Selection and budgets come in the next phase.
