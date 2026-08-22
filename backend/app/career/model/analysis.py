from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

ANALYZE_STARTED_MESSAGE = (
    "Analysis started. Poll GET /careers/analyses/{analysis_id} for results."
)


class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class AnalysisPreferences(BaseModel):
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Areas the user explicitly asked to focus the "
        "recommendations on (e.g. 'AI', 'DevOps'). Empty if none.",
    )
    excluded_roles: list[str] = Field(
        default_factory=list,
        description="Career roles the user does NOT want recommended "
        "(e.g. 'QA', 'Data Analyst'). Empty if none.",
    )


class AnalyzeRequest(BaseModel):
    preferences: Optional[AnalysisPreferences] = Field(
        default=None,
        description="Optional per-request preferences that steer the analysis. "
        "Omit the whole field to use the user's stored profile interests.",
    )


class AnalyzeResponse(BaseModel):
    analysis_id: str = Field(
        description="ID of the created analysis. Poll "
        "GET /careers/analyses/{analysis_id} with this value until the analysis "
        "is READY."
    )
    status: AnalysisStatus = Field(
        default=AnalysisStatus.PENDING,
        description="Lifecycle status of the async analysis: PENDING | READY | FAILED.",
    )
    message: str = Field(
        default=ANALYZE_STARTED_MESSAGE,
        description="Human-readable confirmation and polling instructions.",
    )


class ProfileInsight(BaseModel):
    summary: str = Field(
        description="2-3 sentence objective summary of the candidate's overall "
        "profile, strongest areas, and most notable career signals."
    )
    hard_skills: list[str] = Field(
        default_factory=list,
        description="Technical skills evidenced by the profile (e.g. Python, "
        "Docker, SQL). Most relevant and strongest first.",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Interpersonal / professional skills evidenced by the "
        "profile (e.g. Communication, Leadership, Problem Solving).",
    )


class Recommendation(BaseModel):
    rec_index: int = Field(
        description="0-indexed position of this recommendation within the "
        "analysis. This is the value sent to POST /careers/paths to generate a "
        "career path from this recommendation."
    )
    title: str = Field(
        description="Career role / job title being recommended "
        "(e.g. 'Backend Engineer')."
    )
    description: str = Field(
        description="1-2 sentence description of what this role entails and why "
        "it is a good direction for the candidate."
    )
    match_score: int = Field(
        ge=0,
        le=100,
        description="How strongly the candidate's profile matches this role, "
        "as a percentage from 0 to 100. Higher means a stronger match.",
    )
    reasoning: str = Field(
        description="Concise explanation of why this role is recommended, "
        "citing concrete evidence from the candidate's profile."
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Skills the candidate still needs to develop to be a strong "
        "fit for this role. Empty if none.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Short keywords that categorize this role (e.g. Backend, "
        "Python, Cloud). Used for filtering and display.",
    )
    is_expanded: bool = Field(
        default=False,
        description="True once a career path has been generated from this "
        "recommendation. Server-managed; never sent by the LLM.",
    )
    linked_path_id: Optional[str] = Field(
        default=None,
        description="ID of the career_paths document created from this "
        "recommendation, or null if none has been generated yet. "
        "Server-managed; never sent by the LLM.",
    )


class AnalysisSummary(BaseModel):
    analysis_id: str = Field(
        description="ID of the analysis document (matches analyses._id)."
    )
    status: AnalysisStatus = Field(
        description="Lifecycle status of the analysis: PENDING | READY | FAILED.",
    )
    created_at: datetime = Field(
        description="ISO8601 timestamp of when the analysis was created."
    )
    profile_insight: Optional[ProfileInsight] = Field(
        default=None,
        description="The LLM-generated profile insight. Only populated when "
        "status is READY; null while PENDING or FAILED.",
    )
    recommendations_count: int = Field(
        default=0,
        description="Number of career recommendations generated for this "
        "analysis. 0 until the analysis is READY.",
    )


class AnalysisDetail(BaseModel):
    analysis_id: str = Field(
        description="ID of the analysis document (matches analyses._id)."
    )
    status: AnalysisStatus = Field(
        description="Lifecycle status of the analysis: PENDING | READY | FAILED.",
    )
    created_at: datetime = Field(
        description="ISO8601 timestamp of when the analysis was created."
    )
    profile_insight: Optional[ProfileInsight] = Field(
        default=None,
        description="The LLM-generated profile insight. Only populated when "
        "status is READY; null while PENDING or FAILED.",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="The full list of career recommendations. Empty until the "
        "analysis is READY.",
    )


class AnalysisList(BaseModel):
    analyses: list[AnalysisSummary] = Field(
        default_factory=list,
        description="All analyses for the authenticated user, newest first.",
    )


class RecommendationDraft(BaseModel):
    """Recommendation as returned by the LLM (no server-owned fields)."""

    title: str = Field(
        description="Career role / job title being recommended "
        "(e.g. 'Backend Engineer')."
    )
    description: str = Field(
        description="1-2 sentence description of what this role entails and why "
        "it is a good direction for the candidate."
    )
    match_score: int = Field(
        description="How strongly the candidate's profile matches this role. "
        "Any integer; the server clamps it to the valid 0-100 range. Higher "
        "means a stronger match.",
    )
    reasoning: str = Field(
        description="Concise explanation of why this role is recommended, "
        "citing concrete evidence from the candidate's profile."
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Skills the candidate still needs to develop to be a strong "
        "fit for this role. Empty if none.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Short keywords that categorize this role (e.g. Backend, "
        "Python, Cloud).",
    )

    @field_validator("match_score")
    @classmethod
    def clamp_match_score(cls, value: int) -> int:
        return max(0, min(100, value))


class AnalysisLLMOutput(BaseModel):
    """Validates the raw LLM analysis payload; server assigns the rest."""

    profile_insight: ProfileInsight = Field(
        description="Overall profile insight synthesizing the candidate's "
        "skills, strengths, and signals from their CV, LinkedIn, and interests.",
    )
    recommendations: list[RecommendationDraft] = Field(
        default_factory=list,
        description="Ranked career recommendations, strongest match first. "
        "3-5 recommendations is ideal.",
    )
