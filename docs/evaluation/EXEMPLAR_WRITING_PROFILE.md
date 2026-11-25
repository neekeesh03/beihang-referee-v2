# Exemplar writing profile

Objective prose metrics for five high-quality documents supplied by the project owner, computed with `referee/verification/writing.py`. The texts themselves are not included. **Five documents from different fields and eras cannot define a norm.** The table shows how much strong writing varies, so a manuscript's numbers can be read in context.

| Document | Words | Median sentence (words) | 90th pct sentence | Share over 40 words | Passive per 100 sent. | Hedges /1000 w | we/I/our /1000 w | Signposts /1000 w |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gollwitzer 1999 (psychology) | 8100 | 23.0 | 40 | 0.099 | 57.1 | 4.8 | 5.2 | 1.7 |
| Einstein 1905 (physics, English translation) | 8649 | 31.0 | 64 | 0.364 | 40.3 | 5.7 | 19.1 | 0.5 |
| Wang et al. 2026 (TPAMI survey) | 9501 | 22.0 | 44 | 0.126 | 19.1 | 2.2 | 2.0 | 1.6 |
| Wang et al. 2026 (IEEE COMST survey) | 24057 | 24.0 | 47 | 0.149 | 15.2 | 2.2 | 3.0 | 1.0 |
| Noble 2017 (editorial advice) | 2030 | 22 | 38 | 0.071 | 25.9 | 11.8 | 0.5 | 0.0 |

## What the table does and does not say
- Median sentence length is 22 to 31 words across all five. Einstein's translated 1905 prose has the longest sentences (over a third exceed 40 words) (equations inside sentences inflate the count) and is still widely read as clear, so long sentences alone are not a fault.
- Hedging runs from 2.2 to 11.8 per 1000 words. The writing-advice article hedges most because it gives advice rather than reporting results. The flag threshold in the tool (25 per 1000 words) is far above everything here.
- The two surveys use far less passive voice than the psychology article (about 15 to 19 against 57 per 100 sentences), and the physics paper sits between. The passive-voice figure is a crude pattern count (a form of 'to be' plus a past participle), so treat it as rough. It is reported but never flagged.
- Pronoun use differs widely (Einstein 19 per 1000 words; the surveys 2 to 3). Not flagged.
- Undefined acronyms were found in neither the psychology nor the physics paper; the two surveys leave a handful undefined (for example GPT, AWS, UAV, TPU), which is what the flag exists to catch. Page headers and capitalised headings are filtered out first; it is still a heuristic.

Observed writing techniques (not metrics) are in `core/WRITING_QUALITY.md`.
