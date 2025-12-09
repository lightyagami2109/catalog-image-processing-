# Diagnose Why Renditions Aren't Being Created

Follow these steps **in order** to find the exact issue:

## Step 1: Check if Worker is Running

**On Render:**
1. Go to your Render dashboard
2. Open your Web Service
3. Click **Logs** tab
4. Look for these messages:
   ```
   ✓ Worker started as background task
   Using fallback database queue
   ```

**If you DON'T see these:**
- Worker is NOT running
- **Fix:** Go to Settings → Environment → Add `ENABLE_WORKER=true`
- Redeploy

## Step 2: Check Job Status

Run this locally or in Render Shell:
```bash
python debug_jobs.py
```

This shows:
- All jobs and their status
- Error messages (if any)
- Which renditions exist

**What to look for:**
- `Status: pending` → Worker should pick it up
- `Status: processing` → Might be stuck
- `Status: failed` → Check error message
- `Status: completed` but no renditions → Problem!

## Step 3: Check Render Logs for Errors

In Render → Logs, look for:

**Good signs:**
```
📋 Found pending job 1 for asset 1
  ✓ Created thumb rendition for asset 1 (100x56)
  ✓ Created card rendition for asset 1 (400x225)
  ✓ Created zoom rendition for asset 1 (1200x675)
✓ Job 1 completed for asset 1 - all renditions created
```

**Bad signs:**
```
✗ ERROR in job 1 for asset 1:
  [error message here]
```

**Common errors you might see:**

### Error: "Original file not found"
**Cause:** File was deleted or path wrong
**Fix:** Re-upload the image

### Error: "cannot identify image file"
**Cause:** Corrupted image or wrong format
**Fix:** Try a different image file

### Error: Permission denied
**Cause:** Storage directory not writable
**Fix:** Check storage permissions on Render

### No errors but no renditions
**Cause:** Worker might not be processing
**Fix:** Check Step 1 - worker might not be running

## Step 4: Test with a Fresh Upload

After checking everything above:

1. **Upload a new test image:**
   ```bash
   curl -X POST "YOUR_RENDER_URL/upload/" \
     -F "file=@test.jpg" \
     -F "tenant_name=test"
   ```

2. **Watch Render logs in real-time** (keep Logs tab open)

3. **You should see:**
   ```
   📋 Found pending job X for asset Y
   [rendition creation messages]
   ✓ Job X completed
   ```

4. **If you see nothing:**
   - Worker is not running
   - Check `ENABLE_WORKER=true` is set
   - Redeploy

## Step 5: Verify Code is Deployed

**Check if latest code is deployed:**
1. In Render dashboard → Your service
2. Check the commit hash in deployment history
3. Should match: `fe54457` (latest commit)

**If not:**
- Click "Manual Deploy" → "Deploy latest commit"
- Wait for deployment

## Step 6: Check Environment Variables

In Render → Settings → Environment, verify:

- ✅ `ENABLE_WORKER=true` (MUST be set!)
- ✅ `DATABASE_URL=postgresql+asyncpg://...` (with +asyncpg)
- ✅ `STORAGE_PATH=/mnt/storage`
- ✅ `SECRET_KEY=...`
- ✅ `PURGE_DAYS=30`

## Quick Fix Checklist

Run through this checklist:

- [ ] Worker logs show "✓ Worker started as background task"
- [ ] `ENABLE_WORKER=true` is set in environment
- [ ] Latest code is deployed (commit fe54457)
- [ ] `debug_jobs.py` shows jobs exist
- [ ] Render logs show worker processing jobs
- [ ] No error messages in logs
- [ ] Storage path is writable

## If Still Not Working

### Option 1: Reset and Re-upload
```bash
# Reset stuck jobs
python force_reprocess.py

# Then re-upload image
curl -X POST "YOUR_URL/upload/" -F "file=@image.jpg" -F "tenant_name=test"
```

### Option 2: Check Storage
The issue might be storage-related. On Render, storage is at `/mnt/storage`. Check if it's writable.

### Option 3: Check Database
Make sure database connection is working:
```bash
# In Render Shell
python -c "from app.db import settings; print('DB OK' if settings.database_url else 'DB MISSING')"
```

## Most Common Issue

**90% of the time, the issue is:**
- Worker not running (`ENABLE_WORKER` not set or false)
- Old code deployed (fix not in production yet)

**Solution:**
1. Set `ENABLE_WORKER=true` in Render environment
2. Redeploy to latest commit
3. Re-upload image
4. Check logs

---

## Still Stuck?

Share these details:
1. Output of `python debug_jobs.py`
2. Render logs (last 50 lines)
3. Environment variables (without sensitive data)
4. Whether you see "Worker started" in logs

This will help identify the exact issue.
