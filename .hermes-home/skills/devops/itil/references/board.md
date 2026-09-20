# Notice board (sticky notes)

Live face of the desk. Vault logs stay the record. The corkboard is how WarPuppy sees open work without opening markdown.

How to pin / peel / park: `/clarity-stickynote` only. Do not edit `stickynotes.json` by hand. Do not invent a second board.

Cockpit: http://192.168.1.10:3001 (**Clarity cockpit**) and http://192.168.1.10:9108/

## When

| Record | Kind | Pin | Peel / park |
|--------|------|-----|-------------|
| INC P1 or P2 | WARN | As soon as classified. P1: pin in the same breath as telling WarPuppy. | Peel when the INC is resolved or closed. |
| INC P3 or P4 | — | No note. Vault only. | — |
| PRB / KE open | FIND | When the problem is opened or becomes a known error. | Peel when the PRB is closed. Park if accepted as residual risk. |
| CHG normal or emergency, waiting auth or scheduled | DECIDE | When the CHG is logged. | Peel when implemented or cancelled. |
| CHG standard | — | No note. | — |
| REQ waiting on WarPuppy | DECIDE | When blocked on a yes. | Peel when fulfilled or refused. |
| CSI waiting on WarPuppy | DECIDE | When logged if it needs a decision. | Peel when checked and closed. |
| Reusable workaround, no PRB yet | LEARN | After restore, once. | Peel when a KE exists (the FIND replaces it). |

One note per record ID. Title = kebab of the ID (`inc-2026-001`). Project: `Service-Desk`. Scope: `cross`. Body: ID, service, one-line state. No secrets, no mail, no rands.

## Pin shape

```bash
python3 ~/.grok/skills/clarity-stickynote/scripts/board.py pin \
  --kind WARN --scope cross --project Service-Desk \
  --title inc-2026-001 \
  --body "INC-2026-001 P1 llama :8081 down. Restoring."
```

After pin / peel / park, the script already snapshots to the cockpit. Do not also hand-edit Grafana.

## Do not

- Pin informational events.
- Pin ordinary project work.
- Leave a WARN up after the service is back.
- Duplicate the same INC as WARN and FIND.
