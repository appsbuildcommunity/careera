import json

from app.profile.model.analyse_profile import (
    CareerPathRecommendation,
    ProfileAnalysisRequest,
    ProfileAnalysisResponse,
    UserProfile,
)
from app.share.model.llmchat import LLMChat
from app.share.utils import call_llm, extract_json_payload
from app.profile.db.persiste import store_analysis_result

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


def _build_chat(profile: ProfileAnalysisRequest) -> LLMChat:
    user_payload = {
        "resume_text": profile.resume_text,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "preferences": profile.preferences.model_dump(),
    }

    return (
        LLMChat(system=SYSTEM_PROMPT)
        .add_user(
            "Analyze this profile and return the JSON structure only:\n"
            + json.dumps(user_payload)
        )
    )



async def analyse_profile(profile: ProfileAnalysisRequest, user: dict) -> ProfileAnalysisResponse:
    raw_response = await call_llm(_build_chat(profile))

    payload = extract_json_payload(raw_response)

    profile_data = payload.get("profile", {})
    recommendations_data = payload.get("recommendations", [])

    result = ProfileAnalysisResponse(
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

