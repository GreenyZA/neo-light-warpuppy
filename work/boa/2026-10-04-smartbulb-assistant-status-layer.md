# BOA Report — Smart-Bulb Personal-Assistant Status Layer

- **Date:** 2026-10-04
- **Author:** Monica (orchestrator), for the Board of Advisors
- **Question (user):** "Is the GPU good enough to function as a personal-assistant
  layer? The RX 480 should be strong enough to handle simple blinking patterns. I
  want certain blinking patterns always programmed into Hermes when it's working;
  when it needs an answer from me it flashes white↔red to signal action required,
  then returns to its original dim cold-white state. Is this something the GPU can
  do?"
- **ITIL:** classification "incident" is a false positive (keyword "error"); this is
  really a **CHANGE / feature request** (new subsystem). Treated as a design decision.
- **Governance:** tier T3, swarm_size 1 (repo BOA). Human design decision required.

---

## 1. Direct answer to the user

**Yes — the feature is absolutely doable. But not on the GPU, and the GPU is not
the component that should drive it.**

There is a **category error** in the question: "blinking patterns" are *not a GPU
workload*. The GPU renders no pixels here. A blink is a sequence of three cheap
things: a **timer**, a **colour write over the LAN**, and a **state flag**. That is
I/O orchestration, and the right home for it is the **CPU** — specifically Hermes's
own event system on the box that is already running Hermes.

**The GPU is the wrong tool for the job, and using it would be worse, not better.**

---

## 2. Why the GPU is the wrong component

| Requirement | What actually does the work | GPU involved? |
|---|---|---|
| Know the agent is "working" | Hermes agent lifecycle event | No |
| Know it "needs your input" | Hermes approval/question event | No |
| Blink timing (e.g. 0.25 s on/off) | CPU timer / `asyncio.sleep` | No |
| Change bulb colour | HTTP request to Tapo bulb on LAN | No |
| Return to dim cold white | one more HTTP write | No |

- The bulb is a **network device** (`192.168.1.225`). Every pattern step is a LAN
  round-trip (~tens of ms), not a shader.
- Driving this from the GPU would add VRAM contention and complexity for **zero**
  benefit — the GPU would just be a slow, awkward CPU.
- Worse: **the GPU service is single-slot (`-np 1`) and already saturates 4 GB
  VRAM**. Putting assistant-status logic there risks evicting the model — the exact
  class of resource conflict that caused today's incident.

**Conclusion: keep the GPU for inference (where it "shines"), and run the status
layer on the CPU where it belongs.**

---

## 3. What the "assistant layer" actually is — a state machine

The correct architecture is a small **status broker**: agent events → bulb patterns.

```
Hermes agent event ──► status broker (CPU) ──► Tapo bulb (LAN)
   working                state machine            pattern renderer
   needs_input            (priority + lock)        (predefined patterns)
   done / error
   idle (timeout)
```

### Required states & patterns (proposed defaults — user to confirm)

| State | Trigger | Pattern | End state |
|---|---|---|---|
| **idle** | default / after any sequence | steady **dim cold white** (CT ~4000K, bri ~21) | stays |
| **working** | agent turn starts | slow **dim cold-white breathe** (or soft blue pulse) | loops while working |
| **needs_input** | agent asks a question / approval | **white ↔ red flash**, bright | on answer: back to idle |
| **done** | turn completes OK | short **green** pulse ×1 | back to idle |
| **error** | turn fails | **red** steady ×2 | back to idle |

Patterns the user "wants always programmed in" become named entries in the broker,
each a list of (colour, brightness, duration) steps.

### Critical design rule — return to base

The bulb must **always return to the dim cold-white baseline** when nothing is
happening. This is the "original state" the user described. So the broker owns a
`base_state` and every pattern ends by restoring it.

### Precedence — the thing that will bite if ignored

If "working" and "needs_input" fire together, which wins? **`needs_input` must
pre-empt everything** — that's the whole point (it needs the human). The broker
needs a **priority + mutex**: only one pattern drives the bulb at a time; a
higher-priority state interrupts and, when it clears, the lower one resumes.

---

## 4. Where the patterns should live

The user said "always programmed into Hermes". Two viable homes:

