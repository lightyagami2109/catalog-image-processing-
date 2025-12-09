# Quick Test - Verify Renditions Work

## Step 1: Start the Server

**Terminal 1:**
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

Wait until you see:
```
✓ Worker started as background task
✓ Application started
INFO:     Uvicorn running on http://0.0.0.0:10000
```

## Step 2: Run the Test

**Terminal 2 (wait 5 seconds after Step 1):**
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
bash run_test.sh
```

This will:
1. ✅ Check server is running
2. ✅ Create a test image
3. ✅ Upload it
4. ✅ Wait 20 seconds for processing
5. ✅ Check if all 3 renditions were created

## Expected Output

**If working:**
```
✅ SUCCESS! All 3 renditions created!
   ✅ thumb  - 100x75 (X bytes)
   ✅ card   - 400x300 (X bytes)
   ✅ zoom   - 800x600 (X bytes)
```

**If not working:**
```
❌ Only 0/3 renditions created
```

## Manual Test (Alternative)

If the script doesn't work, test manually:

```bash
# 1. Create test image
python3 -c "from PIL import Image; Image.new('RGB', (800, 600), 'blue').save('test.jpg')"

# 2. Upload
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=test"

# Save the asset_id from response (e.g., 1)

# 3. Wait 20 seconds

# 4. Check renditions
curl "http://localhost:10000/retrieve/asset/1" | python3 -m json.tool

# Look for "renditions" array - should have 3 items!
```

## What to Look For

In the response, check the `renditions` array:

```json
{
  "renditions": [
    {"preset": "thumb", ...},  ← Should see this
    {"preset": "card", ...},   ← Should see this
    {"preset": "zoom", ...}     ← Should see this
  ]
}
```

**3 items = ✅ Working!**
**0 items = ❌ Not working - check worker logs**
