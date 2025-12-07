# 2-Day Study Guide

## Day 1: Core Concepts & Code Walkthrough

### Morning (3-4 hours): Architecture & Models

**Files to Read:**
1. `app/models.py` - Database schema
   - Understand: Asset, Rendition, Job, PoisonJob, Tenant relationships
   - Key fields: `content_hash` (SHA256), `perceptual_hash`, `status` (job states)

2. `app/db.py` - Database setup
   - Async SQLAlchemy engine configuration
   - Session management with `get_db()` dependency
   - Settings from environment variables

3. `app/storage.py` - Storage adapter
   - Local filesystem implementation
   - S3 adapter hooks (commented out)
   - File path structure: `originals/` and `renditions/`

**Key Concepts:**
- Async SQLAlchemy with `asyncpg` (PostgreSQL) or `aiosqlite` (SQLite)
- Idempotency via content hash (SHA256 + perceptual hash)
- Storage abstraction for swapping to S3

**Practice:**
- Draw the database schema relationships
- Trace a file upload through storage.save_original()

### Afternoon (3-4 hours): Hashing & Image Processing

**Files to Read:**
1. `app/hashing.py` - Content hashing
   - `compute_sha256()` - Exact content hash
   - `compute_perceptual_hash()` - Image similarity hash
   - `hash_distance()` - Hamming distance for comparison

2. `app/utils.py` - Image operations
   - `create_rendition()` - Preset-based resizing
   - `save_rendition()` - JPEG encoding with quality
   - `compute_psnr()` - Quality metric (PSNR in dB)
   - `compare_images()` - Combined quality comparison

**Key Concepts:**
- SHA256 for exact duplicate detection
- Perceptual hash (average hash) for similar image detection
- PSNR > 30 dB = good quality
- Rendition presets: thumb (100×100), card (400×400), zoom (max 1200px)

**Practice:**
- Run `pytest tests/test_hashing.py -v`
- Understand why identical images have hash_distance = 0

### Evening (2 hours): API Endpoints

**Files to Read:**
1. `app/api/upload.py` - Upload endpoint
   - File validation
   - Content hash computation
   - Idempotency check (existing asset)
   - Job creation

2. `app/api/retrieve.py` - Asset/rendition retrieval
   - Asset metadata endpoint
   - Rendition file serving

3. `app/api/compare.py` - Quality comparison
   - PSNR computation
   - Perceptual hash distance
   - Per-preset comparison

**Practice:**
- Test upload with curl (see README)
- Verify idempotency: upload same image twice

---

## Day 2: Workers, Reliability & Deployment

### Morning (3-4 hours): Worker & Queue System

**Files to Read:**
1. `app/workers.py` - Async worker
   - Redis queue integration (`worker_loop_redis()`)
   - Fallback database polling (`worker_loop_fallback()`)
   - Job processing with retry logic
   - Exponential backoff: 2^retry_count seconds

2. `app/main.py` - FastAPI app
   - Startup/shutdown events
   - Health check endpoint
   - Router registration

**Key Concepts:**
- Redis queue: `LPUSH` to add, `BRPOP` to consume
- Fallback mode: Poll database for `status='pending'` jobs
- Retry logic: max 3 attempts, exponential backoff
- Poison jobs: Move permanently failed jobs to `poison_jobs` table

**Practice:**
- Run worker locally: `bash app/scripts/run_worker.sh`
- Upload image and watch worker process it
- Check job status in database

### Afternoon (3-4 hours): Reliability & Testing

**Files to Read:**
1. `app/api/purge.py` - Safe deletion
   - Dry-run mode
   - Age-based filtering (PURGE_DAYS)
   - Unreferenced rendition cleanup

2. `app/api/metrics.py` - Usage statistics
   - Tenant-level aggregation
   - Asset/rendition counts
   - Total bytes calculation

3. `tests/` - Test suite
   - `test_hashing.py` - Hash computation tests
   - `test_idempotency.py` - Duplicate upload behavior
   - `test_api_endpoints.py` - API integration tests

