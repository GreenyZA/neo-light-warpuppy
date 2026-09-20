# ITIL 4 practices — map for Light Engine

34 practices. We run nine. The rest stay on this list so Neo does not invent a tenth skill.

Purposes below are the public ITIL 4 purpose statements, shortened.

## Run these (skills on disk)

| Practice | Purpose | Skill |
|----------|---------|-------|
| Service desk | Capture demand for incident resolution and service requests. Single point of contact. | `/itil-service-desk` |
| Incident management | Minimize the negative impact of incidents by restoring normal service operation as quickly as possible. | `/itil-incident` |
| Problem management | Reduce likelihood and impact of incidents by identifying causes and managing workarounds and known errors. | `/itil-problem` |
| Change enablement | Maximize successful changes by assessing risk, authorizing, and managing the change schedule. | `/itil-change` |
| Service request management | Handle predefined, user-initiated service requests effectively. | `/itil-request` |
| Monitoring and event management | Observe, analyze, and respond to state changes that matter. | `/itil-event` |
| Continual improvement | Align practices and services with changing needs through ongoing improvement. | `/itil-improve` |
| Knowledge management | Maintain and improve effective use of information and knowledge. | `/itil-knowledge` |
| Service level management | Set business-based targets and assess delivery against them. | `/itil-level` |

## Do not stand up (use what already exists)

| Practice | What we already do |
|----------|-------------------|
| Service catalogue management | `catalogue.md` is the catalogue. Keep it true. |
| Service configuration management | Catalogue rows are the CIs. No CMDB tool. |
| Information security management | Keys in `~/.config/`. No secrets in the vault. Ask before anything security-sensitive. |
| Risk management | Ask WarPuppy before destructive / public / irreversible. |
| Relationship management | `/clarity-olivia` + Customers notes. |
| Supplier management | Google, GitHub, OR, NV — keys and accounts already documented outside the vault. |
| Measurement and reporting | Daily report + Grafana. No second dashboard. |
| Deployment management | Git push / compose up. Fold into `/itil-change`. |
| Release management | Fold into `/itil-change` until we ship to a client. |
| Service validation and testing | Smoke the change. Fold into `/itil-change`. |
| Infrastructure and platform management | acer + Lenovo + `/clarity-gpu` + `omarchy`. |
| Software development and management | `~/Work`, `~/Projects`, `/ponytail`. |
| Architecture management | Constitutions + INDEX. |
| Strategy / portfolio / project | Command Center + board. |
| Service financial management | Billing project. After the lock. No invented rands. |
| Availability / capacity and performance | Grafana + `/clarity-gpu`. Raise a problem if a pattern appears. |
| Service continuity | Vault-Restore. Dry-run is lock job 3. |
| Service design / business analysis | Board + constitutions when designing a client service. |
| Organizational change management | WarPuppy's call. Do not run people-change theatre. |
| Workforce and talent | Not a practice we run. |
| IT asset management | Two machines. Catalogue is enough. |
| Service desk (tooling) | Markdown logs. Not a ticket product. |

If a job looks like one of the parked practices, do the work with the existing skill or note, and log under the nearest run practice (usually change, problem, or improve).
