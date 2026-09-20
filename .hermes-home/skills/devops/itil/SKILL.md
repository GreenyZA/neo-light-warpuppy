---
name: itil
description: >
  Apply ITIL 4 to Light Engine operations. Classify demand as incident,
  problem, change, request, or event. Includes the service catalogue,
  classification rules, P1-P4 priority matrix, incident response flow,
  problem management, change enablement, and SLA targets. Use when the
  user says /itil, ITIL, ITSM, major incident, known error, service desk,
  change enablement, "log this as ITIL", or names incident / problem /
  change / request in an ops sense.
version: 1.0.0
author: Light Engine (Neo) + Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [itil, itsm, service-desk, incident, problem, change, event, devops]
    category: devops
    requires_toolsets: []
environments:
  - light-engine
---

# ITIL 4 for Light Engine

ITIL 4 framework for Light Engine operations. Neo is the service desk. WarPuppy is the authority (CAB, major-incident owner).

ITIL® is a registered trademark of PeopleCert. This skill applies public ITIL 4 concepts. It is not official training and does not copy PeopleCert publications.

Records: `~/Documents/Clarity/01-Projects/Service-Desk/`. Open P1/P2 work also goes on the corkboard via `/clarity-stickynote` — map in `references/board.md`. Facts live in `references/`. Do not restate them here.

---

## Service Catalogue

Services and Configuration Items (CIs) for Light Engine. Keep it true.

| Service | CI / URL | Host | Owner skill | Notes |
|---------|----------|------|-------------|-------|
| TOS (Token Optimiser Skill) | callers + `hops.jsonl` + MATRIX | Lenovo + acer | `/token-optimiser` | live. Routing edits = Change. Hops stale = Incident |
| T1 Vulkan (fast) | http://192.168.1.10:8081 | acer | `/clarity-gpu` | 3B model, 4096 ctx. HTTP 200 when healthy |
| T2 free cloud (MiniMax) | cloud | — | TOS routing | Free tier. First fallback after T1 |
| T3 paid (SuperGrok/Ultra) | cloud | — | `/bring-grok` | Only when local/free failed. Never default |
| Vault | `~/Documents/Clarity` | Lenovo (+ acer mirror) | `/clarity-ingest` `/clarity-improve` | live |
| Board of Advisors (BOA) | parallel seat agents | this session | `/board-of-advisors` | Six seats: Ethics, Educator, Builder, Operator, Product, Privacy |
| Swarm | delegate_task workers | this session | `/swarm-decision` | Parallel agent dispatch for non-trivial work |
| Grafana | http://192.168.1.10:3001 | acer | `acer-obs` | HTTP 200 `/login` |
| Prometheus | http://192.168.1.10:9090 | acer | `acer-obs` | Metrics store |
| Wiki | http://192.168.1.10:3020 | acer | vault → wiki only | Read-only vault mirror |

---

## Classification Rules

One type per demand. If mixed, treat the break as incident first.

| Signal | Type |
|--------|------|
| Unplanned break or quality drop | **Incident** |
| Cause, or suspected cause, of one or more incidents | **Problem** |
| Add, modify, or remove anything that could affect a service | **Change** |
| Pre-agreed, user-initiated, normal part of the service | **Request** |
| State change of a CI that matters | **Event** |

### TOS routing rules (from BOA 2026-08-19)

| What | Type |
|------|------|
| Run `gate.sh` / `route-grunt.sh` (operate the service) | Not a ticket. Normal operations. |
| Hops stale, weekly climbing, lanes up | **Incident** |
| Edit TOS routing (SKILL, MATRIX, callers, hooks, gate, stop hook) | **Change** |
| Why hops stay at zero (root cause) | **Problem** |

---

## Priority Matrix

Impact × urgency.

| | Urgent (getting worse, no workaround, user stuck now) | Not urgent (workaround exists, or can wait) |
|---|---|---|
| **High impact** (client-facing, or a named shop-floor service down, or WarPuppy blocked) | **P1** major | **P2** |
| **Low impact** (one convenience, non-critical CI, quality niggle) | **P3** | **P4** |

### Response targets (SAST)

| Priority | First update | Restore aim |
|----------|--------------|-------------|
| P1 | immediate | 30 min |
| P2 | 30 min | 4 h |
| P3 | next work block | 1 day |
| P4 | next daily report | when it fits |

