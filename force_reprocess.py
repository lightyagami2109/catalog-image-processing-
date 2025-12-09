#!/usr/bin/env python3
"""Force reprocess jobs to create renditions."""
import asyncio
import sys
from sqlalchemy import select
from app.db import AsyncSessionLocal, init_db
from app.models import Job, Asset

async def force_reprocess():
    """Reset all jobs to pending so worker will process them."""
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Find all jobs that are not completed
        result = await session.execute(
            select(Job).where(Job.status != "completed")
        )
        jobs = result.scalars().all()
        
        if not jobs:
            print("✅ No jobs to reprocess - all are completed!")
            return
        
        print(f"Found {len(jobs)} job(s) to reprocess:\n")
        
        for job in jobs:
            # Get asset info
            result = await session.execute(
                select(Asset).where(Asset.id == job.asset_id)
            )
            asset = result.scalar_one_or_none()
            
            filename = asset.filename if asset else f"asset_{job.asset_id}"
            
            print(f"  Job {job.id}: Asset {job.asset_id} ({filename})")
            print(f"    Current status: {job.status}")
            print(f"    Retry count: {job.retry_count}")
            if job.error_message:
                print(f"    Error: {job.error_message}")
            
            # Reset job
            job.status = "pending"
            job.retry_count = 0
            job.error_message = None
            print(f"    → Reset to 'pending' - worker will process it\n")
        
        await session.commit()
        print(f"✅ Reset {len(jobs)} job(s) to pending status")
        print("\n💡 The worker should pick these up and process them now.")
        print("   Wait 10-15 seconds, then check renditions again.")

if __name__ == "__main__":
    try:
        asyncio.run(force_reprocess())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
