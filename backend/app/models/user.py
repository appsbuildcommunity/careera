from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Request Models
class GoogleLoginRequest(BaseModel):
    """Google OAuth login request"""
    id_token: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

# Response Models
class UserProfile(BaseModel):
    """User profile data"""
    cv_parsed_text: Optional[str] = None
    linkedin_parsed_text: Optional[str] = None
    interests: Optional[dict] = None

class UserGamification(BaseModel):
    """User gamification stats"""
    total_xp: int = 0
    level: int = 1

class UserResponse(BaseModel):
    """User data returned to client"""
    id: str
    email: str
    name: str
    avatar: Optional[str] = None

class LoginResponse(BaseModel):
    """Response after successful login"""
    message: str
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    user: UserResponse

class RefreshResponse(BaseModel):
    """Response after token refresh"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes

class LogoutResponse(BaseModel):
    """Response after logout"""
    message: str = "Successfully logged out"

# Database Models
class UserInDB(BaseModel):
    """Complete user document in MongoDB"""
    email: str
    name: str
    avatar: Optional[str] = None
    created_at: datetime
    last_login: datetime
    profile: Optional[UserProfile] = None
    gamification: UserGamification = UserGamification()
    analyses_ids: List[str] = []
    career_paths_ids: List[str] = []