# Test Locally - Step by Step

Follow these steps to test if renditions are working locally:

## Step 1: Kill Any Existing Processes

```bash
# Kill any process on port 10000
lsof -ti:10000 | xargs kill -9 2>/dev/null || true

# Or manually find and kill:
# ps aux | grep uvicorn
# kill <PID>
```

## Step 2: Start the Server

**Terminal 1:**
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

You should see:
```
Starting up...
✓ Database tables created
⚠ Redis not configured, using fallback queue
✓ Worker started as background task
✓ Application started
INFO:     Uvicorn running on http://0.0.0.0:10000
```

**Note:** The integrated worker should start automatically if `ENABLE_WORKER` is not set to "false".

## Step 3: Start Worker Separately (Optional - for better logs)

**Terminal 2:**
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
bash app/scripts/run_worker.sh
```

You should see:
```
Starting image processing worker...
Using fallback database queue
```

## Step 4: Run the Test

**Terminal 3:**
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
python3 test_local.py
```

This will:
1. Check server is running
2. Create a test image
3. Upload it
4. Wait 15 seconds
5. Check if all 3 renditions were created

## Step 5: Check Results

The test will show:
- ✅ All 3 renditions created → **SUCCESS!**
- ❌ Missing renditions → Check worker logs

## Manual Test (Alternative)

If the automated test doesn't work, test manually:

### 1. Upload an image:
```bash
# Create a test image first
python3 -c "from PIL import Image; Image.new('RGB', (800, 600), 'blue').save('test.jpg')"

# Upload it
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=test"
```

Save the `asset_id` from the response (e.g., `1`).

### 2. Wait 15 seconds

### 3. Check renditions:
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

Should show:
```json
{
  "renditions": [
    {"preset": "thumb", ...},
    {"preset": "card", ...},
    {"preset": "zoom", ...}
  ]
}
```

### 4. Check job status:
```bash
python3 debug_jobs.py
```

## Troubleshooting

### Server won't start
- Check if port 10000 is in use: `lsof -ti:10000`
- Kill the process: `lsof -ti:10000 | xargs kill -9`
- Check for errors in terminal

### Worker not processing
- Check Terminal 1 logs for "Worker started"
- Or check Terminal 2 (if running worker separately)
- Look for error messages

### No renditions created
- Check worker logs for errors
- Run `python3 debug_jobs.py` to see job status
- Check if storage directory exists: `ls -la storage/`

## Expected Output

**If working correctly, you should see in worker logs:**
```
📋 Found pending job 1 for asset 1
  ✓ Created thumb rendition for asset 1 (100x75)
  ✓ Created card rendition for asset 1 (400x300)
  ✓ Created zoom rendition for asset 1 (800x600)
✓ Job 1 completed for asset 1 - all renditions created
```

**If not working, you'll see errors:**
```
✗ ERROR in job 1 for asset 1:
  [error message here]
```

---

## Quick Test Command

Run this all at once (after killing existing processes):

```bash
# Terminal 1
cd "/Users/anshmansingh/Desktop/ojt 4 tyr" && uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload

# Terminal 2 (wait 5 seconds, then run)
cd "/Users/anshmansingh/Desktop/ojt 4 tyr" && sleep 5 && python3 test_local.py
```
