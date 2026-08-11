import asyncio
from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from fastapi import BackgroundTasks

from app.career.model.analysis import (
    AnalyzeRequest,
    AnalysisPreferences,
    AnalysisStatus,
)
from app.career.service.analysis import (
    create_analysis,
    get_analysis,
    list_analyses,
    run_analysis,
)
from app.share.api.errors import AppError

USER_ID = str(ObjectId())

LLM_RESULT = {
    "profile_insight": {
        "summary": "Backend engineer with strong Python and API skills.",
        "hard_skills": ["Python", "FastAPI"],
        "soft_skills": ["Communication"],
    },
    "recommendations": [
        {
            "title": "Backend Engineer",
            "description": "Build scalable services.",
            "match_score": 92,
            "reasoning": "Strong Python match.",
            "missing_skills": ["Docker"],
            "tags": ["Backend"],
        },
        {
            "title": "Full-Stack Developer",
            "description": "Build web apps.",
            "match_score": 78,
            "reasoning": "Good foundation.",
            "missing_skills": ["React"],
            "tags": ["Full-Stack"],
        },
    ],
}


def _user_with_cv(**profile_kwargs):
    profile = {
        "cv_parsed_text": "Python backend engineer",
        "linkedin_parsed_text": "Built REST APIs",
        "interests": {"roles": ["Backend Engineer"], "focus_areas": ["AI"]},
    }
    profile.update(profile_kwargs)
    return {"_id": ObjectId(USER_ID), "profile": profile}


def _analysis_doc(status: str, **extra):
    doc = {
        "_id": ObjectId(),
        "user_id": ObjectId(USER_ID),
        "created_at": datetime.utcnow(),
        "status": status,
    }
    doc.update(extra)
    return doc


def test_create_analysis_raises_profile_incomplete_when_no_cv(fake_db):
    async def scenario():
        with pytest.raises(AppError) as excinfo:
            await create_analysis(USER_ID, None, BackgroundTasks())
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.code == "PROFILE_INCOMPLETE"
    assert error.status_code == 400


def test_create_analysis_raises_profile_incomplete_when_no_user_doc(fake_db):
    async def scenario():
        with pytest.raises(AppError) as excinfo:
            await create_analysis(USER_ID, None, BackgroundTasks())
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.code == "PROFILE_INCOMPLETE"


def test_create_analysis_schedules_run_analysis(fake_db):
    fake_db.users.docs.append(_user_with_cv())
    background_tasks = BackgroundTasks()

    response = asyncio.run(
        create_analysis(USER_ID, None, background_tasks)
    )

    assert response.status == AnalysisStatus.PENDING
    assert response.message.startswith("Analysis started.")
    assert len(background_tasks.tasks) == 1
    task = background_tasks.tasks[0]
    assert task.func is run_analysis
    assert task.args == (response.analysis_id, USER_ID, None)
    assert task.kwargs == {}


def test_create_analysis_forwards_preferences_to_background_task(fake_db):
    fake_db.users.docs.append(_user_with_cv())
    request = AnalyzeRequest(
        preferences=AnalysisPreferences(
            focus_areas=["AI"], excluded_roles=["QA"]
        )
    )
    background_tasks = BackgroundTasks()

    asyncio.run(create_analysis(USER_ID, request, background_tasks))

    task = background_tasks.tasks[0]
    preferences = task.args[2]
    assert isinstance(preferences, AnalysisPreferences)
    assert preferences.focus_areas == ["AI"]
    assert preferences.excluded_roles == ["QA"]


def test_list_analyses_maps_and_sorts_newest_first(fake_db):
    older = _analysis_doc(
        "PENDING", created_at=datetime.utcnow() - timedelta(days=1)
    )
    newer = _analysis_doc(
        "READY",
        created_at=datetime.utcnow(),
        profile_insight=LLM_RESULT["profile_insight"],
        recommendations=[
            {
                "rec_index": 0,
                "title": "Backend Engineer",
                "description": "d",
                "match_score": 92,
                "reasoning": "r",
                "missing_skills": [],
                "tags": [],
                "is_expanded": False,
                "linked_path_id": None,
            }
        ],
    )
    fake_db.analyses.docs.extend([older, newer])

    result = asyncio.run(list_analyses(USER_ID))

    assert [a.analysis_id for a in result.analyses] == [
        str(newer["_id"]),
        str(older["_id"]),
    ]
    ready = result.analyses[0]
    assert ready.status == AnalysisStatus.READY
    assert ready.profile_insight is not None
    assert ready.profile_insight.hard_skills == ["Python", "FastAPI"]
    assert ready.recommendations_count == 1
    pending = result.analyses[1]
    assert pending.status == AnalysisStatus.PENDING
    assert pending.profile_insight is None
    assert pending.recommendations_count == 0


