# Hands-On Guide - Step-by-Step Usage

This guide walks you through using each section of the project with actual commands you can run right now.

## Prerequisites

1. **Start the server** (if not already running):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
   ```

2. **Start the worker** (in another terminal):
   ```bash
   bash app/scripts/run_worker.sh
   ```

3. **Have a test image ready** (any `.jpg`, `.png`, etc.)

---

## Section 1: Upload - Upload Your First Image

### Step 1: Prepare Your Image
Find an image file on your computer. For example: `photo.jpg`, `image.png`, etc.

### Step 2: Upload the Image
Open your terminal and run:

```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@/path/to/your/image.jpg" \
  -F "tenant_name=my_tenant"
```

**Replace `/path/to/your/image.jpg` with your actual image path.**

**Example:**
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@/Users/anshmansingh/Desktop/myphoto.jpg" \
  -F "tenant_name=test_tenant"
```

### Step 3: Check the Response
You should see something like:
```json
{
  "asset_id": 1,
  "status": "uploaded",
  "message": "Image uploaded and queued for processing",
  "content_hash": "abc123...",
  "job_id": 1
}
```

**✅ Success!** Your image is uploaded. Note the `asset_id` (in this example: `1`).

### Step 4: Try Uploading the Same Image Again
Run the same command again. You should see:
```json
{
  "asset_id": 1,
  "status": "exists",
  "message": "Asset with identical content already exists (idempotent)",
  "content_hash": "abc123..."
}
```

**✅ This shows idempotency working!** The same image won't be uploaded twice.

### Using Python Instead?
```python
import requests

url = "http://localhost:10000/upload/"
files = {"file": open("your_image.jpg", "rb")}
data = {"tenant_name": "my_tenant"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

## Section 2: Retrieve - Get Your Image Information

### Step 1: Get Asset Metadata
Use the `asset_id` from your upload (in our example: `1`):

```bash
curl "http://localhost:10000/retrieve/asset/1"
```

### Step 2: Check the Response
You'll see:
```json
{
  "asset_id": 1,
  "filename": "your_image.jpg",
  "content_hash": "abc123...",
  "width": 1920,
  "height": 1080,
  "bytes": 245678,
  "color_space": "RGB",
  "created_at": "2024-01-15T10:30:00",
  "renditions": [
    {
      "preset": "thumb",
      "file_path": "renditions/1_thumb.jpg",
      "width": 100,
      "height": 56,
      "bytes": 5432,
      "quality": 85
    },
    {
      "preset": "card",
      "file_path": "renditions/1_card.jpg",
      "width": 400,
      "height": 225,
      "bytes": 12345,
      "quality": 85
    },
    {
      "preset": "zoom",
      "file_path": "renditions/1_zoom.jpg",
      "width": 1200,
      "height": 675,
      "bytes": 45678,
      "quality": 85
    }
  ]
}
```

**Note:** If `renditions` is empty `[]`, wait a few seconds and try again. The worker needs time to process.

### Step 3: Download a Thumbnail
```bash
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o downloaded_thumb.jpg
```

This downloads the thumbnail to `downloaded_thumb.jpg` in your current directory.

### Step 4: Download Card Size
```bash
curl "http://localhost:10000/retrieve/rendition/1/card" -o downloaded_card.jpg
```

### Step 5: Download Zoom Size
```bash
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o downloaded_zoom.jpg
```

**✅ Check your directory!** You should now have three downloaded images.

### Using Python Instead?
```python
import requests

# Get metadata
response = requests.get("http://localhost:10000/retrieve/asset/1")
asset = response.json()
print(f"Asset: {asset['filename']}")
print(f"Renditions: {len(asset['renditions'])}")

# Download thumbnail
response = requests.get("http://localhost:10000/retrieve/rendition/1/thumb")
with open("thumb.jpg", "wb") as f:
    f.write(response.content)
