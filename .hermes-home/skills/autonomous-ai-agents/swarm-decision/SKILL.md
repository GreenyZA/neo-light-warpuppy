---
name: swarm-decision
description: "Assess task complexity and size agent swarms appropriately."
version: 0.1.0
author: warpuppy, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [swarm, delegation, multi-agent, orchestration, decision]
    related_skills: [hermes-agent, rust-gpu-engineering]
---

# Swarm Decision Skill

Assess every non-trivial task before starting work. Decide if a swarm is needed, size it appropriately, and only then dispatch. Never default to "swarm" — default to "assess first."

## When to Use

- Any task that touches more than 1 file or module
- Any new feature, refactor, or architecture change
- Any testing campaign or multi-step implementation
- Any time you're about to write code or modify the codebase

**Don't use for:** single-file typo fixes, single-tool-call queries, reading/exploring code, answering questions.

## The Decision Framework

### Step 1: Assess Task Complexity

Score the task on these dimensions:

| Dimension | Trivial (1) | Simple (2) | Moderate (3) | Complex (4) | Multi-system (5) |
|-----------|-------------|------------|--------------|-------------|------------------|
| Files touched | 1 | 2-3 | 3-5 | 5-8 | 8+ |
| Modules/crates | 1 | 1-2 | 2-3 | 3-5 | 5+ |
| Sequential tool calls | <5 | 5-10 | 10-20 | 20-40 | 40+ |
| Cross-cutting concerns | None | Minimal | Some | Significant | Architectural |
| Test/verify complexity | None | Low | Medium | High | Multi-stage |

**Total score:** Add all dimensions.

### Step 2: Decide Swarm Size

| Score | Decision | Agents | Pattern |
|-------|----------|--------|---------|
| 5-8 | **Solo** | 1 | Just do it yourself |
| 9-12 | **Pair** | 2 | Worker + Reviewer |
| 13-18 | **Swarm** | 3-5 | Parallel workers, each with Reviewer |
| 19-25 | **Mega-swarm** | 5-10 | Full hierarchy with Top-Level Approver |

### Step 3: Decompose (if swarm)

For swarms, decompose into independent tasks:
- Each task = one Worker with clear scope
- Tasks must be independent (no shared file writes)
- If tasks are dependent, sequence them (not parallel)
- Each Worker gets: goal, context, constraints, verification command

### Step 4: Dispatch

Use `delegate_task(tasks=[...])` with ALL tasks in ONE call.
- Don't split into multiple delegate_task calls
- Don't spawn more agents than the runtime cap (check `hermes config get delegation.max_concurrent_children`)
- Don't spawn agents for trivial sub-tasks

## Sizing Rules

### When to use SOLO (score 5-8)
- Single-file bug fix
- Adding a test to one crate
- Updating documentation
- Simple refactoring within one module
- **Rule:** If you can finish it in <10 tool calls, do it yourself

### When to use PAIR (score 9-12)
- Feature touching 2-3 files in one crate
- Adding a new module with tests
- Refactoring a single crate's API
- **Pattern:** Worker implements → Reviewer reviews → done

### When to use SWARM (score 13-18)
- Feature touching 3-5 files across 2-3 crates
- Implementing a new subsystem (e.g., Vulkan renderer, SGP4 propagator)
- Multi-crate refactoring
- **Pattern:** N parallel Workers → each gets Reviewer → Top-Level Approver

### When to use MEGA-SWARM (score 19-25)
- Architecture changes across 5+ crates
- New feature spanning the entire stack
- Major refactoring or migration
- **Pattern:** Full hierarchy with all specialist Workers + Reviewers + Top-Level Approver

## Anti-Patterns

1. **Swarm for trivial work** — spawning 5 agents to fix a typo
2. **Overspawning** — 10 agents when 3 would do (wastes tokens, time)
3. **Underspawning** — solo work on a multi-system task (misses parallelism, takes too long)
4. **Splitting dependent tasks** — parallel agents writing to the same file
5. **Skipping the Reviewer** — Worker finishes, done. No. Always pair.
6. **Fixed swarm size** — always spawning N regardless of task. Assess first.

## Integration with Multi-Agent System

This skill works WITH the existing Worker ↔ Reviewer ↔ Top-Level Approver hierarchy:

1. **Assess** → decide swarm size
2. **Decompose** → create independent tasks
3. **Dispatch** → `delegate_task(tasks=[...])`
4. **Each Worker** → implements within its domain
5. **Each Reviewer** → reviews its Worker's output
6. **Top-Level Approver** → reviews integrated change (for swarms of 3+)

For PAIR pattern (2 agents), skip the Top-Level Approver — the Reviewer's clean pass is sufficient.

## Quick Reference

```
1. Score the task (5 dimensions, 1-5 each)
2. Total score → decide size (Solo/Pair/Swarm/Mega-swarm)
3. Decompose into independent tasks
4. Dispatch via delegate_task(tasks=[...])
5. Each Worker → Reviewer loop
6. Top-Level Approver (if 3+ Workers)
7. Final clean pass → DONE
```

## Pitfalls

1. **Don't assess after starting work** — assess BEFORE writing any code
2. **Don't fix the swarm size** — re-assess if the task changes mid-flight
3. **Don't skip decomposition** — a swarm of 1 is just solo work with extra steps
4. **Don't forget the Reviewer** — every Worker gets one, no exceptions
5. **Don't ignore dependencies** — if Task B needs Task A's output, sequence them

## Verification

- [ ] Task scored on all 5 dimensions
- [ ] Swarm size matches score
- [ ] Tasks are independent (no shared file writes)
- [ ] Each Worker has clear scope and verification command
- [ ] Reviewer assigned to each Worker
- [ ] Top-Level Approver assigned (if 3+ Workers)
- [ ] All agents dispatched in ONE delegate_task call
