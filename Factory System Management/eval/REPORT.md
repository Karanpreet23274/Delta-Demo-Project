# Evaluation report

Cases: **34 / 34 passed**. Method: exact match on `answer_type` and the per-case checks in `eval/cases.yaml` (no LLM-as-judge). LLM mode: `mock`.

## Results by case

| Case | Category | answer_type | Pass | Latency ms | Notes |
|---|---|---|---|---|---|
| alloc-baseline | allocation | allocation | ✅ | 2410 |  |
| trap-cheapest-late-O005 | cheapest_late | allocation | ✅ | 3212 |  |
| trap-cheapest-late-O012 | cheapest_late | allocation | ✅ | 3285 |  |
| trap-cheapest-late-O019 | cheapest_late | allocation | ✅ | 2751 |  |
| explain-O077 | cheapest_late | allocation | ✅ | 91 |  |
| single-plant-O090 | allocation | allocation | ✅ | 780 |  |
| no-on-time-option-flagged | allocation | allocation | ✅ | 1194 |  |
| cheapest-on-time | allocation | allocation | ✅ | 2911 |  |
| weights-cost-only | weights | allocation | ✅ | 3436 |  |
| weights-greener | weights | allocation | ✅ | 10191 |  |
| weights-carbon-only | weights | allocation | ✅ | 10138 |  |
| tradeoff-10pct | tradeoff | scenario | ✅ | 6264 |  |
| tradeoff-frontier | tradeoff | scenario | ✅ | 6892 |  |
| baseline-for-replans | allocation | allocation | ✅ | 1231 |  |
| replan-B-30-event | capacity_loss | scenario | ✅ | 10271 |  |
| replan-C-50-weeks-1-2 | capacity_loss | scenario | ✅ | 775 |  |
| replan-A-40 | capacity_loss | scenario | ✅ | 10245 |  |
| replan-B-100-impossible | capacity_loss | scenario | ✅ | 10247 |  |
| infeasible-unmakeable-product | infeasible | infeasible | ✅ | 779 |  |
| infeasible-oversized-order | infeasible | infeasible | ✅ | 877 |  |
| refuse-ignore-capacity | guard | refused | ✅ | 50 |  |
| refuse-ignore-eligibility | guard | refused | ✅ | 25 |  |
| clarify-cut-carbon | guard | clarification_needed | ✅ | 27 |  |
| clarify-which-plant | guard | clarification_needed | ✅ | 26 |  |
| replan-loaded-event | capacity_loss | scenario | ✅ | 870 |  |
| replan-C-down-two-weeks | capacity_loss | scenario | ✅ | 640 |  |
| replan-scenario-json-no-type | capacity_loss | scenario | ✅ | 824 |  |
| refuse-single-plant | guard | refused | ✅ | 30 |  |
| refuse-prompt-injection | guard | refused | ✅ | 26 |  |
| refuse-forecast | guard | refused | ✅ | 21 |  |
| brief-faithful | brief | brief | ✅ | 76 |  |
| invent-savings | invent_numbers | refused | ✅ | 37 |  |
| invent-unasked-figure | invent_numbers | brief | ✅ | 86 |  |
| number-guard-catches-fabrication | invent_numbers | — | ✅ | 0 |  |

## Metrics

| Metric | Value |
|---|---|
| Plan validity (validator on every plan returned) | 100% of 25 plans |
| Solver plan, 70/30 (cost / carbon / late) | 1,659,756 / 179.4 t / 2 |
| Greedy cheapest-plant plan (cost / carbon / late) | 1,617,691 / 233.0 t / 114 |
| Greedy plan passes the never-late validator? | no — 112 violations (capacity ok: True) |
| Re-plan quality (Δcost, Δcarbon, % orders unchanged) | +7,889 / -0.4 t / 91%; -2,410 / +1.4 t / 83%; +44,023 / -23.7 t / 69%; +34,743 / +2.8 t / 43%; -45,260 / +18 t / 71%; -5,821 / +2.1 t / 50%; -45,260 / +18 t / 71% |
| Brief faithfulness | 2 / 2 briefs pass the number check |
| Latency p50 / p95 | 870 ms / 10245 ms |
| LLM calls per request (mean) | 0.00 |
| Tokens per request (mean) | 0 |

## Configuration comparison: solver backend (70/30, never late)

| Backend | Status | Total cost | Carbon t | Valid | Solve ms |
|---|---|---|---|---|---|
| cpsat | OPTIMAL | 1,659,698 | 179.4 | True | 3172 |
| pulp | OPTIMAL | 1,659,706 | 179.5 | True | 915 |

Choice: CP-SAT is the default backend; see the timings above. CBC is kept as a cross-check of the optimum.
