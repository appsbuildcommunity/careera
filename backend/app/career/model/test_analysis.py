import pytest

from app.career.model.analysis import (
    ANALYZE_STARTED_MESSAGE,
    AnalysisLLMOutput,
    AnalysisPreferences,
    AnalysisStatus,
    AnalyzeRequest,
    AnalyzeResponse,
    RecommendationDraft,
)


def test_analysis_status_values():
    assert AnalysisStatus.PENDING.value == "PENDING"
    assert AnalysisStatus.READY.value == "READY"
    assert AnalysisStatus.FAILED.value == "FAILED"


def test_analyze_request_body_is_optional():
    assert AnalyzeRequest() == AnalyzeRequest(preferences=None)


def test_analyze_request_preferences():
    request = AnalyzeRequest(
        preferences=AnalysisPreferences(
            focus_areas=["AI"], excluded_roles=["QA"]
        )
    )
    assert request.preferences is not None
    assert request.preferences.focus_areas == ["AI"]
    assert request.preferences.excluded_roles == ["QA"]


def test_analyze_response_defaults():
    response = AnalyzeResponse(analysis_id="abc123")
    assert response.status == AnalysisStatus.PENDING
    assert response.message == ANALYZE_STARTED_MESSAGE


@pytest.mark.parametrize(
    ("raw", "clamped"),
    [(150, 100), (-5, 0), (70, 70), (100, 100), (0, 0)],
)
def test_llm_match_score_is_clamped_to_0_100(raw, clamped):
    draft = RecommendationDraft(
        title="t", description="d", match_score=raw, reasoning="r"
    )
    assert draft.match_score == clamped


def test_llm_output_recommendations_have_no_server_owned_fields():
    output = AnalysisLLMOutput.model_validate(
        {
            "profile_insight": {
                "summary": "s",
                "hard_skills": ["Python"],
                "soft_skills": ["Communication"],
            },
            "recommendations": [
                {
                    "title": "Backend Engineer",
                    "description": "d",
                    "match_score": 92,
                    "reasoning": "r",
                    "missing_skills": ["Docker"],
                    "tags": ["Backend"],
                }
            ],
        }
    )
    rec = output.recommendations[0]
    assert rec.match_score == 92
    assert not hasattr(rec, "rec_index")
    assert not hasattr(rec, "is_expanded")
    assert not hasattr(rec, "linked_path_id")
