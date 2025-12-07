"""Upload endpoint for image assets."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from PIL import Image
import io

from app.db import get_db, settings
from app.models import Asset, Job, Tenant
from app.storage import storage
from app.hashing import compute_content_hash

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/")
async def upload_image(
    file: UploadFile = File(...),
    tenant_name: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an image file. Creates asset record and queues processing job.
    Returns asset ID and status.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read file content
    content = await file.read()
    
    # Open image to validate and get metadata
    try:
        image = Image.open(io.BytesIO(content))
        # Convert to RGB if needed
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Compute content hash for idempotency
    sha256, perceptual_hash = compute_content_hash(image, content)
    
    # Check if asset with same content hash already exists
    result = await db.execute(
        select(Asset).where(Asset.content_hash == sha256)
    )
    existing_asset = result.scalar_one_or_none()
    
    if existing_asset:
        # Asset already exists - return existing asset info
        return {
            "asset_id": existing_asset.id,
            "status": "exists",
            "message": "Asset with identical content already exists (idempotent)",
            "content_hash": sha256
        }
    
    # Get or create tenant
    result = await db.execute(
        select(Tenant).where(Tenant.name == tenant_name)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        await db.flush()  # Get tenant.id
    
    # Save original file
    file_path = storage.save_original(content, file.filename)
    
    # Create asset record
    asset = Asset(
        tenant_id=tenant.id,
        filename=file.filename,
        content_hash=sha256,
        perceptual_hash=perceptual_hash,
        original_bytes=len(content),
        width=image.width,
        height=image.height,
        color_space=image.mode
    )
    db.add(asset)
    await db.flush()  # Get asset.id
    
    # Create processing job
    job = Job(
        asset_id=asset.id,
        status="pending",
        retry_count=0,
        max_retries=3
    )
    db.add(job)
    
    await db.commit()
    
    # If Redis is available, add job to queue
    # Note: In production, you might want to use a connection pool
    try:
        import aioredis
        if settings.redis_url:
            redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
            await redis.lpush("image_jobs", f'{{"job_id": {job.id}}}')
            await redis.close()
    except Exception:
        # Fallback to database polling (worker will pick it up)
        pass
    
    return {
        "asset_id": asset.id,
        "status": "uploaded",
        "message": "Image uploaded and queued for processing",
        "content_hash": sha256,
        "job_id": job.id
    }

