from enum import Enum

class DifficultyLevel ( str ,  Enum ):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"

class NodeType(str, Enum):
    PROJECT = "PROJECT"
    LEARNING = "LEARNING"
    INTERVIEW = "INTERVIEW"

class NodeStatus(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    COMPLETED = "COMPLETED"

class ExperienceLevel(str, Enum):
    ENTRY = "ENTRY"
    MID = "MID"
    SENIOR = "SENIOR"

class SubmissionType(str, Enum):
    CODE = "CODE"
    TEXT_ANSWER = "TEXT_ANSWER"
    GITHUB_LINK = "GITHUB_LINK"
