# Complete Usage Guide - Catalog Image Processing Pipeline

This guide explains how each section of the project works and how to use it.

## Table of Contents
1. [Upload Section](#1-upload-section)
2. [Retrieve Section](#2-retrieve-section)
3. [Compare Section](#3-compare-section)
4. [Metrics Section](#4-metrics-section)
5. [Purge Section](#5-purge-section)
6. [Worker Process](#6-worker-process)
7. [Complete Workflow Example](#7-complete-workflow-example)

---

## 1. Upload Section

### What It Does
The upload endpoint accepts image files, validates them, stores them, and queues them for processing into different sizes (renditions).

### How It Works

**Step-by-Step Process:**
1. **File Validation**: Checks if the uploaded file is an image
2. **Image Processing**: Opens the image using PIL to validate it's a valid image file
3. **Content Hashing**: Computes SHA256 hash for idempotency (prevents duplicate uploads)
4. **Duplicate Check**: If an identical image already exists, returns the existing asset
5. **Tenant Management**: Gets or creates a tenant (for multi-tenant support)
6. **File Storage**: Saves the original image to disk
7. **Database Record**: Creates an Asset record with metadata (dimensions, file size, etc.)
8. **Job Creation**: Creates a processing job that will generate renditions (thumb, card, zoom)
9. **Queue Job**: Adds job to Redis queue (or database if Redis unavailable)

### How to Use

**Basic Upload:**
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@your_image.jpg" \
  -F "tenant_name=my_tenant"
```

**Using Python:**
```python
import requests

url = "http://localhost:10000/upload/"
files = {"file": open("image.jpg", "rb")}
data = {"tenant_name": "my_tenant"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response (New Upload):**
```json
{
  "asset_id": 1,
  "status": "uploaded",
  "message": "Image uploaded and queued for processing",
  "content_hash": "abc123...",
  "job_id": 1
}
```

**Response (Duplicate - Idempotent):**
```json
{
  "asset_id": 1,
  "status": "exists",
  "message": "Asset with identical content already exists (idempotent)",
  "content_hash": "abc123..."
}
```

### Key Features
- **Idempotency**: Uploading the same image twice returns the existing asset (no duplicates)
- **Automatic Processing**: Creates a job that will generate renditions automatically
- **Multi-tenant**: Supports different tenants (organizations/users)
- **Metadata Extraction**: Automatically extracts width, height, color space, file size

---

## 2. Retrieve Section

### What It Does
Retrieves asset metadata and actual image files (both originals and renditions).

### How It Works

**Two Endpoints:**

1. **Get Asset Metadata** (`GET /retrieve/asset/{asset_id}`)
   - Fetches asset information from database
   - Includes all renditions (thumb, card, zoom) that have been created
   - Returns JSON with metadata

2. **Get Rendition File** (`GET /retrieve/rendition/{asset_id}/{preset}`)
   - Fetches the actual image file for a specific rendition
   - Validates preset name (must be: thumb, card, or zoom)
   - Returns the image file directly

### How to Use

**Get Asset Metadata:**
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

**Response:**
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

**Download a Rendition:**
```bash
# Download thumbnail
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg

# Download card size
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg

# Download zoom size
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

**Using Python:**
```python
import requests

# Get metadata
response = requests.get("http://localhost:10000/retrieve/asset/1")
asset_data = response.json()
print(f"Asset has {len(asset_data['renditions'])} renditions")

# Download a rendition
response = requests.get("http://localhost:10000/retrieve/rendition/1/thumb")
with open("thumb.jpg", "wb") as f:
    f.write(response.content)
```

### Available Rendition Presets
- **thumb**: 100×100 pixels (fits within, maintains aspect ratio)
- **card**: 400×400 pixels (fits within, maintains aspect ratio)
- **zoom**: Maximum 1200px on longer edge (maintains aspect ratio)

---

## 3. Compare Section

### What It Does
Compares an uploaded image against the original asset and all its renditions, providing quality metrics.

### How It Works

**Step-by-Step Process:**
1. **Fetch Asset**: Gets the asset from database
2. **Load Uploaded Image**: Reads and validates the uploaded comparison image
3. **Load Original**: Reads the original asset image from storage
4. **Compute Metrics**: For each rendition (and original):
   - **PSNR** (Peak Signal-to-Noise Ratio): Measures image quality (higher = better, >30 dB is good)
   - **Perceptual Hash Distance**: Measures visual similarity (lower = more similar)
   - **File Size**: Size in bytes
5. **Return Results**: JSON with comparison metrics for each preset

### How to Use

**Compare Image:**
```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@compare_image.jpg"
```

**Response:**
```json
{
  "asset_id": 1,
  "comparisons": {
    "original": {
      "file_size_bytes": 245678,
      "psnr_db": 45.2,
      "perceptual_hash_distance": 0,
      "note": "PSNR > 30 dB is good quality. Lower hash distance = more similar."
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
  },
  "note": "PSNR > 30 dB indicates good quality. Lower perceptual_hash_distance = more similar."
}
```

**Using Python:**
```python
import requests

url = "http://localhost:10000/compare/1"
files = {"file": open("compare_image.jpg", "rb")}

response = requests.post(url, files=files)
results = response.json()

for preset, metrics in results["comparisons"].items():
    print(f"{preset}: PSNR={metrics['psnr_db']:.2f} dB, "
          f"Hash Distance={metrics['perceptual_hash_distance']}")
```

### Understanding Metrics
- **PSNR (dB)**: 
  - > 40 dB: Excellent quality
  - 30-40 dB: Good quality
  - < 30 dB: Lower quality (may have visible artifacts)
- **Perceptual Hash Distance**: 
  - 0: Identical images
  - 1-5: Very similar
  - 6-10: Similar
  - > 10: Different images

---

## 4. Metrics Section

### What It Does
Provides usage statistics for tenants, including asset counts, rendition counts, and storage usage.

### How It Works

**Two Endpoints:**

1. **Get Tenant Metrics** (`GET /metrics/tenant/{tenant_name}`)
   - Fetches statistics for a specific tenant
   - Counts assets and renditions
   - Calculates total storage used (bytes)

2. **Get All Metrics** (`GET /metrics/`)
   - Returns metrics for all tenants
   - Useful for system-wide monitoring

### How to Use

**Get Specific Tenant Metrics:**
```bash
curl "http://localhost:10000/metrics/tenant/my_tenant"
```

**Response:**
```json
{
  "tenant_id": 1,
  "tenant_name": "my_tenant",
  "asset_count": 25,
  "rendition_count": 75,
  "total_bytes": 15728640,
  "asset_bytes": 10485760,
  "rendition_bytes": 5242880
}
```

**Get All Tenants:**
```bash
curl "http://localhost:10000/metrics/"
```

**Response:**
```json
{
  "tenants": [
    {
      "tenant_id": 1,
      "tenant_name": "my_tenant",
      "asset_count": 25,
      "rendition_count": 75,
      "total_bytes": 15728640
    },
    {
      "tenant_id": 2,
      "tenant_name": "another_tenant",
      "asset_count": 10,
      "rendition_count": 30,
      "total_bytes": 5242880
    }
  ]
}
```

**Using Python:**
```python
import requests

# Get specific tenant
response = requests.get("http://localhost:10000/metrics/tenant/my_tenant")
metrics = response.json()
print(f"Tenant '{metrics['tenant_name']}' has {metrics['asset_count']} assets")
print(f"Total storage: {metrics['total_bytes'] / 1024 / 1024:.2f} MB")

# Get all tenants
response = requests.get("http://localhost:10000/metrics/")
all_metrics = response.json()
for tenant in all_metrics["tenants"]:
    print(f"{tenant['tenant_name']}: {tenant['asset_count']} assets")
```

### Use Cases
- **Billing**: Calculate storage costs per tenant
- **Monitoring**: Track system usage and growth
- **Quotas**: Enforce storage limits per tenant
- **Analytics**: Understand usage patterns

---

## 5. Purge Section

### What It Does
Safely deletes old renditions that are no longer referenced, helping free up storage space.

### How It Works

**Step-by-Step Process:**
1. **Find Old Renditions**: Queries renditions older than specified days (default: 30)
2. **Check References**: Only deletes renditions where the asset no longer exists (unreferenced)
3. **Dry Run Mode**: By default, only reports what would be deleted (safe)
4. **Actual Deletion**: When `dry_run=false`, deletes files from storage and database records
5. **Error Handling**: Continues even if some deletions fail, reports errors

### How to Use

**Dry Run (Safe - Just Reports):**
```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true"
```

**Response:**
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

**Actual Purge (Deletes Files):**
```bash
# Use default 30 days
curl -X POST "http://localhost:10000/purge/?dry_run=false"

# Custom number of days
curl -X POST "http://localhost:10000/purge/?dry_run=false&days=60"
```

**Response:**
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

**Using Python:**
```python
import requests

# Dry run first (always recommended)
response = requests.post("http://localhost:10000/purge/?dry_run=true")
result = response.json()
print(f"Would delete {result['renditions_to_delete']} renditions")
print(f"Would free {result['deleted_bytes'] / 1024 / 1024:.2f} MB")

# If satisfied, actually delete
if result['renditions_to_delete'] > 0:
    response = requests.post("http://localhost:10000/purge/?dry_run=false")
    result = response.json()
    print(f"Deleted {result['deleted_count']} renditions")
```

### Safety Features
- **Dry Run by Default**: Won't delete anything unless explicitly set to `dry_run=false`
- **Unreferenced Only**: Only deletes renditions where the asset is gone
- **Error Reporting**: Lists any errors that occurred during deletion
- **Configurable**: Can specify custom number of days

---

## 6. Worker Process

### What It Does
The worker is a background process that picks up jobs from the queue and processes them to create renditions.

### How It Works

**Step-by-Step Process:**
1. **Poll for Jobs**: Checks for pending jobs (from Redis queue or database)
2. **Process Job**: For each job:
   - Loads the original image
   - Creates renditions for each preset (thumb, card, zoom)
   - Saves rendition files to storage
   - Creates database records for renditions
   - Marks job as completed
3. **Retry Logic**: If a job fails:
   - Retries up to 3 times
   - Uses exponential backoff (2s, 4s, 8s delays)
   - After 3 failures, moves to "poison jobs" table
4. **Queue System**: 
   - Uses Redis if available (faster)
   - Falls back to database polling if Redis unavailable

### How It Runs

**Automatic (Integrated Worker):**
When `ENABLE_WORKER=true` in environment, the worker runs as a background task in the same process as the web server.

**Manual (Separate Process):**
```bash
# Start worker separately
bash app/scripts/run_worker.sh

# Or directly
python -m app.workers
```

**What Happens:**
1. Upload creates a job with status "pending"
2. Worker picks up the job
3. Worker creates all renditions (thumb, card, zoom)
4. Job status changes to "completed"
5. Asset now has renditions available via retrieve endpoint

### Monitoring

**Check Job Status:**
You can query the database to see job status:
- `pending`: Waiting to be processed
- `processing`: Currently being processed
- `completed`: Successfully finished
- `failed`: Permanently failed (after max retries)

**Worker Logs:**
```
✓ Job 1 completed for asset 1
⚠ Job 2 failed, retrying in 2s (attempt 1/3)
✗ Job 3 failed permanently after 3 retries
```

---

## 7. Complete Workflow Example

Here's a complete example of using all sections together:

### Step 1: Upload an Image
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@photo.jpg" \
  -F "tenant_name=my_company"
```

**Response:**
```json
{
  "asset_id": 1,
  "status": "uploaded",
  "job_id": 1
}
```

### Step 2: Wait for Processing
The worker will automatically process the job (usually takes a few seconds). You can check if renditions are ready by retrieving the asset.

### Step 3: Check Asset Status
```bash
curl "http://localhost:10000/retrieve/asset/1"
```

If renditions are ready, you'll see them in the response. If not, wait a bit and try again.

### Step 4: Download Renditions
```bash
# Download thumbnail
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg

# Download card size
curl "http://localhost:10000/retrieve/rendition/1/card" -o card.jpg

# Download zoom size
curl "http://localhost:10000/retrieve/rendition/1/zoom" -o zoom.jpg
```

### Step 5: Compare Quality
```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@modified_image.jpg"
```

### Step 6: Check Metrics
```bash
curl "http://localhost:10000/metrics/tenant/my_company"
```

### Step 7: Clean Up (Periodically)
```bash
# First, see what would be deleted
curl -X POST "http://localhost:10000/purge/?dry_run=true"

# If satisfied, actually delete
curl -X POST "http://localhost:10000/purge/?dry_run=false&days=30"
```

---

## Quick Reference

### Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload/` | POST | Upload image, create asset and job |
| `/retrieve/asset/{id}` | GET | Get asset metadata |
| `/retrieve/rendition/{id}/{preset}` | GET | Download rendition image |
| `/compare/{id}` | POST | Compare image quality |
| `/metrics/tenant/{name}` | GET | Get tenant statistics |
| `/metrics/` | GET | Get all tenants statistics |
| `/purge/` | POST | Delete old renditions |
| `/healthz` | GET | Health check |

### Rendition Presets

| Preset | Size | Use Case |
|--------|------|----------|
| `thumb` | 100×100 | Thumbnails, lists |
| `card` | 400×400 | Cards, previews |
| `zoom` | Max 1200px | Detailed view |

### Common Status Codes

- `200`: Success
- `400`: Bad Request (invalid file, invalid preset, etc.)
- `404`: Not Found (asset doesn't exist, rendition not created yet)
- `500`: Server Error

---

## Tips and Best Practices

1. **Always Check Asset Status**: Before downloading renditions, check if they're ready
2. **Use Dry Run First**: Always run purge with `dry_run=true` first
3. **Monitor Metrics**: Regularly check metrics to track usage
4. **Idempotency**: Don't worry about uploading the same image twice - it's safe
5. **Worker Monitoring**: If renditions aren't being created, check worker logs
6. **Storage Management**: Run purge periodically to free up space

---

## Troubleshooting

**Renditions not available?**
- Check if worker is running
- Check job status in database
- Wait a few seconds and try again

**Upload fails?**
- Ensure file is a valid image
- Check file size limits
- Verify database connection

**Purge not working?**
- Remember to set `dry_run=false` for actual deletion
- Check that renditions are actually old enough
- Verify storage permissions

---

For more information, see the main [README.md](README.md).
