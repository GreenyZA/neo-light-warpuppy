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
