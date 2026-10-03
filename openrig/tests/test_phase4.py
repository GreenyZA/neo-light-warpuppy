"""
OpenRig — Phase 4 Tests

Tests for APM (Agent Productivity Monitoring).
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

from openrig.apm import APM


class TestAPMHealth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.apm = APM(log_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_healthy(self):
        self.apm.record_progress("slice_completed", {"slice": "test"})
        health = self.apm.check_health()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["ceremony_count"], 0)
        self.assertEqual(health["progress_count"], 1)

    def test_ceremony_overload(self):
        for i in range(5):
            self.apm.record_ceremony("boa_session", {"question": f"test-{i}"})
        health = self.apm.check_health()
        self.assertEqual(health["status"], "critical")
        self.assertIn("bureaucracy", health["pathologies"])
        self.assertTrue(any("CEREMONY OVERLOAD" in a for a in health["alerts"]))

    def test_high_ratio(self):
        for i in range(10):
            self.apm.record_ceremony("review", {"task": f"test-{i}"})
        for i in range(1):
            self.apm.record_progress("slice_completed", {"slice": "test"})
        health = self.apm.check_health()
        self.assertIn("bureaucracy", health["pathologies"])

    def test_repetition(self):
        for i in range(5):
            self.apm.record_ceremony("review", {"task": "same"})
        health = self.apm.check_health()
        self.assertIn("recursive_proof_loop", health["pathologies"])

    def test_just_following_orders(self):
        for i in range(4):
            self.apm.record_ceremony("approval", {"task": f"test-{i}"})
        health = self.apm.check_health()
        self.assertIn("just_following_orders", health["pathologies"])

    def test_mixed_events(self):
        self.apm.record_ceremony("boa_session", {"question": "test"})
        self.apm.record_ceremony("review", {"task": "test"})
        self.apm.record_progress("slice_completed", {"slice": "test"})
        health = self.apm.check_health()
        self.assertEqual(health["status"], "healthy")

    def test_get_stats(self):
        self.apm.record_ceremony("boa_session", {"question": "test"})
        self.apm.record_progress("slice_completed", {"slice": "test"})
        stats = self.apm.get_stats()
        self.assertEqual(stats["total_ceremony"], 1)
        self.assertEqual(stats["total_progress"], 1)
        self.assertIn("boa_session", stats["ceremony_types"])
        self.assertIn("slice_completed", stats["progress_types"])

    def test_clear_old(self):
        self.apm.record_ceremony("boa_session", {"question": "test"})
        self.apm.clear_old(days=0)  # Clear everything
        health = self.apm.check_health()
        self.assertEqual(health["ceremony_count"], 0)

    def test_custom_thresholds(self):
        apm = APM(log_dir=Path(self.tmpdir), config={"ceremony_threshold": 1})
        apm.record_ceremony("boa_session", {"question": "test"})
        apm.record_ceremony("review", {"task": "test"})
        health = apm.check_health()
        self.assertEqual(health["status"], "critical")


if __name__ == "__main__":
    unittest.main()
