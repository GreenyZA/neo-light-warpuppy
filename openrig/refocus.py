"""
OpenRig — Refocus (Intent-Chain Tracing)

Phase 1: Stub — logs intent chain. Full implementation in Phase 3.
Refocus traces the chain of intentions from slice → mission → project
to prevent doghouse-to-moonbase scope creep.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class Refocus:
    """Intent-chain tracing for scope-creep prevention."""

    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent.parent / "work" / "refocus"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def trace(self, task: str, intent_chain: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trace the intent chain for a task.

        intent_chain format:
        {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse"
        }
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task": task,
            "intent_chain": intent_chain,
            "aligned": self._check_alignment(intent_chain),
        }
        self._log(entry)
        return entry

    def _check_alignment(self, chain: Dict[str, Any]) -> bool:
        """Check if slice aligns with mission and project. Stub: always True in Phase 1."""
        # Phase 3: implement actual alignment check
        return True

    def _log(self, entry: Dict[str, Any]):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = self.log_dir / f"refocus-{ts}.json"
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        files = sorted(self.log_dir.glob("refocus-*.json"), reverse=True)[:limit]
        results = []
        for f in files:
            with open(f) as fh:
                results.append(json.load(fh))
        return results