print("Downloaded thumb.jpg")
```

---

## Section 3: Compare - Check Image Quality

### Step 1: Prepare a Comparison Image
You need an image to compare against your uploaded asset. This could be:
- A modified version of the same image
- A different image
- The same image downloaded and re-uploaded

### Step 2: Run the Comparison
Use the `asset_id` from your upload (example: `1`):

```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@/path/to/compare_image.jpg"
```

**Replace `/path/to/compare_image.jpg` with your comparison image.**

### Step 3: Check the Results
You'll see quality metrics:
```json
{
  "asset_id": 1,
  "comparisons": {
    "original": {
      "file_size_bytes": 245678,
      "psnr_db": 45.2,
      "perceptual_hash_distance": 0
    },
    "thumb": {
      "file_size_bytes": 5432,
      "psnr_db": 32.5,
      "perceptual_hash_distance": 5
    },
    "card": {
      "file_size_bytes": 12345,
      "psnr_db": 38.1,
      "perceptual_hash_distance": 3
    },
    "zoom": {
      "file_size_bytes": 45678,
      "psnr_db": 42.3,
      "perceptual_hash_distance": 1
    }
  }
}
```

**Understanding the metrics:**
- **PSNR > 30 dB**: Good quality ✅
- **PSNR < 30 dB**: Lower quality ⚠️
- **Hash distance 0**: Identical images
- **Hash distance 1-5**: Very similar
- **Hash distance > 10**: Different images

### Using Python Instead?
```python
import requests

url = "http://localhost:10000/compare/1"
files = {"file": open("compare_image.jpg", "rb")}

response = requests.post(url, files=files)
results = response.json()

for preset, metrics in results["comparisons"].items():
    psnr = metrics['psnr_db']
    quality = "Good" if psnr > 30 else "Lower"
    print(f"{preset}: {psnr:.1f} dB ({quality})")
```

---

## Section 4: Metrics - Check Usage Statistics

### Step 1: Get Metrics for Your Tenant
Use the tenant name you used during upload (example: `my_tenant`):

```bash
curl "http://localhost:10000/metrics/tenant/my_tenant"
```

### Step 2: Check the Response
```json
{
  "tenant_id": 1,
  "tenant_name": "my_tenant",
  "asset_count": 5,
  "rendition_count": 15,
  "total_bytes": 15728640,
  "asset_bytes": 10485760,
  "rendition_bytes": 5242880
}
```

**What this tells you:**
- `asset_count`: How many images you've uploaded
- `rendition_count`: Total renditions created (3 per asset)
- `total_bytes`: Total storage used
- `asset_bytes`: Storage for original images
- `rendition_bytes`: Storage for renditions

### Step 3: Get All Tenants
```bash
curl "http://localhost:10000/metrics/"
```

This shows metrics for all tenants in the system.

### Using Python Instead?
```python
import requests

# Get specific tenant
response = requests.get("http://localhost:10000/metrics/tenant/my_tenant")
metrics = response.json()

print(f"Tenant: {metrics['tenant_name']}")
print(f"Assets: {metrics['asset_count']}")
print(f"Storage: {metrics['total_bytes'] / 1024 / 1024:.2f} MB")

# Get all tenants
response = requests.get("http://localhost:10000/metrics/")
all_metrics = response.json()
for tenant in all_metrics["tenants"]:
    print(f"{tenant['tenant_name']}: {tenant['asset_count']} assets")
```

---

## Section 5: Purge - Clean Up Old Files

### ⚠️ IMPORTANT: Always Start with Dry Run!

### Step 1: Dry Run (Safe - No Deletion)
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true"
```

### Step 2: Check What Would Be Deleted
```json
{
  "dry_run": true,
  "purge_days": 30,
  "cutoff_date": "2023-12-15T10:00:00",
  "renditions_found": 50,
  "renditions_to_delete": 12,
  "deleted_count": 0,
  "deleted_bytes": 0,
  "errors": null
}
```

**This shows:**
- How many renditions would be deleted
- How much space would be freed
- **Nothing is actually deleted yet!**

### Step 3: If You're Satisfied, Actually Delete
**Only run this if you're sure!**

```bash
curl -X POST "http://localhost:10000/purge/?dry_run=false"
```

