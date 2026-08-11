import json
from typing import Any, Callable, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult

from app.share.service.llm.exceptions import LLMProviderError


class MockChatModel(BaseChatModel):
    """LangChain chat model returning deterministic canned JSON.

    Selects the canned payload from the prompt (system + user text), so a single
    instance serves analysis, path, and template generation. No network or API
    key required — used when ``LLM_PROVIDER=mock``.
    """

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = "\n".join(getattr(m, "content", "") or "" for m in messages).lower()
        payload = self._payload_for(prompt)
        message = AIMessage(content=json.dumps(payload))
        return ChatResult(generations=[ChatGeneration(message=message)])

    def with_structured_output(
        self,
        schema: dict[str, Any] | type,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ):
        """Return the mock runnable chained to a JSON output parser."""
        return self | JsonOutputParser()

    @staticmethod
    def _payload_for(prompt: str) -> dict[str, Any]:
        for marker, factory in _PROMPT_MARKERS.items():
            if marker in prompt:
                return factory()
        raise LLMProviderError("Mock provider does not recognize this prompt type.")


def _career_analysis() -> dict[str, Any]:
    return {
        "profile_insight": {
            "summary": (
                "Backend engineer with strong Python, API design, and database "
                "experience, plus solid collaboration skills."
            ),
            "hard_skills": ["Python", "FastAPI", "MongoDB", "REST APIs"],
            "soft_skills": ["Problem Solving", "Communication", "Teamwork"],
        },
        "recommendations": [
            {
                "title": "Backend Engineer",
                "description": "Design and build scalable server-side services and APIs.",
                "match_score": 92,
                "reasoning": (
                    "Existing Python and API skills align strongly with backend engineering."
                ),
                "missing_skills": ["Docker", "System Design", "Kubernetes"],
                "tags": ["Backend", "Python", "APIs"],
            },
            {
                "title": "Full-Stack Developer",
                "description": "Build complete web applications spanning frontend and backend.",
                "match_score": 78,
                "reasoning": (
                    "Backend strength combined with demonstrated problem solving "
                    "supports full-stack growth."
                ),
                "missing_skills": ["React", "Next.js", "TypeScript"],
                "tags": ["Full-Stack", "Web"],
            },
            {
                "title": "DevOps Engineer",
                "description": "Automate infrastructure, deployments, and CI/CD pipelines.",
                "match_score": 65,
                "reasoning": (
                    "Automation and systems thinking show aptitude for DevOps work."
                ),
                "missing_skills": ["Terraform", "AWS", "CI/CD"],
                "tags": ["DevOps", "Cloud"],
            },
        ],
    }


def _career_path() -> dict[str, Any]:
    return {
        "title": "Backend Engineer Career Path",
        "description": (
            "A step-by-step journey from core backend fundamentals to "
            "production-ready systems."
        ),
        "tags": ["Backend", "Python", "APIs"],
        "missing_skills": ["Docker", "System Design", "Kubernetes"],
        "nodes": [
            {
                "title": "Python & API Fundamentals",
                "description": "Master core Python and REST API design principles.",
                "type": "LEARNING",
                "difficulty": "EASY",
                "tags": ["Python", "APIs"],
            },
            {
                "title": "Databases & System Design",
                "description": "Learn data modeling, MongoDB, and system design fundamentals.",
                "type": "LEARNING",
                "difficulty": "MEDIUM",
                "tags": ["Databases", "System Design"],
            },
            {
                "title": "Scalable API Project",
                "description": "Build and deploy a production-grade REST API.",
                "type": "PROJECT",
                "difficulty": "MEDIUM",
                "tags": ["Backend", "APIs"],
            },
            {
                "title": "Backend Engineering Interview",
                "description": "Practice backend system design and coding interviews.",
                "type": "INTERVIEW",
                "difficulty": "HARD",
                "tags": ["Interview"],
            },
        ],
    }


