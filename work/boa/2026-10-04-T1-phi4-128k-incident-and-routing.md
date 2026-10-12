# BOA Report — T1 Local Tier: Phi-4-mini 128K on RX 480 (Vulkan)

- **Date:** 2026-10-04
- **Author:** Monica (orchestrator), for the Board of Advisors
- **Project:** neo-light / neo-light-warpuppy (token_optimiser)
- **ITIL classification:** INCIDENT (conf 1.0, prefix INC) + CHANGE (config fix)
- **Governance tier (repo BOA):** T3 / conf 25 (see note at end)
- **Evidence dir:** `~/.hermes/cache/scratch/phi-smoke/`
- **Artifacts:** results.jsonl, workloads.jsonl, orchestration.jsonl, final_probes.jsonl, mem.jsonl

---

## 1. Incident record (ITIL)

**Symptom.** Acer host hard-locked twice — boots ended 02:24:55 and 02:28:09.
Kernel logged `amdgpu_vm_validate() failed` ×2907 and `Not enough memory for
command submission`. `llama-vulkan.service` crash-looped (restart counter 6),
6.1 GB memory peak + 2.7 GB swap peak.

**Root cause.** T1 launcher requested `-c 131072` (128K) with **f16 KV cache**.
Measured KV cost on this model = **128 KiB/token** (llama.cpp pads head_dim to 128),
so 131072 × 128 KiB = **16 GiB** KV + 2.37 GiB weights = 18.4 GiB requested. The
RX 480 has **4 GB VRAM + 8 GB GTT** = 12 GB GPU-addressable; the overflow fell
through GTT into host RAM+swap and exhausted the box.

**Fix applied (CHANGE).**
- `llama-vulkan-server.sh`: added `-ctk q4_0 -ctv q4_0` → KV 16 GiB → **4.6 GiB**.
- `token_optimiser/config.py` + `config_user.py`: `context_tokens`/`max_prompt_tokens`
  → **131072**, `vram_usage_gb` 2.5 → **6.9**, `kv_cache_type: q4_0`.
- systemd unit description corrected.
- Backout preserved: `llama-vulkan-server.sh.20261004-128k-f16-KV-CRASH.bak`.

**Verification.** Service active; `/props` reports `n_ctx = 131072`; health ok;
resident VRAM 3.94 GB + GTT 4.4 GB.

---

## 2. Vulkan verification (the card must do the work)

| Check | Result |
|---|---|
| Holds `/dev/dri/renderD128` | ✅ pid 40989, mmap access |
| VRAM resident | ✅ 3767–3941 MB (weights + KV on GPU) |
| GPU busy during decode | ✅ **max 98.3%, avg 79.6%** (radeontop) |
| GPU temp idle → load | ✅ 49 °C → 74–75 °C |
| Decode throughput | ✅ ~47 tok/s (500–600 tok sustained) |
| CPU fallback | ❌ none — all 32 layers on Vulkan0 |

**Verdict: Vulkan compute confirmed.** This is where the card shines — it is doing
the matrix math, not the CPU.

---

## 3. Capability & quality (evidence)

| Suite | Result |
|---|---|
| Capability | **12/15** pass |
| Edge cases (empty, whitespace, unicode, 4K-char word, max_tokens=1, temp 1.5, newlines, invalid JSON) | **8/8** pass |
| Needle recall 2K / 4K / 8K | ✅ all exact |
| Long-context coherence 4K & 8K (5 facts) | ✅ **5/5 both** — q4_0 KV retains facts |
| Memory leak (soak) | ✅ RSS Δ 0 MB, VRAM ±11 MB over 270 s |
| Concurrency | single slot (`-np 1`) — parallel requests serialise |

**The 3 capability failures are real model weaknesses, not infra:** multi-step
arithmetic ($17.60 vs $13.60), letter counting (4 vs 6), unit conversion
(10.5 vs 3500 m). Phi-4-mini is a strong instruction/reasoning/translation/refusal
model with **unreliable exact math and exact counting**.

---

## 4. Workload profile (what to route to T1)