P1 / major: tell WarPuppy now. Then restore. Then log.

---

## Incident Response Flow

Minimize negative impact by restoring normal service as fast as possible.

### Flow: Detect → Log → Classify → Resolve → Close

1. **Detect** — Something is down or quality has dropped. Confirm it is an incident (unplanned break or quality drop).
2. **Log** — Open `INC-YYYY-NNN` in `~/Documents/Clarity/01-Projects/Service-Desk/incidents.md`.
3. **Classify P1–P4** — Priority matrix above. P1: tell WarPuppy immediately, pin a WARN sticky.
4. **Known error?** — Check `problems.md` for a matching `KE-`. If one exists, apply the workaround now.
5. **Resolve** — Smallest safe restore. Use the technical skill that owns the CI. Workaround counts as restore. If a change is needed, open CHG in parallel — do not wait for RCA.
6. **Confirm** — User can use the service again. Set status `resolved` or `workaround`.
7. **Close** — Record complete. Peel the WARN. Link to a problem if recurring or cause unclear.

### Record template

```
### INC-YYYY-NNN — YYYY-MM-DD HH:MM SAST
- Service / CI:
- Symptom:
- Priority:
- Status:
- Workaround:
- Restore action:
- Problem:
- Closed:
```

### Do not

- Delay restore to find the root cause.
- Reboot or `compose down -v` as a first move.
- Put passwords or tokens in the INC.
- Skip the log because the fix was "quick."

---

## Problem Management

Reduce likelihood and impact of incidents by identifying causes and managing workarounds and known errors.

### Flow: Root Cause → Known Error → Workaround

1. **Trigger** — Repeat INC, major INC with unknown cause, or suspected cause before the next INC.
2. **Open** — `PRB-YYYY-NNN` in `problems.md`. Link the INC IDs. Pin a FIND sticky.
3. **Workaround now** — If one exists, write it so the next incident can apply it without thinking.
4. **Root cause analysis** — Start where you are: last INC, Grafana, unit logs, `diagnose-crash`, `/clarity-gpu`. One cause statement. "Unknown" is allowed; then it is not a known error yet.
5. **Known error** — When cause is understood, mark `KE-YYYY-NNN` on the same row. Keep the workaround current.
6. **Permanent fix** — A change. Open `CHG-YYYY-NNN`. Do not fix live in the problem record.
7. **Close** — Change is in and a watch period shows no repeat (or WarPuppy accepts residual risk). Peel the FIND.

### Error control vs problem control

- **Problem control:** understand the cause.
- **Error control:** known error + workaround + decision to fix or accept.

Both live in `problems.md`. No second tracker.

### Record template

```
### PRB-YYYY-NNN — YYYY-MM-DD
- Incidents:
- Status:
- Cause:
- Known error:
- Workaround:
- Change:
- Closed:
```

---

## Change Enablement

Maximize successful changes by assessing risk, authorizing, and managing the change schedule.

### Types

| Type | When | Auth |
|------|------|------|
| **Standard** | On the list, done the same way, low risk | Pre-authorized. Log after or while doing it. |
| **Normal** | Everything else reversible | WarPuppy says yes. Schedule it. |
| **Emergency** | Needed to restore P1, or delay makes it worse | WarPuppy. If unreachable, do it, then tell him. |

### Standard changes (this shop)

- Restart `llama-vulkan` (`ssh server 'systemctl --user restart llama-vulkan'`).
- Restart a named compose stack **without** `-v`.
- `acer-obs` status / targets / logs (read).
- Pin / peel a sticky note.
- Vault note edits that do not change constitution, public face, or secrets.
- Daily report.
- Run TOS callers / `gate.sh` (operate the service). **Editing** TOS routing is not standard.

Anything that changes image tags, volumes, firewall, host packages, DNS, public repos, or Portainer admin is **not standard**. TOS routing edits are **normal** until the same change has worked twice. Then it can become standard.

### CHG numbering

`CHG-YYYY-NNN` where NNN increments from the last CHG in `changes.md`. Year is Africa/Johannesburg.

### Steps

