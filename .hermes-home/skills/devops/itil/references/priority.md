# Priority

Impact × urgency. One home.

| | Urgent (getting worse, no workaround, user stuck now) | Not urgent (workaround exists, or can wait) |
|---|---|---|
| **High impact** (client-facing, or a named shop-floor service down, or WarPuppy blocked) | **P1** major | **P2** |
| **Low impact** (one convenience, non-critical CI, quality niggle) | **P3** | **P4** |

## P1 / major

Tell WarPuppy immediately. Then restore. Then log.

Examples: wiki, Grafana, Portainer, llama `:8081`, vault unreadable, client site down, mail hook dead when he needs it.

## Response (desk clock, SAST)

Targets, not contracts. One home for these clocks. `slas.md` holds service-specific drafts only.

| Priority | First update | Restore aim |
|----------|--------------|-------------|
| P1 | immediate | 30 min |
| P2 | 30 min | 4 h |
| P3 | next work block | 1 day |
| P4 | next daily report | when it fits |

A workaround that gives the outcome counts as restore. The problem stays open.
