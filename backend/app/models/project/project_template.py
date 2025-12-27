from  pydantic  import  BaseModel , computed_field
from app.models.enums import DifficultyLevel
from datetime import datetime

class SubTaskTemplate ( BaseModel ):
    """Subtask model for tags"""
    subtask_index: int 
    title: str 
    description: str 
    acceptance_criteria: str 
    hint: str 
    model_solution: str 


class TaskTemplate ( BaseModel ):
    """Task model for tags"""
    task_index: int 
    title: str 
    description: str 
    subtasks: list[SubTaskTemplate]

    @computed_field
    @property
    def total_subtasks(self) -> int:
        return len(self.subtasks)

# Project template models
class ProjectTemplate ( BaseModel ):
    """Project template model"""
    title: str 
    description: str 
    difficulty: DifficultyLevel  
    tags: list[str] 
    min_pass_score: float 
    estimated_duration: int 
    estimated_minutes: int 
    tasks: list[TaskTemplate]
    created_at: datetime

    @computed_field
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @computed_field
    @property
    def total_subtasks(self) -> int:
        return sum(task.total_subtasks for task in self.tasks)

