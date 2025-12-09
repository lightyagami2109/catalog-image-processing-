# Where to See All 3 Renditions

## 📍 Main Location: Retrieve Asset Endpoint

The **`/retrieve/asset/{asset_id}`** endpoint shows all renditions in the response.

### Endpoint:
```
GET /retrieve/asset/{asset_id}
```

### Example:
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

### Response Structure:

```json
{
  "asset_id": 1,
  "filename": "image.jpg",
  "content_hash": "abc123...",
  "width": 1920,
  "height": 1080,
  "bytes": 245678,
  "color_space": "RGB",
  "created_at": "2024-01-15T10:30:00",
  
  "renditions": [                    ← 👈 HERE! This array shows all renditions
    {
      "preset": "thumb",             ← ✅ Thumbnail rendition
      "file_path": "renditions/1_thumb.jpg",
      "width": 100,
      "height": 56,
      "bytes": 5432,
      "quality": 85
    },
    {
      "preset": "card",              ← ✅ Card rendition
      "file_path": "renditions/1_card.jpg",
      "width": 400,
      "height": 225,
      "bytes": 12345,
      "quality": 85
    },
    {
      "preset": "zoom",              ← ✅ Zoom rendition
      "file_path": "renditions/1_zoom.jpg",
      "width": 1200,
      "height": 675,
      "bytes": 45678,
      "quality": 85
    }
  ]
}
```

## ✅ How to Check if All 3 Are Created

### Method 1: Count the Array
Look at the `renditions` array:
- **3 items** = ✅ All created!
- **0 items** = ❌ None created yet (wait or check worker)
- **1-2 items** = ⚠️ Some missing (check worker logs)

### Method 2: Check Presets
Look for these 3 presets in the array:
- ✅ `"preset": "thumb"`
- ✅ `"preset": "card"`
- ✅ `"preset": "zoom"`

### Method 3: Use the Diagnostic Script
```bash
python3 check_renditions.py
```

This will show:
```
Renditions:
  ✅ thumb - 100x56 (5,432 bytes)
  ✅ card - 400x225 (12,345 bytes)
  ✅ zoom - 1200x675 (45,678 bytes)
```

## 🔍 Other Places Renditions Appear

### 1. Compare Endpoint
When you compare an image, renditions are used in the comparison:

```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@compare.jpg"
```

Response includes comparisons for each rendition:
```json
{
  "comparisons": {
    "thumb": {...},    ← Uses thumb rendition
    "card": {...},     ← Uses card rendition
    "zoom": {...}      ← Uses zoom rendition
  }
}
```

### 2. Download Individual Renditions
You can download each rendition separately:

```bash
# Download thumbnail
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg

# Download card
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg

# Download zoom
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

If these work, renditions exist!

## 📊 Visual Guide

### What You'll See:

**✅ SUCCESS (All 3 Created):**
```json
{
  "renditions": [
    {"preset": "thumb", ...},   ← Item 1
    {"preset": "card", ...},    ← Item 2
    {"preset": "zoom", ...}     ← Item 3
  ]
}
```

**❌ NOT READY (None Created Yet):**
```json
{
  "renditions": []              ← Empty array
}
```

**⚠️ PARTIAL (Some Missing):**
```json
{
  "renditions": [
    {"preset": "thumb", ...}    ← Only 1 item
  ]
}
```

## 🧪 Quick Test

1. **Upload an image:**
   ```bash
   curl -X POST "http://localhost:10000/upload/" \
     -F "file=@test.jpg" \
     -F "tenant_name=test"
   ```
   
   Save the `asset_id` from response (e.g., `1`)

2. **Wait 15 seconds** for processing

3. **Check renditions:**
   ```bash
   curl "http://localhost:10000/retrieve/asset/1" | python3 -m json.tool
   ```
   
   Look for the `renditions` array - should have 3 items!

## 📝 Summary

**Main Endpoint:** `GET /retrieve/asset/{asset_id}`

**Location in Response:** `renditions` array (lines 47-57 in the code)

**What to Look For:**
- Array length = 3 ✅
- Contains: `thumb`, `card`, `zoom` ✅
- Each has: `width`, `height`, `bytes`, `file_path` ✅

---

**If `renditions` is empty `[]`:**
- Wait a bit longer (worker might still processing)
- Check worker logs for errors
- Run `python3 debug_jobs.py` to see job status
