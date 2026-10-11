# Evaluation report

Cases: **28 / 28 passed**. Method: exact match on `answer_type` and the per-case checks in `eval/cases.yaml` (no LLM-as-judge). LLM mode: `mock`.

## Results by case

| Case | Category | answer_type | Pass | Latency ms | Notes |
|---|---|---|---|---|---|
| alloc-baseline | allocation | allocation | ✅ | 699 |  |
| trap-cheapest-late-O005 | cheapest_late | allocation | ✅ | 706 |  |
| trap-cheapest-late-O012 | cheapest_late | allocation | ✅ | 510 |  |
| trap-cheapest-late-O019 | cheapest_late | allocation | ✅ | 705 |  |
| explain-O077 | cheapest_late | allocation | ✅ | 150 |  |
| single-plant-O090 | allocation | allocation | ✅ | 799 |  |
| no-on-time-option-flagged | allocation | allocation | ✅ | 722 |  |
| cheapest-on-time | allocation | allocation | ✅ | 2854 |  |
| weights-cost-only | weights | allocation | ✅ | 4298 |  |
| weights-greener | weights | allocation | ✅ | 10287 |  |
| weights-carbon-only | weights | allocation | ✅ | 10302 |  |
| tradeoff-10pct | tradeoff | scenario | ✅ | 5911 |  |
| tradeoff-frontier | tradeoff | scenario | ✅ | 5929 |  |
| baseline-for-replans | allocation | allocation | ✅ | 701 |  |
| replan-B-30-event | capacity_loss | scenario | ✅ | 6648 |  |
| replan-C-50-weeks-1-2 | capacity_loss | scenario | ✅ | 772 |  |
| replan-A-40 | capacity_loss | scenario | ✅ | 10463 |  |
| replan-B-100-impossible | capacity_loss | scenario | ✅ | 10440 |  |
| infeasible-unmakeable-product | infeasible | infeasible | ✅ | 494 |  |
| infeasible-oversized-order | infeasible | infeasible | ✅ | 528 |  |
| refuse-ignore-capacity | guard | refused | ✅ | 35 |  |
| refuse-ignore-eligibility | guard | refused | ✅ | 32 |  |
| clarify-cut-carbon | guard | clarification_needed | ✅ | 33 |  |
| clarify-which-plant | guard | clarification_needed | ✅ | 37 |  |
| brief-faithful | brief | brief | ✅ | 153 |  |
| invent-savings | invent_numbers | refused | ✅ | 34 |  |
| invent-unasked-figure | invent_numbers | brief | ✅ | 153 |  |
| number-guard-catches-fabrication | invent_numbers | — | ✅ | 0 |  |

## Metrics

| Metric | Value |
|---|---|
| Plan validity (validator on every plan returned) | 100% of 22 plans |
| Solver plan, 70/30 (cost / carbon / late) | 1,659,706 / 179.5 t / 2 |
| Greedy cheapest-plant plan (cost / carbon / late) | 1,617,691 / 233.0 t / 114 |
| Greedy plan passes the never-late validator? | no — 112 violations (capacity ok: True) |
| Re-plan quality (Δcost, Δcarbon, % orders unchanged) | +7,889 / -0.3 t / 91%; -1,762 / +1.4 t / 81%; +41,392 / -23.9 t / 70%; +33,377 / +3.1 t / 44% |
| Brief faithfulness | 2 / 2 briefs pass the number check |
| Latency p50 / p95 | 705 ms / 10440 ms |
| LLM calls per request (mean) | 0.00 |
| Tokens per request (mean) | 0 |

## Configuration comparison: solver backend (70/30, never late)

| Backend | Status | Total cost | Carbon t | Valid | Solve ms |
|---|---|---|---|---|---|
| cpsat | OPTIMAL | 1,659,698 | 179.4 | True | 574 |
| pulp | OPTIMAL | 1,659,706 | 179.4 | True | 2080 |

Choice: CP-SAT is the default backend; see the timings above. CBC is kept as a cross-check of the optimum.
