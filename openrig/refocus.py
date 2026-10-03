"""
OpenRig — Refocus (Intent-Chain Tracing)

Phase 3: Full implementation — pre-dispatch intent-chain tracing.
Refocus traces the chain of intentions from slice → mission → project
to prevent doghouse-to-moonbase scope creep.

The core question: "Is what you're doing right now aligned with the bigger picture?"
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


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
            "alignment_score": self._alignment_score(intent_chain),
            "warnings": self._generate_warnings(intent_chain),
        }
        self._log(entry)
        return entry

    def pre_dispatch_check(self, task: str, slice_id: Optional[str] = None, intent_chain: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Pre-dispatch check — runs before any worker is spawned.
        
        Returns a governance decision:
        {
            "should_dispatch": bool,
            "aligned": bool,
            "alignment_score": float,
            "warnings": List[str],
            "requires_human": bool,
        }
        """
        if intent_chain is None and slice_id:
            # Try to load from factory
            intent_chain = self._load_intent_chain(slice_id)
        
        if intent_chain is None:
            # No intent chain available — allow dispatch but flag
            return {
                "should_dispatch": True,
                "aligned": True,
                "alignment_score": 1.0,
                "warnings": ["No intent chain available — cannot verify alignment"],
                "requires_human": False,
            }
        
        aligned = self._check_alignment(intent_chain)
        score = self._alignment_score(intent_chain)
        warnings = self._generate_warnings(intent_chain)
        
        # If alignment is poor, require human review
        requires_human = score < 0.3
        
        return {
            "should_dispatch": not requires_human,
            "aligned": aligned,
            "alignment_score": score,
            "warnings": warnings,
            "requires_human": requires_human,
        }

    def _check_alignment(self, chain: Dict[str, Any]) -> bool:
        """Check if slice aligns with mission and project."""
        score = self._alignment_score(chain)
        return score >= 0.5

    def _alignment_score(self, chain: Dict[str, Any]) -> float:
        """
        Compute alignment score between slice, mission, and project.
        
        Uses keyword overlap with a base score for any overlap.
        Returns 0.0 (no alignment) to 1.0 (perfect alignment).
        """
        project = chain.get("project", "").lower()
        mission = chain.get("mission", "").lower()
        slice_text = chain.get("slice", "").lower()
        
        if not project or not mission or not slice_text:
            return 0.0
        
        # Extract keywords (meaningful words, not stop words)
        project_kw = self._keywords(project)
        mission_kw = self._keywords(mission)
        slice_kw = self._keywords(slice_text)
        
        if not project_kw or not mission_kw or not slice_kw:
            return 0.0
        
        # Helper: base 0.4 if any overlap, plus bonus for more overlap
        def overlap_score(a: Set[str], b: Set[str]) -> float:
            if not a or not b:
                return 0.0
            overlap = len(a & b)
            if overlap == 0:
                return 0.0
            return 0.4 + (overlap / max(len(a), len(b))) * 0.6
        
        # Slice should share keywords with mission
        slice_mission = overlap_score(slice_kw, mission_kw)
        
        # Mission should share keywords with project
        mission_project = overlap_score(mission_kw, project_kw)
        
        # Slice should share some keywords with project (direct line of sight)
        slice_project = overlap_score(slice_kw, project_kw)
        
        # Weighted average: slice-mission is most important
        score = (slice_mission * 0.5) + (mission_project * 0.3) + (slice_project * 0.2)
        
        return min(score, 1.0)

    def _generate_warnings(self, chain: Dict[str, Any]) -> List[str]:
        """Generate warnings for misalignment."""
        warnings = []
        score = self._alignment_score(chain)
        
        if score < 0.3:
            warnings.append("CRITICAL: Slice has very low alignment with project intent — likely scope creep")
        elif score < 0.5:
            warnings.append("WARNING: Slice has marginal alignment with project intent — review recommended")
        
        # Check for moonbase indicators
        slice_text = chain.get("slice", "").lower()
        moonbase_keywords = ["also", "additionally", "while we're at it", "might as well", "bonus", "extra"]
        for kw in moonbase_keywords:
            if kw in slice_text:
                warnings.append(f"MOONBASE INDICATOR: Slice contains '{kw}' — possible scope creep")
        
        return warnings

    def _keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Simple keyword extraction — remove stop words, keep meaningful terms
        stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
            "their", "what", "which", "who", "whom", "where", "when", "why",
            "how", "all", "each", "every", "both", "few", "more", "most", "other",
            "some", "such", "no", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "because", "if", "then", "else", "when",
            "up", "down", "out", "off", "over", "under", "again", "further",
            "once", "here", "there", "all", "any", "both", "each", "few",
            "more", "most", "other", "some", "such", "no", "nor", "not",
            "only", "own", "same", "so", "than", "too", "very", "also",
        }
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return {w for w in words if w not in stop_words and len(w) > 2}

    def _load_intent_chain(self, slice_id: str) -> Optional[Dict[str, Any]]:
        """Load intent chain from the IntelligenceFactory."""
        try:
            from openrig.factory import IntelligenceFactory
            factory = IntelligenceFactory()
            return factory.get_intent_chain(slice_id)
        except Exception:
            return None

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

    def get_stats(self) -> Dict[str, Any]:
        """Get refocus statistics."""
        entries = self.get_recent(1000)
        if not entries:
            return {"total": 0, "aligned": 0, "misaligned": 0, "avg_score": 0.0}
        
        aligned = sum(1 for e in entries if e.get("aligned"))
        misaligned = len(entries) - aligned
        avg_score = sum(e.get("alignment_score", 0) for e in entries) / len(entries)
        
        return {
            "total": len(entries),
            "aligned": aligned,
            "misaligned": misaligned,
            "avg_score": round(avg_score, 3),
        }
