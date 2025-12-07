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
│   Worker    │  ← Integrated Worker (runs in same process)
│  (workers)  │  Processes jobs, creates renditions
│             │  Uses database queue (no Redis needed)
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

## Render Deployment (Non-Docker, Free Tier)

### Step 1: Create PostgreSQL Database

1. On Render Dashboard, click **New** → **PostgreSQL**
2. Configure:
   - **Name:** `catalog-pipeline-db`
   - **Region:** Choose closest (e.g., Oregon)
   - **Database:** `catalogdb`
3. Click **Create Database**
4. After creation, open database → **Connections** tab
5. Copy **Internal Database URL**
6. **IMPORTANT:** Change `postgresql://` to `postgresql+asyncpg://`
   - Example: `postgresql+asyncpg://user:pass@host:port/dbname`

### Step 2: Create Web Service

1. On Render Dashboard, click **New** → **Web Service**
2. Connect your repository
3. Configure:
   - **Name:** `catalog-image-pipeline`
   - **Environment:** `Python 3`
   - **Python Version:** `3.11` (important - set explicitly)
   - **Build Command:** `pip install --upgrade pip setuptools wheel && pip install --only-binary :all: pillow pydantic-core asyncpg && pip install -r requirements.txt --prefer-binary --no-cache-dir`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`

### Step 3: Add Environment Variables

In Web Service settings → **Environment** section, add:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
STORAGE_PATH=/mnt/storage
SECRET_KEY=<generate-random-string>
PURGE_DAYS=30
ENABLE_WORKER=true
```

**Note:** 
- Generate `SECRET_KEY` with: `openssl rand -hex 32`
- `ENABLE_WORKER=true` starts worker in same process (no separate worker service needed)
- **No Redis needed** - worker uses database polling fallback

### Step 4: Deploy and Verify

1. Click **Create Web Service** (or **Save Changes** if editing)
2. Wait for deployment (2-5 minutes)
3. Check logs for:
   ```
   ✓ Database tables created
   ⚠ Redis not configured, using fallback queue
   ✓ Worker started as background task
   ✓ Application started
   ```
4. Test health check:
   ```bash
   curl https://your-service.onrender.com/healthz
   ```
5. Seed test data (from Render Shell or locally):
   ```bash
   python app/scripts/seed_corpus.py https://your-service.onrender.com
   ```
6. Verify endpoints:
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
| `STORAGE_PATH` | Local storage path | `./storage` |
| `SECRET_KEY` | Secret key for app | `change_me` |
| `PURGE_DAYS` | Days before purging old renditions | `30` |
| `ENABLE_WORKER` | Enable integrated worker (runs in same process) | `true` |
| `PORT` | Server port | `10000` |

**Note:** Redis is not required. The worker uses database polling when Redis is not configured.

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
- **Queue**: Uses database polling (no Redis required). Worker runs in same process as Web Service for free tier deployment.
- **Quality Metrics**: Uses PSNR (Peak Signal-to-Noise Ratio). Can swap to SSIM if needed (see `app/utils.py`).
- **Python Version**: Requires Python 3.11+ (specified in `runtime.txt`). Python 3.13 may have compatibility issues with some packages.
- **Build**: Uses binary wheels for Pillow, pydantic-core, and asyncpg to avoid compilation errors on Render.

