"""
OpenRig — Intelligence Factory (Project → Mission → Slice)

The software development lifecycle as a primitive.
Projects break into missions, missions break into slices.
Each slice has a spec (intent) and proof (evidence of completion).
Orchestrators sequence missions; the project sequences releases.
"""

import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Slice:
    """A specific change with a spec and proof."""
    id: str
    title: str
    spec: str  # What we're trying to achieve
    proof: str = ""  # Evidence of completion
    status: str = "pending"  # pending, in_progress, done, blocked
    mission_id: str = ""
    project_id: str = ""
    assigned_seat: str = ""
    tier: str = ""  # T1/T2/T3 routing
    dependencies: List[str] = field(default_factory=list)  # slice IDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "spec": self.spec,
            "proof": self.proof,
            "status": self.status,
            "mission_id": self.mission_id,
            "project_id": self.project_id,
            "assigned_seat": self.assigned_seat,
            "tier": self.tier,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slice":
        return cls(**data)


@dataclass
class Mission:
    """An entire release or accomplishment."""
    id: str
    title: str
    outcome: str  # What we want to release/accomplish
    slice_ids: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, done, blocked
    project_id: str = ""
    sequence: int = 0  # Order within project

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "outcome": self.outcome,
            "slice_ids": self.slice_ids,
            "status": self.status,
            "project_id": self.project_id,
            "sequence": self.sequence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mission":
        return cls(**data)


@dataclass
class Project:
    """The big picture — what we're trying to build and why."""
    id: str
    title: str
    intent: str  # High-level intent
    mission_ids: List[str] = field(default_factory=list)
    status: str = "pending"
    created: str = ""

    def __post_init__(self):
        if not self.created:
            self.created = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "intent": self.intent,
            "mission_ids": self.mission_ids,
            "status": self.status,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(**data)


class IntelligenceFactory:
    """
    The intelligence factory — manages the Project→Mission→Slice hierarchy.
    
    This is the software development lifecycle as a primitive:
    - Projects break into missions (releases)
    - Missions break into slices (specific changes)
    - Each slice has a spec (intent) and proof (evidence)
    - Orchestrators sequence missions
    - The project sequences releases
    """

    def __init__(self, projects_dir: Optional[Path] = None):
        if projects_dir is None:
            projects_dir = Path(__file__).resolve().parent.parent / "work" / "projects"
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_id: str, title: str, intent: str) -> Project:
        """Create a new project."""
        project = Project(id=project_id, title=title, intent=intent)
        self._save_project(project)
        return project

    def create_mission(self, project_id: str, mission_id: str, title: str, outcome: str, sequence: int = 0) -> Mission:
        """Create a new mission within a project."""
        mission = Mission(
            id=mission_id,
            title=title,
            outcome=outcome,
            project_id=project_id,
            sequence=sequence,
        )
        self._save_mission(mission)
        # Add to project
        project = self.get_project(project_id)
        if project:
            project.mission_ids.append(mission_id)
            self._save_project(project)
        return mission

    def create_slice(self, project_id: str, mission_id: str, slice_id: str, title: str, spec: str, dependencies: Optional[List[str]] = None) -> Slice:
        """Create a new slice within a mission."""
        slice_obj = Slice(
            id=slice_id,
            title=title,
            spec=spec,
            mission_id=mission_id,
            project_id=project_id,
            dependencies=dependencies or [],
        )
        self._save_slice(slice_obj)
        # Add to mission
        mission = self.get_mission(mission_id)
        if mission:
            mission.slice_ids.append(slice_id)
            self._save_mission(mission)
        return slice_obj

    def get_project(self, project_id: str) -> Optional[Project]:
        path = self.projects_dir / project_id / "project.yaml"
        if not path.exists():
            return None
        with open(path) as f:
            data = yaml.safe_load(f)
        return Project.from_dict(data)

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        # Search all projects for this mission
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            path = project_dir / "missions" / f"{mission_id}.yaml"
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f)
                return Mission.from_dict(data)
        return None

    def get_slice(self, slice_id: str) -> Optional[Slice]:
        # Search all projects/missions for this slice
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            missions_dir = project_dir / "missions"
            if not missions_dir.exists():
                continue
            for mission_dir in missions_dir.iterdir():
                if not mission_dir.is_dir():
                    continue
                path = mission_dir / "slices" / f"{slice_id}.yaml"
                if path.exists():
                    with open(path) as f:
                        data = yaml.safe_load(f)
                    return Slice.from_dict(data)
        return None

    def list_projects(self) -> List[Project]:
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            path = project_dir / "project.yaml"
            if path.exists():
                with open(path) as f:
                    data = yaml.safe_load(f)
                projects.append(Project.from_dict(data))
        return projects

    def list_missions(self, project_id: str) -> List[Mission]:
        project = self.get_project(project_id)
        if not project:
            return []
        missions = []
        for mid in project.mission_ids:
            mission = self.get_mission(mid)
            if mission:
                missions.append(mission)
        return sorted(missions, key=lambda m: m.sequence)

    def list_slices(self, mission_id: str) -> List[Slice]:
        mission = self.get_mission(mission_id)
        if not mission:
            return []
        slices = []
        for sid in mission.slice_ids:
            slice_obj = self.get_slice(sid)
            if slice_obj:
                slices.append(slice_obj)
        return slices

    def get_intent_chain(self, slice_id: str) -> Dict[str, str]:
        """Trace the intent chain from slice → mission → project."""
        slice_obj = self.get_slice(slice_id)
        if not slice_obj:
            return {}
        mission = self.get_mission(slice_obj.mission_id)
        project = self.get_project(slice_obj.project_id)
        return {
            "project": project.intent if project else "",
            "mission": mission.outcome if mission else "",
            "slice": slice_obj.spec,
        }

    def auto_slice(self, task: str, project_id: str, mission_id: str, threshold_files: int = 3, threshold_modules: int = 2) -> List[Slice]:
        """
        Auto-create slices when a task exceeds thresholds.
        This is the swarm delegation hook — when a task is too big for one worker,
        break it into slices that can be worked in parallel.
        """
        # Phase 2: stub — creates a single slice
        # Phase 3+: implement actual decomposition
        slice_id = f"slice-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        slice_obj = self.create_slice(
            project_id=project_id,
            mission_id=mission_id,
            slice_id=slice_id,
            title=task[:50],
            spec=task,
        )
        return [slice_obj]

    def _save_project(self, project: Project):
        project_dir = self.projects_dir / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(project.to_dict(), f, default_flow_style=False)

    def _save_mission(self, mission: Mission):
        project_dir = self.projects_dir / mission.project_id
        missions_dir = project_dir / "missions"
        missions_dir.mkdir(parents=True, exist_ok=True)
        with open(missions_dir / f"{mission.id}.yaml", "w") as f:
            yaml.dump(mission.to_dict(), f, default_flow_style=False)

    def _save_slice(self, slice_obj: Slice):
        project_dir = self.projects_dir / slice_obj.project_id
        missions_dir = project_dir / "missions" / slice_obj.mission_id
        slices_dir = missions_dir / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        with open(slices_dir / f"{slice_obj.id}.yaml", "w") as f:
            yaml.dump(slice_obj.to_dict(), f, default_flow_style=False)
