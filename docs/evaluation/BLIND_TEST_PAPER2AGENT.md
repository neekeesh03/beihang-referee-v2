# Blind test: Referee-directed AI review vs. the published Nature peer-review file

**Question.** If an AI is directed by Beihang Referee (workflow, rules, quote verification, admission gate), how much of what real Nature referees asked does it find, and does it reach the same overall outcome?

**Paper and ground truth.** "Paper2Agent: Reimagining Research Papers As Interactive and Reliable AI Agents" (arXiv:2509.06917 v1, 8 Sep 2025, the version the referees saw). Ground truth is the first-round (Version 0) reports of Referees 1 to 3 in the Nature peer-review file for the published paper (CC BY 4.0). Concerns below are paraphrased.

**Method.** A separate AI agent (no access to the peer-review file, no web access) read the v1 manuscript text and reviewed it through `referee.direction` (`start_review`, `check_numbers`, `find_passages`, `verify_quote`, `submit_concerns`). Outputs: `examples/blind_review_paper2agent.md`. I (the author of the tool) then mapped its requests to the referees' concerns by hand. The mapping is my judgment and is listed so you can audit it.

**Result.**
- Outcome: the gate returned **MAJOR_REVISION**; the Nature referees' round-1 requests also amounted to a major revision (new evaluations, ablations and framing changes were all requested). The review also said, separately, that the work fits a specialist methods venue; Referee 1 reached that same view in later rounds.
- 5 concerns admitted, 6 downgraded. All 28 anchor quotes verified as exact text.
- Of 28 distinct referee concerns: **11 matched clearly, 9 partly, 8 missed**. Strict recall 39%; counting partial matches as half, 55%; counting any overlap, 71%.
- Precision: 10 of the 11 requests correspond to a referee concern. The unmatched one (distinguish accessibility from adoption) is reasonable but was not raised by them.

| # | Referee concern (paraphrased) | Found? |
| --- | --- | --- |
| 1 | Success rate across many papers not measured | partial |
| 2 | Only easy, well-documented repositories | yes |
| 3 | n = 15 per set, no intervals or power | yes |
| 4 | "Novel" queries are variations of tutorial queries | yes |
| 5 | Tools validated on the same tutorials used for testing | yes |
| 6 | Survivorship: removed tools not counted (attempted vs retained) | yes |
| 7 | Build time and cost not amortised; cost and hardware unreported | yes |
| 8 | MCP not compared with a simpler alternative (skill files) | **missed** |
| 9 | Claude-only; no other agent tested | partial |
| 10 | Baseline given less information (confounded) | yes |
| 11 | No ablation of the pipeline's sub-agents | **missed** |
| 12 | "Discovery/identified" wording for the ADHD result | **missed** |
| 13 | SORT1 vs CELSR2/PSRC1 scores indistinguishable | yes |
| 14 | No inter-rater reliability or rubric for ground truth | partial |
| 15 | Failure modes, out-of-scope inputs, hallucination rate | partial |
| 16 | Non-biology domains untested | partial |
| 17 | Key algorithm details only in the repository | partial |
| 18 | No statistics on the runtime comparison | partial |
| 19 | Maintenance burden as code evolves | partial |
| 20 | No evidence the Scanpy agent adapts parameters | **missed** |
| 21 | No security threat model | yes |
| 22 | Inherited bugs from the original code | **missed** |
| 23 | Novelty vs CodeOcean, Binder, Paper2Code not tabulated | **missed** (no literature retrieval was used) |
| 24 | Run-to-run variance of a stochastic system | yes |
| 25 | TISSUE and Scanpy need quantitative evaluation | yes |
| 26 | "Novel query" and "pass" not defined | partial |
| 27 | Can it adapt or train models, not only run code | **missed** |
| 28 | Figure legibility; unclear input in Fig. 1B | **missed** |

**Friction found in the tool (all fixed afterwards).**
1. The reference checker treated an issue number, `21(6509)`, as a future year. Fixed: only years within the next 10 are flagged.
2. The closure-criterion test used 11 keywords and rejected four good criteria. Fixed: much broader stems, still rejecting vague ones like "Fix it."
3. The five-major cap downgraded two valid concerns. Fixed: cap 8; overflow becomes a ranked should-fix, not a minor comment.
4. Fix-type classification called "compare saved outputs" and "run a matched control" plain wording. Fixed with extra keywords.

**What the misses suggest, and the caveat.** Most misses are standard methodological requests (ablations, simpler-alternative baselines, inherited errors, adaptation, wording of claims, closest-system comparison). I added `core/COVERAGE_CHECKLIST.md` to the playbook to prompt for them. **That checklist is built from this same peer-review file, so re-running on this paper would be circular and prove nothing.** The honest next test is a different paper with a public peer-review file, reviewed blind with the checklist.

**Limits of this test.** One paper, one reviewing AI, one run, hand-mapped by the tool's author; the published referees' concerns are themselves a sample of what could be raised. Not a benchmark.
