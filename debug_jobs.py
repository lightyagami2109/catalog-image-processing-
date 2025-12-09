#!/usr/bin/env python3
"""Debug script to check job status and errors."""
import asyncio
import sys
from sqlalchemy import select
from app.db import AsyncSessionLocal, init_db
from app.models import Job, Asset, Rendition

async def debug_jobs():
    """Check all jobs and their status."""
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Get all jobs
        result = await session.execute(select(Job).order_by(Job.id.desc()))
        jobs = result.scalars().all()
        
        if not jobs:
            print("❌ No jobs found in database.")
            return
        
        print(f"\n📊 Found {len(jobs)} job(s) in database\n")
        print("=" * 80)
        
        for job in jobs:
            # Get asset info
            result = await session.execute(
                select(Asset).where(Asset.id == job.asset_id)
            )
            asset = result.scalar_one_or_none()
            
            filename = asset.filename if asset else f"asset_{job.asset_id} (NOT FOUND)"
            
            print(f"\n🔍 Job ID: {job.id}")
            print(f"   Asset ID: {job.asset_id}")
            print(f"   Filename: {filename}")
            print(f"   Status: {job.status}")
            print(f"   Retry Count: {job.retry_count}/{job.max_retries}")
            print(f"   Created: {job.created_at}")
            if job.updated_at:
                print(f"   Updated: {job.updated_at}")
            
            if job.error_message:
                print(f"   ⚠️  ERROR: {job.error_message}")
            
            # Check renditions
            result = await session.execute(
                select(Rendition).where(Rendition.asset_id == job.asset_id)
            )
            renditions = result.scalars().all()
            
            print(f"   Renditions: {len(renditions)}/3")
            for r in renditions:
                print(f"     - {r.preset}: {r.width}x{r.height} ({r.bytes:,} bytes)")
            
            if job.status == "pending":
                print(f"   💡 Status: PENDING - Worker should pick this up")
            elif job.status == "processing":
                print(f"   ⚠️  Status: PROCESSING - Job might be stuck!")
            elif job.status == "failed":
                print(f"   ❌ Status: FAILED - Check error message above")
            elif job.status == "completed":
                if len(renditions) < 3:
                    print(f"   ⚠️  Status: COMPLETED but only {len(renditions)}/3 renditions!")
                else:
                    print(f"   ✅ Status: COMPLETED - All renditions created")
            
            print("=" * 80)
        
        # Summary
        pending = [j for j in jobs if j.status == "pending"]
        processing = [j for j in jobs if j.status == "processing"]
        completed = [j for j in jobs if j.status == "completed"]
        failed = [j for j in jobs if j.status == "failed"]
        
        print(f"\n📈 Summary:")
        print(f"   Pending: {len(pending)}")
        print(f"   Processing: {len(processing)}")
        print(f"   Completed: {len(completed)}")
        print(f"   Failed: {len(failed)}")
        
        if processing:
            print(f"\n⚠️  WARNING: {len(processing)} job(s) stuck in 'processing' status!")
            print(f"   These might need to be reset.")
        
        if failed:
            print(f"\n❌ {len(failed)} job(s) failed. Check error messages above.")

if __name__ == "__main__":
    try:
        asyncio.run(debug_jobs())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
