from fastapi import APIRouter, HTTPException, status, Depends
from app.models import ProfileAnalysisRequest, ProfileAnalysisResponse
from app.services import analyse_profile_service
from app.utils.auth import get_current_user


router = APIRouter(prefix="/analyse", tags=["Profile Analysis"])

@router.post("/profile", status_code=200)
async def analyse_profile(profile: ProfileAnalysisRequest, 
                              user: dict = Depends(get_current_user)) -> ProfileAnalysisResponse:
    if not profile.resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text cannot be empty."
        )

    try:
        return await analyse_profile_service(profile, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing profile: {str(e)}"
        )

