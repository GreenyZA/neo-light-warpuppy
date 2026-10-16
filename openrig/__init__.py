"""OpenRig — Declarative multi-agent control plane for neo-light.

Phases 1-4 + swarm-guard verifier (tool-evidence / heuristic / LLM band).
"""

__version__ = "0.2.0-swarm-guard"

from openrig.loader import is_enabled, load_rigspec, RigSpec
try:
    from openrig.verifier import verify, ToolTrace, is_guard_enabled, guard_many, names_from_hermes_trace
except Exception:  # pragma: no cover - keeps import safe if deps missing
    verify = None  # type: ignore
    ToolTrace = None  # type: ignore
    is_guard_enabled = None  # type: ignore
    guard_many = None  # type: ignore
    names_from_hermes_trace = None  # type: ignore
