# Service-Desk records

Vault path: `~/Documents/Clarity/01-Projects/Service-Desk/`

Open work WarPuppy must see also lives on the corkboard. Pin / peel via `/clarity-stickynote`. Map: `board.md`.

No secrets. No mail bodies. No calendar dumps.

| File | What |
|------|------|
| `README.md` | How to use the desk |
| `catalogue.md` | Services + CIs |
| `incidents.md` | Incident log |
| `problems.md` | Problems + known errors |
| `changes.md` | Change schedule / RFC log |
| `requests.md` | Service request log |
| `improve.md` | Continual improvement register |
| `slas.md` | Draft service targets |
| `knowledge.md` | Short articles + pointers |

## IDs

Next number = last number in that file + 1. Year is Africa/Johannesburg.

`INC-YYYY-NNN` · `PRB-YYYY-NNN` · `KE-YYYY-NNN` · `CHG-YYYY-NNN` · `REQ-YYYY-NNN` · `CSI-YYYY-NNN`

A known error is a problem that has been analyzed. Give it a `KE-` in the same `problems.md` row. Do not open a second file.

## Status words

`open` · `in progress` · `workaround` · `resolved` · `closed` · `scheduled` · `cancelled`

Close when the user (WarPuppy, or the client) can use the service again and the record is complete. Resolved + no loose ends = closed.

## Do not

- Duplicate a record in Daily-Notes. Daily report can say "INC-2026-001 closed".
- Log events that stay informational. Only exceptions that become incidents (or a problem).
