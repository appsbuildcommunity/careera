import json
import re
from typing import Any

from app.profile.model.analyse_profile import (
    CareerPathRecommendation,
    ProfileAnalysisRequest,
    ProfileAnalysisResponse,
    UserProfile,
)
from app.share.utils.call_llm import call_llm
from app.database.persiste import store_analysis_result

SYSTEM_PROMPT = """You are a senior career coach and technical profile analyst.
Analyze the user's profile and return ONLY valid JSON with this exact shape:
{
  "profile": {
    "profile_summary": "string",
    "hard_skills": ["string"],
    "soft_skills": ["string"]
  },
  "recommendations": [
    {
      "role": "string",
      "match_percentage": 0,
      "missing_skills": ["string"],
      "learning_path": ["string"]
    }
  ]
}

Rules:
- Return 3 to 5 career recommendations.
- Match percentage must be an integer from 0 to 100.
- Keep role names practical and specific.
- Use the provided resume, GitHub, LinkedIn, and preferences.
- Do not include markdown, explanations, or extra keys.
"""


def _build_messages(profile: ProfileAnalysisRequest) -> list[dict[str, Any]]:
    user_payload = {
        "user_id": profile.user_id,
        "resume_text": profile.resume_text,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "preferences": profile.preferences.model_dump(),
    }

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Analyze this profile and return the JSON structure only:\n"
                f"{json.dumps(user_payload, ensure_ascii=True, indent=2)}"
            ),
        },
    ]


def _extract_json_payload(raw_response: str) -> dict[str, any]:
    cleaned = raw_response.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start != -1 and json_end != -1:
        cleaned = cleaned[json_start : json_end + 1]

    return json.loads(cleaned)


async def analyse_profile(profile: ProfileAnalysisRequest, user: dict) -> ProfileAnalysisResponse:
    """Analyze user profile and generate career path recommendations."""
    raw_response = await call_llm(_build_messages(profile))

    try:
        payload = _extract_json_payload(raw_response)
        profile_data = payload.get("profile", {})
        recommendations_data = payload.get("recommendations", [])

        result =  ProfileAnalysisResponse(
            profile=UserProfile(
                profile_summary=profile_data.get("profile_summary", ""),
                hard_skills=profile_data.get("hard_skills", []),
                soft_skills=profile_data.get("soft_skills", []),
            ),
            recommendations=[
                CareerPathRecommendation(
                    role=item.get("role", ""),
                    match_percentage=item.get("match_percentage", 0),
                    missing_skills=item.get("missing_skills", []),
                    learning_path=item.get("learning_path", []),
                )
                for item in recommendations_data
            ],
        )
        await store_analysis_result(user.get("user_id", "999"), result)
        return result
    except (json.JSONDecodeError, TypeError, ValueError, KeyError) as e:
        print(f"Failed to parse LLM response, returning fallback result. {e} ")
        raise e



