# Fix: Get Renditions Created Right Now

Your asset shows `"renditions": []` - renditions are not being created. Here's how to fix it:

## Quick Fix Steps

### Step 1: Check if Worker is Running

The worker needs to be running to process jobs and create renditions.

**If deployed on Render:**
1. Go to your Render dashboard
2. Check your Web Service logs
3. Look for: `"✓ Worker started as background task"` or `"Using fallback database queue"`

**If worker is NOT running, you'll see:**
- No worker messages in logs
- Jobs stuck in "pending" status

### Step 2: Verify the Fix is Deployed

The fix was just pushed to GitHub. You need to redeploy:

**On Render:**
1. Go to your service dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait for deployment to complete (2-5 minutes)
4. Check logs to confirm worker started

### Step 3: Check Job Status

After redeploying, check if your job is being processed:

```bash
# Replace YOUR_SERVICE_URL with your actual Render URL
curl "YOUR_SERVICE_URL/retrieve/asset/1"
```

If renditions are still empty, the job might be stuck. Let's check:

### Step 4: Re-upload the Image (After Redeploy)

After redeploying with the fix:

1. **Upload the image again:**
   ```bash
   curl -X POST "YOUR_SERVICE_URL/upload/" \
     -F "file=@Screenshot_2025-12-03_at_2.51.23_PM.png" \
     -F "tenant_name=your_tenant"
   ```

2. **Wait 15-20 seconds** for processing

3. **Check renditions:**
   ```bash
   curl "YOUR_SERVICE_URL/retrieve/asset/NEW_ASSET_ID"
   ```

   You should now see:
   ```json
   {
     "renditions": [
       {"preset": "thumb", ...},
       {"preset": "card", ...},
       {"preset": "zoom", ...}
     ]
   }
   ```

## If Still Not Working

### Check Worker Logs on Render

1. Go to Render dashboard → Your service → **Logs** tab
2. Look for:
   - `"✓ Job X completed for asset Y - all renditions created"`
   - `"✓ Created thumb rendition for asset Y"`
   - Any error messages

### Common Issues

**Issue 1: Worker not enabled**
- Check environment variable: `ENABLE_WORKER=true` must be set
- In Render: Settings → Environment → Add `ENABLE_WORKER=true`

**Issue 2: Old code still deployed**
- Make sure you redeployed after the fix
- Check deployment logs show the latest commit hash

**Issue 3: Job failed silently**
- Check Render logs for error messages
- Look for: `"✗ Job X failed"` or exception traces

**Issue 4: Database connection issues**
- Worker can't connect to database
- Check `DATABASE_URL` is correct in Render environment variables

## Manual Fix: Force Re-process

If the job is stuck, you can manually trigger re-processing by uploading the same image again (it's idempotent, so safe).

Or create a script to reset and reprocess:

```python
# reset_and_reprocess.py
import asyncio
import requests
from app.db import AsyncSessionLocal, init_db
from app.models import Job, Asset
from sqlalchemy import select

async def reset_jobs():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Find all pending/processing jobs
        result = await session.execute(
            select(Job).where(Job.status.in_(["pending", "processing", "failed"]))
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            job.status = "pending"
            job.retry_count = 0
            job.error_message = None
            print(f"Reset job {job.id} for asset {job.asset_id}")
        
        await session.commit()
        print(f"Reset {len(jobs)} jobs - worker will pick them up")

if __name__ == "__main__":
    asyncio.run(reset_jobs())
```

## Expected Behavior After Fix

Once the fix is deployed and working:

1. **Upload image** → Returns `asset_id` and `job_id`
2. **Wait 10-15 seconds**
3. **Check asset** → Should show 3 renditions:
   - `thumb` (100×100)
   - `card` (400×400)  
   - `zoom` (max 1200px)

## Verify Fix is Working

After redeploy, test:

```bash
# 1. Upload
curl -X POST "YOUR_SERVICE_URL/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=test"

# Response shows asset_id (e.g., 2)

# 2. Wait 15 seconds

# 3. Check
curl "YOUR_SERVICE_URL/retrieve/asset/2"

# Should show renditions array with 3 items ✅
```

---

## Summary

1. ✅ **Fix is committed to GitHub** (commit: 01a085a)
2. ⚠️ **You need to REDEPLOY** on Render to get the fix
3. ⏳ **Wait for deployment** to complete
4. 🔄 **Re-upload your image** (or wait for existing job to process)
5. ✅ **Check renditions** - should now have 3 items

The fix ensures images are converted to RGB before creating renditions, which was causing the issue.
