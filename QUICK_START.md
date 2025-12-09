# Quick Start - Copy & Paste Commands

## 🚀 Start Here

### 1. Start the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

### 2. Start the Worker (in another terminal)
```bash
bash app/scripts/run_worker.sh
```

---

## 📤 UPLOAD - Upload an Image

```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@your_image.jpg" \
  -F "tenant_name=my_tenant"
```

**What happens:**
- ✅ Image is validated
- ✅ Saved to storage
- ✅ Asset record created
- ✅ Job queued for processing
- 📝 **Save the `asset_id` from response!**

**Response:**
```json
{
  "asset_id": 1,
  "status": "uploaded",
  "job_id": 1
}
```

---

## 📥 RETRIEVE - Get Your Image

### Get Asset Information
```bash
curl "http://localhost:10000/retrieve/asset/1"
```
*(Replace `1` with your asset_id)*

**Shows:**
- Image metadata (width, height, size)
- List of available renditions
- Creation date

### Download Thumbnail (100×100)
```bash
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
```

### Download Card Size (400×400)
```bash
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg
```

### Download Zoom Size (max 1200px)
```bash
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

**Note:** Wait 5-10 seconds after upload for renditions to be ready!

---

## 🔍 COMPARE - Check Image Quality

```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@compare_image.jpg"
```

**Returns:**
- PSNR (quality score) - >30 dB is good ✅
- Perceptual hash distance - lower = more similar
- File sizes for each rendition

---

## 📊 METRICS - Check Usage

### Get Your Tenant Stats
```bash
curl "http://localhost:10000/metrics/tenant/my_tenant"
```

**Shows:**
- Number of assets uploaded
- Number of renditions created
- Total storage used (bytes)

### Get All Tenants
```bash
curl "http://localhost:10000/metrics/"
```

---

## 🗑️ PURGE - Clean Up Old Files

### ⚠️ ALWAYS START WITH DRY RUN!

```bash
# See what would be deleted (safe)
curl -X POST "http://localhost:10000/purge/?dry_run=true"
```

### Actually Delete (be careful!)
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=false"
```

### Custom Days (e.g., 60 days)
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true&days=60"
```

---

## 🔄 Complete Example Workflow

```bash
# 1. Upload
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test.jpg" \
  -F "tenant_name=demo"

# 2. Wait 5 seconds...

# 3. Get info (use asset_id from step 1)
curl "http://localhost:10000/retrieve/asset/1"

# 4. Download renditions
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg

# 5. Check metrics
curl "http://localhost:10000/metrics/tenant/demo"
```

---

## 🎯 Available Presets

| Preset | Size | Use Case |
|--------|------|----------|
| `thumb` | 100×100 | Thumbnails, lists |
| `card` | 400×400 | Cards, previews |
| `zoom` | Max 1200px | Detailed view |

---

## ⚡ Quick Tips

1. **Always save the `asset_id`** from upload response
2. **Wait 5-10 seconds** after upload before retrieving renditions
3. **Use dry_run=true** before purge
4. **Check metrics** to monitor usage
5. **Same image twice?** No problem - idempotent! ✅

---

## 🐍 Python Alternative

```python
import requests

# Upload
files = {"file": open("image.jpg", "rb")}
data = {"tenant_name": "my_tenant"}
r = requests.post("http://localhost:10000/upload/", files=files, data=data)
asset_id = r.json()["asset_id"]

# Retrieve
r = requests.get(f"http://localhost:10000/retrieve/asset/{asset_id}")
print(r.json())

# Download
r = requests.get(f"http://localhost:10000/retrieve/rendition/{asset_id}/thumb")
with open("thumb.jpg", "wb") as f:
    f.write(r.content)
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Renditions not available | Wait 5-10 seconds, try again |
| Asset not found | Check asset_id is correct |
| Invalid preset | Use: `thumb`, `card`, or `zoom` |
| Worker not processing | Check worker is running |

---

**For detailed explanations, see [HANDS_ON_GUIDE.md](HANDS_ON_GUIDE.md)**
