"""
OpenRig — TOS Integration Layer

Wires the Token Optimiser System (TOS) into the OpenRig control plane.
Provides hooks for:
- Slice routing (route slices through T1/T2/T3)
- Refocus pre-dispatch checks (intent-chain alignment)
- APM event recording (ceremony vs progress)
- Seat assignment (workers assigned to RigSpec seats)

This module lives in the main repo (not the token_optimiser submodule)
to avoid fork conflicts.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from openrig.loader import load_rigspec, is_enabled, RigSpec
from openrig.refocus import Refocus
from openrig.apm import APM


class TOSIntegration:
    """
    Integration layer between TOS (token_optimiser) and OpenRig.
    
    Usage:
        integration = TOSIntegration()
        if integration.is_active():
            # Pre-dispatch: check intent chain
            check = integration.pre_dispatch_check(task, slice_id)
            if not check["should_dispatch"]:
                return  # Blocked by refocus
            
            # Dispatch workers
            workers = integration.assign_workers(task, worker_count)
            
            # Post-dispatch: record APM events
            integration.record_ceremony("boa_session", {"question": task})
            integration.record_progress("slice_completed", {"slice": slice_id})
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, log_dir: Optional[Path] = None):
        self._config = config or {}
        self._log_dir = log_dir
        self._rigspec: Optional[RigSpec] = None
        self._refocus: Optional[Refocus] = None
        self._apm: Optional[APM] = None
        self._active = False
        
        if is_enabled():
            self._initialize()

    def _initialize(self):
        """Initialize OpenRig components."""
        try:
            self._rigspec = load_rigspec()
            errors = self._rigspec.validate()
            if errors:
                print(f"OpenRig: RigSpec validation errors: {errors}")
                return
            self._refocus = Refocus(log_dir=self._log_dir)
            self._apm = APM(log_dir=self._log_dir)
            self._active = True
        except Exception as e:
            print(f"OpenRig: Failed to initialize: {e}")
            self._active = False

    def is_active(self) -> bool:
        """Check if OpenRig integration is active."""
        return self._active

    def get_rigspec(self) -> Optional[RigSpec]:
        """Get the loaded RigSpec."""
        return self._rigspec

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
        if not self._active or not self._refocus:
            return {
                "should_dispatch": True,
                "aligned": True,
                "alignment_score": 1.0,
                "warnings": [],
                "requires_human": False,
            }
        
        return self._refocus.pre_dispatch_check(task, slice_id=slice_id, intent_chain=intent_chain)

    def assign_workers(self, task: str, worker_count: int) -> List[Dict[str, Any]]:
        """
        Assign workers to RigSpec seats.
        
        Returns a list of worker assignments:
        [
            {"worker_id": 1, "seat_id": "engineer", "address": "engineer@governance-pod", "task": "..."},
            ...
        ]
        """
        if not self._active or not self._rigspec:
            return [{"worker_id": i+1, "seat_id": None, "address": None, "task": task} for i in range(worker_count)]
        
        # Get available seats from worker-pod
        worker_seats = self._rigspec.get_seats_in_pod("worker-pod")
        
        # If no worker seats defined, use all seats
        if not worker_seats:
            worker_seats = self._rigspec.seats
        
        # Assign workers to seats in round-robin
        assignments = []
        for i in range(worker_count):
            seat = worker_seats[i % len(worker_seats)]
            assignments.append({
                "worker_id": i + 1,
                "seat_id": seat["id"],
                "address": seat["address"],
                "task": task,
                "framing": seat.get("framing", ""),
            })
        
        return assignments

    def record_ceremony(self, event_type: str, details: Dict[str, Any]):
        """Record a ceremony event (BOA session, governance log, review loop)."""
        if self._active and self._apm:
            self._apm.record_ceremony(event_type, details)

    def record_progress(self, event_type: str, details: Dict[str, Any]):
        """Record a progress event (slice completed, tokens spent, task shipped)."""
        if self._active and self._apm:
            self._apm.record_progress(event_type, details)

    def check_health(self) -> Dict[str, Any]:
        """Check the health of the agent system."""
        if not self._active or not self._apm:
            return {"status": "inactive", "ceremony_count": 0, "progress_count": 0}
        return self._apm.check_health()

    def get_slice_routing(self, slice_id: str, task: str) -> Dict[str, Any]:
        """
        Route a slice through T1/T2/T3.
        
        This is the TOS routing decision for a slice.
        """
        # Import TOS router lazily to avoid circular imports
        try:
            from token_optimiser.router import TokenRouter
            router = TokenRouter()
            decision = router.assess(task, {"slice_id": slice_id})
            return {
                "slice_id": slice_id,
                "tier": decision.tier,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
                "parallelize": decision.parallelize,
                "swarm_recommendation": decision.swarm,
            }
        except Exception as e:
            return {
                "slice_id": slice_id,
                "tier": "T2",
                "confidence": 50,
                "rationale": f"Fallback: {e}",
                "parallelize": False,
                "swarm_recommendation": {"recommendation": "solo"},
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get OpenRig + TOS integration stats."""
        if not self._active or not self._rigspec:
            return {"active": False}
        
        return {
            "active": True,
            "rigspec": {
                "name": self._rigspec.meta.get("name"),
                "version": self._rigspec.meta.get("version"),
                "seats": len(self._rigspec.seats),
                "pods": len(self._rigspec.pods),
                "edges": len(self._rigspec.edges),
            },
            "apm": self._apm.get_stats() if self._apm else {},
            "refocus": self._refocus.get_stats() if self._refocus else {},
        }


# Singleton instance
_integration: Optional[TOSIntegration] = None


def get_integration() -> TOSIntegration:
    """Get the singleton TOSIntegration instance."""
    global _integration
    if _integration is None:
        _integration = TOSIntegration()
    return _integration