**Key Concepts:**
- Safe purge: Only delete unreferenced renditions older than N days
- Metrics aggregation: Count assets, renditions, total bytes per tenant
- Test coverage: Hashing, idempotency, API endpoints

**Practice:**
- Run full test suite: `pytest -q`
- Test purge with dry-run: `curl -X POST "http://localhost:10000/purge/?dry_run=true"`
- Check metrics: `curl "http://localhost:10000/metrics"`

### Evening (2 hours): Deployment & Review

**Files to Read:**
1. `render/render.md` - Render deployment steps
2. `app/scripts/seed_corpus.py` - Test data seeding
3. `README.md` - Deployment checklist

**Key Concepts:**
- Render Web Service: Build + Start commands
- Background Worker: Separate service for job processing
- Environment variables: DATABASE_URL, REDIS_URL, STORAGE_PATH
- Health check: `/healthz` endpoint

**Practice:**
- Review Render deployment steps
- Understand non-Docker deployment (pip install, uvicorn)
- Trace a request from upload → job → rendition → retrieve

---

## Quick Exam Questions

### 1. Idempotency
**Q:** How does the system ensure idempotent uploads?  
**A:** Computes SHA256 hash of image bytes. If an asset with the same `content_hash` exists, returns existing asset instead of creating a duplicate.

**Code:** `app/api/upload.py` lines 45-55

### 2. Retry & Backoff
**Q:** What happens when a job fails?  
**A:** Job retries up to 3 times with exponential backoff (2, 4, 8 seconds). After max retries, moved to `poison_jobs` table.

**Code:** `app/workers.py` lines 80-105

### 3. Queue Isolation
**Q:** How does the worker handle Redis unavailability?  
**A:** Falls back to database polling: queries for `status='pending'` jobs every 2 seconds.

**Code:** `app/workers.py` lines 120-135

### 4. Storage Tradeoffs
**Q:** What are the tradeoffs between local filesystem and S3?  
**A:** 
- Local: Fast, simple, but not scalable, no redundancy
- S3: Scalable, redundant, but requires network calls, costs per request

**Code:** `app/storage.py` - Local adapter with S3 hooks commented

### 5. Compare Endpoint Metrics
**Q:** What metrics does `/compare` return?  
**A:** 
- File size (bytes)
- PSNR (Peak Signal-to-Noise Ratio in dB)
- Perceptual hash distance (Hamming distance)

**Code:** `app/api/compare.py` lines 77-105

### 6. Rendition Presets
**Q:** What are the three rendition presets and their dimensions?  
**A:** 
- `thumb`: 100×100 fit
- `card`: 400×400 fit  
- `zoom`: Max 1200px on longer edge

**Code:** `app/utils.py` lines 7-12

### 7. Database Models
**Q:** What is the relationship between Asset, Rendition, and Job?  
**A:** 
- Asset has many Renditions (one-to-many)
- Asset has many Jobs (one-to-many)
- Job references Asset via `asset_id` foreign key

**Code:** `app/models.py`

### 8. Quality Metrics
**Q:** What does PSNR > 30 dB indicate?  
**A:** Good image quality. PSNR measures similarity between original and processed image. Higher = better quality.

**Code:** `app/utils.py` lines 50-70

---

## Study Tips

1. **Run the code:** Don't just read - execute and trace through with a debugger
2. **Test idempotency:** Upload the same image twice, verify it returns existing asset
3. **Watch the worker:** Monitor job processing in real-time
4. **Check the database:** Inspect tables after operations to understand data flow
5. **Review error handling:** Understand retry logic and poison job creation

## Exam Focus Areas

- **Idempotency:** Content hash computation and duplicate detection
- **Async patterns:** SQLAlchemy async, asyncio, Redis async
- **Reliability:** Retry with exponential backoff, poison jobs
- **Storage:** Local vs S3 tradeoffs, file path management
- **Quality metrics:** PSNR calculation, perceptual hash distance
- **Deployment:** Render non-Docker setup, environment variables

Good luck! 🚀

