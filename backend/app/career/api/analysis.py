from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends

from app.auth.utils.auth import get_current_user
from app.career.model.analysis import (
    AnalysisDetail,
    AnalysisList,
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.career.service import analysis as analysis_service

router = APIRouter(prefix="/careers", tags=["Career Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def create_analysis(
    background_tasks: BackgroundTasks,
    request: Optional[AnalyzeRequest] = Body(default=None),
    current_user: dict = Depends(get_current_user),
) -> AnalyzeResponse:
    return await analysis_service.create_analysis(
        user_id=current_user["user_id"],
        request=request,
        background_tasks=background_tasks,
    )


@router.get("/analyses", response_model=AnalysisList)
async def list_analyses(
    current_user: dict = Depends(get_current_user),
) -> AnalysisList:
    return await analysis_service.list_analyses(user_id=current_user["user_id"])


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
) -> AnalysisDetail:
    return await analysis_service.get_analysis(
        user_id=current_user["user_id"],
        analysis_id=analysis_id,
    )
