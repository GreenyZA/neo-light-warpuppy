"""
OpenRig — APM (Agent Productivity Monitoring)

Phase 1: Stub — tracks ceremony vs progress. Full implementation in Phase 4.
APM watches the ratio of ceremony (checks, handoffs, approvals) to progress
(slices completed, tokens spent, tasks shipped) to detect coordination pathologies.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class APM:
    """Agent Productivity Monitoring — ceremony vs progress."""

    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent.parent / "work" / "boa" / "governance"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def record_ceremony(self, event_type: str, details: Dict[str, Any]):
        """Record a ceremony event (BOA session, governance log, review loop)."""
        self._log("ceremony", event_type, details)

    def record_progress(self, event_type: str, details: Dict[str, Any]):
        """Record a progress event (slice completed, tokens spent, task shipped)."""
        self._log("progress", event_type, details)

    def _log(self, category: str, event_type: str, details: Dict[str, Any]):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = self.log_dir / f"apm-{category}-{ts}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "event_type": event_type,
            "details": details,
        }
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)

    def get_ratio(self) -> Dict[str, Any]:
        """Get ceremony vs progress ratio. Stub: returns counts only in Phase 1."""
        ceremony = len(list(self.log_dir.glob("apm-ceremony-*.json")))
        progress = len(list(self.log_dir.glob("apm-progress-*.json")))
        return {
            "ceremony_count": ceremony,
            "progress_count": progress,
            "ratio": ceremony / progress if progress > 0 else float("inf"),
            "threshold_exceeded": ceremony > 3 and progress == 0,
        }
