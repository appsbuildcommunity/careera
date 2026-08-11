from datetime import datetime

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.utils.auth import get_current_user
from app.career.api.analysis import router
from app.share.api.errors import register_error_handler

USER_ID = str(ObjectId())
ANALYSES_PREFIX = "/api/v1/careers"

READY_DOC = {
    "_id": ObjectId(),
    "user_id": ObjectId(USER_ID),
    "created_at": datetime.utcnow(),
    "status": "READY",
    "profile_insight": {
        "summary": "Backend engineer with strong Python skills.",
        "hard_skills": ["Python"],
        "soft_skills": ["Communication"],
    },
    "recommendations": [
        {
            "rec_index": 0,
            "title": "Backend Engineer",
            "description": "Build scalable services.",
            "match_score": 92,
            "reasoning": "Strong Python match.",
            "missing_skills": ["Docker"],
            "tags": ["Backend"],
            "is_expanded": False,
            "linked_path_id": None,
        }
    ],
}

LLM_RESULT = {
    "profile_insight": {
        "summary": "Backend engineer with strong Python skills.",
        "hard_skills": ["Python"],
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
        }
    ],
}


def _make_app() -> FastAPI:
    app = FastAPI()
    register_error_handler(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: {"user_id": USER_ID}
    return app


def _client(fake_db) -> TestClient:
    return TestClient(_make_app())


def test_post_analyze_returns_profile_incomplete_shape(fake_db):
    resp = _client(fake_db).post(f"{ANALYSES_PREFIX}/analyze")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "PROFILE_INCOMPLETE"
    assert body["message"] == "CV must be uploaded before running analysis."
    assert body["status_code"] == 400


def test_post_analyze_returns_202_pending(fake_db, monkeypatch):
    async def _fake_generate_json(**kwargs):
        return LLM_RESULT

    monkeypatch.setattr(
        "app.career.service.analysis.generate_json", _fake_generate_json
    )
    fake_db.users.docs.append(
        {"_id": ObjectId(USER_ID), "profile": {"cv_parsed_text": "Python backend"}}
    )

    resp = _client(fake_db).post(f"{ANALYSES_PREFIX}/analyze", json={})

    assert resp.status_code == 202
    body = resp.json()
    assert body["analysis_id"]
    assert body["status"] == "PENDING"
    assert body["message"].startswith("Analysis started.")


def test_get_analyses_returns_ready_summary(fake_db):
    fake_db.analyses.docs.append(dict(READY_DOC))

    resp = _client(fake_db).get(f"{ANALYSES_PREFIX}/analyses")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["analyses"]) == 1
    item = data["analyses"][0]
    assert item["analysis_id"] == str(READY_DOC["_id"])
    assert item["status"] == "READY"
    assert item["profile_insight"] is not None
    assert item["recommendations_count"] == 1


def test_get_analysis_returns_detail(fake_db):
    fake_db.analyses.docs.append(dict(READY_DOC))

    resp = _client(fake_db).get(
        f"{ANALYSES_PREFIX}/analyses/{READY_DOC['_id']}"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY"
    assert data["profile_insight"]["summary"].startswith("Backend engineer")
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["rec_index"] == 0
    assert data["recommendations"][0]["is_expanded"] is False
    assert data["recommendations"][0]["linked_path_id"] is None


def test_get_analysis_returns_documented_not_found_shape(fake_db):
    resp = _client(fake_db).get(f"{ANALYSES_PREFIX}/analyses/507f1f77bcf86cd799439011")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "ANALYSIS_NOT_FOUND"
    assert body["status_code"] == 404


def test_get_analysis_invalid_id_returns_not_found(fake_db):
    resp = _client(fake_db).get(f"{ANALYSES_PREFIX}/analyses/not-an-object-id")
    assert resp.status_code == 404
    assert resp.json()["error"] == "ANALYSIS_NOT_FOUND"
