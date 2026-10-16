# OpenRig Skill

**Use when:** Working with the OpenRig system in neo-light — creating projects, missions, slices, checking intent chains, or using the intelligence factory.

## What is OpenRig?

OpenRig is a declarative multi-agent control plane. It turns AI coding agents from a pile of terminal sessions into a persistent, organized team. The core abstraction is the **intelligence factory**: the software development lifecycle as a primitive.

## Core Concepts

### Seat
A stable agent configuration with an address and tribal wisdom inheritance. "The agent is not the chair, it sits in the chair." Seats provide:
- Stable configuration (role, skills, model settings)
- Stable address for messaging
- Tribal wisdom inheritance (learnings passed between agent generations)

### Pod
A shared-context team. Agents in the same pod share memory and communicate freely. Pods are defined in `rigspec.yaml`.

### Project → Mission → Slice
The intelligence factory hierarchy:
- **Project** — the big picture, what we're building and why
- **Mission** — an entire release or accomplishment
- **Slice** — a specific change with a spec (intent) and proof (evidence)

### Refocus
Intent-chain tracing from slice → mission → project. Prevents doghouse-to-moonbase scope creep by asking: "Is what you're doing right now aligned with the bigger picture?"

### APM (Agent Productivity Monitoring)
Watches the ratio of ceremony (checks, handoffs, approvals) to progress (slices completed, tasks shipped). Alerts the BOA when ceremony exceeds thresholds.

## How to Use

### Create a Project
```python
from openrig.factory import IntelligenceFactory
factory = IntelligenceFactory()
project = factory.create_project("my-project", "My Project", "Build something great")
```

### Create a Mission
```python
mission = factory.create_mission("my-project", "mission-1", "First Release", "Ship the first version", sequence=1)
```

### Create a Slice
```python
slice_obj = factory.create_slice("my-project", "mission-1", "slice-1", "Add feature X", "Implement feature X with tests")
```

### Check Intent Chain
```python
chain = factory.get_intent_chain("slice-1")
# Returns: {"project": "...", "mission": "...", "slice": "..."}
```

### Auto-Slice (Swarm Hook)
```python
slices = factory.auto_slice("Big task description", "my-project", "mission-1")
# Creates slices when task exceeds thresholds
```

## File Structure

```
work/projects/
└── <project-id>/
    ├── project.yaml
    └── missions/
        └── <mission-id>/
            ├── mission.yaml
            └── slices/
                └── <slice-id>.yaml
```

## Feature Flag

Set `NEO_OPENRIG_MODE=1` to enable OpenRig mode. When unset, falls back to the current token_optimiser path.

## Governance

- Privacy keywords force T1 routing regardless of pod configuration
- Human-ask gates survive all migrations
- learning_log.jsonl audit trail is preserved
- Tribal wisdom inheritance must pass review loops before propagation
- Every worker has a paired reviewer
- Swarms of 3+ require a Top-Level Approver

## Phases

| Phase | What | Status |
|-------|------|--------|
| 1 | RigSpec + Seats + Pods | DONE |
| 2 | Intelligence Factory (Project→Mission→Slice) | IN PROGRESS |
| 3 | Refocus (intent-chain tracing) | PENDING |
| 4 | APM (ceremony vs progress) | PENDING |
| 5 | Dogfood + Package | PENDING |

## Scope Verifier (NEW in v0.2.0-swarm-guard)

The verifier (`openrig.verifier`) is the guardrail between a worker finishing
and its output shipping. It exists because v1/v2 of the guardrail
(LLM-verdict-on-worker-transcript) under- or over-detected scope drift.

### Three layers, cheapest first

1. **Tool evidence** � O(1), zero model calls. If the worker touched any
   tool outside the slice's ALLOWED set, FAIL immediately.
2. **Heuristic pre-filter** � O(n) text, zero model calls. Looks for
   action verbs (`sent`, `installed`, `drafted`, `created ticket`, ...).
   Side-effect-free phrasing passes; suspicious ones escalate.
3. **LLM ambiguous band** � O(1) model call, invoked ONLY when layers 1-2
   cannot classify. Opt-in via `use_llm=True`.

Layer 3 degrades safely (FAIL-closed → human review) when no LLM endpoint
is available, so production never trusts ambiguous cases.

### Usage

```python
from openrig.verifier import verify, ToolTrace, is_guard_enabled
trace = ToolTrace()
# inside the worker: trace.record("file_write", {"path": "x"})
result = verify(
    slice_id="invoice-hours-02",
    tool_calls=trace.names(),
    output_text=worker_output,
    allowed_tools={"vault_read", "csv_write_local"},
    non_goals=["do not create invoice", "do not email client"],
    spec="Recompute billable hours ...",
)
# result["verdict"] in {"PASS", "FAIL"}; result["layer"] in {tool, heuristic, llm, human-gate, ...}
if result["verdict"] != "PASS":
    # log to work/refocus or escalate to human
    ...
```

### Tool-call capture contract

For the verifier to work in production, the execution layer (Hermes
`delegate_task`, OpenAI Agents SDK, whatever) must surface a per-worker list
of tool function names. The verifier takes whatever string list is provided;
if the runtime cannot expose this, tool-evidence degrades to "no tools" and
all slices fall through to heuristic/LLM layers (recovering the v1 80%
recall behaviour). Agents should call `trace.record(name, args)` from each
tool handler and persist `trace.names()` with the worker result.

### Permission model

`build_allowed_tools(slice_id, non_goals=...)` infers a per-slice tool set
from the non_goals text ("Allowed: read, search") or falls back to the
read-only baseline. Passed-in `allowed_tools` always wins.
