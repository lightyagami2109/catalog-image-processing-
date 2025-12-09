# Troubleshooting: Renditions Not Being Created

If your project is not producing all three renditions (thumb, card, zoom), follow this guide.

## Quick Check

Run the diagnostic script:
```bash
python check_renditions.py
```

This will show you:
- Which assets exist
- Which renditions are missing
- Job status and any errors

## Common Issues & Solutions

### Issue 1: Worker Not Running

**Symptoms:**
- Uploads work, but renditions never appear
- `check_renditions.py` shows all renditions as missing
- No worker logs visible

**Solution:**
```bash
# Check if worker is running
ps aux | grep worker

# If not running, start it:
bash app/scripts/run_worker.sh

# Or if using integrated worker, check ENABLE_WORKER env:
echo $ENABLE_WORKER  # Should be "true" or not set
```

### Issue 2: Worker Running But Jobs Not Processing

**Symptoms:**
- Worker is running
- Jobs show status "pending" but never change to "processing"
- No error messages

**Solution:**
1. **Check database connection:**
   ```bash
   # Verify DATABASE_URL is set correctly
   python -c "from app.db import settings; print(settings.database_url)"
   ```

2. **Check if using Redis:**
   - If Redis is configured but not running, worker may fail silently
   - Worker should fall back to database polling
   - Check worker logs for Redis connection errors

3. **Restart worker:**
   ```bash
   # Stop current worker (Ctrl+C)
   # Then restart:
   bash app/scripts/run_worker.sh
   ```

### Issue 3: Jobs Failing with Errors

**Symptoms:**
- `check_renditions.py` shows job status as "failed"
- Error messages in job records
- Worker logs show exceptions

**Common Errors:**

#### Error: "Original file not found"
**Cause:** Original image file was deleted or path is wrong
**Solution:**
- Re-upload the image
- Check storage path: `ls storage/originals/`

#### Error: Image mode issues (RGBA, P, etc.)
**Cause:** Image has transparency or unsupported color mode
**Solution:**
- ✅ **FIXED** - The worker now automatically converts images to RGB
- If still happening, update to latest code

#### Error: Permission denied
**Cause:** Storage directory not writable
**Solution:**
```bash
chmod -R 755 storage/
```

### Issue 4: Only Some Renditions Created

**Symptoms:**
- Some presets work (e.g., thumb) but others don't (e.g., zoom)
- Partial renditions in database

**Solution:**
1. Check worker logs for specific errors
2. Verify all presets are defined:
   ```python
   python -c "from app.utils import RENDITION_PRESETS; print(list(RENDITION_PRESETS.keys()))"
   # Should show: ['thumb', 'card', 'zoom']
   ```

3. Check if image is too small for certain presets
   - Very small images might not need all renditions
   - This is normal behavior

### Issue 5: Renditions Created But Files Missing

**Symptoms:**
- Database shows renditions exist
- But files not found on disk
- Retrieve endpoint returns 404

**Solution:**
```bash
# Check if files exist
ls -la storage/renditions/

# Check storage path configuration
python -c "from app.db import settings; print(settings.storage_path)"
```

## Step-by-Step Diagnostic Process

### Step 1: Check Current State
```bash
python check_renditions.py
```

### Step 2: Check Worker Status
```bash
# Is worker running?
ps aux | grep -i worker

# Check worker logs (if running in terminal)
# Look for:
# - "✓ Job X completed"
# - "⚠ Job X failed"
# - Error messages
```

### Step 3: Check Database
```python
python -c "
import asyncio
from app.db import AsyncSessionLocal, init_db
from app.models import Job
from sqlalchemy import select

async def check():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.status == 'pending'))
        pending = result.scalars().all()
        print(f'Pending jobs: {len(pending)}')
        for job in pending:
            print(f'  Job {job.id} for asset {job.asset_id}')

asyncio.run(check())
"
```

### Step 4: Test Upload and Monitor
```bash
# 1. Upload a test image
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=test"

# 2. Note the asset_id and job_id from response

# 3. Wait 10 seconds

# 4. Check renditions
python check_renditions.py

# 5. Or check directly
curl "http://localhost:10000/retrieve/asset/1"
```

## Manual Fix: Re-process Failed Jobs

If jobs are stuck or failed, you can manually reset them:

```python
import asyncio
from app.db import AsyncSessionLocal, init_db
from app.models import Job
from sqlalchemy import select

async def reset_jobs():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Find failed or stuck jobs
        result = await session.execute(
            select(Job).where(Job.status.in_(["failed", "processing"]))
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            job.status = "pending"
            job.retry_count = 0
            job.error_message = None
            print(f"Reset job {job.id} for asset {job.asset_id}")
        
        await session.commit()
        print(f"Reset {len(jobs)} jobs")

asyncio.run(reset_jobs())
```

## Verification

After fixing, verify all renditions are created:

```bash
# 1. Check diagnostic
python check_renditions.py

# 2. Test retrieve endpoint
curl "http://localhost:10000/retrieve/asset/1"

# Should show all 3 renditions:
# - thumb
# - card  
# - zoom

# 3. Try downloading each
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

## What Was Fixed

The worker code has been updated to:
1. ✅ Convert images to RGB mode before processing (fixes RGBA/transparency issues)
2. ✅ Better error handling and logging
3. ✅ More detailed progress messages

**If you're still having issues after these fixes:**
1. Make sure you've restarted the worker with the updated code
2. Check worker logs for specific error messages
3. Run `python check_renditions.py` to see detailed status
4. Try re-uploading an image to test with the fixed code

## Quick Test

```bash
# 1. Start server
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload

# 2. In another terminal, start worker
bash app/scripts/run_worker.sh

# 3. Upload test image
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=test"

# 4. Wait 10 seconds, then check
python check_renditions.py

# 5. Should show all 3 renditions ✅
```

---

**Still having issues?** Check:
- Worker logs for error messages
- Database connection is working
- Storage directory exists and is writable
- All dependencies are installed correctly
