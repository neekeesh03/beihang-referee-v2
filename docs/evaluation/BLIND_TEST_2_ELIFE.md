# Blind test 2: Referee-directed AI review vs. eLife public reviews

**Why this paper.** The first blind test (`BLIND_TEST_PAPER2AGENT.md`) used the same research area as the tool's own topic and a checklist built from that very review file. This test uses a different field, a paper the owner and the tool had never touched, and the coverage checklist as it stood afterwards.

**Paper and ground truth.** Das, Nag and Arun, "Early readers know letter shape without knowing letter names", eLife reviewed preprint v1 (25 Nov 2025; developmental psychology / cognitive neuroscience; a large sample of children). Ground truth: the three public reviews of v1 (Reviewers 1 to 3, eLife, CC BY). The reviewed-preprint page shows the manuscript exactly as submitted, "not revised".

**Method.** Same as test 1. A separate AI agent saw only the manuscript text (no web, no access to the reviews) and reviewed it through `referee.direction`, following the playbook including the coverage checklist. I then mapped its requests to the reviewers' concerns by hand. Outputs: `examples/blind_review_elife_letter_shape.md`.

**Result.**
- Gate: **MAJOR_REVISION**; 8 concerns admitted, 2 downgraded (cap), all 36 quote anchors verified exactly. eLife's own assessment called the evidence "incomplete" and asked for more analyses or revised interpretations, consistent with a major revision. (eLife reviews do not give an accept/reject label, so the outcome match is by that assessment.)
- Of the **12 distinct reviewer concerns: 8 matched clearly, 4 partly, 0 missed.** Strict recall 67%; with partial credit as half, 83%.

| # | Reviewer concern (paraphrased) | Found? |
| --- | --- | --- |
| 1 | Naming (production) vs shape recognition: task-type confound | yes |
| 2 | Independence of shape and name knowledge not supported | yes |
| 3 | Does shape knowledge drive reading? RAN result makes this speculative | yes |
| 4 | Passive exposure never directly tested | yes |
| 5 | Pearson assumptions and ceiling effect; conclusion rests on a non-significant partial correlation | yes |
| 6 | Reading ability not measured; overgeneralised to reading | yes |
| 7 | Limited novelty versus earlier letter-familiarity work | partial (discussed under venue fit, not raised as a request) |
| 8 | Familiarity vs recognition not justified as distinct constructs | partial |
| 9 | Analysis too simple (suggests mixed-effects, latent-variable models) | partial (asked for child- and item-aware intervals and exact model formulas) |
| 10 | Circularity in defining groups from the same performance | partial |
| 11 | Multiple regression mentioned but not fully reported | yes |
| 12 | Many correlations, no multiple-comparison correction | yes |

**Extra concerns the reviewers did not raise.** The AI also asked, for example, whether the single "unpaired signed-rank test" was the right test, and why 285 children took one task but 208 are reported for both. I checked these against the manuscript text: the phrase "unpaired signed-rank test" does appear, and the 285 and 208 figures are both there, so the observations are grounded. Whether they matter scientifically is a question for an expert, so precision is not scored here.

**Offline checks on this paper.** The numerical checker parsed 0 tests: the paper reports `r = 0.29, p = .004` without degrees of freedom, which cannot be recomputed. That is a real coverage limit (most psychology papers report correlations this way). The writing check flagged four sentences over 60 words (one of 115 words) and the acronym UKRI, which are fair, minor flags.

**Friction found (fixed).** The gate counted a concern the AI itself rated "minor" toward the major-concern cap. Concerns rated minor are now reported as minor comments and no longer use the cap.

**How to read this honestly.**
- Test 1 gave 39% strict recall and test 2 gives 67%. They are not comparable: different field, 28 vs 12 reviewer concerns, and eLife public reviews are shorter and less exhaustive than Nature's three-round files. The checklist was written after test 1 and was available in test 2, so some of the difference may come from it, but this cannot be isolated.
- One paper, one run, hand-mapped by the tool's author, same model family as test 1. Not a benchmark.
- The reviewers' concerns are a sample of what could be raised, so full recall of them is not full coverage of the paper's problems.