### Step 4: Check Results
```json
{
  "dry_run": false,
  "purge_days": 30,
  "cutoff_date": "2023-12-15T10:00:00",
  "renditions_found": 50,
  "renditions_to_delete": 12,
  "deleted_count": 12,
  "deleted_bytes": 524288,
  "errors": null
}
```

**Now files are actually deleted!**

### Step 5: Custom Number of Days
To purge files older than 60 days instead of 30:
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true&days=60"
```

### Using Python Instead?
```python
import requests

# Always dry run first!
response = requests.post("http://localhost:10000/purge/?dry_run=true")
result = response.json()

print(f"Would delete: {result['renditions_to_delete']} renditions")
print(f"Would free: {result['deleted_bytes'] / 1024 / 1024:.2f} MB")

# If satisfied, actually delete
if result['renditions_to_delete'] > 0:
    confirm = input("Delete these files? (yes/no): ")
    if confirm.lower() == "yes":
        response = requests.post("http://localhost:10000/purge/?dry_run=false")
        result = response.json()
        print(f"Deleted {result['deleted_count']} renditions")
```

---

## Complete Workflow Example

Follow these steps in order to see the full pipeline:

### 1. Upload an Image
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@test_image.jpg" \
  -F "tenant_name=demo"
```

**Save the `asset_id` from the response!** (Let's say it's `1`)

### 2. Wait 5-10 Seconds
The worker needs time to process and create renditions.

### 3. Check Asset Status
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

**If `renditions` is empty, wait a bit more and try again.**

### 4. Download All Renditions
```bash
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

**✅ Check your folder - you should have 3 new images!**

### 5. Compare Quality
```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@test_image.jpg"
```

### 6. Check Metrics
```bash
curl "http://localhost:10000/metrics/tenant/demo"
```

### 7. Clean Up (Optional)
```bash
# First, see what would be deleted
curl -X POST "http://localhost:10000/purge/?dry_run=true"

# If satisfied, actually delete (be careful!)
# curl -X POST "http://localhost:10000/purge/?dry_run=false"
```

---

## Quick Reference Card

### Upload
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@image.jpg" \
  -F "tenant_name=my_tenant"
```

### Retrieve Asset Info
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

### Download Rendition
```bash
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
```

### Compare Image
```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@compare.jpg"
```

### Get Metrics
```bash
curl "http://localhost:10000/metrics/tenant/my_tenant"
```

### Purge (Dry Run)
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true"
```

---

## Common Issues & Solutions

### Issue: "Renditions not available"
**Solution:** Wait 5-10 seconds and try again. The worker needs time to process.

### Issue: "Asset not found"
**Solution:** Check that you're using the correct `asset_id`. Get it from the upload response.

### Issue: "Invalid preset"
**Solution:** Use only: `thumb`, `card`, or `zoom` (lowercase).

### Issue: "File must be an image"
**Solution:** Make sure you're uploading a valid image file (jpg, png, etc.).

### Issue: Worker not processing
**Solution:** 
1. Check if worker is running: `ps aux | grep worker`
2. Check worker logs for errors
3. Restart worker: `bash app/scripts/run_worker.sh`

---

## Testing with Multiple Images

### Upload Multiple Images
```bash
# Image 1
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@image1.jpg" \
  -F "tenant_name=test"

# Image 2
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@image2.jpg" \
  -F "tenant_name=test"

# Image 3
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@image3.jpg" \
  -F "tenant_name=test"
```

### Check Total Usage
```bash
curl "http://localhost:10000/metrics/tenant/test"
```

You should see `asset_count: 3` and `rendition_count: 9` (3 assets × 3 renditions each).

---

## Next Steps

1. **Try uploading different image formats** (jpg, png, etc.)
2. **Test idempotency** by uploading the same image twice
3. **Compare different images** to see quality differences
4. **Monitor metrics** as you upload more images
5. **Experiment with purge** (always use dry_run first!)

---

## Need Help?

- Check the main [README.md](README.md) for architecture details
- See [USAGE_GUIDE.md](USAGE_GUIDE.md) for detailed explanations
- Check server logs for error messages
- Verify database is running and accessible

Happy coding! 🚀
