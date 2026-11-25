# Response to the independent validation of v2

An independent validation compared v2 with v1 on a supplied paper and listed 45 issues. Each is handled below as **Fixed** (changed and covered by a test), **Partly**, **Not done**, or **Hypothesis** (plausible, untested). I did not have the validated paper or the two reports, so I could not reproduce the review difference. I fixed what could be verified in the code. What I cannot show is that defect discovery is now as good as v1's; that needs the controlled experiment at the end.

## Two causes I verified in the code
1. **Style and decision rules were loaded into the discovery stage.** In v2 the pipeline's core reviewer prompt (`CoreReviewStage`) was extended with the human-voice rules, the stopping rules ("stop looking once the claims that carry the paper have been checked", "typically 1 to 5") and the decision calibration. Those are writing and editing instructions, and the stopping rule tells the reviewer to hunt less. This matches the validation's "prompt overload" and "competing objectives". **Fixed:** the discovery stage now gets only the core reviewer prompt, `PHASES.md`, `DEFECT_HUNT.md` and `COVERAGE_CHECKLIST.md`. Style, stopping and decision rules are released in later phases only. The director's default playbook also withholds them until the AI asks for the adjudicate or write phase. Whether this restores v1's discovery is **untested**.
2. **The 1-to-5 guidance was not enforced.** The prompt said 1 to 5 majors; the code allowed 12 (`max_major_comments`). A 13-comment report is what that mismatch produces. **Fixed:** both pipeline paths now merge near-duplicates and cap at `min(config max, 3 x central claims)`; the director does the same. Items dropped by the cap are listed with their reason.

## Item by item

### 1. Scientific reasoning
| Issue | Status |
| --- | --- |
| Weaker defect discovery; interpreting rather than investigating | Partly. Cause 1 above removed. New `core/DEFECT_HUNT.md` asks for mechanisms (how could the result appear without the claim being true) and a trace claim -> figure -> analysis -> code/data. Untested against v1. |
| Missed the cross-participant lag-alignment error | Partly. `DEFECT_HUNT.md` lists alignment and timing defects first; `inspect_code` points at lag/shift operations and at a lag set once and reused inside a per-participant loop (tested on a planted example). A pointer finds where to look; it does not find the error. Not shown on your paper. |
| Less code-level investigation | Partly. `inspect_code` (MCP) and `trace_claim` added; they work on Python files only and only point. No code execution. |
| Methodological comments without failure mechanisms | Partly. The gate requires a failure mechanism, but only a human or a verifier AI can judge its depth. |
| Less actionable corrections | Partly. Each concern now carries a `fix_type` and a testable closure criterion. |
| Weak prioritisation | Fixed. Each admitted concern gets P0 (decisive), P1 or P2; the review order and decision follow priority. |

### 2. Architecture and prompts
| Issue | Status |
| --- | --- |
| Prompt overload; competing objectives | Fixed for discovery (cause 1). A fully separated multi-stage architecture for the pipeline is **not done**. |
| Little advance in core reasoning | Agreed. v2 additions were mostly management. v3 changes are aimed at discovery and verification, not reporting. |
| Insufficient cross-agent collaboration | **Not done.** Specialist agents still do not question or extend each other's findings. This needs a designed exchange protocol and an experiment. |
| Information lost during synthesis | Partly. Admitted concerns are code-assigned into the final review. Everything not admitted is now listed in an audit trail; the director's `lint_review` flags any admitted concern missing from the written review. |
| New capabilities not integrated across paths | Partly. The graded decision and offline checks now run in both the core and the full pipeline. Writing and response tools exist only in the director. |
| Weaker verification in the simplified workflow | Partly. The director now has strict gate checks plus an optional independent-verifier handoff (`require_verification`). The default is still `self_only` and is labelled provisional in the decision. It is **not** the same standard as the pipeline's independent verifier unless you use the handoff. |

