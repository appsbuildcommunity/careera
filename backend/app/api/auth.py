from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime
from bson import ObjectId

from app.models.user import (
    GoogleLoginRequest, 
    RefreshTokenRequest,
    LoginResponse, 
    RefreshResponse, 
    LogoutResponse,
    UserResponse,
    UserInDB,
    UserGamification
)
from app.utils.auth import (
    verify_google_token,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    blacklist_token,
    security
)
from app.database.connection import get_database

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post("/login/dev", response_model=LoginResponse, status_code=200)
async def dev_login(email: str = "dev@test.com", name: str = "Test Developer"):
    """
    DEV ONLY - Quick login without Google OAuth
    
    ⚠️ Remove this endpoint before production!
    
    Usage:
    POST /api/v1/auth/login/dev?email=john@test.com&name=John
    """
    db = await get_database()
    
    # Find or create test user
    user = await db.users.find_one({"email": email})
    
    if not user:
        # Create new test user
        result = await db.users.insert_one({
            "email": email,
            "name": name,
            "avatar": None,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "profile": None,
            "gamification": {"total_xp": 0, "level": 1},
            "analyses_ids": [],
            "career_paths_ids": []
        })
        user_id = str(result.inserted_id)
    else:
        # Update existing user
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        user_id = str(user["_id"])
        name = user["name"]
    
    # Generate tokens
    token_data = {"sub": user_id, "email": email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return LoginResponse(
        message="DEV login successful - Remember to remove this endpoint in production!",
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(id=user_id, email=email, name=name, avatar=None)
    )

@router.get("/me", response_model=UserResponse, status_code=200)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Protected route - requires valid access token
    """
    db = await get_database()
    
    # Get user from database
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        avatar=user.get("avatar")
    )