import json
import re
from typing import Any
from uuid import uuid4
from string import Template

from app.project.model.project_generation import (
    ProjectsGenerationRequest,
    ProjectsGenerationResponse,
    ProjectExpandRequest,
    ProjectExpandResponse,
    ProjectGenerationRequest,
    ProjectGenerationResponse,
    ProjectSeed,
    Phase,
    Task,
)
from app.project.model.enums import SubmissionType
from app.share.utils.call_llm import call_llm

PROJECTS_GENERATION_PROMPT = Template("""You are a senior software architect and career coach.

Generate a list of project ideas as STRICTLY VALID JSON (parsable by json.loads), with this exact structure:

{
    "projects": [
        {
            "title": "string",
            "description": "string",
            "specifications": "markdown string with sections: Overview, Architecture, Features, Constraints",
            "suggested_tech_stack": ["string"]
        }
    ]
}

Constraints:
- MUST return 3-5 projects
- Projects MUST align to target role, experience level, skills, and preferences
- Each project should be realistically buildable and portfolio-worthy
- Output MUST be raw JSON only (no markdown, no explanations, no trailing commas)

USER CAREER CONTEXT(JSON):
        $request

""")


PROJECT_EXPAND_PROMPT = Template("""You are a senior software architect and project coach.

Generate one project as STRICTLY VALID JSON (parsable by json.loads), with this exact structure:

{
    "title": "string",
    "description": "string",
    "specifications": "markdown string with sections: Overview, Architecture, Features, Constraints (in detail)",
    "phases": [
        {
            "title": "string",
            "description": "string",
            "tasks": [
                {
                    "task_number": integer,
                    "submission_type": "CODE_SNIPPET|GITHUB_LINK|TEXT_ANSWER",
                    "title": "string",
                    "description": "string",
                    "acceptance_criteria": "string"
                }
            ]
        }
    ]
}

Constraints:
- MUST return 3-5 phases
- Each phase MUST have 2–5 tasks
- task_number MUST be sequential starting from 1 within each phase
- Output MUST be raw JSON only (no markdown, no explanations, no trailing commas)

USER REQUEST(JSON):
        $request

""")

def _build_generation_payload(project_request: ProjectsGenerationRequest) -> dict[str, Any]:
    return {
        "user_id": project_request.user_id,
        "target_role": project_request.target_role,
        "experience_level": project_request.experience_level.value,
        "preferred_tech_stack": project_request.preferred_tech_stack,
        "hard_skills": project_request.hard_skills,
        "soft_skills": project_request.soft_skills,
        "interested_roles": project_request.interested_roles,
        "ignored_roles": project_request.ignored_roles,
        "previous_phase_completion": project_request.previous_phase_completion or [],
    }


def _build_projects_generation_messages(project_request: ProjectsGenerationRequest) -> list[dict[str, str]]:
    request_payload = _build_generation_payload(project_request)

    return [
        {
            "role": "system",
            "content": PROJECTS_GENERATION_PROMPT.substitute(
                request=json.dumps(request_payload, ensure_ascii=True, indent=2)
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate project candidates JSON only:\n"
                f"{json.dumps(request_payload, ensure_ascii=True, indent=2)}"
            ),
        },
    ]


def _build_project_expand_messages(expand_request: ProjectExpandRequest) -> list[dict[str, str]]:
    request_payload = {
        "user_id": expand_request.user_id,
        "target_role": expand_request.target_role,
        "experience_level": expand_request.experience_level.value,
        "preferred_tech_stack": expand_request.preferred_tech_stack,
        "hard_skills": expand_request.hard_skills,
        "soft_skills": expand_request.soft_skills,
        "selected_project": expand_request.selected_project.model_dump(),
        "previous_phase_completion": expand_request.previous_phase_completion or [],
    }

    return [
        {
            "role": "system",
            "content": PROJECT_EXPAND_PROMPT.substitute(
                request=json.dumps(request_payload, ensure_ascii=True, indent=2)
            ),
        },
        {
            "role": "user",
            "content": (
                "Expand this selected project into implementation phases and tasks. JSON only:\n"
                f"{json.dumps(request_payload, ensure_ascii=True, indent=2)}"
            ),
        },
    ]


