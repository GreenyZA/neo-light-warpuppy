"""
OpenRig — APM (Agent Productivity Monitoring)

Phase 4: Full implementation — ceremony vs progress monitoring.
APM watches the ratio of ceremony (checks, handoffs, approvals) to progress
(slices completed, tokens spent, tasks shipped) to detect coordination pathologies.

Coordination pathologies detected:
- Bureaucracy: ceremony grows while progress stalls
- Recursive proof loop: repeated proof/verification with no new progress
- Just-following-orders: approvals without context alignment
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


class APM:
    """Agent Productivity Monitoring — ceremony vs progress."""

    # Default thresholds
    DEFAULT_CEREMONY_THRESHOLD = 3  # Alert if ceremony > 3 and progress == 0
    DEFAULT_RATIO_THRESHOLD = 5.0  # Alert if ceremony/progress > 5
    DEFAULT_REPETITION_THRESHOLD = 3  # Alert if same event type repeats > 3 times

    def __init__(self, log_dir: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent.parent / "work" / "boa" / "governance"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or {}
        self.ceremony_threshold = self.config.get("ceremony_threshold", self.DEFAULT_CEREMONY_THRESHOLD)
        self.ratio_threshold = self.config.get("ratio_threshold", self.DEFAULT_RATIO_THRESHOLD)
        self.repetition_threshold = self.config.get("repetition_threshold", self.DEFAULT_REPETITION_THRESHOLD)

    def record_ceremony(self, event_type: str, details: Dict[str, Any]):
        """Record a ceremony event (BOA session, governance log, review loop)."""
        self._log("ceremony", event_type, details)

    def record_progress(self, event_type: str, details: Dict[str, Any]):
        """Record a progress event (slice completed, tokens spent, task shipped)."""
        self._log("progress", event_type, details)

    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the agent system.
        
        Returns a health assessment:
        {
            "status": "healthy" | "warning" | "critical",
            "ceremony_count": int,
            "progress_count": int,
            "ratio": float,
            "alerts": List[str],
            "pathologies": List[str],
        }
        """
        ceremony = self._get_events("ceremony")
        progress = self._get_events("progress")
        
        ceremony_count = len(ceremony)
        progress_count = len(progress)
        ratio = ceremony_count / progress_count if progress_count > 0 else float("inf")
        
        alerts = []
        pathologies = []
        
        # Check 1: Ceremony with no progress
        if ceremony_count > self.ceremony_threshold and progress_count == 0:
            alerts.append(f"CEREMONY OVERLOAD: {ceremony_count} ceremony events with 0 progress")
            pathologies.append("bureaucracy")
        
        # Check 2: High ceremony/progress ratio
        if ratio > self.ratio_threshold and progress_count > 0:
            alerts.append(f"HIGH RATIO: ceremony/progress = {ratio:.1f} (threshold: {self.ratio_threshold})")
            pathologies.append("bureaucracy")
        
        # Check 3: Repetition (recursive proof loop)
        repetition = self._detect_repetition(ceremony)
        if repetition:
            alerts.append(f"REPETITION: {repetition}")
            pathologies.append("recursive_proof_loop")
        
        # Check 4: Just-following-orders (approvals without progress)
        if ceremony_count > 0 and progress_count == 0:
            approvals = [e for e in ceremony if e.get("event_type") in ("approval", "review", "governance")]
            if len(approvals) > 2:
                alerts.append(f"JUST-FOLLOWING-ORDERS: {len(approvals)} approvals with no progress")
                pathologies.append("just_following_orders")
        
        # Determine status
        has_ceremony_overload = ceremony_count > self.ceremony_threshold and progress_count == 0
        if len(pathologies) >= 2 or has_ceremony_overload:
            status = "critical"
        elif len(pathologies) == 1 or len(alerts) > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "ceremony_count": ceremony_count,
            "progress_count": progress_count,
            "ratio": round(ratio, 2) if ratio != float("inf") else "inf",
            "alerts": alerts,
            "pathologies": list(set(pathologies)),
        }

    def get_ratio(self) -> Dict[str, Any]:
        """Get ceremony vs progress ratio (basic counts)."""
        ceremony = self._get_events("ceremony")
        progress = self._get_events("progress")
        ceremony_count = len(ceremony)
        progress_count = len(progress)
        return {
            "ceremony_count": ceremony_count,
            "progress_count": progress_count,
            "ratio": ceremony_count / progress_count if progress_count > 0 else float("inf"),
            "threshold_exceeded": ceremony_count > self.ceremony_threshold and progress_count == 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get APM statistics."""
        ceremony = self._get_events("ceremony")
        progress = self._get_events("progress")
        
        # Event type breakdown
        ceremony_types = defaultdict(int)
        for e in ceremony:
            ceremony_types[e.get("event_type", "unknown")] += 1
        
        progress_types = defaultdict(int)
        for e in progress:
            progress_types[e.get("event_type", "unknown")] += 1
        
        # Time-based stats
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)
        week_ago = now - timedelta(days=7)
        
        ceremony_24h = sum(1 for e in ceremony if self._parse_ts(e.get("timestamp", "")) > day_ago)
        progress_24h = sum(1 for e in progress if self._parse_ts(e.get("timestamp", "")) > day_ago)
        ceremony_7d = sum(1 for e in ceremony if self._parse_ts(e.get("timestamp", "")) > week_ago)
        progress_7d = sum(1 for e in progress if self._parse_ts(e.get("timestamp", "")) > week_ago)
        
        return {
            "total_ceremony": len(ceremony),
            "total_progress": len(progress),
            "ceremony_types": dict(ceremony_types),
            "progress_types": dict(progress_types),
            "last_24h": {"ceremony": ceremony_24h, "progress": progress_24h},
            "last_7d": {"ceremony": ceremony_7d, "progress": progress_7d},
            "health": self.check_health(),
        }

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent APM events."""
        files = sorted(self.log_dir.glob("apm-*.json"), reverse=True)[:limit]
        results = []
        for f in files:
            with open(f) as fh:
                results.append(json.load(fh))
        return results

    def clear_old(self, days: int = 30):
        """Clear APM events older than N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        for f in self.log_dir.glob("apm-*.json"):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                ts = self._parse_ts(data.get("timestamp", ""))
                if ts < cutoff:
                    f.unlink()
            except Exception:
                pass

    def _get_events(self, category: str) -> List[Dict[str, Any]]:
        """Get all events of a category."""
        files = sorted(self.log_dir.glob(f"apm-{category}-*.json"), reverse=True)
        results = []
        for f in files:
            try:
                with open(f) as fh:
                    results.append(json.load(fh))
            except Exception:
                pass
        return results

    def _detect_repetition(self, events: List[Dict[str, Any]]) -> Optional[str]:
        """Detect if the same event type repeats too often."""
        type_counts = defaultdict(int)
        for e in events:
            type_counts[e.get("event_type", "unknown")] += 1
        
        for event_type, count in type_counts.items():
            if count > self.repetition_threshold:
                return f"'{event_type}' repeated {count} times (threshold: {self.repetition_threshold})"
        return None

    def _parse_ts(self, ts: str) -> datetime:
        """Parse ISO timestamp."""
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    def _log(self, category: str, event_type: str, details: Dict[str, Any]):
        # Use microsecond resolution to avoid filename collisions when
        # multiple events are recorded in the same second.
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        path = self.log_dir / f"apm-{category}-{ts}.json"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "event_type": event_type,
            "details": details,
        }
        with open(path, "w") as f:
            json.dump(entry, f, indent=2)
