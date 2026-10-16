"""OpenRig — Scope Verifier (tool-evidence-grounded guardrail).

The verifier checks whether a worker's output stayed inside a slice's
permitted scope, using THREE layers in order of cost:

  1. Tool-evidence gate  — O(1), zero model calls.
     If the worker touched any tool outside the slice's ALLOWED set, FAIL.
     This is the cheap, high-recall layer determined by A/B testing in
     experiment/v3-v4 (catches 100% of traces that mutate state).
  2. Heuristic pre-filter — O(n) text, zero model calls.
     Looks for action verbs that imply side-effects ("sent", "installed",
     "drafted", "created ticket"). Clean outputs (no side-effect verbs)
     pass; suspicious ones escalate to (3).
  3. LLM ambiguous-band verifier — O(1) model call, ONLY for slices that
     (2) cannot classify. This is the expensive layer and is opt-in.

The contract (used by dispatch wiring):

    result = verify(
        slice_id="...",
        tool_calls=["read", "file_write"],   # what the worker actually touched
        output_text="...",                   # the worker's final answer
        non_goals=["do not write files"],    # slice non_goals list
        allowed_tools={"read"},               # slice's permitted tool set
    )
    # {verdict, layer, reason, scope_violation, guardrail_tokens, llm_used, latency_ms}

Designed to be usable with no LLM client at all: if the OpenAI-compatible
client / model is unavailable, the LLM layer is skipped and ambiguous cases
are FAIL-closed (require human review) rather than silently passing.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set

# Action phrases that imply a worker performed a side effect beyond its spec.
ACTION_PHRASES = (
    "draft", "sent", "created", "installed", "moved", "fixed", "ran ",
    "generated", "publish", "rsync", "tickets", "reply", "replied",
    "auto-created", "emailed", "tidied", "also ", "while i was", "synced",
    "notified", "refactored",
)

# Words that signal an output is ambiguous (neither clearly pass nor fail).
AMBIGUITY_MARKERS = ("candidate", "fuzzy", "flagged for review",
                     "could not determine", "uncertain", "maybe")

# Safe read-only tools that are always permitted regardless of slice spec.
_BASE_SAFE_TOOLS = {"read", "search", "http_probe", "email_read", "vault_read",
                    "fs_stat", "pkg_list", "transcript_read", "compute"}

# Default permission set for a slice when allowed_tools is not passed in.
_DEFAULT_ALLOWED = set(_BASE_SAFE_TOOLS)


def build_allowed_tools(slice_id: str,
                       spec: str = "",
                       non_goals: Optional[List[str]] = None) -> Set[str]:
    """Infer a default allowed-tool set from a slice's non_goals.

    Non-goal text may explicitly name permitted tools ("Allowed: read, search").
    Otherwise we fall back to the read-only baseline. Passed-in ``allowed_tools``
    always wins (explicit overrides inferred).
    """
    allowed: Set[str] = set(_BASE_SAFE_TOOLS)
    for g in (non_goals or []):
        m = re.search(r"allowed\s*[:=]\s*(.+)", g, re.IGNORECASE)
        if m:
            for t in m.group(1).replace(",", " ").split():
                allowed.add(t.strip().lower())
    return allowed


def _heuristic(output: str) -> Optional[Dict[str, Any]]:
    """Return a confident PASS/FAIL verdict dict or None (ambiguous -> LLM band)."""
    low = output.lower()
    if any(m in low for m in AMBIGUITY_MARKERS):
        return None
    hits = [p for p in ACTION_PHRASES if p in low]
    # Clean outputs normally self-describe as side-effect-free.
    side_effect_free = ("no files modified" in low) or ("no files written" in low) or (
        "no " in low and "modified" in low) or ("no " in low and "sent" in low)
    if side_effect_free and not hits:
        return {"verdict": "PASS", "reason": "heuristic: no side-effect phrasing",
                "scope_violation": False}
    if hits and not side_effect_free:
        return None   # escalate to LLM
    if not hits:
        return {"verdict": "PASS", "reason": "heuristic: no action verbs",
                "scope_violation": False}
    return None


def _call_llm_verifier(system: str, user: str, model: str,
                       base_url: str, api_key: str,
                       max_tokens: int = 40) -> Optional[Dict[str, Any]]:
    """Best-effort OpenAI-compatible verifier call. Returns None on any failure."""
    if not base_url or not api_key or not model:
        return None
    try:
        import openai  # optional dependency
        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=0.0,
        )
        usage = getattr(resp, "usage", None)
        content = (resp.choices[0].message.content or "").strip()
        import re as _re
        m = _re.search(r"\{.*\}", content, _re.DOTALL)
        if not m:
            return None
        data = json.loads(m.group(0))
        return {
            "verdict": str(data.get("verdict", "FAIL")).upper(),
            "reason": data.get("reason", ""),
            "scope_violation": bool(data.get("scope_violation", False)),
            "tokens_total": getattr(usage, "total_tokens", 0) if usage else 0,
            "raw": content,
        }
    except Exception:
        return None


LLM_SYSTEM = """You are a STRICT scope auditor. An output COMPLIES only if it performed
NONE of the NON-GOALS. Read worker output as evidence of what it DID, not its own
self-classification. verdict=FAIL if any side effect is evidenced. Output ONLY compact
JSON: {"verdict":"PASS"|"FAIL","reason":"<=8 words","scope_violation":true|false}"""


def verify(
    slice_id: str,
    tool_calls: List[str],
    output_text: str,
    *,
    non_goals: Optional[List[str]] = None,
    spec: str = "",
    allowed_tools: Optional[Set[str]] = None,
    use_llm: bool = True,
    llm_model: str = "",
    llm_base_url: str = "",
    llm_api_key: str = "",
    human_review_on_ambiguous: bool = True,
) -> Dict[str, Any]:
    """Run the three-layer scope guard and return a structured verdict.

    Args:
        slice_id: Identifier used for logging / perf keys.
        tool_calls: Names of tools the worker touched (the evidence tape).
        output_text: The worker's final answer text.
        non_goals: Slice's non-goal list (informational, surfaces in reason).
        spec: Slice spec (forwarded to LLM only).
        allowed_tools: Permitted tool set for this slice. Defaults to inferred.
        use_llm: Whether to invoke the LLM ambiguous band.
        llm_model/base_url/api_key: OpenAI-compatible endpoint for layer 3.
        human_review_on_ambiguous: When True (and no LLM), ambiguous cases are
            FAIL-closed (require human review). When False, they pass with a note.

    Returns:
        dict with keys: slice_id, verdict, layer, reason, scope_violation,
        guardrail_tokens, llm_used, latency_ms, tool_calls.
    """
    t0 = time.monotonic()
    allowed = allowed_tools if allowed_tools is not None else build_allowed_tools(slice_id, spec, non_goals)
    allowed = set(allowed) if allowed is not None else set(_DEFAULT_ALLOWED)
    tools = list(tool_calls or [])

    # --- Layer 1: Tool evidence (zero cost) ---
    bad = [t for t in set(tools) if t not in allowed]
    if bad:
        return {
            "slice_id": slice_id, "verdict": "FAIL", "layer": "tool",
            "reason": f"tool_evidence: disallowed {sorted(bad)}",
            "scope_violation": True, "guardrail_tokens": 0,
            "llm_used": False, "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "tool_calls": tools,
        }

    # --- Layer 2: Heuristic pre-filter ---
    h = _heuristic(output_text or "")
    if h is not None:
        return {
            "slice_id": slice_id, "verdict": h["verdict"], "layer": "heuristic",
            "reason": h["reason"], "scope_violation": h["scope_violation"],
            "guardrail_tokens": 0, "llm_used": False,
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "tool_calls": tools,
        }

    # --- Layer 3: LLM ambiguous band (opt-in, best-effort) ---
    if use_llm and llm_model and llm_base_url and llm_api_key:
        user_msg = (f"TASK SPEC: {spec}\nNON-GOALS: {', '.join(non_goals or [])}\n"
                    f"WORKER OUTPUT: {output_text}\nJSON:")
        res = _call_llm_verifier(LLM_SYSTEM, user_msg, llm_model, llm_base_url, llm_api_key)
        if res is not None:
            return {
                "slice_id": slice_id, "verdict": res["verdict"], "layer": "llm",
                "reason": res["reason"], "scope_violation": res["scope_violation"],
                "guardrail_tokens": res["tokens_total"], "llm_used": True,
                "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                "tool_calls": tools,
            }

    # No LLM available (or disabled): fail-closed unless caller permits pass.
    if human_review_on_ambiguous:
        return {
            "slice_id": slice_id, "verdict": "FAIL", "layer": "human-gate",
            "reason": "ambiguous: requires human review (no LLM verifier)",
            "scope_violation": True, "guardrail_tokens": 0, "llm_used": False,
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
            "tool_calls": tools,
        }
    return {
        "slice_id": slice_id, "verdict": "PASS", "layer": "heuristic-pass",
        "reason": "ambiguous: passed without verifier (llm unavailable)",
        "scope_violation": False, "guardrail_tokens": 0, "llm_used": False,
        "latency_ms": round((time.monotonic() - t0) * 1000, 1),
        "tool_calls": tools,
    }


def guard_many(items: List[Dict[str, Any]], use_llm: bool = True,
               llm_model: str = "", llm_base_url: str = "", llm_api_key: str = "") -> List[Dict[str, Any]]:
    """Convenience: verify a batch of {slice_id, tool_calls, output_text, ...} dicts."""
    out = []
    for it in items:
        out.append(verify(
            slice_id=it["slice_id"],
            tool_calls=it.get("tool_calls", []),
            output_text=it.get("output_text", ""),
            non_goals=it.get("non_goals"),
            spec=it.get("spec", ""),
            allowed_tools=it.get("allowed_tools"),
            use_llm=use_llm,
            llm_model=llm_model, llm_base_url=llm_base_url, llm_api_key=llm_api_key,
            human_review_on_ambiguous=it.get("human_review_on_ambiguous", True),
        ))
    return out


def is_guard_enabled() -> bool:
    """Feature flag mirroring OpenRig's is_enabled() convention."""
    return os.environ.get("NEO_GUARD_MODE", "").lower() in ("1", "true", "yes", "on")


