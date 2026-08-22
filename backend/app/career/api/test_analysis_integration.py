import json
import os
from pathlib import Path

import pytest
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.utils.auth import get_current_user
from app.career.api.analysis import router
from app.share.api.errors import register_error_handler

load_dotenv()

USER_ID = str(ObjectId())
ANALYSES_PREFIX = "/api/v1/careers"

SAMPLE_CV = """PRIYA SHARMA
Backend Engineer - 4 years
Bangkok, Thailand

SUMMARY
Backend engineer with 4 years building Python services and REST APIs for
fintech and e-commerce. Focused on reliability, clean design, and shipping
features end to end.

EXPERIENCE
Senior Backend Engineer, PayFlow (2022-present)
- Designed and maintained a payments microservice handling ~50k requests/day.
- Migrated legacy REST endpoints to FastAPI with OpenAPI-typed contracts.
- Built async workers (Celery + Redis) for retries and webhook delivery.
- Cut p95 latency by 40% with indexed MongoDB queries and caching.

Backend Engineer, ShopKart (2020-2022)
- Built REST APIs for catalog and orders using Python, FastAPI, PostgreSQL.
- Wrote unit and integration tests; raised coverage to 85%.
- Set up CI with GitHub Actions and containerized services with Docker.

EDUCATION
B.Sc. Computer Science, 2020

SKILLS
Python, FastAPI, PostgreSQL, MongoDB, Redis, Celery, Docker, REST APIs,
GitHub Actions, pytest, Linux, Kafka (basic), Kubernetes (learning)
"""

SAMPLE_LINKEDIN = """Backend engineer passionate about distributed systems and
developer experience. I write about async Python, database indexing, and clean
API design. Open to senior backend and platform engineering roles.
"""

SAMPLE_INTERESTS = {
    "roles": ["Backend Engineer", "Platform Engineer"],
    "focus_areas": ["System Design", "Distributed Systems"],
}

DEFAULT_RESULT_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "integration_results"
    / "career_analysis_live.json"
)


def _make_app() -> FastAPI:
    app = FastAPI()
    register_error_handler(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: {"user_id": USER_ID}
    return app


def _result_file() -> Path:
    env_path = os.getenv("INTEGRATION_RESULT_PATH")
    return Path(env_path) if env_path else DEFAULT_RESULT_FILE


def _write_artifact(analysis_id: str, detail: dict) -> Path:
    path = _result_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(detail, indent=2, default=str))
    return path


def _print_summary(detail: dict) -> None:
    insight = detail.get("profile_insight") or {}
    print("\n=== INTEGRATION RESULT: REAL LLM CAREER ANALYSIS ===")
    print(f"analysis_id : {detail['analysis_id']}")
    print(f"status      : {detail['status']}")
    print(f"summary     : {insight.get('summary')}")
    print(f"hard_skills : {', '.join(insight.get('hard_skills') or [])}")
    print(f"soft_skills : {', '.join(insight.get('soft_skills') or [])}")
    for rec in detail.get("recommendations", []):
        print(f"\n[{rec['rec_index']}] {rec['title']} - match {rec['match_score']}%")
        print(f"    {rec['description']}")
        print(f"    reasoning : {rec['reasoning']}")
        print(f"    missing   : {', '.join(rec.get('missing_skills') or [])}")
        print(f"    tags      : {', '.join(rec.get('tags') or [])}")
    print("=" * 45)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("LLM_API_KEY"),
    reason="LLM_API_KEY is not set; skipping live LLM integration test",
)
def test_full_career_analysis_flow_with_real_llm(fake_db, monkeypatch):
    """Run the whole analysis flow over HTTP against a real LLM provider.

    Requires ``LLM_API_KEY`` (and optionally ``LLM_PROVIDER`` / ``LLM_MODEL``)
    to be configured; persistence uses the in-memory fake DB. The resulting
    analysis is written to ``integration_results/career_analysis_live.json``
    and printed to stdout (use ``-s`` to see it).
    """
    monkeypatch.setenv("LLM_PROVIDER", os.getenv("LLM_PROVIDER", "deepseek"))

    fake_db.users.docs.append(
        {
            "_id": ObjectId(USER_ID),
            "profile": {
                "cv_parsed_text": SAMPLE_CV,
                "linkedin_parsed_text": SAMPLE_LINKEDIN,
                "interests": SAMPLE_INTERESTS,
            },
        }
    )

    client = TestClient(_make_app())

    resp = client.post(
        f"{ANALYSES_PREFIX}/analyze",
        json={"preferences": {"focus_areas": ["System Design"]}},
    )
    assert resp.status_code == 202
    body = resp.json()
    analysis_id = body["analysis_id"]
    assert body["status"] == "PENDING"

    detail_resp = client.get(f"{ANALYSES_PREFIX}/analyses/{analysis_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    if detail["status"] != "READY":
        _write_artifact(analysis_id, detail)
        pytest.fail(
            "Analysis did not reach READY. "
            f"Artifact written to {_result_file()}: {detail}"
        )

    insight = detail["profile_insight"]
    assert insight is not None
    assert insight["summary"].strip()
    assert insight["hard_skills"]
    assert insight["soft_skills"]

    recommendations = detail["recommendations"]
    assert len(recommendations) >= 1
    for rec in recommendations:
        assert rec["title"].strip()
        assert rec["description"].strip()
        assert rec["reasoning"].strip()
        assert 0 <= rec["match_score"] <= 100
        assert isinstance(rec["missing_skills"], list)
        assert isinstance(rec["tags"], list)
        assert rec["is_expanded"] is False
        assert rec["linked_path_id"] is None

    list_resp = client.get(f"{ANALYSES_PREFIX}/analyses")
    assert list_resp.status_code == 200
    summaries = list_resp.json()["analyses"]
    summary = next(i for i in summaries if i["analysis_id"] == analysis_id)
    assert summary["status"] == "READY"
    assert summary["recommendations_count"] == len(recommendations)

    artifact = _write_artifact(analysis_id, detail)
    _print_summary(detail)
    print(f"[integration] analysis result written to {artifact}")
