from enum import Enum

class DifficultyLevel (str, Enum ):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"

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
    ENTRY_LEVEL = "ENTRY_LEVEL"
    JUNIOR = "JUNIOR"
    MID_LEVEL = "MID_LEVEL"
    SENIOR = "SENIOR"
    PRINCIPAL = "PRINCIPAL"

class SubmissionType(str, Enum):
    CODE_SNIPPET = "CODE_SNIPPET"
    GITHUB_LINK = "GITHUB_LINK"
    TEXT_ANSWER = "TEXT_ANSWER"

class Sentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
