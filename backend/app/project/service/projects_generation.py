import json
import uuid
from typing import Any
from string import Template

from pydantic import ValidationError

from app.project.db.persiste import (
    store_projects_generation_result,
)
from app.project.service.errors import (
    ProjectGenerationLLMError,
    ProjectGenerationParseError,
    ProjectPersistenceError,
)
from app.share.utils.logger import get_logger

logger = get_logger(__name__)
from app.project.model import (
    ProjectsGenerationRequest,
    ProjectsGenerationResponse,
    ProjectSeed
)
from app.share.model import LLMChat
from app.share.utils import call_llm, extract_json_payload


SYSTEM_PROMPT = Template("""You are a senior software architect and career coach.

Generate a list of project ideas as STRICTLY VALID JSON (parsable by json.loads).

Output EXACTLY this structure:

{
  "projects": [
    {
      "title": "string",
      "description": "string",
      "specifications": "markdown string with sections: Overview, Architecture, Features, Constraints",
      "suggested_tech_stack": ["string"],
      "phases": [
        {
          "title": "string",
          "description": "string"
          "phase_number": "int"
        }
      ]
    }
  ]
}

Rules:
- MUST return 3 to 5 projects
- "phases" MUST contain between 3 and 10 items
- Each phase must represent a major step in the project
- No trailing commas
- No comments
- No explanations outside JSON
- Output MUST be raw JSON only

USER CAREER CONTEXT (JSON):
$request
""")



def _build_generation_payload(project_request: ProjectsGenerationRequest) -> dict[str, Any]:
    return {
        "target_role": project_request.target_role,
        "experience_level": project_request.experience_level.value,
        "preferred_tech_stack": project_request.preferred_tech_stack,
        "hard_skills": project_request.hard_skills,
        "soft_skills": project_request.soft_skills,
        "interested_roles": project_request.interested_roles,
        "ignored_roles": project_request.ignored_roles,
    }


def _build_chat(project_request: ProjectsGenerationRequest) -> LLMChat:
    request_payload = _build_generation_payload(project_request)

    return (
        LLMChat(
            system=SYSTEM_PROMPT.substitute(
                request=json.dumps(request_payload, ensure_ascii=True, indent=2)
            )
        )
        .add_user("Generate project candidates JSON only.")
    )


def _normalize_project_data(project_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize LLM payload to expected project seed schema."""
    normalized = dict(project_data)
    raw_phases = normalized.get("phases", [])

    if not isinstance(raw_phases, list):
        normalized["phases"] = []
        return normalized

    phases = []
    for index, phase in enumerate(raw_phases):
        if not isinstance(phase, dict):
            continue

        item = dict(phase)
        item.setdefault("phase_number", index + 1)

        # project/generate expects phase outline only; tasks can be expanded later
        if not isinstance(item.get("tasks"), list):
            item["tasks"] = []

        phases.append(item)

    normalized["phases"] = phases
    return normalized


async def projects_generation(user_id: str, project_request: ProjectsGenerationRequest) -> ProjectsGenerationResponse:
    """Generate a list of project candidates from career path and preferences."""
    logger.info(f"Starting project generation for user {user_id}")
    try:
        raw_response = await call_llm(_build_chat(project_request))
    except Exception as e:
        logger.error(f"LLM call failed for user {user_id}: {str(e)}")
        raise ProjectGenerationLLMError("Failed to call LLM for project generation") from e

    try:
        payload = extract_json_payload(raw_response)
        projects_data = payload.get("projects", [])

        if not isinstance(projects_data, list):
            raise ValueError("Expected 'projects' to be a list")

        projects = []
        for index, project_data in enumerate(projects_data):
            if not isinstance(project_data, dict):
                raise ValueError(f"Project at index {index} is not an object")

            try:
                projects.append(
                    ProjectSeed(
                        project_id=str(uuid.uuid4()),
                        **_normalize_project_data(project_data)
                    )
                )
            except ValidationError as exc:
                raise ValueError(f"Project at index {index} failed validation: {exc}") from exc

        

        if not projects:
            raise ValueError("No valid projects generated")
    except Exception as e:
        logger.error(f"Parse failed for user {user_id}: {str(e)}")
        raise ProjectGenerationParseError(f"Failed to parse projects payload: {e}") from e

    try:
        await store_projects_generation_result(user_id, projects)
        logger.info(f"Generated {len(projects)} projects for user {user_id}")
    except Exception as e:
        logger.error(f"Persistence failed for user {user_id}: {str(e)}")
        raise ProjectPersistenceError("Failed to persist generated projects") from e

    return ProjectsGenerationResponse(projects=projects)

