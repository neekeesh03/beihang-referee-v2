# Planted-defect fixtures

Two synthetic manuscripts (with analysis code in an appendix) that contain known defects, used to test discovery.
`manuscript_easy.md` has nine planted defects, several announced in the prose. `manuscript_subtle.md` has five defects hidden in code or in numbers, with deliberately clean prose. `truth_*.md` list them.

These are the only place the answer key lives: do not show a truth file to a reviewing model. Use `tests/test_planted_defects.py` for the deterministic part (code pointers and numeric checks) and `docs/evaluation/PROMPT_AB_TEST.md` for how model runs were scored.
Caveat: synthetic papers are easier than real ones. A model that finds every planted defect here has not shown it can find unplanted ones in a real paper.
