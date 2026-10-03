"""
OpenRig — TOS Integration Tests

Tests for the TOS ↔ OpenRig integration layer.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Ensure the package root is importable
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from openrig.integration import TOSIntegration, get_integration


class TestTOSIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Ensure OpenRig mode is enabled for tests
        self._old_env = os.environ.get("NEO_OPENRIG_MODE")
        os.environ["NEO_OPENRIG_MODE"] = "1"

    def tearDown(self):
        if self._old_env is not None:
            os.environ["NEO_OPENRIG_MODE"] = self._old_env
        else:
            os.environ.pop("NEO_OPENRIG_MODE", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_active(self):
        integration = TOSIntegration()
        self.assertTrue(integration.is_active())

    def test_get_rigspec(self):
        integration = TOSIntegration()
        rigspec = integration.get_rigspec()
        self.assertIsNotNone(rigspec)
        self.assertEqual(rigspec.meta["name"], "neo-light-warpuppy")

    def test_pre_dispatch_check_pass(self):
        integration = TOSIntegration()
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        }
        result = integration.pre_dispatch_check("build doghouse", intent_chain=chain)
        self.assertTrue(result["should_dispatch"])
        self.assertTrue(result["aligned"])

    def test_pre_dispatch_check_fail(self):
        integration = TOSIntegration()
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "refactor the entire codebase to use microservices",
        }
        result = integration.pre_dispatch_check("refactor", intent_chain=chain)
        self.assertFalse(result["should_dispatch"])
        self.assertTrue(result["requires_human"])

    def test_assign_workers(self):
        integration = TOSIntegration()
        workers = integration.assign_workers("test task", 3)
        self.assertEqual(len(workers), 3)
        self.assertEqual(workers[0]["worker_id"], 1)
        self.assertIsNotNone(workers[0]["seat_id"])

    def test_record_ceremony(self):
        integration = TOSIntegration(log_dir=Path(self.tmpdir))
        integration.record_ceremony("boa_session", {"question": "test"})
        health = integration.check_health()
        self.assertEqual(health["ceremony_count"], 1)

    def test_record_progress(self):
        integration = TOSIntegration(log_dir=Path(self.tmpdir))
        integration.record_progress("slice_completed", {"slice": "test"})
        health = integration.check_health()
        self.assertEqual(health["progress_count"], 1)

    def test_get_slice_routing(self):
        integration = TOSIntegration()
        result = integration.get_slice_routing("slice-1", "build a feature")
        self.assertIn("tier", result)
        self.assertIn("confidence", result)
        self.assertIn("rationale", result)

    def test_get_stats(self):
        integration = TOSIntegration()
        stats = integration.get_stats()
        self.assertTrue(stats["active"])
        self.assertIn("rigspec", stats)
        self.assertIn("apm", stats)
        self.assertIn("refocus", stats)

    def test_singleton(self):
        i1 = get_integration()
        i2 = get_integration()
        self.assertIs(i1, i2)


class TestTOSIntegrationInactive(unittest.TestCase):
    def setUp(self):
        self._old_env = os.environ.get("NEO_OPENRIG_MODE")
        os.environ.pop("NEO_OPENRIG_MODE", None)

    def tearDown(self):
        if self._old_env is not None:
            os.environ["NEO_OPENRIG_MODE"] = self._old_env

    def test_is_inactive(self):
        integration = TOSIntegration()
        self.assertFalse(integration.is_active())

    def test_pre_dispatch_passes_when_inactive(self):
        integration = TOSIntegration()
        result = integration.pre_dispatch_check("any task")
        self.assertTrue(result["should_dispatch"])

    def test_assign_workers_fallback(self):
        integration = TOSIntegration()
        workers = integration.assign_workers("test", 2)
        self.assertEqual(len(workers), 2)
        self.assertIsNone(workers[0]["seat_id"])


if __name__ == "__main__":
    unittest.main()
