"""Extraction router: run the LLM pipeline for a text."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ExtractionServiceDep
from app.schemas.api import ActionRead, ExtractRequest, ExtractResponse

router = APIRouter()


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract action items from a text using the LLM",
)
async def extract(
    payload: ExtractRequest,
    service: ExtractionServiceDep,
) -> ExtractResponse:
    result = await service.extract(payload.text_id)
    return ExtractResponse(
        text_id=result.text_id,
        actions=[ActionRead.model_validate(a) for a in result.actions],
        needs_review_count=result.needs_review_count,
        duration_ms=result.duration_ms,
        injection_detected=result.injection_detected,
    )