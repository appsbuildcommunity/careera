import json
from string import Template
from typing import Any

from pydantic import ValidationError

from app.project.db.persiste import get_generated_project_by_id
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


def _build_phase_context(project: ProjectSeed) -> dict[str, Any]:
    return {
        "title": project.title,
        "description": project.description,
        "specifications": project.specifications,
        "suggested_tech_stack": project.suggested_tech_stack,
        "phases" : project.phases[0]
    }


def _build_chat(project: ProjectSeed, phase_number: int) -> LLMChat:
    return LLMChat(
        system=SYSTEM_PROMPT.substitute(
            phase_number=phase_number,
            project_context=json.dumps(_build_phase_context(project), ensure_ascii=True, indent=2),
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
    project = await get_generated_project_by_id(user_id, project_id)

    if project is None:
        raise ProjectSelectionNotFoundError("Selected project not found for user")

    try:
        raw_response = await call_llm(_build_chat(project, phase_number))
    except Exception as e:
        raise ProjectGenerationLLMError("Failed to call LLM for project expansion") from e

    try:
        payload = extract_json_payload(raw_response)
        phase_data = payload.get("phase")

        if not isinstance(phase_data, dict):
            raise ValueError("Expected 'phase' to be an object")

        phase = Phase(**phase_data)
    except (ValidationError, ValueError, TypeError) as e:
        raise ProjectGenerationParseError(f"Failed to parse expanded phase payload: {e}") from e

    return ExpandedProjectResponse(project=_build_expanded_project(project, phase))
