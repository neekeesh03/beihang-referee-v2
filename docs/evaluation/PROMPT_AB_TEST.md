# Controlled test of the three discovery prompts (planted defects)

**Question.** The independent validation found v2 weaker than v1 at finding defects and suspected that the extra instructions added to v2's discovery prompt were the cause. Does a controlled run show it?

**Conditions** (the same base prompt `CORE_REVIEWER_PROMPT.md`, plus):
- **A (v1):** nothing else.
- **B (v2 as it was):** + human reviewer voice + stopping rules + decision calibration.
- **C (v3):** + phases + defect hunt + coverage checklist (voice, stopping and decision moved to later phases).

**Method.** Nine blind runs per paper (three per condition, assignment shuffled, file names neutral, the reviewer never told the condition or the existence of planted defects). Each run reads its instruction file and the manuscript and writes a referee report ending with a list of concerns. All runs used the same model (Claude, standard tier). I scored the concern lists against the answer keys in `evals/planted_defects/` before looking at which condition each run belonged to.
Two papers: **easy** (9 planted defects, several announced in the prose) and **subtle** (5 planted defects, in code or numbers, clean prose).

## Results
**Planted-defect recall was 100% in every condition on both papers**, with one exception below: every run found all of the easy paper's defects G1 to G8 and all of the subtle paper's S1 to S5. (For S5 only one run also noticed that the p-value itself is wrong; the others caught the degrees-of-freedom mismatch.) The benchmark is saturated: it cannot separate the conditions on these defects.

| | A (v1) | B (v2 old) | C (v3) |
| --- | --- | --- | --- |
| Easy paper, defects found of 9 (3 runs) | 8, 8, 8 | 8, 8, 8 | 9, 9, 9 |
| Subtle paper, defects found of 5 (3 runs) | 5, 5, 5 | 5, 5, 5 | 5, 5, 5 |
| Concerns listed, easy paper (mean) | 16.3 | 16.3 | 17.0 |
| Concerns listed, subtle paper (mean) | 16.3 | 12.3 | 17.3 |
| Report length in words, subtle paper (mean) | 1,400 | 1,439 | 1,824 |

- The one defect that differed was G9 on the easy paper (no shuffled or surrogate null, and no baseline decoder): found in 3 of 3 runs under C and 0 of 6 under A and B. That is what the defect-hunt and coverage text asks for, so it is expected, but it is the only evidence here that the new discovery guidance finds something the older prompts miss. Three runs per condition is far too few to call it significant.
- B (v2 old) listed fewer concerns than A and C on the subtle paper (12.3 against 16.3 and 17.3), consistent with its brevity and stopping rules reducing breadth. It still found every planted defect, so the lost items were lower-value ones.
- C reports were about 30% longer than A on the subtle paper. The length complaint is not solved by the discovery prompt; in the director route `lint_review` limits length at the writing phase.
- All runs also found a real defect I had not planted: the lag is fitted on the same reaction-time series that defines the lapse labels, before cross-validation (circularity and leakage). Two runs also noticed that my own "clean" power analysis was wrong (r = .4 at 80% power needs roughly 46 people, not 20). That was my mistake in writing the fixture, not a planted defect.

## What this does and does not show
- **Not reproduced:** I could not reproduce a v2 < v1 regression on planted code-level defects, including a participant-lag misalignment. With a strong model, all three prompts find these.
- **Why that is weak evidence:** the papers are synthetic, short (about 900 to 1,100 words) and had few defects, the code was inside the manuscript, and the model is strong. The validated paper was real, long and probably had its code outside the main text. Single-run comparisons also carry noise: one missed defect in one run can happen by chance.
- **Other candidate causes** of the validation difference that this test did not cover: whether the code was in the reviewer's context at all; model or provider differences; run-to-run variance; the pipeline's multi-stage handoffs (not the director route tested here).
- **Not an A/B of the pipeline.** I tested the three discovery prompts directly with a model, not the full `referee review` pipeline.

## Deterministic part (no model)
The new `inspect_code` pointers locate all four code defects in the subtle paper (the wrong participant's lag, the post-stimulus bin, the ungrouped cross-validation, the scaler fitted before the split) and `check_numbers` flags the inconsistent `r(18) = .38, p = .03`. Both are tested in `tests/test_planted_defects.py`. The pointer patterns were written after seeing this fixture, so they may be tuned to it. Across 216 unrelated files (Referee's own code plus 40 numpy modules) the inspector produced 6 pointers in total, so noise is low there, but its recall on real scientific code is unknown.

## Next test that would discriminate
A harder benchmark: long real manuscripts with defects found in published corrections or retractions, code supplied as separate files, and 10 or more runs per condition, scored by a second blinded rater.
