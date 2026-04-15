import json
from string import Template
from typing import Any

from pydantic import ValidationError

from app.project.db.persiste import get_generated_project_by_id
from app.share.utils.logger import get_logger

logger = get_logger(__name__)
from app.project.model import (
    ExpandedProjectResponse,
    Phase,
    ProjectSeed,
)
from app.project.service.errors import (
    ProjectGenerationLLMError,
    ProjectGenerationParseError,
    ProjectSelectionNotFoundError,
)
from app.share.model import LLMChat
from app.share.utils import call_llm, extract_json_payload

SYSTEM_PROMPT = Template("""You are senior software architect and mentor.

Generate next project phase as STRICTLY VALID JSON only.

Required output structure:
{
  "phase": {
    "title": "string",
    "description": "string",
    "tasks": [
      {
        "task_number": "int",
        "submission_type": "CODE_SNIPPET | GITHUB_LINK | TEXT_ANSWER",
        "title": "string",
        "description": "string",
        "acceptance_criteria": "string"
      }
    ]
  }
}

Constraints:
- Generate only requested phase number: $phase_number
- Return 2-5 actionable tasks
- Tasks must align with project specs and suggested stack
- JSON only, no markdown

PROJECT CONTEXT(JSON):
$project_context
""")


def _build_phase_context(project: ProjectSeed, phase_number: int) -> dict[str, Any]:
    return {
        "title": project.title,
        "description": project.description,
        "specifications": project.specifications,
        "suggested_tech_stack": project.suggested_tech_stack,
        "phases": project.phases[phase_number - 1].model_dump()
    }


def _build_chat(project: ProjectSeed, phase_number: int) -> LLMChat:
    return LLMChat(
        system=SYSTEM_PROMPT.substitute(
            phase_number=phase_number,
            project_context=json.dumps(_build_phase_context(project, phase_number), ensure_ascii=True, indent=2),
        )
    ).add_user(f"Generate phase {phase_number} JSON only.")


def _build_expanded_project(project: ProjectSeed, phase: Phase) -> ProjectSeed:
    return ProjectSeed(
        project_id=project.project_id,
        title=project.title,
        description=project.description,
        specifications=project.specifications,
        suggested_tech_stack=project.suggested_tech_stack,
        phases=[phase if phase.phase_number == p.phase_number else p for p in project.phases]
    )


async def expend_project(user_id: str, project_id: str, phase_number: int) -> ExpandedProjectResponse:
    """Generate requested phase expansion for project snapshot."""
    logger.info(f"Starting phase expansion for user {user_id}, project {project_id}, phase {phase_number}")
    project = await get_generated_project_by_id(user_id, project_id)

    if project is None:
        logger.warning(f"Project not found for user {user_id}, project_id {project_id}")
        raise ProjectSelectionNotFoundError("Selected project not found for user")

    try:
        raw_response = await call_llm(_build_chat(project, phase_number))
    except Exception as e:
        logger.error(f"LLM expansion failed for user {user_id}, phase {phase_number}: {str(e)}")
        raise ProjectGenerationLLMError("Failed to call LLM for project expansion") from e

    try:
        payload = extract_json_payload(raw_response)
        phase_data = payload.get("phase")

        if not isinstance(phase_data, dict):
            raise ValueError("Expected 'phase' to be an object")

        phase_data["phase_number"] = phase_number

        phase = Phase(**phase_data)
        logger.info(f"Phase {phase_number} expansion completed for user {user_id}, project {project_id}")
    except (ValidationError, ValueError, TypeError) as e:
        logger.error(f"Phase parse failed for user {user_id}, phase {phase_number}: {str(e)}")
        raise ProjectGenerationParseError(f"Failed to parse expanded phase payload: {e}") from e

    return ExpandedProjectResponse(project=_build_expanded_project(project, phase))
