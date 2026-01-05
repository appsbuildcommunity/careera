from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from datetime import datetime
from app.models.enums import SessionStatus


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class SubtaskStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    FORFEITED = "FORFEITED"

class SubtaskSession(BaseModel):
    subtask_index: int 
    user_submission: str | None
    score: float | None
    status: SubtaskStatus = SubtaskStatus.PENDING
    feedback: str | None

class TaskSession(BaseModel):
    task_index: int 
    status: TaskStatus = TaskStatus.PENDING
    subtasks: List[SubtaskSession] 

class ProjectSession(BaseModel):
    user_id: str 
    template_id: str 
    path_id: str | None
    node_step: int 

    status: SessionStatus = SessionStatus.IN_PROGRESS
    current_task_index: int 
    current_subtask_index: int 
    total_score: int 

    xp_earned: int 
    attempt_number: int 

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None
    duration_seconds: int | None

    tasks: List[TaskSession] 

