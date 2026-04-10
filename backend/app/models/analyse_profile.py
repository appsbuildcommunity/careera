from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request Models
class UserPreferences(BaseModel):
    """User career preferences"""
    interested_roles: List[str] = []
    ignored_roles: List[str] = []


class ProfileAnalysisRequest(BaseModel):
    """Request to analyze user profile and generate career paths"""
    user_id: Optional[str] = None
    resume_text: str
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    preferences: UserPreferences = UserPreferences()


# Response Models
class CareerPathRecommendation(BaseModel):
    """Individual career path recommendation"""
    role: str
    match_percentage: int = Field(ge=0, le=100)
    missing_skills: List[str] = []
    learning_path: List[str] = []

class UserProfile(BaseModel):
    """User profile summary with skills"""
    profile_summary: str
    hard_skills: List[str] = []
    soft_skills: List[str] = []

class ProfileAnalysisResponse(BaseModel):
    """Response with career path analysis results"""
    profile: UserProfile
    recommendations: List[CareerPathRecommendation] = []

# Database Models
class CareerPathInDB(BaseModel):
    """Career path analysis document in MongoDB"""
    id: str
    user_id: str
    profile_summary: str
    hard_skills: List[str] = []
    soft_skills: List[str] = []
    recommendations: List[CareerPathRecommendation] = []
    created_at: datetime
    updated_at: datetime
    preferences: UserPreferences = UserPreferences()
