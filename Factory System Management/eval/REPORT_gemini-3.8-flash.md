# Evaluation report

Cases: **34 / 34 passed**. Method: exact match on `answer_type` and the per-case checks in `eval/cases.yaml` (no LLM-as-judge). LLM mode: `gemini-3.8-flash`.

## Results by case

| Case | Category | answer_type | Pass | Latency ms | Notes |
|---|---|---|---|---|---|
| alloc-baseline | allocation | allocation | ✅ | 24159 |  |
| trap-cheapest-late-O005 | cheapest_late | allocation | ✅ | 18475 |  |
| trap-cheapest-late-O012 | cheapest_late | allocation | ✅ | 12999 |  |
| trap-cheapest-late-O019 | cheapest_late | allocation | ✅ | 20280 |  |
| explain-O077 | cheapest_late | allocation | ✅ | 29559 |  |
| single-plant-O090 | allocation | allocation | ✅ | 19852 |  |
| no-on-time-option-flagged | allocation | allocation | ✅ | 238279 |  |
| cheapest-on-time | allocation | allocation | ✅ | 209685 |  |
| weights-cost-only | weights | allocation | ✅ | 11540 |  |
| weights-greener | weights | allocation | ✅ | 13576 |  |
| weights-carbon-only | weights | allocation | ✅ | 19256 |  |
| tradeoff-10pct | tradeoff | scenario | ✅ | 14626 |  |
| tradeoff-frontier | tradeoff | scenario | ✅ | 14909 |  |
| baseline-for-replans | allocation | allocation | ✅ | 9466 |  |
| replan-B-30-event | capacity_loss | scenario | ✅ | 12008 |  |
| replan-C-50-weeks-1-2 | capacity_loss | scenario | ✅ | 3975 |  |
| replan-A-40 | capacity_loss | scenario | ✅ | 19526 |  |
| replan-B-100-impossible | capacity_loss | scenario | ✅ | 13342 |  |
| infeasible-unmakeable-product | infeasible | infeasible | ✅ | 9848 |  |
| infeasible-oversized-order | infeasible | infeasible | ✅ | 8945 |  |
| refuse-ignore-capacity | guard | refused | ✅ | 5542 |  |
| refuse-ignore-eligibility | guard | refused | ✅ | 5887 |  |
| clarify-cut-carbon | guard | clarification_needed | ✅ | 5887 |  |
| clarify-which-plant | guard | clarification_needed | ✅ | 6167 |  |
| replan-loaded-event | capacity_loss | scenario | ✅ | 9744 |  |
| replan-C-down-two-weeks | capacity_loss | scenario | ✅ | 9350 |  |
| replan-scenario-json-no-type | capacity_loss | scenario | ✅ | 3824 |  |
| refuse-single-plant | guard | refused | ✅ | 5454 |  |
| refuse-prompt-injection | guard | refused | ✅ | 5840 |  |
| refuse-forecast | guard | refused | ✅ | 6119 |  |
| brief-faithful | brief | brief | ✅ | 8691 |  |
| invent-savings | invent_numbers | refused | ✅ | 5862 |  |
| invent-unasked-figure | invent_numbers | brief | ✅ | 8717 |  |
| number-guard-catches-fabrication | invent_numbers | — | ✅ | 0 |  |

## Metrics

| Metric | Value |
|---|---|
| Plan validity (validator on every plan returned) | 100% of 25 plans |
| Solver plan, 70/30 (cost / carbon / late) | 1,659,698 / 179.4 t / 2 |
| Greedy cheapest-plant plan (cost / carbon / late) | 1,617,691 / 233.0 t / 114 |
| Greedy plan passes the never-late validator? | no — 112 violations (capacity ok: True) |
| Re-plan quality (Δcost, Δcarbon, % orders unchanged) | +5,869 / +1.3 t / 92%; +4,051 / +0.2 t / 81%; +41,914 / -23.2 t / 75%; +33,733 / +2.1 t / 41%; -45,260 / +18 t / 71%; -47,086 / +16 t / 61%; -45,260 / +18 t / 71% |
| Brief faithfulness | 2 / 2 briefs pass the number check |
| Latency p50 / p95 | 9848 ms / 29559 ms |
| LLM calls per request (mean) | 2.39 |
| Router: model vs fallback | llm 7, rules_fallback 23 |
| Writer: model vs template | llm 7, template 19 |
| Tokens per request (mean) | 478 |

## Configuration comparison: solver backend (70/30, never late)

| Backend | Status | Total cost | Carbon t | Valid | Solve ms |
|---|---|---|---|---|---|
| cpsat | OPTIMAL | 1,659,706 | 179.5 | True | 478 |
| pulp | OPTIMAL | 1,659,706 | 179.4 | True | 3145 |

Choice: CP-SAT is the default backend; see the timings above. CBC is kept as a cross-check of the optimum.
