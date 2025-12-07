"""Async worker for processing image jobs with Redis queue fallback."""
import asyncio
import os
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
import io

from app.db import AsyncSessionLocal, settings, init_db
from app.models import Asset, Rendition, Job, PoisonJob
from app.storage import storage
from app.utils import create_rendition, save_rendition, RENDITION_PRESETS


# Try to import Redis, fallback if not available
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Get Redis client if available, else None."""
    if not REDIS_AVAILABLE or not settings.redis_url:
        return None
    try:
        redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        return redis
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}. Using fallback queue.")
        return None


async def process_job(job_id: int, session: AsyncSession):
    """
    Process a single job: create renditions for an asset.
    Implements retry logic with exponential backoff.
    """
    # Fetch job with asset
    result = await session.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job or job.status != "pending":
        return
    
    # Update status to processing
    job.status = "processing"
    await session.commit()
    
    try:
        # Fetch asset
        result = await session.execute(
            select(Asset).where(Asset.id == job.asset_id)
        )
        asset = result.scalar_one_or_none()
        
        if not asset:
            raise ValueError(f"Asset {job.asset_id} not found")
        
        # Read original image
        original_path = f"originals/{asset.filename}"
        if not storage.file_exists(original_path):
            raise FileNotFoundError(f"Original file not found: {original_path}")
        
        original_bytes = storage.read_file(original_path)
        image = Image.open(io.BytesIO(original_bytes))
        
        # Process each rendition preset
        for preset in RENDITION_PRESETS.keys():
            # Check if rendition already exists (idempotency)
            result = await session.execute(
                select(Rendition).where(
                    Rendition.asset_id == asset.id,
                    Rendition.preset == preset
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                continue  # Skip if already exists
            
            # Create rendition
            rendition_image = create_rendition(image.copy(), preset)
            rendition_bytes = save_rendition(rendition_image)
            
            # Save rendition file
            file_path = storage.save_rendition(rendition_bytes, preset, asset.id)
            
            # Create rendition record
            rendition = Rendition(
                asset_id=asset.id,
                preset=preset,
                file_path=file_path,
                bytes=len(rendition_bytes),
                width=rendition_image.width,
                height=rendition_image.height,
                quality=85,
                color_space=rendition_image.mode
            )
            session.add(rendition)
        
        # Mark job as completed
        job.status = "completed"
        await session.commit()
        print(f"✓ Job {job_id} completed for asset {asset.id}")
        
    except Exception as e:
        error_msg = str(e)
        job.error_message = error_msg
        job.retry_count += 1
        
        # Check if max retries exceeded
        if job.retry_count >= job.max_retries:
            # Move to poison jobs
            poison = PoisonJob(
                asset_id=job.asset_id,
                original_job_id=job.id,
                error_message=error_msg,
                retry_count=job.retry_count
            )
            session.add(poison)
            job.status = "failed"
            print(f"✗ Job {job_id} failed permanently after {job.retry_count} retries")
        else:
            # Retry with exponential backoff
            job.status = "pending"
            backoff_seconds = 2 ** job.retry_count  # 2, 4, 8 seconds
            print(f"⚠ Job {job_id} failed, retrying in {backoff_seconds}s (attempt {job.retry_count}/{job.max_retries})")
            await asyncio.sleep(backoff_seconds)
        
        await session.commit()


async def worker_loop_redis(redis: aioredis.Redis):
    """Worker loop using Redis queue."""
    queue_name = "image_jobs"
    
    while True:
        try:
            # Blocking pop from queue (timeout 1 second)
            job_data = await redis.brpop(queue_name, timeout=1)
            
            if job_data:
                _, job_json = job_data
                job_dict = json.loads(job_json)
                job_id = job_dict["job_id"]
                
                # Create new session for each job
                async with AsyncSessionLocal() as session:
                    await process_job(job_id, session)
        except Exception as e:
            print(f"Error in Redis worker loop: {e}")
            await asyncio.sleep(1)


async def worker_loop_fallback():
    """Fallback worker loop using database polling."""
    print("Using fallback database queue (no Redis)")
    
    while True:
        try:
            # Create new session for each poll
            async with AsyncSessionLocal() as session:
                # Poll for pending jobs
                result = await session.execute(
                    select(Job).where(Job.status == "pending").limit(1)
                )
                job = result.scalar_one_or_none()
                
                if job:
                    await process_job(job.id, session)
                else:
                    # No jobs, wait a bit
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"Error in fallback worker loop: {e}")
            await asyncio.sleep(1)


async def main():
    """Main worker entry point."""
    print("Starting image processing worker...")
    
    # Initialize database
    await init_db()
    
    # Try to connect to Redis
    redis = await get_redis_client()
    
    if redis:
        print("✓ Connected to Redis")
        await worker_loop_redis(redis)
    else:
        print("Using fallback database queue")
        await worker_loop_fallback()


if __name__ == "__main__":
    asyncio.run(main())

