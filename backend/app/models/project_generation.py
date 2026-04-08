from pydantic import BaseModel, Field
from typing import Optional, List

from app.models.enums import ExperienceLevel, SubmissionType

# Request Models
class ProjectGenerationRequest(BaseModel):
    """Request to generate a project idea based on user profile"""
    user_id: Optional[str] = None
    target_role: str
    experience_level: ExperienceLevel
    preferred_tech_stack: List[str] = Field(default_factory=list)

class TaskEvaluationRequest(BaseModel):
    """Request to evaluate a submitted task"""
    user_id: str
    project_id: str
    phase_number: int
    task_number: int
    submission_type: SubmissionType
    user_submission: str


# Response Models
class ProjectGenerationResponse(BaseModel):
    """Response containing generated project details"""
    project_id: str
    title: str
    description: str
    specifications: str
    phases : List[Phase]

class TaskEvaluationResponse(BaseModel):
    """Response after evaluating a submitted task"""
    project_id: str
    phase_number: int
    task_number: int
    feedback: str
    score: int
    passed: bool
    suuggestions: Optional[List[str]] = []

class Task(BaseModel):
    step_number: int
    submission_type: SubmissionType
    title: str
    description: str
    acceptance_criteria: str

class Phase(BaseModel):
    title: str
    description: str
    tasks: List[Task]


# Database Models
class ProjectInDB(BaseModel):
    """Complete project document in MongoDB"""
    project_id: str
    title: str
    description: str
    specifications: str
    phases : List[Phase]
