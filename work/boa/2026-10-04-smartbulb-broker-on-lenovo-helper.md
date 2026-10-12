# BOA Report — Smart-Bulb Status Broker on the Lenovo Helper (anvil)

- **Date:** 2026-10-04
- **Author:** Monica (orchestrator), for the Board of Advisors
- **Question (user):** "Is this something we can run on the Lenovo as part of its
  helper function?"
- **Context:** follow-up to `2026-10-04-smartbulb-assistant-status-layer.md`
- **ITIL:** CHANGE (new helper service). Not an incident.

---

## Direct answer

**Yes — and the Lenovo is the *better* home for the broker than the Acer.**

The Lenovo (`anvil`, 192.168.1.8) is a **headless, always-on helper**. A status
broker *should* be a small always-on background daemon, so putting it on the
helper is not a compromise — it is the correct placement.

## Verified facts (measured this session)

| Check | Result |
|---|---|
| Lenovo reachable | ✅ ping 192.168.1.8 OK, `ssh anvil` OK |
| **Bulb reachable FROM the Lenovo** | ✅ YES — anvil can ping 192.168.1.225 |
| Python on Lenovo | ✅ 3.14.7 |
| systemd user bus on Lenovo | ✅ running (can host a service) |
| Existing helper services | ✅ distccd `:3632` active, helper-status `:9129` active |
| Lenovo role | vanilla Arch, **headless** (no GUI/Omarchy/bar) |
| Hardware | i5-7500T 4c/4t, 15 GiB — massively overkill for a timer + LAN writes |

## Why the Lenovo is the right host

1. **Always-on.** A status light must work whether or not the Acer's desktop is up.
   The helper is the box designed to always be available.
2. **Direct path to the bulb.** Verified: anvil reaches 192.168.1.225 on the LAN,
   with no dependency on the Acer being awake.
3. **Fits the helper role.** anvil already runs `helper-status :9129`, distccd, NFS.
   A bulb-status broker is the same class of service: headless, LAN-facing, tiny.
4. **Zero contention.** It is CPU/IO work; it cannot disturb the Lenovo's helper
   duties (distcc, mirror, T1b) any more than `helper-status` already does.
5. **Survives reboots/shells.** As a systemd service on the headless box it is
   always there — which is exactly what "always programmed into Hermes" requires.

## Architecture (updated)

```
Hermes agent (any box)                 Lenovo helper (anvil, always-on)
  working ──┐                            ┌─ status broker (systemd service)
  needs_input ──► HTTP/local call ──────►│    • base_state = dim cold white
  done/error ┘   to broker :9xxx         │    • pattern library (config)
                                          │    • priority + mutex
                                          └─► Tapo bulb (192.168.1.225)
Omarchy panel (Acer) ── queries broker status API (viewer/override only)
```

- The **broker lives on the Lenovo**, owns base state, the pattern library and the
  precedence mutex, and is the only thing that talks to the bulb.
- **Hermes emits events** to the broker (a tiny local HTTP call). Hermes does not
  touch the bulb directly.
- The **Omarchy panel becomes a viewer** on the Acer (queries the broker's status
  endpoint); it no longer owns control.

## Board decisions

### Architect
Put the broker on the always-on headless node; keep it the single writer to the
bulb. Hermes and the panel are *clients*. This removes the Acer-desktop dependency
entirely — the light works even when the workstation is off.

### Engineer
- Run it as a **systemd system service** on anvil (headless → no login session; a
  user service would need `loginctl enable-linger`, so system service is cleaner).
- **Install the Tapo library on the Lenovo** — the old `.tapo-venv` was on the Acer
  and was wiped 2026-10-02; it does not exist on anvil yet.
- **Credentials** (`.env`) must be provisioned on anvil (not copied from the dead
  Acer venv — re-enter from the vault).
- Bind the broker to the LAN (`192.168.1.8:<port>`) and firewall it to the LAN,
  consistent with `helper-status :9129` ("LAN from acer only").
- Reuse the existing command vocabulary from `status.py`
  (`white`, `red`, `flash`, `pulse`, `blink`, `ct`, `brightness`).

### Researcher
- This mirrors the `helper-status :9129` pattern already proven on anvil: a small
  Python HTTP service exposing helper state on the LAN. Precedent exists on this
  very box.
- No GPU anywhere in the path — CPU/IO only, as established in the prior report.

### Reviewer — risks & blind spots
1. **Single point of failure is now the Lenovo.** If anvil is off/down, the light
   goes dark. Acceptable (it is the always-on helper), but the broker must fail
   silently and never block Hermes waiting on a light.
2. **Two writers risk.** Until the Acer panel is demoted to a viewer, both could
   write the bulb. Cut the panel over to read-only *before* enabling the broker.
3. **Credentials on a second box.** Store in a root-owned `.env` (mode 600) on
   anvil; do not commit; do not copy the dead Acer file.
4. **No bulb state feedback** (error 1003) — broker tracks last-commanded state.
5. **LAN exposure** — bind to LAN and firewall, matching the `:9129` precedent.
6. **WOL interaction** — if anvil is asleep, the light is unavailable; consider
   arming WOL or accepting the gap.

### Budget (Token Optimiser)
Zero tokens, zero GPU. Deterministic state machine on the helper CPU. Not an LLM
task — do not route it anywhere.

### Executive (Chair) — decision
1. **Proceed. Host the broker on the Lenovo helper (anvil) as a systemd service.**
2. **Prerequisites:** install Tapo lib on anvil; provision credentials; demote the
   Acer panel to a viewer.
3. **First prototype:** broker with `idle` + `working` + `needs_input` only, then
   extend to the full pattern library.
4. **Keep the GPU out of it** — reaffirmed.

## Open questions for the user
1. Confirm broker **host = Lenovo** (this report's recommendation) — yes/no?
2. Which **port** for the broker on anvil (e.g. `:9130`, next to helper-status `:9129`)?
3. Demote the Omarchy panel to **viewer-only** now, or keep dual control during build?

## Decision log (Monica)

- **Port: `192.168.1.8:9130`** — chosen 2026-10-04. Verified free on anvil
  (current listeners: 22, 53, 111, 2049, 3632, 5037, 5355, 9129, 20048 + ephemerals).
  Sits immediately next to `helper-status :9129` so firewall rules group as `9129-9130`
  and the convention reads "9129 = helper status, 9130 = light status".
