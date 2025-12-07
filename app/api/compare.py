"""Compare endpoint for image quality metrics."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from PIL import Image
from pathlib import Path
import io

from app.db import get_db, settings
from app.models import Asset, Rendition
from app.utils import compare_images, RENDITION_PRESETS
from app.hashing import compute_perceptual_hash

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/{asset_id}")
async def compare_image(
    asset_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare uploaded image against renditions of an asset.
    Returns per-preset file size and quality metrics (PSNR + perceptual hash distance).
    """
    # Get asset
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )
    
    # Read uploaded image
    content = await file.read()
    try:
        uploaded_image = Image.open(io.BytesIO(content))
        if uploaded_image.mode not in ("RGB", "RGBA"):
            uploaded_image = uploaded_image.convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Get original asset image
    from app.storage import storage
    original_path = f"originals/{asset.filename}"
    if not storage.file_exists(original_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original asset file not found"
        )
    
    original_bytes = storage.read_file(original_path)
    original_image = Image.open(io.BytesIO(original_bytes))
    if original_image.mode not in ("RGB", "RGBA"):
        original_image = original_image.convert("RGB")
    
    # Get renditions
    result = await db.execute(
        select(Rendition).where(Rendition.asset_id == asset_id)
    )
    renditions = result.scalars().all()
    
    # Compare uploaded image with original
    uploaded_hash = compute_perceptual_hash(uploaded_image)
    original_hash = asset.perceptual_hash
    
    comparison_results = {}
    
    # Compare with original
    original_comparison = compare_images(
        original_image, uploaded_image, original_hash, uploaded_hash
    )
    comparison_results["original"] = {
        "file_size_bytes": len(content),
        **original_comparison
    }
    
    # Compare with each rendition
    for rendition in renditions:
        rendition_path = Path(settings.storage_path) / rendition.file_path
        if not rendition_path.exists():
            continue
        
        rendition_bytes = rendition_path.read_bytes()
        rendition_image = Image.open(io.BytesIO(rendition_bytes))
        if rendition_image.mode not in ("RGB", "RGBA"):
            rendition_image = rendition_image.convert("RGB")
        
        rendition_hash = compute_perceptual_hash(rendition_image)
        
        comparison = compare_images(
            uploaded_image, rendition_image, uploaded_hash, rendition_hash
        )
        
        comparison_results[rendition.preset] = {
            "file_size_bytes": rendition.bytes,
            **comparison
        }
    
    return {
        "asset_id": asset_id,
        "comparisons": comparison_results,
        "note": "PSNR > 30 dB indicates good quality. Lower perceptual_hash_distance = more similar."
    }