1. Classify type. If it is a restore, keep the INC open.
2. Write `CHG-YYYY-NNN` in `changes.md` **before** a normal or emergency change. Standard may be logged immediately after. Normal / emergency: pin a DECIDE sticky.
3. State: what, why, CI, risk, backout, when.
4. Get auth if required. Do not implement a normal change on a nod.
5. Implement. Smallest step. Smoke the service from the catalogue. TOS routing: `tos-op-check.sh` must exit 0 before the CHG is done.
6. Backout if smoke fails. Then tell WarPuppy.
7. Close when smoke passed. Peel the DECIDE.

### Record template

```
### CHG-YYYY-NNN — YYYY-MM-DD
- Type: standard | normal | emergency
- CI:
- What:
- Why:
- Risk:
- Backout:
- Auth:
- When:
- Status:
- Result:
```

### Do not

- `docker compose down -v`.
- Change Portainer image tag or reset admin.
- Force-push, delete remotes, or flip repo visibility.
- Skip backout on a normal change.

---

## Service Request Management

Handle predefined, user-initiated service requests effectively.

### On the menu (this shop)

- Status of a named service (acer-obs, GPU, wiki, calendar).
- Restart that is a standard change.
- Pin / peel a sticky note.
- Daily report.
- Calendar check.
- Draft a client mail — send only when WarPuppy says fire.
- Copy of a vault note or public teaser link.

Add a line only when we have done the same ask twice and WarPuppy wants it standing.

### Steps

1. Confirm it is predefined. If not: refuse, or treat as new work / a change.
2. Log `REQ-YYYY-NNN` in `requests.md`.
3. Fulfil with the owning skill. Ask before send / public / destructive. If blocked on WarPuppy, pin a DECIDE sticky.
4. Close when the user has the thing. Peel the DECIDE.

### Record template

```
### REQ-YYYY-NNN — YYYY-MM-DD
- Who:
- Ask:
- Status:
- Result:
```

---

## Event Management

Observe, analyze, and respond to state changes that matter.

### Types

| Type | Meaning | Action |
|------|---------|--------|
| Informational | Expected (backup finished, unit started) | Usually ignore. No record. |
| Warning | Approaching a limit | Watch. Note in daily report if it persists. |
| Exception | Unexpected, or a service is or will be affected | Treat as an incident. |

### Checks

```
acer-obs status
acer-obs targets
ssh server 'systemctl --user is-active llama-vulkan'
```

Crash dump → `diagnose-crash` as well as this classification.

### Steps

1. Name the CI and the state change. Check the service catalogue.
2. Type it. Informational stops here.
3. Exception → incident. Warning that repeats → consider a problem.
4. Do not log every scrape.

---

## Decide with the seven principles

1. **Focus on value** — who is blocked, and what outcome do they need?
2. **Start where you are** — check Grafana, the unit, the last record, the known-error list. Do not rebuild.
3. **Progress iteratively with feedback** — smallest restore or change that works. Then look again.
4. **Collaborate and promote visibility** — log it. Pin the corkboard. Tell WarPuppy on P1. Do not hide a workaround.
5. **Think and work holistically** — Lenovo + acer + client. A "fix" that breaks the wiki is not a fix.
6. **Keep it simple and practical** — no extra practice, form, or CAB theatre.
7. **Optimize and automate** — after it works twice the same way, make it a standard change or a script. Not before.

---

## Do not

- Stand up all 34 practices. Map is in `references/practices.md`. Run only what is on disk.
- Invent ticket numbers, SLAs, or rands.
- Put secrets, mail bodies, or calendar dumps in Service-Desk notes.
- Touch TCIMS. That repo stays later.
- Call vault tidy `/clarity-improve` a CSI item.
- Skip the log because the fix was "quick."
- Open both an incident and a request for the same ask.
- Treat an outage as a request.
- Open five CSI items in one turn.

---

## Record IDs

`INC-YYYY-NNN` · `PRB-YYYY-NNN` · `KE-YYYY-NNN` · `CHG-YYYY-NNN` · `REQ-YYYY-NNN` · `CSI-YYYY-NNN`

A known error is a problem that has been analyzed. Give it a `KE-` in the same row.

## Status words

`open` · `in progress` · `workaround` · `resolved` · `closed` · `scheduled` · `cancelled`

Close when the user can use the service again and the record is complete.
