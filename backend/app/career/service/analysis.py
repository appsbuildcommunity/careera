import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import BackgroundTasks

from app.career.model.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisDetail,
    AnalysisLLMOutput,
    AnalysisList,
    AnalysisPreferences,
    AnalysisStatus,
    AnalysisSummary,
    ProfileInsight,
    Recommendation,
)
from app.career.utils.json import object_id_str, to_object_id
from app.database.connection import get_database
from app.profile.service.profile import ProfileData, get_profile
from app.share.api.errors import api_error
from app.share.service.llm import generate_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert career analyst. Analyze the candidate's profile and "
    "produce a structured career analysis with tailored recommendations."
)


def _build_prompt(
    profile: ProfileData, preferences: Optional[AnalysisPreferences]
) -> str:
    parts: list[str] = ["Career analysis of the following candidate profile:"]
    if profile.cv_parsed_text:
        parts.append(f"\nCV:\n{profile.cv_parsed_text}")
    if profile.linkedin_parsed_text:
        parts.append(f"\nLinkedIn:\n{profile.linkedin_parsed_text}")
    interests = profile.interests or {}
    roles = interests.get("roles")
    focus_areas = interests.get("focus_areas")
    if roles:
        parts.append(f"\nInterested roles: {', '.join(roles)}")
    if focus_areas:
        parts.append(f"\nFocus areas: {', '.join(focus_areas)}")
    if preferences:
        if preferences.focus_areas:
            parts.append(
                f"\nRequested focus areas: {', '.join(preferences.focus_areas)}"
            )
        if preferences.excluded_roles:
            parts.append(f"\nExcluded roles: {', '.join(preferences.excluded_roles)}")
    parts.append("\nReturn JSON matching the 'career analysis' schema.")
    return "\n".join(parts)


async def create_analysis(
    user_id: str,
    request: Optional[AnalyzeRequest],
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    """Validate the profile and schedule the analysis as a background task."""
    profile = await get_profile(user_id)
    if not profile.cv_parsed_text:
        api_error(
            code="PROFILE_INCOMPLETE",
            message="CV must be uploaded before running analysis.",
            status_code=400,
        )

    db = await get_database()
    result = await db.analyses.insert_one(
        {
            "user_id": to_object_id(user_id),
            "created_at": datetime.now(timezone.utc),
            "status": AnalysisStatus.PENDING.value,
        }
    )
    analysis_id = str(result.inserted_id)
    preferences = request.preferences if request else None
    background_tasks.add_task(run_analysis, analysis_id, user_id, preferences)
    return AnalyzeResponse(analysis_id=analysis_id)


async def list_analyses(user_id: str) -> AnalysisList:
    """Return all analyses for the user, newest first."""
    db = await get_database()
    cursor = db.analyses.find({"user_id": to_object_id(user_id)}).sort(
        "created_at", -1
    )
    items: list[AnalysisSummary] = []
    async for doc in cursor:
        items.append(_to_summary(doc))
    return AnalysisList(analyses=items)


async def get_analysis(user_id: str, analysis_id: str) -> AnalysisDetail:
    """Return a single analysis or raise ``404 ANALYSIS_NOT_FOUND``."""
    try:
        object_id = to_object_id(analysis_id)
    except ValueError:
        api_error(
            code="ANALYSIS_NOT_FOUND",
            message="Analysis not found.",
            status_code=404,
        )

    db = await get_database()
    doc = await db.analyses.find_one(
        {"_id": object_id, "user_id": to_object_id(user_id)}
    )
    if doc is None:
        api_error(
            code="ANALYSIS_NOT_FOUND",
            message="Analysis not found.",
            status_code=404,
        )
    return _to_detail(doc)


async def run_analysis(
    analysis_id: str,
    user_id: str,
    preferences: Optional[AnalysisPreferences],
) -> None:
    """Generate the analysis in the background and persist the result.

    A pure coroutine — the LLM call runs through the provider's native async
    path (``ainvoke``) and DB writes are awaited, so the event loop stays
    responsive to other requests. Any exception marks the analysis ``FAILED``;
    no partial fields are written.
    """
    try:
        profile = await get_profile(user_id)
        result = await generate_json(
            system=SYSTEM_PROMPT,
            user=_build_prompt(profile, preferences),
            response_model=AnalysisLLMOutput,
        )
        output = AnalysisLLMOutput.model_validate(result)
        recommendations = [
            Recommendation(
                rec_index=index,
                title=rec.title,
                description=rec.description,
                match_score=rec.match_score,
                reasoning=rec.reasoning,
                missing_skills=rec.missing_skills,
                tags=rec.tags,
            )
            for index, rec in enumerate(output.recommendations)
        ]
        db = await get_database()
        await db.analyses.update_one(
            {"_id": to_object_id(analysis_id), "user_id": to_object_id(user_id)},
            {
                "$set": {
                    "profile_insight": output.profile_insight.model_dump(),
                    "recommendations": [rec.model_dump() for rec in recommendations],
                    "status": AnalysisStatus.READY.value,
                }
            },
        )
    except Exception:
        logger.exception("Career analysis %s failed", analysis_id)
        try:
            db = await get_database()
            await db.analyses.update_one(
                {"_id": to_object_id(analysis_id), "user_id": to_object_id(user_id)},
                {"$set": {"status": AnalysisStatus.FAILED.value}},
            )
        except Exception:
            logger.exception("Failed to mark analysis %s as FAILED", analysis_id)


def _to_summary(doc: dict) -> AnalysisSummary:
    return AnalysisSummary(
        analysis_id=str(doc["_id"]),
        status=AnalysisStatus(doc["status"]),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        profile_insight=_insight_if_ready(doc),
        recommendations_count=len(doc.get("recommendations") or []),
    )


def _to_detail(doc: dict) -> AnalysisDetail:
    is_ready = doc.get("status") == AnalysisStatus.READY.value
    recommendations = (
        [_to_recommendation(rec) for rec in (doc.get("recommendations") or [])]
        if is_ready
        else []
    )
    return AnalysisDetail(
        analysis_id=str(doc["_id"]),
        status=AnalysisStatus(doc["status"]),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        profile_insight=_insight_if_ready(doc),
        recommendations=recommendations,
    )


def _insight_if_ready(doc: dict) -> Optional[ProfileInsight]:
    if doc.get("status") != AnalysisStatus.READY.value:
        return None
    insight = doc.get("profile_insight")
    return ProfileInsight.model_validate(insight) if insight else None


def _to_recommendation(rec: dict) -> Recommendation:
    return Recommendation(
        rec_index=rec.get("rec_index", 0),
        title=rec.get("title", ""),
        description=rec.get("description", ""),
        match_score=rec.get("match_score", 0),
        reasoning=rec.get("reasoning", ""),
        missing_skills=rec.get("missing_skills") or [],
        tags=rec.get("tags") or [],
        is_expanded=rec.get("is_expanded", False),
        linked_path_id=object_id_str(rec.get("linked_path_id")),
    )