1. **The smartbulb Omarchy plugin** (existing `status.py` already has `flash`,
   `blink`, `pulse`, `white`, `red` commands) — extend it into a long-running
   daemon that subscribes to agent events. Pro: reuse; Con: shell plugin is
   desktop-scoped, dies with the shell.
2. **A Hermes-native status broker** (small CPU service + a hook on agent
   lifecycle events) — survives shell restarts, works headless. Pro: robust;
   Con: new component.

**Recommendation:** a small **CPU daemon** (systemd user service) that exposes a
tiny local API (`set_state working|needs_input|done|error|idle`) and owns the
pattern library + precedence. Hermes calls it on lifecycle events. The Omarchy
panel becomes just a viewer/override. This keeps patterns "always there"
regardless of whether the desktop is up.

---

## 5. Board decisions

### Architect
Decouple: **agent events** (CPU) → **broker** (CPU) → **bulb** (LAN). The GPU is
not in this path. Make the broker own `base_state`, a pattern library, and a
priority mutex. Single source of truth for "what the bulb is doing".

### Engineer
- **Feasible today.** The Tapo library path works (local HTTP returns 1003; the
  `l530` library is the verified path). Existing commands already cover
  white/red/flash/pulse.
- **Rebuild note:** the plugin + `.tapo-venv` were wiped on 2026-10-02 — this
  needs a rebuild first (see `omarchy-smartbulb` skill). The bulb itself pings OK.
- **Latency reality:** each colour change is a LAN call (~tens of ms) plus the
  bulb's own response time. A 0.25 s on/off flash is at the edge of what the
  firmware keeps up with; test the real cadence before committing to fast blinks.
  Prefer ≥0.3–0.5 s steps.
- **Don't over-drive the bulb.** Rapid network writes can drop commands; add a
  small queue and coalesce.

### Researcher
- Comparable systems (Hue "status lights", Stream Deck, CI "traffic lights") all
  run this on a **CPU service**, never a GPU. Precedent is unanimous.
- The bulb is a **network device**, so throughput is bounded by LAN + firmware,
  not by any local compute — the GPU's power is irrelevant to the bottleneck.

### Reviewer — risks & blind spots
1. **Wrong layer** — the biggest risk is building it on the GPU. Reject.
2. **GPU contention** — single-slot model; never let status logic share the VRAM.
3. **Precedence bugs** — simultaneous states; needs a mutex + priority.
4. **Base-state drift** — the bulb doesn't report state back (error 1003), so the
   broker must track last-commanded state itself (as `status.py` already does).
5. **Bulb offline** — if the LAN/bulb is down, the broker must degrade silently
   (never block the agent waiting on a light).
6. **Over-lighting** — an always-on bright "working" light is distracting; default
   to **dim** and make brightness configurable.
7. **Pattern library vs ad-hoc** — user wants patterns "always programmed in";
   version them in config, not hardcoded, so they can be edited.

### Budget (Token Optimiser)
- This is **CPU/IO work — zero tokens, zero GPU**. It must NOT be routed to T1/T2/T3
  at all; it is not an LLM task. It is a deterministic state machine.
- If any part needs an LLM (it shouldn't), it would be a one-off build, not runtime.

### Executive (Chair) — decision
1. **Proceed — but build it on the CPU, not the GPU.** The GPU is not required and
   must not be used for this.
2. **Design:** CPU status broker (systemd user service) owning base state, a
   configurable pattern library, and a priority mutex; Hermes emits lifecycle
   events; Omarchy panel becomes a viewer.
3. **First step:** rebuild the smartbulb plugin + `.tapo-venv` (wiped 2026-10-02),
   then prototype the broker with just `working` + `needs_input` + `idle`.
4. **Test the real blink cadence** before finalising fast patterns.

---

## 6. Open questions for the user (one at a time)
1. Confirm the state set and the **exact patterns** for each (colours, brightness,
   cadence) — especially "working" and the white↔red "needs input" flash rate.
2. Broker as a **standalone CPU daemon** (survives shell restarts, headless) vs
   **inside the Omarchy plugin**?
3. Should "working" be **always-on while the agent is busy**, or only during
   specific operations?
