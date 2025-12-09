#!/usr/bin/env python3
"""Diagnostic script to check if renditions are being created properly."""
import asyncio
import sys
from sqlalchemy import select
from app.db import AsyncSessionLocal, init_db
from app.models import Asset, Rendition, Job

async def check_renditions():
    """Check all assets and their renditions."""
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Get all assets
        result = await session.execute(select(Asset))
        assets = result.scalars().all()
        
        if not assets:
            print("❌ No assets found in database.")
            print("   Upload an image first using: curl -X POST http://localhost:10000/upload/ -F 'file=@image.jpg' -F 'tenant_name=test'")
            return
        
        print(f"\n📊 Found {len(assets)} asset(s) in database\n")
        print("=" * 80)
        
        for asset in assets:
            print(f"\n🖼️  Asset ID: {asset.id}")
            print(f"   Filename: {asset.filename}")
            print(f"   Size: {asset.width}x{asset.height}")
            print(f"   Created: {asset.created_at}")
            
            # Check jobs
            result = await session.execute(
                select(Job).where(Job.asset_id == asset.id).order_by(Job.id.desc())
            )
            jobs = result.scalars().all()
            
            if jobs:
                latest_job = jobs[0]
                print(f"   Latest Job Status: {latest_job.status}")
                if latest_job.error_message:
                    print(f"   ⚠️  Error: {latest_job.error_message}")
                if latest_job.retry_count > 0:
                    print(f"   ⚠️  Retries: {latest_job.retry_count}/{latest_job.max_retries}")
            
            # Check renditions
            result = await session.execute(
                select(Rendition).where(Rendition.asset_id == asset.id)
            )
            renditions = result.scalars().all()
            
            expected_presets = ["thumb", "card", "zoom"]
            found_presets = [r.preset for r in renditions]
            
            print(f"\n   Renditions:")
            for preset in expected_presets:
                if preset in found_presets:
                    rendition = next(r for r in renditions if r.preset == preset)
                    print(f"   ✅ {preset:6s} - {rendition.width}x{rendition.height} ({rendition.bytes:,} bytes)")
                else:
                    print(f"   ❌ {preset:6s} - MISSING")
            
            if len(renditions) < 3:
                print(f"\n   ⚠️  WARNING: Only {len(renditions)}/3 renditions found!")
                print(f"   Possible issues:")
                print(f"   1. Worker not running - check: ps aux | grep worker")
                print(f"   2. Job failed - check job status above")
                print(f"   3. Worker processing slowly - wait a few seconds and check again")
                print(f"   4. Check worker logs for errors")
            
            print("=" * 80)
        
        # Summary
        total_assets = len(assets)
        assets_with_all_renditions = sum(
            1 for asset in assets
            if len([r for r in renditions if r.asset_id == asset.id]) == 3
        )
        
        print(f"\n📈 Summary:")
        print(f"   Total assets: {total_assets}")
        print(f"   Assets with all 3 renditions: {assets_with_all_renditions}")
        print(f"   Assets missing renditions: {total_assets - assets_with_all_renditions}")
        
        if total_assets - assets_with_all_renditions > 0:
            print(f"\n💡 To fix:")
            print(f"   1. Make sure worker is running: bash app/scripts/run_worker.sh")
            print(f"   2. Check worker logs for errors")
            print(f"   3. Re-upload images if needed")

if __name__ == "__main__":
    try:
        asyncio.run(check_renditions())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
