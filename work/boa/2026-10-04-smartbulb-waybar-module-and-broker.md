# BOA Report — Smart-Bulb Status: Waybar Module + Lenovo Broker

- **Date:** 2026-10-04
- **Author:** Monica (orchestrator), for the Board of Advisors
- **Trigger (user):** "I moved off of Omarchy but a waybar for the smartbulb would
  be useful with similar flashing patterns than the smartbulb."
- **Supersedes UI layer of:** `2026-10-04-smartbulb-assistant-status-layer.md`
  and `2026-10-04-smartbulb-broker-on-lenovo-helper.md`

---

## 1. Environment change (measured)

| | Before | Now |
|---|---|---|
| Desktop | Omarchy shell | **vanilla Hyprland** (`~/.config/hypr/hyprland.lua`) |
| Bar | Omarchy panel (QML) | **waybar v0.15.0** (`~/.config/waybar/config`) |
| Bulb plugin | `~/.config/omarchy/plugins/warpuppy.smartbulb/` | **gone** |
| Tapo venv | `~/.tapo-venv` | **gone** (Acer) — and **never existed on anvil** |
| `tapo` python lib | installed | **not installed** (either box) |

**Consequence:** the QML panel is dead. The UI layer must be rebuilt as a **waybar
custom module**. The control/broker layer design is unchanged.

## 2. Recovered prior design (from `~/.grok/skills/omarchy-smartbulb`)

A working design already existed and should be reused, not reinvented:

- `~/.grok/skills/omarchy-smartbulb/scripts/bulb.sh` on the **Acer** is a wrapper
  that **SSHs to the daemon on anvil** and runs
  `python3 ~/.config/omarchy/plugins/warpuppy.smartbulb/status.py <cmd>`.
- Credentials live in anvil's plugin `.env` (never copied off-box).
- Documented patterns:

  | State | Command | Meaning |
  |---|---|---|
  | idle | `white` + `brightness 5` | cool white CT 4000 at 5% — the "cold white" park state |
  | question | `red` | only while a question is genuinely waiting |
  | done | `flash 10` then idle | white↔red flash ×10, return to idle 5% |

- **BUT: the daemon is gone on anvil too.** anvil was reloaded to vanilla Arch
  (2026-10-03) and `~/.config/omarchy/plugins/warpuppy.smartbulb/` does not exist
  there. So both the Acer plugin *and* the anvil daemon must be rebuilt.

## 3. Target architecture (waybar era)

```
Hermes agent (Acer) ──HTTP event──► Lenovo broker (anvil :9130, systemd)
   working                            • base_state = cool white 5%
   needs_input                        • pattern library + priority mutex
   done / error                       • ONLY writer to the bulb
                                       └─► Tapo bulb 192.168.1.225
waybar custom/smartbulb (Acer) ──GET /status──► anvil :9130
   (JSON: text/class/tooltip)          (viewer; flashes in sync with the bulb)
```

- **Broker = single source of truth** on anvil. Both the bulb and the waybar
  module read the *same* state, so the bar and the light stay in sync automatically.
- The old `bulb.sh` SSH path is replaced by a direct call to the broker on `:9130`
  (fewer moving parts; no SSH per action).

## 4. Waybar module design (matches existing bar conventions)

The bar already uses this pattern (`custom/anvil` → `tf-helper-bar` → `curl`):

```json
"custom/smartbulb": {
  "exec": "/home/warpuppy/.local/bin/waybar-bulb",
  "interval": 2,
  "return-type": "json",
  "tooltip": true,
  "on-click": "/home/warpuppy/.local/bin/waybar-bulb set idle",
  "on-click-right": "/home/warpuppy/.local/bin/waybar-bulb set working"
}
```

`waybar-bulb` = a small script that `curl`s `http://192.168.1.8:9130/status` and
prints waybar JSON `{"text","class","tooltip"}` (fallback `{"text":"bulb ?","class":"off"}`
when anvil is down — same resilience as `tf-helper-bar`).

**Flashing in the bar (the user's ask):** waybar is GTK-CSS, which supports
`@keyframes`, so the module can flash in sync with the bulb:

```css
@keyframes bulb-flash { 50% { color: #ff4444; background: rgba(255,0,0,0.15); } }
#custom-smartbulb.needs_input { color: #ff4444; animation: bulb-flash 0.5s steps(1) infinite; }
#custom-smartbulb.working     { color: #33ccff; animation: bulb-flash 2s ease-in-out infinite; }
#custom-smartbulb.done        { color: #33ff88; }
#custom-smartbulb.idle        { color: #8899aa; }
#custom-smartbulb.off         { color: #666; }
```

State → visual mapping (bar mirrors the bulb):

| State | Bulb | Bar |
|---|---|---|
| idle | cool white 5% | dim grey dot |
| working | slow dim breathe (blue) | slow blue pulse |
| needs_input | **white↔red flash** | **red flash @0.5 s** |
| done | green pulse ×1 | brief green |
| error | red ×2 | red solid |

## 5. Board decisions

### Architect
Two layers, cleanly separated: **control (anvil broker)** and **display (waybar
module)**. Broker is the only bulb writer; bar is a reader. This is the same
split the existing `:9129` helper already uses, so it is consistent with the fleet.

### Engineer
- **Rebuild required:** broker on anvil (systemd system service, headless — no
  `enable-linger` needed), with the `tapo` library installed there.
- **waybar module** on the Acer: script + config entry + style.css keyframes.
- Reuse the proven command vocabulary (`white`, `red`, `flash`, `pulse`,
  `brightness`, `ct`).
- Keep `interval` at 2 s (matches the other custom modules) — the *bulb* carries
  the fast flash; the bar animates via CSS so it doesn't need a fast poll.

### Researcher
- The waybar module pattern (`exec` + `curl` + JSON + interval) is already proven
  on this exact bar (`custom/anvil`, `custom/cpu`, `custom/gpu`). Follow it.
- CSS `@keyframes` animation on waybar module classes is supported in v0.15.

### Reviewer — risks & blind spots
1. **Blocker: nothing is built.** Both daemon (anvil) and plugin (Acer) are gone.
   The broker must be written from scratch; only the *design* is recovered.
2. **Tapo lib absent on both boxes** — install step required before any control.
3. **Two writers** — retire `bulb.sh`'s direct path; everything goes through the
   broker so precedence is enforced in one place.
4. **anvil down** → bar shows `off`, light dark; must fail silently (no agent block).
5. **Credentials** — re-enter on anvil `.env` (mode 600, root-owned); never copy
   the dead file, never commit.
6. **Waybar CSS animation cost** — negligible, but avoid sub-0.5 s animations that
   redraw the bar constantly; the bulb handles fast cadence.

### Budget (Token Optimiser)
Zero tokens, zero GPU. Deterministic I/O. Not an LLM task.

### Executive (Chair) — decision
1. **Proceed.** UI layer = **waybar custom module** (not QML). Control layer =
   **anvil broker on `:9130`**.
2. **Build order:** (a) install `tapo` on anvil + credentials; (b) write broker +
   systemd unit; (c) write `waybar-bulb` + config + CSS; (d) test patterns.
3. **Reuse** the recovered `bulb.sh` pattern vocabulary; retire the SSH path.
4. GPU stays out of it.

## 6. Open questions for the user
1. Approve building the **broker on anvil + waybar module** (this design)?
2. Confirm the **patterns** to hard-wire: reuse the recovered defaults
   (idle = cool white 5%, needs_input = red, done = white↔red flash ×10) or change them?
3. Waybar module **text/icon**: a dot (`●`), a bulb glyph, or a short word?
