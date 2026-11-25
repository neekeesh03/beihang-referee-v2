# Where Beihang Referee fits: positioning against two 2026 surveys

Sources (supplied by the project owner and read in full for the parts cited): 
- Wang et al., "The Hitchhiker's Guide to Autonomous Research: A Survey of Scientific Agents", IEEE TPAMI 48(11), 2026 (called *the scientific-agents survey* below).
- Wang et al., "Large Model-Based Agents: State-of-the-Art, Cooperation Paradigms, Security and Privacy, and Future Trends", IEEE Communications Surveys & Tutorials 28, 2026 (called *the LM-agents survey*).

Works those surveys cite (CycleResearcher, AI Scientist-v2, Reviewer2, ReviewCritique) are mentioned only as cited by them; I have not read those papers.

## Placement in the scientific-agents taxonomy
The survey splits the research life cycle into six stages: literature mining, hypothesis, experiment design, experiment verification, analysis and result, and **evaluation and review**. Referee works at the last stage, and also touches literature mining (prior-art and reference checks).

The survey rates agents on two axes. **Capability envelope** is E1 (linear execution of one or more stages), E2 (cross-stage closed loop) or E3 (end-to-end scientific cycle). **Capability maturity** is M1 (benchmark competence), M2 (expert reliability) or M3 (real-world robustness). Roles are Assistant, Partner and Avatar.

Honest placement of Referee:
- **Envelope: E1.** It runs a fixed review workflow with revision rounds. It does not close a loop back into experiments.
- **Role: Assistant**, by design. A human stays in charge and the user's own AI does the reasoning.
- **Maturity: below M1.** M1 needs demonstrated competence on controlled tasks or benchmarks. Referee has one blind test on one paper (`docs/evaluation/BLIND_TEST_PAPER2AGENT.md`) and unit tests. That is a prototype, not benchmark competence.

What would move it up, using the survey's own evidence categories:
- **M1:** run on public review-alignment benchmarks the survey lists for this stage (Reviewer2 and ReviewCritique, "measuring agents' alignment with human reviewers") and report agreement with human reviews.
- **M2:** expert assessment: working referees or editors scoring whether the concerns are valid and the recommendation sensible.
- **M3:** sustained use on real submissions, with failure recovery and maintenance.

## How the design answers the survey's concerns
The LM-agents survey divides agent hallucination into four kinds. Each has a matching control in Referee:

| Hallucination kind (LM-agents survey) | Referee control |
| --- | --- |
| Input-conflicting: output diverges from what the user provided | Every concern anchor must be an exact quote that `verify_quote` finds in the manuscript |
| Context-conflicting: output contradicts earlier turns | Frozen concern ledger; `revision_round` can only close a concern with a quote from the revised text |
| Knowledge-conflicting: output contradicts the knowledge base | Passage retrieval over the manuscript; Crossref and Europe PMC lookups for references and prior art |
| Fact-conflicting: output contradicts real-world facts | Offline recomputation of reported statistics; DOI existence and retraction checks |

The same survey describes **indirect prompt injection**: instructions hidden in retrieved data that take over an agent. A manuscript is exactly such data. Referee treats manuscript text as untrusted, scans for instruction-like text in `start_review`, and tells the assistant to report it and not obey it.

The scientific-agents survey says M3-level agents need "auditable workflows, risk-aware autonomy boundaries, human-in-the-loop control" and "queryable provenance over artifacts, prompts, model versions, tool invocations". Referee implements a small version: an append-only log of every tool run per manuscript (`provenance_log`), a fixed recommendation the AI cannot override, and a director model where the human's own AI does the judging. This is a design match to the survey's wish list, not evidence of M3 maturity.

MCP, which the LM-agents survey lists among agent communication protocols, is how Referee connects to any assistant.

## Limits of this positioning
The surveys are secondary sources and the mapping to their taxonomy is my own judgment. Nothing here claims Referee outperforms existing automated-review systems; it has not been compared with them.
