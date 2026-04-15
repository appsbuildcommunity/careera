import json
import uuid
from typing import Any
from string import Template

from app.project.db.persiste import store_projects_generation_result
from app.project.model.project_generation import (
    ProjectsGenerationRequest,
    ProjectsGenerationResponse,
    ProjectSeed
)
from app.share.model.llmchat import LLMChat
from app.share.utils import call_llm, extract_json_payload

SYSTEM_PROMPT = Template("""You are a senior software architect and career coach.

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




async def projects_generation(project_request: ProjectsGenerationRequest) -> ProjectsGenerationResponse:
    """Generate a list of project candidates from career path and preferences."""
    raw_response = await call_llm(_build_chat(project_request))

    try:
        payload = extract_json_payload(raw_response)
        projects_data = payload.get("projects", [])

        if not isinstance(projects_data, list):
            raise ValueError("Expected 'projects' to be a list")

        projects = [
            ProjectSeed(
                project_id=str(uuid.uuid4()),
                **project_data
            )
            for project_data in projects_data
            if isinstance(project_data, dict)
        ]

        if not projects:
            raise ValueError("No valid projects generated")

        await store_projects_generation_result("999", projects)

        return ProjectsGenerationResponse(projects=projects)
    except Exception as e:
        raise ValueError(f"Failed to generate projects list payload: {e}") from e

