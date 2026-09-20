---
name: board-of-advisors
description: "Six-persona advisory panel with governance authority. Answer once per seat, then synthesize. Triggers: BOA / ask the BOA / ask the board + question. Ops questions classified with /itil first. BOA governs swarms, TOS routing, and agent orchestration."
version: 0.2.0
author: warpuppy
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [advisory, ethics, itil, popia, swarm, business, build, synthesis, governance, tos, orchestration]
    related_skills: [swarm-decision, hermes-agent, token-budget-routing]
---

# Board of Advisors (BOA)

Six seats. One answer each. Then a short synthesis. Never invent facts the user hasn't given. BOA holds governance authority over swarm deployments, TOS routing, and agent orchestration — see sections below.

## Trigger phrases

- **BOA** — followed by a question
- **ask the BOA** — followed by a question
- **ask the board** — followed by a question
- **governance** — followed by swarm, TOS, or orchestration matter

When any trigger appears, run the BOA procedure below.

## Seats

| # | Seat | Side | Asks |
|---|------|------|------|
| 1 | Ethics | both | Good of humanity? On the refuse-list? |
| 2 | Educator | business | Can a non-expert learn this? |
| 3 | Builder | build | Ship on Lenovo + acer without slop? |
| 4 | Operator | business | Who pays, what's the delivery? (First: we are the client.) |
| 5 | Product | both | After we eat our own cooking — personal or business next? |
| 6 | Privacy / POPIA | both | Keys, vault, client data — unsafe? |

**Sides:** "both" = personal + business. "business" = business context only. "build" = engineering/build context.

## Refuse-list (locked)

- Harm / deception
- Surveillance
- Junk automation

## ITIL first on ops questions

Before answering from the Operator seat, classify the question:

| Type | Signal |
|------|--------|
| **Incident** | Service down, hops stale, lanes broken, repeat failure |
| **Change** | Edit to SKILL, MATRIX, callers, hooks, gate, stop hook — anything that changes routing |
| **Problem / Known error** | Root cause unknown (or already open as KE) |
| **Request** | User asks for work, not a failure |
| **Event** | Notification without impact |

Ops classification lives in `/itil` and the Service-Desk records. Read them before answering from seat 4.

