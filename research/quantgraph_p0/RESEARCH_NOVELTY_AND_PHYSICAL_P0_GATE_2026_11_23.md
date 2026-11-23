# QuantGraph-RAG — 23 Nov 2026 falsification-first literature and physical P0

**Status: P0 CONDITIONAL ENGINEERING PASS; SCIENTIFIC NOVELTY AND JOURNAL GO NOT ESTABLISHED.** This branch does not certify image truth, solve visual RAG, or claim an advance over published 2026 chart agents. This report deliberately records evidence *against* overclaiming.

## 1. Original research question and negative novelty search

Broad claim initially proposed: evidence-constrained numerical reasoning over scientific charts, extracting chart values, preserving uncertainty, applying arithmetic constraints, and abstaining when the visual evidence cannot pin a unique number. The claim is **NOT** currently defensible as novel in that broad form.

Closest established published / public preprints (source links / dates verified 2026-11-23):

| Source | Established mechanism / reported gap | Consequence for novelty |
|---|---|---|
| [Chart-MRAG, ACL 2026](https://aclanthology.org/2026.acl-long.1164/) | 4,738 chart-grounded real document QAs; with gold retrieved material MLLM reported 71.15% correctness and 80.74% coverage; mixed visual/text bias | Real multimodal scientific-document failures exist, but not a solution claim |
| [ChartAgent, ACL 2026](https://aclanthology.org/2026.acl-long.843/) | Tool-driven spatial visual subtasks, crop, locate chart axes, multi-step grounded reasoning; strong results on ChartBench/ChartX | Crop / OCR / tool loop / geometric grounding ALREADY KNOWN |
| [Chart-RVR, EMNLP Findings Oct 2026](https://aclanthology.org/2026.findings-emnlp.691/) | Verifiable process-reward chain STRUCTURE -> JSON evidence table -> derivation, compared on six benchmarks | Auditability and executable evidence chain ALREADY ADVANCED |
| [ChartR, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Chen_ChartR_Evaluating_Reasoning_Accuracy_and_Robustness_in_Chart_Question_Answering_CVPR_2026_paper.pdf) | Multi-step chart reasoning ground-truth and perturbation robustness; value extraction bottleneck | Need test separately value extraction and reasoning |
| [ChartRecover, Communications Engineering 2026](https://www.nature.com/articles/s44172-026-00691-8) | Detect marks, fit pixel-to-data linear/log-linear axis mapping, recover scientific chart values | Axis calibration / chart digitization NOT new |
| [GoT-CQA 2026](https://arxiv.org/search/?query=GoT-CQA&searchtype=all) | Directed graph-of-thought chart arithmetic | Calling solution a graph is insufficient |
| [When Does an Image Determine the Answer?, Sep–Nov 2026](https://arxiv.org/abs/2609.34480) | Executable chart evidence witnesses for answerability vs missing information and abstention | Mere abstention / identifiability ALREADY STUDIED |
| [Chartographer, EMNLP 2026](https://aclanthology.org/2026.emnlp-main.580/) | Counterfactual executable chart QA with answer-changing chart variants | Need counterfactual generalization; no cherry-picked example |
| [E2A-Bench, EMNLP Findings 2026](https://aclanthology.org/2026.findings-emnlp.450/) | Evidence-to-action grounding and calibration can fail despite seemingly good hallucination score | Precision/coverage and risk-coverage must both be evaluated |
| [Numeric-Reasoning Guardrails for Financial Charts, 2026](https://journal.jci.co.id/jitie/article/view/603) | OCR evidence, restricted calculator, calibrated abstention | Overlaps broadly; lower-tier paper not a verified strong SOTA baseline |

**No accessible published method in the reviewed set was found with the *exact* shared-axis affine feasible-world LP representation for joint numerical answer-set bounding over retrieved chart evidence. This is NOT proof of uniqueness**, and the method itself is a standard application of robust LP / affine arithmetic rather than a new mathematical theorem. Unknown or unpublished work may overlap. Strongest existing published ChartAgent / Chart-RVR should be actual baselines before any novelty GO.

## 2. Minimal *conditional* mathematical mechanism

Given human-verified single-source linear chart axis (v_i = a p_i + b), its tick intervals (v(t)\in[L_t,U_t]), bounded chart pixel mark positions (p_i\in[l_i,u_i]), and fixed orientation, construct one shared polytope of *feasible* ((a,b,v_1,...,v_n)). Bounding a linear numerical query (q(v)=\sum_i c_i v_i + c_0) amounts to two LP optimizations. This preserves correlation from the common axis slope/intercept across marks. Independent-interval control first bounds each mark separately and then combines marginal intervals. The dependent formulation cannot be wider mathematically for a linear objective if both are evaluated on exactly the same feasible domain. Common calibration and interval arithmetic are established; this is a minimal post-processing probe, not journal novelty.

Precise scope: TWO independently uncertain axis ticks with measured pixel positions; mark selection and axis association already known; **linear** y-axis only; unit labeling externally checked. No implicit guarantee of source text/legend, mark identity, plot interpretation, image pixel alignment, statistical confidence, or formal floating-point certificates. SciPy/HiGHS floating numerical tolerance means even reported feasible interval is not a formally rigorous proof without outward-rounded or exact/rational verification.

### Deterministic synthetic example, not a chart dataset result

- Shared axis two tick value intervals: y=100 -> [-2,2], y=0 -> [98,102], decreasing; mark A pixel 20, B pixel 80.
- Marginal independent bounds for A−B: [56,64], width 8.
- Joint shared calibration bounds for A−B: [57.6,62.4], width 4.8, a 40% reduction **on this synthetic construction only**.
- The intervals contain all 1,000 sampled feasible worlds in test, and 14/14 adversarial tests passed [CI 45114381392](https://github.com/AiDevnew168/scale_rag/actions/runs/45114381392).

### Additional independent EXACT rational bound implementation

To avoid mistaking floating-point numerical LP for a mathematical certificate, a second **standard-library-only** implementation now enumerates every feasible 2D affine calibration polytope vertex using `fractions.Fraction` and exactly bounds linear mark expressions after choosing extremal permissible pixel endpoints. This is exact for the finite, bounded, affine input model with **guaranteed tick orientation** and trusted rational data; it is not a proof the chart images actually satisfy those inputs. Code: `exact_affine.py` with nine adversarial tests in `test_exact_affine.py`; [independent CI run 45115023600](https://github.com/AiDevnew168/scale_rag/actions/runs/45115023600) **9/9 PASS**, including 10,000 random rational sampled worlds and the original chart conditional interval. Toy bounds reproduced exactly as `288/5` and `312/5`. This mathematics is known convex/rational optimization, **not an original theorem**. A trusted-source flag cannot authenticate the image without independent image provenance and annotation adjudication.

## 3. Original unmodified real public chart checks

- [vis-nlp/ChartQA source commit 044eabfc306abfe9340c5741f0093aefc5973d06](https://github.com/vis-nlp/ChartQA/tree/044eabfc306abfe9340c5741f0093aefc5973d06/ChartQA%20Dataset/val). Original PNGs obtained in [CI 45114472338](https://github.com/AiDevnew168/scale_rag/actions/runs/45114472338), image bytes kept only in original GitHub Actions artifact for human review; images not copied into repository.
- `4576.png` original SHA256 `ce394c49e5272c52ffe0e8c6d945c440b835c4a4fdd6ef7e5539eb604d881e4d`: visual source clearly prints blue-line 2018 **72%** and 2013 60%. The question gold label **0.72** is correct when expressed as a fraction, but the released extracted CSV contains `772` for 2018 blue: source TABLE EXTRACTION CORRUPTION, **NOT WRONG GOLD**.
- `5734.png` original SHA256 `535b11db104f4ac29b94fc0add0a931f22a05b2c9ce3e08e54d2de49d3fb6a39`: visual source labels the 2016 Jobs series **68%**, matching original gold 68; extracted CSV reports Jobs in 2016 as 0: **TABLE MISSING/INCORRECT ENTRY**, NOT WRONG GOLD.
- Two examples were deliberately inspected after finding source-CSV mismatch, **NOT random/blind benchmark samples**. No 2-case error rate or OCR/generalization claims allowed. Grounded observation: never treat an extracted OCR/CSV table as an infallible oracle.

### Actual original pixel and conditional LP integration

- [CI 45114770267](https://github.com/AiDevnew168/scale_rag/actions/runs/45114770267), [artifact 14791052277](https://github.com/AiDevnew168/scale_rag/actions/runs/45114770267/artifacts/14791052277), ZIP SHA256 `81557dabe54fd53e077d155e908b9a1b01453d3bd2d2e85226292955d5a393af`.
- Original 415x467 `4576.png`, exact SHA locked; **manually-selected after inspecting** the picture: top/bottom tick pixel y=104/340 mapped to 100%/0%; fixed original blue curve ROI windows at 2018 and 2013. The code actually segments 42 and 51 original blue-colored pixels and uses each mark's pixel min/max as interval, NOT label text.
- Source pixel evidence yields **2018 [69.915%,73.305%]**, 2013 **[58.051%,61.441%]**, and their difference **[8.475,15.254] percentage points**. Original printed 72% and 60% lie within the intervals.
- **Crucial negative result:** this pixel-only system **abstains** on the precise 72% answer; the original image has printed numeric label `72` available to a strong OCR control. With these manually fixed axes, no dependency advantage can be claimed over independent intervals. This is a functionality smoke test and illustrative *potential weakness*, not an accuracy win.
- Testing scientific chart RAG would require scientific chart corpus & linked papers, frozen retrieval and independent ground-truth adjudication. ChartQA is generic charts; this experiment does NOT test RAG, scientific data retrieval, Qwen-VL API or SOTA chart agents.

## 4. Hard gate and non-circular next experiment

**NO-GO for a journal-method claim at this stage.** A stronger analysis is allowed only if an original **nontrivial** error type is present in independent 2026 benchmark queries, cannot be fixed by OCR/axis extractor + deterministic calculator or strong ChartAgent/Chart-RVR, and is demonstrably addressed by the joint-dependency model with lower actual false-precision risk and cost. Require:

1. Document ID and original chart image provenance, associated source page and independent label/correct chart series, preferably scientific Chart-MRAG; outside knowledge restricted to training.
2. Evaluate raw image + question at SAME visual/token budget: strong 2026 agent/chart reconstruction baseline, OCR+calculator with unit checks, interval arithmetic with independent values, and shared feasible-world method. Do not use the released OCR CSV as unquestionable gold.
3. Select ~100 never-consulted charts across document/source clusters (at least ~30 numerical relational and uncertainty-sensitive), score *end-to-end answered correctness plus risk/coverage*, exact chart-grounded evidence, semantic answerability, numeric interval coverage with visible human annotation; independently adjudicate ambiguous cases. No filtering failed examples after outcomes; preregister metric and failure gate.
4. A nontrivial precommitted minimum e.g. >=8 percentage point absolute answered-and-correct increase at matched coverage plus lower false-confident answers, **before** out-of-source final test; after failure STOP the path rather than add complex modules or change objective.
5. The research contribution must include an independently verified property NOT already offered by exact chart digitization, ordinary LP or standard uncertainty propagation. Neither the P0 code nor the literature review proves that property.

**New research 2026 overlap:** [ChartAgent, ACL 2026](https://aclanthology.org/2026.acl-long.843/) and [Chart-RVR, EMNLP Findings 2026](https://aclanthology.org/2026.findings-emnlp.691/) are mandatory direct comparisons, not optional citations. Their visual subtask tooling and structured evidence/calculation trace further rule out generic 'visual agent plus program' novelty.

**Decision:** implementation and source read integrity P0 = PASS; actual multimodal RAG performance = NOT TESTED; advantage over competitive baseline = NOT TESTED; mathematical novelty = UNPROVEN; high-impact journal candidacy = NO-GO for now. The result should be saved as a negative/conditional proof, not portrayed as a promising publication-level breakthrough.