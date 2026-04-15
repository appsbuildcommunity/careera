from fastapi import APIRouter, HTTPException, status, Depends
from app.project.model import ProjectsGenerationRequest, ProjectsGenerationResponse
from app.auth.utils.auth import get_current_user
from app.project.service import projects_generation_service

router = APIRouter(prefix="/project", tags=["Project Related endpoints"])

@router.post("/generate", status_code=200)
async def generate_projects(req: ProjectsGenerationRequest ,user: dict = Depends(get_current_user)) -> ProjectsGenerationResponse:
    try:
        return await projects_generation_service(user["user_id"], req)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating projects"
        ) from exc
