"""Regras de negócio para ``vision_analysis``.

Mantém o vínculo bidirecional descrito na seção 4 do PDF
(``plant_image`` ⇄ ``vision_analysis``, cardinalidade 1:0..1).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import plant_image_repo, vision_analysis_repo
from app.schemas.vision_analysis import (
    VisionAnalysis,
    VisionAnalysisCreate,
)


def register_analysis(data: VisionAnalysisCreate) -> VisionAnalysis:
    image = plant_image_repo.get(data.image_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"image_id {data.image_id} não existe",
        )
    if image.get("analysis_id") is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="esta imagem já possui uma análise associada",
        )

    record = data.model_dump()
    record["health_status"] = data.health_status.value
    record["id"] = uuid4()
    record["analyzed_at"] = data.analyzed_at or datetime.now(timezone.utc)
    vision_analysis_repo.add(record)

    # Mantém o vínculo bidirecional plant_image.analysis_id
    plant_image_repo.update(image["id"], {"analysis_id": record["id"]})

    return VisionAnalysis(**record)


def get_analysis(analysis_id: UUID) -> Optional[VisionAnalysis]:
    record = vision_analysis_repo.get(analysis_id)
    return VisionAnalysis(**record) if record else None


def get_analysis_for_image(image_id: UUID) -> Optional[VisionAnalysis]:
    record = vision_analysis_repo.find_one(lambda r: r["image_id"] == image_id)
    return VisionAnalysis(**record) if record else None


def list_analyses(*, limit: int = 100, offset: int = 0) -> List[VisionAnalysis]:
    rows = vision_analysis_repo.list(
        order_by="analyzed_at", descending=True, limit=limit, offset=offset
    )
    return [VisionAnalysis(**row) for row in rows]
