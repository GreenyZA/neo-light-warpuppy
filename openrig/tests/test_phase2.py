"""
OpenRig — Phase 2 Tests

Tests for the Intelligence Factory (Project→Mission→Slice hierarchy).
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

from openrig.factory import IntelligenceFactory, Project, Mission, Slice


class TestIntelligenceFactory(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.factory = IntelligenceFactory(projects_dir=Path(self.tmpdir))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_project(self):
        project = self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.assertEqual(project.id, "test-proj")
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.intent, "Test intent")
        self.assertEqual(project.status, "pending")

    def test_create_mission(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        mission = self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1", sequence=1)
        self.assertEqual(mission.id, "mission-1")
        self.assertEqual(mission.outcome, "Ship v1")
        self.assertEqual(mission.sequence, 1)

    def test_create_slice(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        slice_obj = self.factory.create_slice("test-proj", "mission-1", "slice-1", "Add feature", "Implement feature X")
        self.assertEqual(slice_obj.id, "slice-1")
        self.assertEqual(slice_obj.spec, "Implement feature X")
        self.assertEqual(slice_obj.status, "pending")

    def test_get_project(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        project = self.factory.get_project("test-proj")
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")

    def test_get_mission(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        mission = self.factory.get_mission("mission-1")
        self.assertIsNotNone(mission)
        self.assertEqual(mission.outcome, "Ship v1")

    def test_get_slice(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        self.factory.create_slice("test-proj", "mission-1", "slice-1", "Add feature", "Implement feature X")
        slice_obj = self.factory.get_slice("slice-1")
        self.assertIsNotNone(slice_obj)
        self.assertEqual(slice_obj.spec, "Implement feature X")

    def test_list_projects(self):
        self.factory.create_project("proj-1", "Project 1", "Intent 1")
        self.factory.create_project("proj-2", "Project 2", "Intent 2")
        projects = self.factory.list_projects()
        self.assertEqual(len(projects), 2)

    def test_list_missions(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1", sequence=2)
        self.factory.create_mission("test-proj", "mission-2", "Second Release", "Ship v2", sequence=1)
        missions = self.factory.list_missions("test-proj")
        self.assertEqual(len(missions), 2)
        # Should be sorted by sequence
        self.assertEqual(missions[0].id, "mission-2")
        self.assertEqual(missions[1].id, "mission-1")

    def test_list_slices(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        self.factory.create_slice("test-proj", "mission-1", "slice-1", "Add feature A", "Implement A")
        self.factory.create_slice("test-proj", "mission-1", "slice-2", "Add feature B", "Implement B")
        slices = self.factory.list_slices("mission-1")
        self.assertEqual(len(slices), 2)

    def test_get_intent_chain(self):
        self.factory.create_project("test-proj", "Test Project", "Be a good dog owner")
        self.factory.create_mission("test-proj", "mission-1", "Make outdoors comfortable", "Build doghouse")
        self.factory.create_slice("test-proj", "mission-1", "slice-1", "Build usable doghouse", "Build a doghouse")
        chain = self.factory.get_intent_chain("slice-1")
        self.assertEqual(chain["project"], "Be a good dog owner")
        self.assertEqual(chain["mission"], "Build doghouse")
        self.assertEqual(chain["slice"], "Build a doghouse")

    def test_auto_slice(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        slices = self.factory.auto_slice("Big task", "test-proj", "mission-1")
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0].project_id, "test-proj")
        self.assertEqual(slices[0].mission_id, "mission-1")

    def test_slice_dependencies(self):
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        self.factory.create_mission("test-proj", "mission-1", "First Release", "Ship v1")
        self.factory.create_slice("test-proj", "mission-1", "slice-1", "Add feature A", "Implement A")
        slice2 = self.factory.create_slice("test-proj", "mission-1", "slice-2", "Add feature B", "Implement B", dependencies=["slice-1"])
        self.assertEqual(slice2.dependencies, ["slice-1"])

    def test_project_persistence(self):
        """Test that projects are saved to disk and can be reloaded."""
        self.factory.create_project("test-proj", "Test Project", "Test intent")
        # Create a new factory instance pointing to the same directory
        factory2 = IntelligenceFactory(projects_dir=Path(self.tmpdir))
        project = factory2.get_project("test-proj")
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")


if __name__ == "__main__":
    unittest.main()
