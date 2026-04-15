from pydantic import BaseModel, Field
from typing import Any, Optional, List

from app.models.enums import ExperienceLevel, SubmissionType

# Request Models
class ProjectsGenerationRequest(BaseModel):
    """Request to generate a list of project ideas from career path and preferences."""
    user_id: Optional[str] = None
    target_role: str
    experience_level: ExperienceLevel
    preferred_tech_stack: List[str] = Field(default_factory=list)
    hard_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    interested_roles: List[str] = Field(default_factory=list)
    ignored_roles: List[str] = Field(default_factory=list)
    previous_phase_completion: Optional[List[dict[str, Any]]] = None


class ProjectGenerationRequest(ProjectsGenerationRequest):
    """Backward-compatible alias for projects list generation request."""


class ProjectSeed(BaseModel):
    """Project candidate generated for user selection."""
    project_id: str
    title: str
    description: str
    specifications: str
    suggested_tech_stack: List[str] = Field(default_factory=list)


class ProjectsGenerationResponse(BaseModel):
    """Response containing a list of candidate projects."""
    projects: List[ProjectSeed]


class ProjectExpandRequest(BaseModel):
    """Request to expand one selected project into implementation phases and tasks."""
    user_id: Optional[str] = None
    target_role: str
    experience_level: ExperienceLevel
    preferred_tech_stack: List[str] = Field(default_factory=list)
    hard_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    selected_project: ProjectSeed
    previous_phase_completion: Optional[List[dict[str, Any]]] = None

class TaskEvaluationRequest(BaseModel):
    """Request to evaluate a submitted task"""
    user_id: str
    project_id: str
    phase_number: int
    task_number: int
    submission_type: SubmissionType
    user_submission: str


class Task(BaseModel):
    task_id: Optional[str] = None
    task_number: int
    submission_type: SubmissionType
    title: str
    description: str
    acceptance_criteria: str

class Phase(BaseModel):
    title: str
    description: str
    tasks: List[Task]


# Response Models
class ProjectGenerationResponse(BaseModel):
    """Response containing expanded project details."""
    project_id: str
    title: str
    description: str
    specifications: str
    phases: List[Phase]


class ProjectExpandResponse(ProjectGenerationResponse):
    """Alias response model for expanded project details."""


class TaskEvaluationResponse(BaseModel):
    """Response after evaluating a submitted task"""
    project_id: str
    phase_number: int
    task_number: int
    feedback: str
    score: int
    passed: bool
    suggestions: Optional[List[str]] = Field(default_factory=list)


# Database Models
class ProjectInDB(BaseModel):
    """Complete project document in MongoDB"""
    project_id: str
    title: str
    description: str
    specifications: str
    phases: List[Phase]