Decode ≈ 47 tok/s; prefill 150–280 tok/s (unique text). Time-to-first-token is the
gating cost for big prompts.

| Workload class | Prompt | Output | Decode | GPU busy max | T1 fit |
|---|---|---|---|---|---|
| chat / classify / short transform | tiny | tiny | ~98 tok/s | 100% | ✅ excellent |
| extract JSON / translate | small | small | ~52 tok/s | 20% | ✅ good |
| code gen / explain | small | 130–200 | ~49 tok/s | 95% | ✅ good |
| reasoning / math | small | ~120 | ~49 tok/s | 96% | ✅ good (verify math) |
| long generation (documentation) | tiny | 700 | ~47 tok/s | 98% | ✅ excellent (85% busy) |
| summarise long doc | 2K | 55 | ~39 tok/s | 96% | ✅ good |
| RAG QA 8K | 4.3K | tiny | ~42 tok/s | 100% | ⚠️ ok, TTFT ~20 s |
| **orchestration turn** | 10–30K | small | ~16–24 | — | ❌ poor (TTFT) |
| **tool-calling / agentic** | any | — | — | — | ❌ **fails** |

---

## 5. Orchestration fitness — can T1 replace Longcat-2.5 as orchestrator?

**Answer: No.** Two independent blockers.

1. **No tool-calling.** Phi-4-mini does not implement the OpenAI `tool_calls`
   protocol. With tools supplied it returns `finish_reason: "stop"` and *prints*
   `read_file('config.py')` as text. An orchestrator must emit structured tool
   calls; this model cannot.
2. **Prefill latency.** Orchestration prompts are 10–30K tokens. Measured TTFT:

   | prompt tokens | TTFT | total |
   |---|---|---|
   | 1.8K | 5.8 s | 6.4 s |
   | 3.7K | 7.7 s | 8.2 s |
   | 7.3K | 20.5 s | 21.3 s |
   | 14.6K | 62.3 s | 63.6 s |

   Extrapolated: ~2.5 min @24K, ~3–4.5 min @32K per turn. A 20-turn session =
   hours, serialised on one slot.

**Conclusion:** T1 is a **worker/inference tier**, not an **orchestrator tier**.
Longcat-2.5 (T2 cloud, function-calling, fast) stays the orchestrator. T1 should
receive *delegated, self-contained, single-shot* work.

---

## 6. Board decisions

### Architect — system design
T1 is a **capacity tier** (free, local, private), not a **capability tier**
(no tools, weak exact math). Keep the 128K context via q4_0 KV: it is the only way
to get long context on a 4 GB card, and quality at 4K/8K is intact (5/5 facts).
Design rule: T1 serves **short-prompt / long-output** and **long-prompt / short-output
at ≤8K**; route anything agentic or >16K-prompt elsewhere.

### Engineer — implementation
- Fix is correct and minimal (`-ctk q4_0 -ctv q4_0`). No further tuning needed.
- Config drift resolved (config_user.py was stale Phi-3.5/4096 while launcher ran Phi-4/128K).
- **Residual risk:** q4_0 KV is a 4-bit quantisation of attention state; it is
  quality-lossy vs f16 at long context, and it is RAM-spill-dependent (4.6 GB KV
  does not fit 4 GB VRAM — it lives in GTT/host RAM). If host RAM is pressured by
  other work, T1 degrades or dies. Consider a **second service instance** with
  `-c 8192` f16 (fully in VRAM, ~3.3 GB, no spill) for latency-critical small
  prompts, and the 128K q4_0 instance for long context.

### Researcher — evidence
- KV cost 128 KiB/token is llama.cpp's actual measured allocation, not an estimate.
- Prefill scales roughly linearly with prompt length on this card; decode is
  roughly flat at ~47 tok/s until very long context, where GTT spill drags it to 16–24.
- Comparable hardware (RX 480, 4 GB, Vulkan) with a 3B-class model typically lands
  40–70 tok/s decode — this card is in the expected band; the win is *free + local*,
  not raw speed.

