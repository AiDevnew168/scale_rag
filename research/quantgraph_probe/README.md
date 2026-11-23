# QuantGraph critical literature and mathematical falsification probe (2026-11-23)

**Scientific status: UNRESOLVED NOVELTY, NOT PAPER GO.** The old generic "extract chart values, execute arithmetic, build evidence graph, calibrate abstention" idea is ALREADY substantially occupied by published 2025/2026 systems. This new branch implements only a correctness kernel conditional on externally verified inputs. No actual RAG improvement, chart perception or real baseline has been measured.

## Verified published neighbors and what they already do

| Source | Primary real contribution | Implication |
|---|---|---|
| [Chart-MRAG, ACL 2026](https://aclanthology.org/2026.acl-long.1164/) | 4738 chart/text MRAG QA; 71.15% best cited correctness with ground-truth retrieval; keypoint graph and ChartOCR; paper explicitly points to improved OCR and broader models in limitations | Open errors exist, but no evidence that this precise numeric-bound task is globally unsolved |
| [TFGR, IEEE CAI 2026](https://www.microsoft.com/en-us/research/publication/table-first-guarded-reasoning-outperforming-larger-mllms-in-chart-question-answering/) | Chart2Table + guarded CoT, 93.96% on ChartQA vs its 88.00% baseline | Table-first + calculator by itself is **NOT** novel |
| [ChartR, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Chen_ChartR_Evaluating_Reasoning_Accuracy_and_Robustness_in_Chart_Question_Answering_CVPR_2026_paper.html) | Step-by-step benchmark documents value extraction and accumulated-error weakness | Justifies narrow measurement study, not a novelty theorem |
| [SCI-CQA/VIEM, 2026](https://pubmed.ncbi.nlm.nih.gov/42809469/) | 5629 QA scientific-chart benchmark and visual salient element module | OCR/visual focus intervention already researched |
| [Scientific chart extraction/reconstruction, 2026](https://www.nature.com/articles/s44172-026-00691-8) | Pixel-localization and coordinate-map error analyzed | Pixel-to-axis conversion ALREADY studied |
| [Numerical-Reasoning Guardrails, 2026](https://journal.jci.co.id/jitie/article/view/603) | OCR evidence + executable arithmetic + calibrated abstention, numerical chart questions | Very close method claim; benchmark rigor and venue differ |
| [AERIS-Chart, 2026](https://www.ijsrtjournal.com/article/aeris-chart-evidence-sufficient-and-uncertainty-calibrated-retrieval-for-chart-claim-verification) | Chart retrieval, structured evidence graph, numerical verification, calibrated insufficiency/abstain | Warning: generic evidence graph + uncertainty already claimed; venue quality alone is not a novelty rebuttal |
| [Chartography, 2026](https://arxiv.org/abs/2608.10677) | Professional chart benchmark; 51/100 tasks have expert-set answer ranges | Numeric ranges themselves ALREADY considered |
| [ChartNet, CVPR 2026](https://huggingface.co/datasets/ibm-granite/ChartNet) | Real chart images + rendering code + data tables and disjoint human-reviewed evaluation subset | Candidate for real image/data supervision but original and permissive dataset versions have distinct licenses |

## Candidate that might still be differentiated (NOT established unsolved)

For **retrieved** scientific document charts, use *actual externally validated uncertain mark localization* and axis calibration to derive a bounded source-evidence numerical claim. Preserve repeated-source dependencies and evaluate query-specific risk/coverage against a TFGR-grade table-first + calculator + calibrated abstention control.

The question is whether the stricter **end-to-end empirical mark-coverage calibration with source-dependent arithmetic** improves correct numerical decisions under fixed answer rate and budget, not whether symbolic interval arithmetic is new. The current exact rational/affine implementation is standard mathematics; it provides NO methodological novelty.

## Proven conditional kernel; never mislabel as empirical guarantee

- Only linear axes with two externally validated tick coordinates; true mark pixel MUST lie in the externally verified pixel interval. User-supplied Boolean 'verified' alone is NOT independent proof.
- Mathematically exact rational pixel-to-value projection and affine dependence cancellation (same mark subtraction gives exactly zero); conservative independent interval products/quotients and zero-denominator fail-close.
- Proven true/false on strict comparator only when full interval lies on one side. Otherwise ABSTAIN.
- Out of scope: image recognition, OCR, logarithmic/nonlinear axes, uncertainty about calibrating tick locations, real graph retrieval, natural language question to executable AST, units, correlated multi-mark detector errors, missing glyphs, trained neural backbone, calibrated probabilistic claims, interactive study, published SOTA.

## Baseline-first experiment contract (pre-results)

**Artifact status**: no original image/chart numeric benchmark was run. These are engineering invariant tests only.

1. Acquire legally accessible and **version-pinned** original real chart image + answer/underlying table samples, with 100+ numerical QA and 30+ ambiguous/unsupported cases; family-/document-disjoint calibration/test, fixed before model answers. If unavailable, BLOCKED rather than substituting toy numerical wins.
2. Train/evaluate a real detector/axis calibration with observed pixel-interval coverage; report image-level and series-/mark-level localization coverage. If intervals fail to cover true mark locations, mathematical answer soundness is invalid.
3. Run direct strong TFGR-like Chart2Table + calculator, a strong recent chart-specific VLM, and their calibrated abstention variants with identical source images/context/budget. Include a simple interval arithmetic baseline and a point-estimate baseline. NO MCF/graph solver until a measured gap demands it.
4. Pre-register **risk–coverage**, correct answer fraction, abstain fraction, interval coverage/width, latency and cost. A nominal +8 percentage-point selective accuracy with <50% of answerable queries retained is NOT success. No leakage of human test data into tuning.
5. If strongest practical baseline resolves the initially observed visual uncertainty failure modes, or this method is indistinguishable from an already published 2026 technique, **NO-GO**; no architecture expansion to rescue result.
6. The exact narrowed novelty claim requires a further systematic 2026 literature verification; absence of a named implementation from *this* review does not prove nobody has solved it.

## Reproduce the immediate, limited result

```bash
python -m unittest discover -s research/quantgraph_probe -p 'test_*.py' -v
```

Expected: 15 mathematical invariant tests PASS. This is **not** an empirical model test or a chart RAG result.
