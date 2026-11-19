# Structural-consistency feasibility: real human-labeled edge audit (2026-11-19)

**Decision:** **NO-GO for developing a new constrained Flow/ILP solver for candidate A on the evidence now available.** This is an evidence-based stop decision for the *present hypothesis and datasets*, not a theorem that multimodal semantic evidence graph repair cannot help.

## Why a new dataset was essential

TopoGraphRAG-Bench official annotations were inspected directly (source SHA256 `3bd203243a5c50a664f719e686608f9e4bfb0b9b31f0ea9514b324b2986247ff`):
- 1,014 `bridge_chain` questions: exactly two ordered evidence nodes, no multi-node graph-choice hardness.
- 708 `synthesis` questions: sets of required evidence facts, but no exhaustive positive/negative pairwise relation labels or validated multiple competing evidence graphs.
- 302 single-hop questions.

Thus a defensible *wrong-edge recovery* comparison cannot be inferred from their evidence-set Recall@k or simple gold-node directions. This is not the old QASPER/MCF-vs-CE top-k task.

## Independent human-labeled structural-link control: FUNSD

- Original FUNSD archive (public, research/educational use): https://guillaumejaume.github.io/FUNSD/dataset.zip
- SHA256: `c31735649e4f441bcbb4fd0f379574f7520b42286e80b01d80b445649d54761f`
- Source data: 199 real annotated scanned forms. Official split: 149 training and 50 test. 149 further split into 119 learned scorer + 30 validation documents.
- **Test set:** 50 documents, 837 human-annotated question-to-answer links, 21,727 candidate pairs. Other-type links (227) excluded, and 64 positive question nodes plus 16 positive answer nodes have degree greater than one.
- Inputs held identical: **oracle fixed node types** (which entities are questions and answers), each entity's text and bounding-box position; a logistic pair scorer trained exclusively on 119 train documents. Gold test links do not enter scores.
- Thresholds per decoder selected exclusively by validation micro F1.
- Six methods: local independent top-1/top-2, globally sorted degree-constrained Greedy (cap 1/2), exact min-cost-flow b-matching (cap 1/2). Flow and Greedy of the same capacity used the **same** validated threshold (cap1 tau=0, cap2 tau=2).
- No direct image pixels, no QA generation, no end-to-end RAG. Missing annotations treated as negatives; not an exhaustive semantic-compatibility benchmark.

### Official execution evidence

- Human-relation linking experiment (success): https://github.com/AiDevnew168/scale_rag/actions/runs/44511093908
- Gold ceiling exact-flow audit (success): https://github.com/AiDevnew168/scale_rag/actions/runs/44511476885
- Source code: `research/topo_fea/funsd_relation_gate.py`
- Workflow: `.github/workflows/funsd_relation_gate.yml`
- Pinned random seed: `261119`; dependency versions in workflow. Full per-document and summary artifacts attached to the successful run.

## Held-out 50-document performance

| Decoder | True-positive | False-positive | False-negative | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Independent cap 1 | 565 | 139 | 272 | .80256 | .67503 | .73329 |
| Greedy cap 1 | 572 | 57 | 265 | .90938 | .68339 | **.78035** |
| Flow cap 1 | 570 | 64 | 267 | .89905 | .68100 | .77498 |
| Independent cap 2 | 516 | 170 | 321 | .75219 | .61649 | .67761 |
| Greedy cap 2 | 614 | 250 | 223 | .71065 | .73357 | **.72193** |
| Flow cap 2 | 614 | 255 | 223 | .70656 | .73357 | .71981 |

2,000 document-level bootstrap replications, exploratory intervals:
- Flow cap 1 minus Greedy cap 1: -0.537 F1 percentage points, CI95 [-1.608,+0.149].
- Flow cap 2 minus Greedy cap 2: -0.212 pp, CI95 [-0.674,+0.164].
- Flow cap 1 minus independent cap 1: +4.169 pp, CI95 [+1.962,+6.950].
- Flow cap 2 minus independent cap 2: +4.220 pp, CI95 [+1.403,+7.065].

**Interpretation:** Global capacity constraints improve upon independent decisions, but exact min-cost-flow does **not** outperform capacity-constrained greedy under identical scores, capacities and thresholds. The improvement relative to independent choices cannot be attributed uniquely to the Flow solver.

## Gold-capacity exact upper bounds

A separate exact max-flow audit on gold edges alone (oracle diagnostic, never included in prediction) found:

| Maximum degree at both endpoint types | Best gold edges retained | Maximum gold edge recall |
|---|---:|---:|
| cap 1 | 595 / 837 | 71.087% |
| cap 2 | 664 / 837 | 79.331% |
| cap 3 | 706 / 837 | 84.349% |

Gold sets violate a cap-1 solution in 24 of 50 documents, cap 2 in 13, cap 3 in 9. The constrained greedy cap-1 decoder recovered **572/595 = 96.13%** of the gold links theoretically retainable under its capacity assumption. Consequently much of its missed gold is caused by *an invalid structural capacity assumption*, not insufficient global search.

## Research decision and provenance limitations

1. The older Track A CE/MCF result already showed that merely improving top-k evidence selection with flow is not a strong research proposition.
2. The new TopoGraphRAG annotation schema cannot independently validate multiple correct/incorrect edges required for an original semantic topology objective.
3. On a **different human-labeled structural edge task**, global constraints did help, but exact Flow failed to improve on simple greedy and the constraint model was itself wrong for many gold graphs.
4. The task is adjacent to multimodal document relation extraction, **not** a direct RAG result; transfer to scientific multimodal graph repair is unproven.
5. No new article algorithm should be developed based on these results. A revival of candidate A would require a fully labeled, multi-edge scientific RAG benchmark with competing valid/invalid joins, held-out documents, a strong relation scorer, and a real advantage over simple capacitated greedy; none is established.

**Research gate: stop candidate A in its current form. Prefer looking for a different, independently demonstrated structural problem (e.g., workload-aware partitioning that preserves necessary bridges) instead of recycling another evidence-selection or pair-linking algorithm.**