### 3. Evidence verification
| Issue | Status |
| --- | --- |
| Quote accepted because it exists, even if it does not support the criticism | Partly. The gate now checks the quote shares specific terms with the concern (a lexical guard: it caught a real acknowledgments sentence used against a causal-inference concern). Semantic support is judged by the independent verifier handoff, which is not automatic. |
| Weak steelman enforcement | Fixed. `survives_steelman` must be true, and the explanation text may not contradict it. |
| Invalid confidence values pass | Fixed. NaN, infinity, below 0 or above 1, booleans and text are refused. This was a real bug: NaN passed the old `< 0.5` test. |
| Closure by evidence that does not address the problem | Fixed. The closing quote must exist in the revision, share terms with the closure criterion, and be changed text (or carry an explicit justification). |
| Concerns overwritten across rounds | Fixed. Ledgers are hash-checked and append-only; round 1 is write-once; later rounds append versions with a parent hash. A tampered ledger is detected. This is a hash chain, not git. |
| Irrelevant numerical flags without measurement assumptions | Partly. GRIM now fires only when nearby text indicates integer-valued data. Statistic-vs-p checks do not depend on such assumptions. |

### 4. Editorial decision
| Issue | Status |
| --- | --- |
| Keyword-dependent classification | Fixed for the director: the reviewer states `fix_type` and `consequence_level`; keywords are a fallback only. The pipeline path still infers some of it from text. |
| Negation ("no new data are needed") read as new data | Fixed in the fallback (tested). |
| Several minor concerns trigger a major revision | Fixed. Only consequential concerns (central, or at least changes-interpretation) count toward "three or more". Five minor concerns stay a minor revision (tested). |
| Explanation contradicts the concerns | Fixed. The basis names the driving concerns, their priority and fix type (tested). |
| Count influences decisions more than significance | Fixed together with the two items above. |

### 5. Report quality
| Issue | Status |
| --- | --- |
| 28 pages vs 14; redundancy; fragmentation; low information per page | Partly. `lint_review` enforces a word budget, flags repeated sentences and a concern spread over several sections. It only helps if the AI runs it; the pipeline's LLM-written report is not linted. |
| 13 major comments vs 1 to 5 | Fixed in code (cause 2). |
| Overemphasis on comprehensiveness | Addressed by phase separation; effect on the supplied report not measured. |

### 6. Testing
| Issue | Status |
| --- | --- |
| Functionality tests only; no semantic edge cases | Partly. `tests/test_reasoning_regression.py` adds adversarial suites (irrelevant evidence, NaN and out-of-range confidence, failing steelman, vague closure, false closure, minor-count escalation, decision explanation) and `referee/evals/reasoning_metrics.py` reports rates: unsupported-admission rate 0, false-closure rate 0, critical-defect retention 1.0, and handoff retention. These test the gate, not an LLM's scientific insight. |
| No cross-agent consistency tests | Partly. Gate-to-review retention is tested; real multi-agent handoffs are not. |
| No synthesis-quality tests | Partly (lint and retention metrics). |
| No reasoning regression metrics | Partly: gate-level metrics exist; there are none for model discovery quality. |

## Recommended V3 directions: status
Done or partly done: separate discovery from writing; claim-to-code tracing (pointers only); preserve discoveries (audit trail, lint); semantic relevance (lexical plus verifier); unify verification (opt-in); structured judgments instead of keywords; consequence-based priority; consolidation; hash-chained ledgers; stronger closure; claim-based stopping; fewer conflicting prompts; reasoning-focused tests with the four requested measures (for the gate).
**Not done:** structured cross-agent collaboration; stronger specialist statistical and computational agents; red-team improvements; manuscript retrieval unified across every specialist (the core path already used claim-centred context; the full path now uses passage retrieval; some specialists use neither); metrics on real model output.

## The experiment that would settle it
On the validated paper: run v1's prompt, v2's old discovery prompt and v3's discovery prompt, 3 blind runs each, same model, scoring each against a hand-made list of real defects (including the lag-alignment error). Report defect retention per version. That separates "prompt interference" from "everything else". I need the paper and the v1 and v2 reports to do this.
