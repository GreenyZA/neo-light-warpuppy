# Worked examples (Light Engine)

Train the classification. Do not copy these as live records unless the event is actually happening.

## 1. llama `:8081` returns connection refused

- Desk: user (WarPuppy / a hop) cannot use T1-fast.
- **Incident** — unplanned quality drop of the Vulkan service.
- Workaround: route grunt to Ollama `:11434` or OR/NV. Say so in the INC.
- Technical how: `/clarity-gpu`.
- If it has died more than once: open or update a **problem**. Known error = "Vulkan unit dead; use Ollama / OR".
- Fixing the unit is a **change** (restart = standard; unit rewrite = normal).

## 2. Olivia asks for a copy of the onboard preview

- Not broken. Pre-agreed client comms once WarPuppy says fire.
- **Request**. Do not open an incident.
- Fulfil with `/clarity-olivia`. Ask before send.
- If the ask is a new kind of work (build her site), that is Engage + Design, not a request, until it is on the catalogue.

## 3. Grafana alert: acer disk > 90%

- **Event**, type exception.
- If a service is at risk or already slow: raise an **incident**.
- If it is a repeating pattern: **problem** (capacity).
- Cleanup or a bigger disk is a **change**.

## 4. Raise Prometheus retention to 180d (Fri 21 09:00)

- Planned. Not an incident.
- **Change**, type normal, already scheduled.
- Log `CHG-` with backout (`restore previous --storage.tsdb.retention.time`).
- Do not `compose down -v`.

## 5. Process dumped core on Lenovo

- **Incident** if a service the user needs is affected.
- Technical how: `diagnose-crash`.
- Recurrence → **problem**.

## 6. "Write the ITIL skill"

- Project work. Not a ticket.
