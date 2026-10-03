"""
OpenRig — Phase 3 Tests

Tests for Refocus intent-chain tracing and pre-dispatch checks.
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

from openrig.refocus import Refocus


class TestRefocusAlignment(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.refocus = Refocus(log_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_perfect_alignment(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        }
        result = self.refocus.trace("build doghouse", chain)
        self.assertTrue(result["aligned"])
        self.assertGreater(result["alignment_score"], 0.5)

    def test_poor_alignment(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "refactor the entire codebase to use microservices",
        }
        result = self.refocus.trace("refactor", chain)
        self.assertFalse(result["aligned"])
        self.assertLess(result["alignment_score"], 0.5)

    def test_moonbase_warning(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a doghouse and also add a swimming pool and bonus patio",
        }
        result = self.refocus.trace("build doghouse + pool", chain)
        self.assertTrue(len(result["warnings"]) > 0)
        self.assertTrue(any("MOONBASE" in w for w in result["warnings"]))

    def test_empty_chain(self):
        chain = {}
        result = self.refocus.trace("task", chain)
        self.assertFalse(result["aligned"])
        self.assertEqual(result["alignment_score"], 0.0)

    def test_pre_dispatch_check_pass(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        }
        result = self.refocus.pre_dispatch_check("build doghouse", intent_chain=chain)
        self.assertTrue(result["should_dispatch"])
        self.assertTrue(result["aligned"])
        self.assertFalse(result["requires_human"])

    def test_pre_dispatch_check_fail(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "refactor the entire codebase to use microservices and kubernetes",
        }
        result = self.refocus.pre_dispatch_check("refactor", intent_chain=chain)
        self.assertFalse(result["should_dispatch"])
        self.assertFalse(result["aligned"])
        self.assertTrue(result["requires_human"])

    def test_pre_dispatch_no_chain(self):
        result = self.refocus.pre_dispatch_check("task")
        self.assertTrue(result["should_dispatch"])
        self.assertTrue(result["aligned"])
        self.assertFalse(result["requires_human"])

    def test_get_stats(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        }
        self.refocus.trace("build doghouse", chain)
        stats = self.refocus.get_stats()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["aligned"], 1)
        self.assertEqual(stats["misaligned"], 0)

    def test_get_recent(self):
        chain = {
            "project": "be a good dog owner",
            "mission": "make the outdoors comfortable for the dog",
            "slice": "build a usable doghouse for the dog",
        }
        self.refocus.trace("build doghouse", chain)
        recent = self.refocus.get_recent(limit=5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["task"], "build doghouse")


if __name__ == "__main__":
    unittest.main()