### Reviewer — risks & blind spots
1. **Tool-calling gap** is the single biggest constraint — document it in the T1
   config so the router never sends agentic tasks to T1.
2. **Math/counting unreliability** — never route exact-arithmetic or
   counting tasks to T1 without verification; T2 or a tool should handle them.
3. **GTT dependence** — the 128K config is only stable while host RAM is free.
   Add a guard: if `free` < ~6 GB, fall back to the 8K f16 profile.
4. **Single slot** — T1 cannot serve concurrent agents; swarms that all hit T1
   will serialise and time out. Cap T1 concurrency at 1.
5. **Not re-tested:** contexts >16K under sustained load (only 15K tested);
   recommend a one-off 32K needle test before advertising full 128K to the router.

### Budget (Token Optimiser) — routing policy
**Route TO T1 (free):** chat, classification, short transforms, extract-JSON,
translation, code gen/explain, single-shot reasoning (non-arithmetic), long-form
documentation generation, summarise ≤4K, RAG QA ≤8K.

**Route to T2 (cloud):** orchestration/agentic turns, tool-calling, exact math &
counting, anything with prompt >16K where TTFT matters, security/privacy-capped
tasks, and anything requiring concurrent handling.

**Never route to T1:** OpenAI tool-call agents; exact arithmetic; >8K prompts when
latency budget < 30 s.

### Executive (Chair) — decision
1. **Close the incident.** The q4_0 KV fix is accepted and verified.
2. **Adopt the routing policy above.** Update `category_free_model_preference` so
   `orchestrator` and `swarm_default` stay on cloud (Longcat), and add explicit
   `tool_calling: cloud-only` and `exact_math: cloud-only` guards.
3. **Keep Longcat-2.5 as orchestrator.** T1 is a worker tier.
4. **Add a host-RAM guard** before loading the 128K profile.
5. **Next action:** one 32K needle test to certify full 128K, then freeze T1 config.

---

## 7. Note on the repo BOA run

`run_boa()` executed with the six seats but on **mock backends** — the seat answers
were templated placeholders (no live model call). The governance decision it
produced (T3 / ITIL INCIDENT conf 1.0) is recorded at
`work/boa/2026-10-04-030901.md`. This report supplies the *substance* the mock
seats cannot. To get live seat answers, wire `_generate_seat_answer` to a real
T2/T3 backend (`BOA_BACKEND=live` currently maps to `mock_backends.py`, which is
itself simulated).

---

## 8. Open items for the user
- Approve the routing-policy edits to `config.py`.
- Decide whether to add the second (8K f16, VRAM-only) T1 instance.
- Approve one 32K needle certification run.

---

# ADDENDUM (2026-10-04, later) — approvals actioned + GPU utilisation study

## A1. Routing guards — DONE

`tool_calling: cloud-only` and `exact_math: cloud-only` are implemented in
`router.py` as two new `CATEGORY_RULES` (`force_cloud: True`) plus a guard in
`_select_tier` placed **before** the privacy short-circuit, so these tasks are
sent to T2 even when the prompt looks private/local.

Verified live:

| Task | Tier | Expected |
|---|---|---|
| "Use the tool to read the file, keep it local-only" | **T2** | T2 (guard beats privacy) ✅ |
| "Calculate the exact sum of these private numbers, offline" | **T2** | T2 ✅ |
| "Summarise this offline confidential document" | **T1** | T1 (genuine privacy) ✅ |
| "Call the function read_file with path config.py" | **T2** | T2 ✅ |

## A2. Second T1 instance (8K f16, VRAM-only) — NOT FEASIBLE

Resource check refutes it:

- VRAM total **4 GB**, the 128K instance already holds **3.94 GB**. Two copies of
  the weights alone = 2 × 2.37 GB = 4.74 GB > VRAM.
- Host RAM: **4.8 GB available** (10 GB used, 1.7 GB swap in use). The first
  instance's KV already spills into GTT/host RAM; a second instance would push
  the host into swap and risk the same OOM class that caused the incident.
- The card has one physical compute device; a second llama-server would contend
  for it and serialise anyway.

