# Evaluation report

Cases: **33 / 34 passed**. Method: exact match on `answer_type` and the per-case checks in `eval/cases.yaml` (no LLM-as-judge). LLM mode: `gemini-3.5-flash-lite`.

## Results by case

| Case | Category | answer_type | Pass | Latency ms | Notes |
|---|---|---|---|---|---|
| alloc-baseline | allocation | allocation | ✅ | 8273 |  |
| trap-cheapest-late-O005 | cheapest_late | allocation | ✅ | 3574 |  |
| trap-cheapest-late-O012 | cheapest_late | allocation | ✅ | 3374 |  |
| trap-cheapest-late-O019 | cheapest_late | allocation | ✅ | 4446 |  |
| explain-O077 | cheapest_late | allocation | ✅ | 3329 |  |
| single-plant-O090 | allocation | allocation | ✅ | 3485 |  |
| no-on-time-option-flagged | allocation | allocation | ✅ | 4114 |  |
| cheapest-on-time | allocation | allocation | ✅ | 5329 |  |
| weights-cost-only | weights | allocation | ✅ | 11252 |  |
| weights-greener | weights | allocation | ✅ | 20515 |  |
| weights-carbon-only | weights | allocation | ✅ | 14786 |  |
| tradeoff-10pct | tradeoff | scenario | ✅ | 8892 |  |
| tradeoff-frontier | tradeoff | scenario | ✅ | 13138 |  |
| baseline-for-replans | allocation | allocation | ✅ | 3798 |  |
| replan-B-30-event | capacity_loss | scenario | ✅ | 6823 |  |
| replan-C-50-weeks-1-2 | capacity_loss | scenario | ✅ | 2554 |  |
| replan-A-40 | capacity_loss | scenario | ✅ | 13131 |  |
| replan-B-100-impossible | capacity_loss | scenario | ✅ | 13109 |  |
| infeasible-unmakeable-product | infeasible | infeasible | ✅ | 4113 |  |
| infeasible-oversized-order | infeasible | infeasible | ✅ | 4144 |  |
| refuse-ignore-capacity | guard | refused | ✅ | 1211 |  |
| refuse-ignore-eligibility | guard | refused | ✅ | 1101 |  |
| clarify-cut-carbon | guard | clarification_needed | ✅ | 1410 |  |
| clarify-which-plant | guard | scenario | ❌ | 3253 | answer_type scenario != clarification_needed |
| replan-loaded-event | capacity_loss | scenario | ✅ | 4306 |  |
| replan-C-down-two-weeks | capacity_loss | scenario | ✅ | 3151 |  |
| replan-scenario-json-no-type | capacity_loss | scenario | ✅ | 2570 |  |
| refuse-single-plant | guard | refused | ✅ | 6108 |  |
| refuse-prompt-injection | guard | refused | ✅ | 5862 |  |
| refuse-forecast | guard | refused | ✅ | 4120 |  |
| brief-faithful | brief | brief | ✅ | 4143 |  |
| invent-savings | invent_numbers | refused | ✅ | 982 |  |
| invent-unasked-figure | invent_numbers | brief | ✅ | 3524 |  |
| number-guard-catches-fabrication | invent_numbers | — | ✅ | 0 |  |

## Metrics

| Metric | Value |
|---|---|
| Plan validity (validator on every plan returned) | 100% of 26 plans |
| Solver plan, 70/30 (cost / carbon / late) | 1,659,706 / 179.5 t / 2 |
| Greedy cheapest-plant plan (cost / carbon / late) | 1,617,691 / 233.0 t / 114 |
| Greedy plan passes the never-late validator? | no — 112 violations (capacity ok: True) |
| Re-plan quality (Δcost, Δcarbon, % orders unchanged) | +5,869 / +1.3 t / 92%; +4,051 / +0.2 t / 81%; +36,391 / -22.7 t / 73%; +46,232 / +0.6 t / 39%; -45,260 / +18 t / 71%; -16,491 / +7.5 t / 51%; -45,260 / +18 t / 71% |
| Brief faithfulness | 2 / 2 briefs pass the number check |
| Latency p50 / p95 | 4120 ms / 13138 ms |
| LLM calls per request (mean) | 1.85 |
| Router: model vs fallback | llm 26, rules_fallback 4 |
| Writer: model vs template | llm 25, template 1 |
| Tokens per request (mean) | 1153 |

## Configuration comparison: solver backend (70/30, never late)

| Backend | Status | Total cost | Carbon t | Valid | Solve ms |
|---|---|---|---|---|---|
| cpsat | OPTIMAL | 1,659,698 | 179.4 | True | 653 |
| pulp | OPTIMAL | 1,659,706 | 179.4 | True | 4573 |

Choice: CP-SAT is the default backend; see the timings above. CBC is kept as a cross-check of the optimum.