def _extract_json_payload(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start != -1 and json_end != -1:
        cleaned = cleaned[json_start : json_end + 1]

    return json.loads(cleaned)


def _normalize_submission_type(value: Any) -> SubmissionType:
    if isinstance(value, SubmissionType):
        return value

    if isinstance(value, str):
        normalized = value.strip().upper()
        try:
            return SubmissionType(normalized)
        except ValueError:
            if normalized == "TEXT":
                return SubmissionType.TEXT_ANSWER

    raise ValueError(f"Unsupported submission_type: {value!r}")


def _to_positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def _normalize_task(task_data: dict[str, Any], fallback_number: int) -> Task:
    task_number = _to_positive_int(
        task_data.get("task_number", task_data.get("step_order", task_data.get("step_number"))),
        fallback_number,
    )

    task_id = task_data.get("task_id") or f"task-{task_number}"

    return Task(
        task_id=task_id,
        task_number=task_number,
        submission_type=_normalize_submission_type(task_data.get("submission_type", SubmissionType.CODE_SNIPPET.value)),
        title=task_data.get("title", "Untitled task"),
        description=task_data.get("description", ""),
        acceptance_criteria=task_data.get("acceptance_criteria", ""),
    )


def _normalize_phase(phase_data: dict[str, Any]) -> Phase:
    tasks = [
        _normalize_task(task_data, index + 1)
        for index, task_data in enumerate(phase_data.get("tasks", []))
    ]

    return Phase(
        title=phase_data.get("title", "Untitled phase"),
        description=phase_data.get("description", ""),
        tasks=tasks,
    )


def _extract_project_data(payload: dict[str, Any]) -> dict[str, Any]:
    projects = payload.get("projects")
    if isinstance(projects, list) and projects:
        first = projects[0]
        if isinstance(first, dict):
            return first
    return payload


def _normalize_project_seed(project_data: dict[str, Any], fallback_index: int) -> ProjectSeed:
    return ProjectSeed(
        project_id=project_data.get("project_id") or f"proj-{uuid4().hex[:8]}-{fallback_index}",
        title=project_data.get("title", f"Project {fallback_index}"),
        description=project_data.get("description", ""),
        specifications=project_data.get("specifications", project_data.get("specification", "")),
        suggested_tech_stack=project_data.get("suggested_tech_stack", project_data.get("tech_stack", [])) or [],
    )


async def projects_generation(project_request: ProjectsGenerationRequest) -> ProjectsGenerationResponse:
    """Generate a list of project candidates from career path and preferences."""
    raw_response = await call_llm(_build_projects_generation_messages(project_request))

    try:
        payload = _extract_json_payload(raw_response)
        projects_data = payload.get("projects", [])

        if not isinstance(projects_data, list):
            raise ValueError("Expected 'projects' to be a list")

        projects = [
            _normalize_project_seed(project_data, index + 1)
            for index, project_data in enumerate(projects_data)
            if isinstance(project_data, dict)
        ]

        if not projects:
            raise ValueError("No valid projects generated")

        return ProjectsGenerationResponse(projects=projects)
    except Exception as e:
        raise ValueError(f"Failed to generate projects list payload: {e}") from e


async def project_expand(expand_request: ProjectExpandRequest) -> ProjectExpandResponse:
    """Expand a selected project into detailed phases and tasks."""
    raw_response = await call_llm(_build_project_expand_messages(expand_request))

    try:
        project_data = _extract_project_data(_extract_json_payload(raw_response))
        phases_data = project_data.get("phases", [])
        result = ProjectExpandResponse(
            project_id=expand_request.selected_project.project_id,
            title=project_data.get("title", "Untitled Project"),
            description=project_data.get("description", ""),
            specifications=project_data.get(
                "specifications",
                project_data.get("specification", expand_request.selected_project.specifications),
            ),
            phases=[_normalize_phase(phase_data) for phase_data in phases_data],
        )
        return result
    except Exception as e:
        raise ValueError(f"Failed to expand project payload: {e}") from e


async def generate_project(project_request: ProjectGenerationRequest) -> ProjectGenerationResponse:
    """Backward-compatible wrapper: generate and expand the first project candidate."""
    generated = await projects_generation(project_request)
    selected_project = generated.projects[0]
    expanded = await project_expand(
        ProjectExpandRequest(
            user_id=project_request.user_id,
            target_role=project_request.target_role,
            experience_level=project_request.experience_level,
            preferred_tech_stack=project_request.preferred_tech_stack,
            hard_skills=project_request.hard_skills,
            soft_skills=project_request.soft_skills,
            selected_project=selected_project,
            previous_phase_completion=project_request.previous_phase_completion,
        )
    )

    return ProjectGenerationResponse(**expanded.model_dump())