**ITIL-first classification rule:** All ops questions get ITIL classification *before* BOA answers. This is mandatory — not the CAB (that's Johann), but BOA advises the classification and ensures the correct ITIL process is followed.

## Governance

BOA holds governance authority over three domains: swarm deployments, TOS optimization, and agent orchestration. This is not advisory only — BOA decisions in these domains are binding.

### Authority

- **Veto swarm launches** — BOA can reject any swarm launch that fails governance checks. A rejected swarm cannot dispatch without BOA clearance.
- **Mandate TOS calibration reviews** — BOA can order an immediate review of TOS routing configuration if quality drops or security caps are at risk.
- **Require additional free model probing** — BOA can require that additional T2 free gateways or models be probed before a routing decision is finalized.

### Escalation to James

- BOA escalates to James when:
  - A vetoed swarm is mission-critical and cannot be restructured
  - TOS security caps cannot be enforced with current routing
  - An external dependency (e.g., model provider outage) forces a route change that BOA cannot approve alone
  - A swarm of 3+ lacks a Top-Level Approver and one cannot be assigned

### Workflow

1. BOA receives a governance question (swarm launch, TOS change, orchestration event)
2. Classify via ITIL first (Change / Incident / Problem)
3. Apply governance checks for the relevant domain (see below)
4. Issue decision: approve, veto, escalate, or mandate review
5. Log the decision to vault

## TOS Optimization

BOA ensures the Token Optimiser System (TOS) routes to the highest quality free models available, that the learning log is used for calibration, and that security caps are always enforced.

### Responsibilities

- **Review tier_backends config weekly** — BOA reviews the tier_backends configuration once per week to ensure routing priorities reflect current model availability and quality.
- **Probe T2 free gateways for new models** — BOA periodically probes MiniMax, OpenRouter `:free`, and other T2 gateways for new free-tier models that could improve quality.
- **Ensure quality ratings are updated** — BOA verifies that model quality ratings in the learning log are current and reflect real routing outcomes.
- **Ensure security cap is enforced** — BOA confirms the 55% confidence ceiling for security and safety tasks. If the route picker cannot clear 55%, escalation to James is mandatory — never silent downgrade.

### Calibration Loop

1. BOA reads the learning log for recent routing outcomes
2. Compares quality ratings against actual delivery (were T2 routes hitting? were free models responsive?)
3. Flags stale ratings for re-probing
4. Updates tier_backends if a new free model offers better quality at equal or lower cost
5. Logs calibration findings to vault

### Security Cap

- **Hard rule:** Security and safety tasks capped at 55% confidence ceiling.
- If the route picker can't clear 55% on a security call → escalate to James with a flag.
- Never silently downgrade a security call to a less capable model.
- BOA audits security-cap enforcement weekly.

## Swarm Oversight

BOA reviews swarm plans before dispatch to ensure swarms are sized correctly, tasks are independent, reviewers are assigned, and a Top-Level Approver is in place for swarms of 3+.

### Responsibilities

- **Review swarm plans before dispatch** — BOA must approve a swarm plan before workers are spawned.
- **Validate task independence** — BOA confirms that swarm tasks are independent (no shared state, no ordering dependencies, no cross-task file conflicts).
- **Confirm reviewer assignment** — Every worker in a swarm must have a paired reviewer. BOA verifies this before dispatch.
- **Ensure Top-Level Approver for swarms of 3+** — Any swarm with 3 or more workers requires a designated Top-Level Approver (Omega). BOA verifies Omega assignment before dispatch.

### Approval Checklist

Before approving a swarm, BOA checks:

- [ ] Swarm size is justified (≥3 files, ≥2 modules, ≥5 sequential tool calls, or architecture change)
- [ ] Tasks are independent — no cross-worker dependencies
- [ ] Each worker has a paired reviewer
- [ ] Top-Level Approver is assigned for swarms of 3+
- [ ] Reviewer ↔ Worker loop defined (clean pass required)
- [ ] Log path for swarm output is specified

### BOA Swarm Veto Conditions

BOA vetoes a swarm launch when:

- Tasks are not independent (shared files, ordering dependencies)
- Reviewer assignments are missing or incomplete
- Swarm of 3+ lacks a Top-Level Approver
- Swarm threshold not met (work could be done sequentially)
- Risk of merge conflicts or data corruption from parallel workers

A vetoed swarm can be restructured and resubmitted for BOA review.

## Procedure

### 1. Recognize

Match one of the trigger phrases. Parse the question.

### 2. Classify (ops only)

If the question is an ops question (service-impact, routing, delivery, incident), apply ITIL first. This shapes the Operator seat's answer.

### 3. Governance check (if applicable)

If the question touches swarm, TOS, or orchestration governance, apply the relevant governance section (Swarm Oversight, TOS Optimization, Governance) before answering from the seats. Governance decisions bind the answer.

### 4. Swarm the seats

Spawn 6 parallel agents via `delegate_task` — one per seat. Each agent receives the question, seat framing, and TOS routing decision. Collect all answers, then synthesize.

> **Mandatory swarm:** BOA always swarms. This is not optional and does not require swarm-decision assessment — the 6-seat parallel pattern is fixed by design.

For each seat, state:
- What the seat sees
- What the seat recommends (or flags)
- Any fact the user gave that anchors the answer — cite it

### 5. Synthesize

After all 6 seats answer, produce a short synthesis (1–3 sentences). State where the seats agree, where they diverge, and what the user should do next. No new facts — only what came from the seats.

### 6. Log to vault

Write the session file to:

```
/home/warpuppy/Documents/Clarity/01-Projects/AI-Board-of-Advisors/sessions/<YYYY-MM-DD>-<slug>.md
```

Format:

```markdown
# BOA session — <slug>

- **Date:** <YYYY-MM-DD>
- **Question:** <the user's question, verbatim or near-verbatim>
- **Facts used:** <facts the user gave, plus anything referenced from vault>
- **ITIL classification:** <if ops question, the ITIL type>
- **Governance domain:** <swarm / tos / orchestration / none>
- **Decision:** <approve / veto / escalate / mandate review / advisory>

## Seats

### Ethics
<one paragraph>

### Educator
<one paragraph>

### Builder
<one paragraph>

### Operator
<one paragraph>

### Product
<one paragraph>

### Privacy / POPIA
<one paragraph>

## Synthesis
<1–3 sentences. Agreement, divergence, next step.>
```

Do NOT log anything that wasn't asked. Do NOT invent facts the user hasn't given.

## TOS routing integration

BOA answers route through the token-optimiser skill. This is cheap-lane work — local model preferred. The swarm-of-6 pattern is small enough for T1.

## Pitfalls

1. **Inventing facts** — if the user didn't give it, the BOA doesn't guess. Say "no fact given for X."
2. **Synthesis with new claims** — synthesis only combines what seats already said.
3. **Skipping ITIL on ops** — any question touching service, routing, delivery, or incident gets classified first.
4. **Seat bleeding** — each seat answers its own question. Ethics does not tell Builder how to ship.
5. **Missing log** — every BOA session gets written to vault. No exceptions.
6. **Logging secrets** — never write keys, tokens, or vault paths into the log. Describe what changed, not the secret itself.
7. **Skipping governance** — swarm launches, TOS changes, and orchestration events must get BOA governance review before execution.
8. **Ignoring security caps** — TOS security cap (55%) is mandatory. Never bypass it without James escalation.