def test_get_analysis_returns_full_detail_when_ready(fake_db):
    doc = _analysis_doc(
        "READY",
        profile_insight=LLM_RESULT["profile_insight"],
        recommendations=[
            {
                "rec_index": 0,
                "title": "Backend Engineer",
                "description": "d",
                "match_score": 92,
                "reasoning": "r",
                "missing_skills": ["Docker"],
                "tags": ["Backend"],
                "is_expanded": False,
                "linked_path_id": None,
            }
        ],
    )
    fake_db.analyses.docs.append(doc)

    detail = asyncio.run(get_analysis(USER_ID, str(doc["_id"])))

    assert detail.status == AnalysisStatus.READY
    assert detail.profile_insight is not None
    assert detail.profile_insight.summary.startswith("Backend engineer")
    assert len(detail.recommendations) == 1
    assert detail.recommendations[0].rec_index == 0
    assert detail.recommendations[0].is_expanded is False
    assert detail.recommendations[0].linked_path_id is None


def test_get_analysis_empty_until_ready(fake_db):
    doc = _analysis_doc("PENDING")
    fake_db.analyses.docs.append(doc)

    detail = asyncio.run(get_analysis(USER_ID, str(doc["_id"])))

    assert detail.status == AnalysisStatus.PENDING
    assert detail.profile_insight is None
    assert detail.recommendations == []


def test_get_analysis_not_found(fake_db):
    async def scenario():
        with pytest.raises(AppError) as excinfo:
            await get_analysis(USER_ID, str(ObjectId()))
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.code == "ANALYSIS_NOT_FOUND"
    assert error.status_code == 404


def test_get_analysis_invalid_id_raises_not_found(fake_db):
    async def scenario():
        with pytest.raises(AppError) as excinfo:
            await get_analysis(USER_ID, "not-a-valid-object-id")
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.code == "ANALYSIS_NOT_FOUND"


def test_get_analysis_user_scoped(fake_db):
    doc = _analysis_doc("READY")
    fake_db.analyses.docs.append(doc)

    async def scenario():
        with pytest.raises(AppError) as excinfo:
            await get_analysis(str(ObjectId()), str(doc["_id"]))
        return excinfo.value

    error = asyncio.run(scenario())
    assert error.code == "ANALYSIS_NOT_FOUND"


def test_run_analysis_persists_ready_with_sequential_indices(fake_db, monkeypatch):
    async def _fake_generate_json(**kwargs):
        return LLM_RESULT

    monkeypatch.setattr(
        "app.career.service.analysis.generate_json", _fake_generate_json
    )
    doc = _analysis_doc("PENDING")
    fake_db.analyses.docs.append(doc)
    fake_db.users.docs.append(_user_with_cv())

    asyncio.run(run_analysis(str(doc["_id"]), USER_ID, None))

    updated = asyncio.run(
        fake_db.analyses.find_one({"_id": doc["_id"]})
    )
    assert updated["status"] == "READY"
    assert updated["profile_insight"]["summary"].startswith("Backend engineer")
    assert [r["rec_index"] for r in updated["recommendations"]] == [0, 1]
    assert updated["recommendations"][0]["is_expanded"] is False
    assert updated["recommendations"][0]["linked_path_id"] is None


def test_run_analysis_marks_failed_on_exception(fake_db, monkeypatch):
    async def _boom(**kwargs):
        raise RuntimeError("llm down")

    monkeypatch.setattr("app.career.service.analysis.generate_json", _boom)
    doc = _analysis_doc("PENDING")
    fake_db.analyses.docs.append(doc)
    fake_db.users.docs.append(_user_with_cv())

    asyncio.run(run_analysis(str(doc["_id"]), USER_ID, None))

    updated = asyncio.run(
        fake_db.analyses.find_one({"_id": doc["_id"]})
    )
    assert updated["status"] == "FAILED"
    assert "profile_insight" not in updated
    assert "recommendations" not in updated