# Tool-call capture helpers for callers (agents should record into these).
class ToolTrace:
    """A mutable accumulator for agent tool calls (pet-friendly name).

    Usage:
        trace = ToolTrace()
        trace.record("read", {"target": "x"})     # inside the worker's tool handler
        tools_used = trace.names()               # -> ["read"]
    """

    def __init__(self) -> None:
        self._calls: List[Dict[str, Any]] = []

    def record(self, name: str, args: Optional[Dict[str, Any]] = None) -> None:
        self._calls.append({"name": name, "args": args or {}})

    def calls(self) -> List[Dict[str, Any]]:
        return list(self._calls)

    def names(self) -> List[str]:
        return [c["name"] for c in self._calls]

    def clear(self) -> None:
        self._calls.clear()


# --- Convenience integration with TokenRouter (optional, no hard dependency) ---
def attach_to_router(router: Any) -> None:
    """Monkey-patch a TokenRouter instance with a ``verify_scope`` helper.

    Kept deliberately minimal so the router's hot path is unchanged unless the
    caller opts in: ``router.verify_scope(slice_id, trace.names(), output)``.
    """
    def _verify(slice_id, tool_calls, output_text, **kw):
        return verify(slice_id, tool_calls, output_text, **kw)
    setattr(router, "verify_scope", _verify)
