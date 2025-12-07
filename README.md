# Catalog Image Processing Pipeline

A small, exam-friendly async FastAPI pipeline for processing catalog images with idempotency, renditions, retries, and quality metrics. Designed for deployment on Render without Docker.

## Architecture

```
┌─────────────┐
│   FastAPI   │  ← Web Service (Render)
│   (main)    │
└──────┬──────┘
       │
       ├─── POST /upload      → Creates Asset + Job
       ├─── GET  /retrieve    → Returns Asset/Rendition
       ├─── POST /compare     → Quality metrics (PSNR)
       ├─── GET  /metrics     → Tenant usage stats
       └─── POST /purge       → Safe deletion
       
       │
       ▼
┌─────────────┐
│  PostgreSQL │  ← Assets, Renditions, Jobs, Metrics
└─────────────┘

       │
       ▼
┌─────────────┐
│   Redis     │  ← Job Queue (optional, falls back to DB polling)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Worker    │  ← Background Worker (Render)
│  (workers)  │  Processes jobs, creates renditions
└─────────────┘
       │
       ▼
┌─────────────┐
│  Storage    │  ← Local filesystem (./storage) or S3
└─────────────┘
```

## Quick Start (Local)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   cp example.env .env
   # Edit .env as needed
   ```

3. **Initialize database:**
   ```bash
   python -c "from app.db import init_db; import asyncio; asyncio.run(init_db())"
   ```

4. **Start FastAPI server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
   ```

5. **Start worker (in another terminal):**
   ```bash
   bash app/scripts/run_worker.sh
   ```

6. **Seed test corpus:**
   ```bash
   python app/scripts/seed_corpus.py
   ```

## Render Deployment (Non-Docker)

### Step 1: Create Web Service

1. On Render Dashboard, click **New** → **Web Service**
2. Connect your repository
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`

### Step 2: Provision PostgreSQL

1. Create a **PostgreSQL** database on Render
2. Copy the **Internal Database URL**
3. In Web Service settings, add environment variable:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
   ```

### Step 3: (Optional) Provision Redis

1. Create a **Redis** instance on Render
2. Copy the **Internal Redis URL**
3. Add environment variable:
   ```
   REDIS_URL=redis://:password@host:port
   ```
   If not set, worker falls back to database polling.

### Step 4: Set Other Environment Variables

Add to Web Service:
```
STORAGE_PATH=/mnt/storage
SECRET_KEY=<generate-random-string>
PURGE_DAYS=30
```

### Step 5: Create Background Worker

1. Click **New** → **Background Worker**
2. Use the same repository
3. **Start Command:** `bash app/scripts/run_worker.sh`
4. Copy all environment variables from Web Service (DATABASE_URL, REDIS_URL, etc.)

### Step 6: Deploy and Verify

1. Deploy both services
2. Check Web Service logs for: `✓ Database tables created`, `✓ Redis connected` (or fallback message)
3. Seed test data:
   ```bash
   # From Render shell or locally pointing to Render service
   python app/scripts/seed_corpus.py http://your-service.onrender.com
   ```
4. Verify endpoints:
   - `GET /healthz` → `{"status": "healthy"}`
   - `GET /metrics` → Tenant metrics
   - `GET /retrieve/asset/1` → Asset details

## API Endpoints

### Upload Image

```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@image.jpg" \
  -F "tenant_name=my_tenant"
```

Response:
```json
{
  "asset_id": 1,
  "status": "uploaded",
  "content_hash": "abc123...",
  "job_id": 1
}
```

### Retrieve Asset

```bash
curl "http://localhost:10000/retrieve/asset/1"
```

### Retrieve Rendition

```bash
curl "http://localhost:10000/retrieve/rendition/1/thumb" -o thumb.jpg
```

### Compare Image

```bash
curl -X POST "http://localhost:10000/compare/1" \
  -F "file=@compare_image.jpg"
```

Returns PSNR and perceptual hash distance per preset.

### Metrics

```bash
curl "http://localhost:10000/metrics/tenant/my_tenant"
```

### Purge (Dry Run)

```bash
curl -X POST "http://localhost:10000/purge/?dry_run=true"
```

### Purge (Actual)

```bash
curl -X POST "http://localhost:10000/purge/?dry_run=false&days=30"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL or SQLite connection string | `sqlite+aiosqlite:///./dev.db` |
| `REDIS_URL` | Redis connection string (optional) | Empty (uses fallback) |
| `STORAGE_PATH` | Local storage path | `./storage` |
| `SECRET_KEY` | Secret key for app | `change_me` |
| `PURGE_DAYS` | Days before purging old renditions | `30` |
| `PORT` | Server port | `10000` |

## Rendition Presets

- **thumb**: 100×100 fit (maintains aspect ratio)
- **card**: 400×400 fit (maintains aspect ratio)
- **zoom**: Max 1200px on longer edge (maintains aspect ratio)

## Idempotency

Uploads are idempotent by content hash (SHA256). Uploading the same image twice returns the existing asset.

## Retry Logic

Jobs retry up to 3 times with exponential backoff (2, 4, 8 seconds). Permanently failed jobs are moved to `poison_jobs` table.

## Testing

Run tests:
```bash
pytest -q
```

Run specific test:
```bash
pytest tests/test_hashing.py -v
pytest tests/test_idempotency.py -v
pytest tests/test_api_endpoints.py -v
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── db.py                # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── storage.py           # Storage adapter (local/S3)
│   ├── workers.py           # Async worker
│   ├── hashing.py           # SHA256 + perceptual hash
│   ├── utils.py             # Image ops, PSNR
│   ├── api/
│   │   ├── upload.py
│   │   ├── retrieve.py
│   │   ├── compare.py
│   │   ├── metrics.py
│   │   └── purge.py
│   └── scripts/
│       ├── run_worker.sh
│       ├── seed_corpus.py
│       └── purge_safe.sh
├── tests/
│   ├── test_hashing.py
│   ├── test_idempotency.py
│   └── test_api_endpoints.py
├── requirements.txt
├── example.env
├── README.md
├── study_guide.md
└── render/
    └── render.md
```

## Study Guide

See [study_guide.md](study_guide.md) for a 2-day exam preparation plan.

## Notes

- **Storage**: Currently uses local filesystem. See `app/storage.py` for S3 adapter hooks.
- **Queue**: Falls back to database polling if Redis is not available.
- **Quality Metrics**: Uses PSNR (Peak Signal-to-Noise Ratio). Can swap to SSIM if needed (see `app/utils.py`).

