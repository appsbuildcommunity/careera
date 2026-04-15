from pydantic import BaseModel, Field
from typing import Optional, List

from app.share.model.enums import ExperienceLevel, SubmissionType

# Request Models
class ProjectsGenerationRequest(BaseModel):
    """Request to generate a list of project ideas from career path and preferences."""
    target_role: str
    experience_level: ExperienceLevel
    preferred_tech_stack: List[str] = Field(default_factory=list)
    hard_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    interested_roles: List[str] = Field(default_factory=list)
    ignored_roles: List[str] = Field(default_factory=list)

# Response Models
class ProjectsGenerationResponse(BaseModel):
    """Response containing a list of candidate projects."""
    projects: List[ProjectSeed]


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

class ProjectSeed(BaseModel):
    """Project candidate generated for user selection."""
    project_id: str
    title: str
    description: str
    specifications: str
    suggested_tech_stack: List[str] = Field(default_factory=list)




# Database Models
class ProjectInDB(BaseModel):
    """Complete project document in MongoDB"""
    project_id: str
    title: str
    description: str
    specifications: str
    phases: List[Phase]
