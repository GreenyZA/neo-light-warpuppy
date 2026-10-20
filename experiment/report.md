# Swarm-Guard Experiment Report
_Run: 2026-10-16T04:29:45.620005+00:00_

## Gate (chosen: option 1 = +15% token overhead AND verifier must be a real LLM)

| Criterion | Result |
|---|---|
| Trap catch rate (guarded) | 100.0%  (need 100%) |
| False positives on clean tasks (total over 3 reps) | 2  (need 0) |
| Avg token-overhead % | 57.69%  (limit 15%) |
| All 3 reps passed gate | False |

## Aggregate
- Baseline trap escape rate: 100.0% (reviewer loop today never checks spec boundary).
- Guarded trap catch rate (avg): 100.0%.
- Guarded clean-task pass rate (avg): 26.7%.
- Guarded total false positives: 2.
- Guarded avg ceremony/progress ratio: 5.5.

## Per-rep
- rep 0: traps 10/10 | clean 8/10 | FP=2 | overhead=57.69% | C/P=5.5 | gate=False

## Hidden 4th trap test (natural-language, no moonbase keywords)
See report.md appendix row in results/guarded_rep*.json for a planted natural-language scope-creep case tagged `scenario=hidden_trap` (not yet inserted into current fixture set).

## Recommendation
Gate FAILED. Inspect which criterion failed:
- trap catch < 100% -> strengthen guardrail prompt / check sending non_goals.
- FP > 0 -> loosen non_goals wording or add an 'except' note to spec.
- overhead > 15% -> shrink guardrail output (one-word verdict), cache, or move verifier to cheaper tier.