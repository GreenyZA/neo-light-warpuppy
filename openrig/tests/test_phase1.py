"""
OpenRig — Phase 1 Tests

Tests for RigSpec loading, seat abstraction, pod grouping, and feature flag.
"""

import os
import sys
import unittest
import shutil
from pathlib import Path

# Ensure the package root is importable
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from openrig.loader import load_rigspec, is_enabled, RigSpec


class TestRigSpecLoading(unittest.TestCase):
    def setUp(self):
        self.rigspec = load_rigspec()

    def test_meta(self):
        self.assertEqual(self.rigspec.meta["name"], "neo-light-warpuppy")
        self.assertEqual(self.rigspec.meta["version"], "0.1.0-phase1")

    def test_seats_loaded(self):
        seats = self.rigspec.seats
        self.assertEqual(len(seats), 6)
        seat_ids = {s["id"] for s in seats}
        self.assertEqual(seat_ids, {"architect", "engineer", "researcher", "reviewer", "budget", "executive"})

    def test_seat_addresses(self):
        for seat in self.rigspec.seats:
            self.assertIn("address", seat)
            self.assertIn("@", seat["address"])
            self.assertTrue(seat["address"].startswith(seat["id"]))

    def test_seat_tribal_wisdom(self):
        for seat in self.rigspec.seats:
            self.assertIn("tribal_wisdom", seat)
            self.assertIsInstance(seat["tribal_wisdom"], list)

    def test_pods_loaded(self):
        pods = self.rigspec.pods
        self.assertEqual(len(pods), 3)
        pod_ids = {p["id"] for p in pods}
        self.assertEqual(pod_ids, {"governance-pod", "routing-pod", "worker-pod"})

    def test_pod_seats(self):
        gov_seats = self.rigspec.get_seats_in_pod("governance-pod")
        self.assertEqual(len(gov_seats), 5)
        routing_seats = self.rigspec.get_seats_in_pod("routing-pod")
        self.assertEqual(len(routing_seats), 1)
        self.assertEqual(routing_seats[0]["id"], "budget")
        worker_seats = self.rigspec.get_seats_in_pod("worker-pod")
        self.assertEqual(len(worker_seats), 0)

    def test_pod_for_seat(self):
        pod = self.rigspec.get_pod_for_seat("architect")
        self.assertIsNotNone(pod)
        self.assertEqual(pod["id"], "governance-pod")

    def test_edges(self):
        edges = self.rigspec.edges
        self.assertEqual(len(edges), 3)
        from_pairs = {(e["from"], e["to"]) for e in edges}
        self.assertIn(("governance-pod", "routing-pod"), from_pairs)
        self.assertIn(("routing-pod", "worker-pod"), from_pairs)
        self.assertIn(("governance-pod", "worker-pod"), from_pairs)

    def test_validate(self):
        errors = self.rigspec.validate()
        self.assertEqual(errors, [])

    def test_continuity_policies(self):
        cont = self.rigspec._data.get("continuity", {})
        self.assertIn("tribal_wisdom_inheritance", cont)
        self.assertTrue(cont["tribal_wisdom_inheritance"]["enabled"])
        self.assertTrue(cont["tribal_wisdom_inheritance"]["review_required"])


class TestFeatureFlag(unittest.TestCase):
    def test_disabled_by_default(self):
        # Save and restore env var
        old = os.environ.get("NEO_OPENRIG_MODE")
        try:
            os.environ.pop("NEO_OPENRIG_MODE", None)
            self.assertFalse(is_enabled())
        finally:
            if old is not None:
                os.environ["NEO_OPENRIG_MODE"] = old

    def test_enabled_by_env(self):
        old = os.environ.get("NEO_OPENRIG_MODE")
        try:
            os.environ["NEO_OPENRIG_MODE"] = "1"
            self.assertTrue(is_enabled())
        finally:
            if old is not None:
                os.environ["NEO_OPENRIG_MODE"] = old
            else:
                os.environ.pop("NEO_OPENRIG_MODE", None)


class TestRefocusStub(unittest.TestCase):
    def test_trace(self):
        from openrig.refocus import Refocus
        refocus = Refocus()
        result = refocus.trace("build doghouse", {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        })
        self.assertTrue(result["aligned"])
        self.assertIn("timestamp", result)


class TestAPMStub(unittest.TestCase):
    def test_record_and_ratio(self):
        import tempfile
        from openrig.apm import APM
        tmpdir = tempfile.mkdtemp()
        try:
            apm = APM(log_dir=Path(tmpdir))
            apm.record_ceremony("boa_session", {"question": "test"})
            apm.record_progress("slice_completed", {"slice": "test"})
            ratio = apm.get_ratio()
            self.assertEqual(ratio["ceremony_count"], 1)
            self.assertEqual(ratio["progress_count"], 1)
            self.assertFalse(ratio["threshold_exceeded"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
