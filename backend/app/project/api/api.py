from fastapi import APIRouter, HTTPException, status, Depends
from app.project.model import ProjectsGenerationRequest, ProjectsGenerationResponse
from app.auth.utils.auth import get_current_user
from app.project.service import projects_generation_service
from app.project.service.errors import (
    ProjectGenerationLLMError,
    ProjectGenerationParseError,
    ProjectPersistenceError,
)

router = APIRouter(prefix="/project", tags=["Project Related endpoints"])

@router.post("/generate", status_code=200)
async def generate_projects(req: ProjectsGenerationRequest ,user: dict = Depends(get_current_user)) -> ProjectsGenerationResponse:
    try:
        return await projects_generation_service(user["user_id"], req)
    except ProjectGenerationParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Generated project payload is invalid"
        ) from exc
    except ProjectGenerationLLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Project generation provider unavailable"
        ) from exc
    except ProjectPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store generated projects"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating projects"
        ) from exc