**Verdict:** do not add a second instance. If latency-critical small prompts are
needed, the correct move is a **single service restarted with a smaller context**
(`-c 8192`, f16, ~3.3 GB, fully in VRAM) — not a concurrent second instance.

## A3. GPU utilisation — what actually keeps the card busy (the user's question)

The GPU is idle *between* requests because the service is single-slot (`-np 1`)
and agent use is sporadic. Measured:

| Pattern | GPU avg busy | GPU max | tok/s |
|---|---|---|---|
| **Sporadic interactive** (work → 6 s idle → work) | **42.4 %** | 97.5 % | 47 |
| **Sustained batch** (back-to-back, no gaps) | **90.9 %** | 98.3 % | 47 |

**Finding: the same card does 2× the useful work per unit time when fed a
continuous queue.** Idle gaps — not the workload type — are what waste the card.

### Workloads that use the GPU most (keep it at ~90 %+ busy)

1. **Long-form generation** (essays, docs, guides, reports) — 700–1500 tokens
   → GPU avg **86–94 %**, the single most GPU-dense class. *This is the answer to
   "give it something that works the GPU hard": batch documentation/report
   generation.*
2. **Code generation** (function/module writing, 130–300 tokens) → ~95 % max busy.
3. **Multi-step reasoning answers** (non-arithmetic) → ~96 % max busy.
4. **Sustained batch of any of the above** → 91 % avg busy.

### Workloads that waste the card (leave it mostly idle)

- Extract-JSON, translate, classify — tiny outputs (~20 % busy, done in <1 s).
- Long-context RAG QA — GPU pinned at 100 % but *thrashing GTT*, 44–76 tok/s;
  high utilisation, low throughput. Busy ≠ efficient.

### Production recommendation

Feed T1 a **background batch queue** of self-contained generation jobs
(doc/report/code drafts, summaries ≤4K) instead of one-off interactive calls.
That converts the card from ~42 % to ~91 % utilised on the same hardware. This is
the "make it happen more often" mechanism: **queue the work, don't trickle it.**

## A4. Corrected performance numbers

| Metric | Value |
|---|---|
| Decode (small ctx) | ~47 tok/s |
| Decode (long ctx, GTT spill) | 28–34 tok/s |
| Decode (90K ctx prefill running) | ~16–24 tok/s |
| Prefill (unique text, ≤16K) | 150–280 tok/s |
| Prefill (32K) | ~76 tok/s |
| Prefill (64K) | ~44 tok/s |
| TTFT 1.8K / 3.7K / 7.3K / 14.6K | 5.8 s / 7.7 s / 20.5 s / 62.3 s |

Prefill throughput **falls with context depth** because the KV cache spills to
GTT/host RAM. This is the hard limit of long context on a 4 GB card.

## A5. 32K needle certification — **PASS (at 64K)**

Because random-word filler tokenises at ~3.6 tokens/word, the run sized to
**64 202 tokens** — a *stronger* test than the requested 32K (passing 64K
certifies 32K a fortiori).

**Result:**

| Metric | Value |
|---|---|
| Verdict | ✅ **PASS** — recalled `ZQ9914` exactly |
| Prompt tokens | 64 202 |
| Wall time | 1323.8 s (~22 min, prefill-dominated) |
| Prefill throughput | 48.5 tok/s |
| GPU busy | **max 100 %, avg 98.5 %** (sustained 22 min) |

This also directly demonstrates the utilisation finding: a single long-context
job held the card at 98.5 % average for 22 minutes — the opposite of the 42 %
sporadic pattern.

A first attempt was invalidated (it ran to ~90K tokens and exceeded the client
timeout) and is preserved as a **failure** in `cert32k.jsonl` — not counted as a
pass. The valid pass is in `cert32k_v2.jsonl`.

**Long-context status: CERTIFIED.** Needle recall verified at 2K, 4K, 8K (smoke)
and 64K (this run). Full 128K remains untested end-to-end (a full 128K prefill
would take ~45+ min at 44 tok/s) but the mechanism is proven to 64K, i.e. half the
advertised window.
