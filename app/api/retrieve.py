"""Retrieve endpoint for assets and renditions."""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.db import get_db, settings
from app.models import Asset, Rendition
from app.storage import storage

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


@router.get("/asset/{asset_id}")
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get asset metadata."""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )
    
    # Get renditions
    result = await db.execute(
        select(Rendition).where(Rendition.asset_id == asset_id)
    )
    renditions = result.scalars().all()
    
    return {
        "asset_id": asset.id,
        "filename": asset.filename,
        "content_hash": asset.content_hash,
        "width": asset.width,
        "height": asset.height,
        "bytes": asset.original_bytes,
        "color_space": asset.color_space,
        "created_at": asset.created_at.isoformat(),
        "renditions": [
            {
                "preset": r.preset,
                "file_path": r.file_path,
                "width": r.width,
                "height": r.height,
                "bytes": r.bytes,
                "quality": r.quality
            }
            for r in renditions
        ]
    }


@router.get("/rendition/{asset_id}/{preset}")
async def get_rendition(
    asset_id: int,
    preset: str,
    db: AsyncSession = Depends(get_db)
):
    """Get rendition file."""
    # Validate preset
    from app.utils import RENDITION_PRESETS
    if preset not in RENDITION_PRESETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid preset. Must be one of: {list(RENDITION_PRESETS.keys())}"
        )
    
    # Get rendition
    result = await db.execute(
        select(Rendition).where(
            Rendition.asset_id == asset_id,
            Rendition.preset == preset
        )
    )
    rendition = result.scalar_one_or_none()
    
    if not rendition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rendition {preset} not found for asset {asset_id}"
        )
    
    # Read file and return
    file_path = Path(settings.storage_path) / rendition.file_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendition file not found on disk"
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="image/jpeg",
        filename=f"{asset_id}_{preset}.jpg"
    )

