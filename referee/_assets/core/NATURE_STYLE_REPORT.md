# Journal-Grade Report Structure (modelled on a real Nature-family peer review file)

Patterns below come from a published Nature peer-review file (five referees, three review rounds, author rebuttals). They describe how experienced referees actually write. They are patterns to follow, not text to copy.

## Round 1 report: structure

1. **Summary.** A neutral, accurate restatement of what the paper does, with the headline numbers the authors report (for example "15/15 queries correct, 22 tools generated in about 3 hours"). Finish with an honest one-paragraph overall view: what is impressive, and the three or four things that would most strengthen it. A reader who skips everything else must still get the verdict.
2. **Strengths.** Specific, quantified, tied to the manuscript. Never generic.
3. **Weaknesses and requests.** Each item has the same shape: *what the manuscript says or does (with numbers)* + *why that limits the conclusion* + *a concrete request* ("expand to at least 100 queries and report confidence intervals", "report how many tools were attempted versus retained"). Requests are specific enough that the authors know when they are done.
4. **Sections some journals expect:** originality and significance (name the closest prior systems, for example by name and link, and ask how this differs); data and methodology; statistics and uncertainty; robustness of conclusions; references and credit; clarity of abstract and conclusions.
5. **Suggested improvements** as a numbered list the authors can answer one by one.
6. **Minor comments:** figure legibility, unclear definitions, hardware specifications, what counts as a passing test.
7. **Remarks on code and data availability.** A short separate paragraph: is it documented, runnable, public?

Recurring concerns worth checking in any paper: survivorship bias (only successes reported), train/test overlap (tools validated on the same material they are tested on), confounded baselines (baseline given less information than the system), small samples with no intervals, single point estimates for stochastic systems, claims worded stronger than evidence ("discovery" versus "prioritised hypothesis"), unreported failure rates, missing ablations, narrow domain, missing cost and maintenance analysis.

## Later rounds: structure

- **Improvements.** Say, item by item, what the authors fixed and how the new evidence settled it. Credit real work.
- **Remaining concerns.** Numbered. Each says exactly why it is not yet settled. Keep to the frozen ledger.
- **New concerns are legitimate only when they come from (a) new data or text the revision introduced, or (b) a verifiable change in the field** (for example a stronger baseline model now exists). State which, and cite the source for (b).
- **Acknowledge partial resolution honestly.** "Handled well for X, but the large-scale benchmark still uses the older model, so Y remains open."
- **Overall assessment.** Separate the two judgements below.
- When satisfied, say so plainly: "the major concerns have been satisfactorily addressed", and list the few residual points.

## Two separate verdicts (do not merge them)

- **Soundness:** are the conclusions supported by the evidence? This sets accept / minor / major / reject.
- **Significance and venue fit:** is the advance large enough for this venue? A paper can be sound and still better suited to a specialist venue ("a high-impact methods venue, where the technical contribution would be valued, rather than a journal that expects broader conceptual advances"). State it separately, and say what evidence would justify aiming higher: for example isolating a capability attributable to the new method itself rather than to the base model.

Different referees may reach different overall views on the same paper. A good report states its own reasoning clearly rather than guessing what others will say.

## Language of claims

Prefer "prioritised" or "generated a computational hypothesis" over "discovered" or "identified" unless there is independent experimental validation. Say plainly when a validation is a secondary analysis of existing data. If a human chose among AI-proposed options, say so.
