from pydantic import BaseModel, Field
from app.models.project.project_template import ProjectTemplate
from app.models.enums import NodeType, DifficultyLevel, SessionStatus
from app.models.project.project_template import TaskTemplate, SubTaskTemplate
from app.models.project.project_session import ProjectSession

#################### Project Expand DTOs ###################

class ProjectExpandRequest(BaseModel):
    """Request model to generate a new project"""
    type: NodeType = Field(..., description="Type of the project to generate")
    title: str = Field(..., min_length=1, description="Title of the project")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the project")
    difficulty: DifficultyLevel

class ProjectExpandResponse(BaseModel):
    """Response model after generating a new project"""
    type : NodeType 
    content: ProjectTemplate

################### Project Abandon DTOs ###################

class ProjectAbandonResponse(BaseModel):
    message: str = "The project attempt has been abandoned."
    status: SessionStatus = SessionStatus.ABANDONED
    session_id: str


################### Session Details DTOs ###################

class ProjectSessionDetailsResponse(BaseModel):
    """Response model for project session details"""
    session: ProjectSession

################### Project Session Start DTOs ###################

class ProjectSessionStartRequest(BaseModel):
    """Request model to start a project attempt"""
    project_id: str = Field(..., min_length=1)
    node_step: int = Field(..., ge=0)

class ProjectSessionStartResponse(BaseModel):
    """Response model after starting a project attempt"""
    session_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    difficulty: DifficultyLevel
    total_tasks: int
    total_subtasks: int

    current_task_index: int = Field(..., ge=0)
    current_subtask_index: int = Field(..., ge=0)

    attempt_number: int = Field(..., ge=1)

    current_task: TaskTemplate
    current_subtask: SubTaskTemplate


################### Project Session Submit DTOs ###################

class ProjectSessionSubmitRequest(BaseModel):
    """Request model to submit a subtask attempt"""
    session_id: str = Field(..., min_length=1)
    user_submission: str = Field(..., min_length=1)


class ProjectSessionSubmitResponse(BaseModel):
    """Response model after submitting a subtask attempt"""
    status : SessionStatus 
    score: int
    feedback: str
    is_task_completed: bool | None
    is_project_completed: bool | None


class ProjectSessionSubmitFailedResponse(ProjectSessionSubmitResponse):
    status : SessionStatus.FAILED
    score: int = 0
    is_task_completed: bool | None = False
    is_project_completed: bool | None = False

class ProjectSessionSubmitPassedResponse(ProjectSessionSubmitResponse):
    status : SessionStatus.PASSED
    next_subtask: SubTaskTemplate

class ProjectSessionSubmitProjectCompletedResponse(ProjectSessionSubmitResponse):
    status : SessionStatus.PASSED
    is_task_completed: bool | None = True
    is_project_completed: bool | None = True
    total_score: float
    xp_earned: float
    total_xp : float
    level : int
    message: str

class ProjectSessionForfeitResponse(ProjectSessionSubmitResponse):
    status : SessionStatus.FORFEITED
    score: int = 0
    message: str = "The subtask has been forfeited."
    solution: str
    next_subtask_index: SubTaskTemplate | None
