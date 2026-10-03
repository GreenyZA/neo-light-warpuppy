"""
OpenRig — RigSpec Loader

Loads and validates the declarative topology (rigspec.yaml).
Provides seat lookup, pod grouping, and edge traversal.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class RigSpec:
    """Loaded and validated RigSpec."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._seats = {s["id"]: s for s in data.get("seats", [])}
        self._pods = {p["id"]: p for p in data.get("pods", [])}
        self._edges = data.get("edges", [])

    @property
    def meta(self) -> Dict[str, Any]:
        return self._data.get("meta", {})

    @property
    def seats(self) -> List[Dict[str, Any]]:
        return list(self._seats.values())

    @property
    def pods(self) -> List[Dict[str, Any]]:
        return list(self._pods.values())

    @property
    def edges(self) -> List[Dict[str, Any]]:
        return self._edges

    def get_seat(self, seat_id: str) -> Optional[Dict[str, Any]]:
        return self._seats.get(seat_id)

    def get_pod(self, pod_id: str) -> Optional[Dict[str, Any]]:
        return self._pods.get(pod_id)

    def get_seats_in_pod(self, pod_id: str) -> List[Dict[str, Any]]:
        pod = self._pods.get(pod_id)
        if not pod:
            return []
        seat_ids = pod.get("seats", [])
        return [self._seats[sid] for sid in seat_ids if sid in self._seats]

    def get_pod_for_seat(self, seat_id: str) -> Optional[Dict[str, Any]]:
        seat = self._seats.get(seat_id)
        if not seat:
            return None
        return self._pods.get(seat.get("pod", ""))

    def get_edges_from(self, pod_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._edges if e.get("from") == pod_id]

    def get_edges_to(self, pod_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._edges if e.get("to") == pod_id]

    def validate(self) -> List[str]:
        """Return list of validation errors. Empty = valid."""
        errors = []
        for seat in self.seats:
            if "id" not in seat:
                errors.append("Seat missing 'id'")
            if "address" not in seat:
                errors.append(f"Seat {seat.get('id', '?')} missing 'address'")
            if "pod" not in seat:
                errors.append(f"Seat {seat.get('id', '?')} missing 'pod'")
            elif seat["pod"] not in self._pods:
                errors.append(f"Seat {seat['id']} references unknown pod '{seat['pod']}'")
        for pod in self.pods:
            if "id" not in pod:
                errors.append("Pod missing 'id'")
            for sid in pod.get("seats", []):
                if sid not in self._seats:
                    errors.append(f"Pod {pod.get('id', '?')} references unknown seat '{sid}'")
        for edge in self._edges:
            if edge.get("from") not in self._pods:
                errors.append(f"Edge from unknown pod '{edge.get('from')}'")
            if edge.get("to") not in self._pods:
                errors.append(f"Edge to unknown pod '{edge.get('to')}'")
        return errors


def load_rigspec(path: Optional[Path] = None) -> RigSpec:
    """Load rigspec.yaml from the given path or default location."""
    if path is None:
        path = Path(__file__).resolve().parent / "rigspec.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return RigSpec(data)


def is_enabled() -> bool:
    """Check if OpenRig mode is enabled via env var."""
    import os
    return os.environ.get("NEO_OPENRIG_MODE", "").lower() in ("1", "true", "yes", "on")