def _learning_template() -> dict[str, Any]:
    return {
        "title": "Python & API Fundamentals",
        "description": (
            "Learn the core Python and API concepts needed to build reliable "
            "backend services."
        ),
        "difficulty": "EASY",
        "tags": ["Python", "APIs"],
        "estimated_duration": "2 hours",
        "estimated_minutes": 120,
        "content": {
            "intro_summary": (
                "This lesson covers Python basics, HTTP semantics, and REST API "
                "design patterns."
            ),
            "key_concepts": [
                {
                    "concept": "HTTP Verbs",
                    "description": "GET, POST, PUT, DELETE and their use cases.",
                    "why_learn": "The foundation of every API.",
                },
                {
                    "concept": "REST Principles",
                    "description": "Resources, statelessness, and status codes.",
                    "why_learn": "Designs predictable and maintainable APIs.",
                },
                {
                    "concept": "Python Typing",
                    "description": "Type hints and dataclasses.",
                    "why_learn": "Improves code clarity and catches bugs early.",
                },
            ],
            "resources": [
                {"label": "FastAPI Docs", "url": "https://fastapi.tiangolo.com"},
                {"label": "MDN HTTP Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP"},
            ],
        },
    }


def _project_template() -> dict[str, Any]:
    return {
        "title": "Scalable API Project",
        "difficulty": "MEDIUM",
        "tags": ["Backend", "APIs"],
        "min_pass_score": 70,
        "estimated_duration": "4 hours",
        "estimated_minutes": 240,
        "total_tasks": 2,
        "total_subtasks": 3,
        "tasks": [
            {
                "task_index": 0,
                "title": "Build the API",
                "description": "Create a REST API with CRUD endpoints.",
                "subtasks": [
                    {
                        "subtask_index": 0,
                        "title": "Models & Schemas",
                        "description": "Define Pydantic models for resources.",
                        "acceptance_criteria": "All resources validate correctly.",
                        "hint": "Use pydantic BaseModel.",
                        "model_solution": "class Item(BaseModel): ...",
                    },
                    {
                        "subtask_index": 1,
                        "title": "Endpoints",
                        "description": "Implement CRUD routes.",
                        "acceptance_criteria": "All CRUD routes respond correctly.",
                        "hint": "Use an APIRouter.",
                        "model_solution": "router = APIRouter() ...",
                    },
                ],
            },
            {
                "task_index": 1,
                "title": "Deploy",
                "description": "Containerize and deploy the service.",
                "subtasks": [
                    {
                        "subtask_index": 0,
                        "title": "Dockerfile",
                        "description": "Write a Dockerfile.",
                        "acceptance_criteria": "Image builds successfully.",
                        "hint": "Base on python slim.",
                        "model_solution": "FROM python:3.12-slim ...",
                    },
                ],
            },
        ],
    }


def _interview_template() -> dict[str, Any]:
    return {
        "title": "Backend Engineering Interview",
        "difficulty": "HARD",
        "tags": ["Interview"],
        "min_pass_score": 70,
        "estimated_duration": "1 hour",
        "estimated_minutes": 60,
        "total_questions": 3,
        "questions": [
            {
                "question_index": 0,
                "text": "Explain how you would design a rate limiter.",
                "hint": "Consider token bucket vs sliding window.",
                "model_answer": (
                    "A token bucket allows bursts up to the bucket capacity while "
                    "enforcing a steady long-term rate."
                ),
            },
            {
                "question_index": 1,
                "text": "What are the tradeoffs of MongoDB vs PostgreSQL?",
                "hint": "Think about schema flexibility and consistency.",
                "model_answer": (
                    "MongoDB offers flexible documents and horizontal scaling, while "
                    "PostgreSQL provides strong relational integrity and joins."
                ),
            },
            {
                "question_index": 2,
                "text": "How do you scale a read-heavy API?",
                "hint": "Caching and read replicas.",
                "model_answer": (
                    "Add a caching layer and route reads to read replicas, keeping "
                    "writes on the primary."
                ),
            },
        ],
    }


_PROMPT_MARKERS: dict[str, Callable[[], dict[str, Any]]] = {
    "career analysis": _career_analysis,
    "career path": _career_path,
    "learning template": _learning_template,
    "project template": _project_template,
    "interview template": _interview_template,
}
