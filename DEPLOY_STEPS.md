# Step-by-Step Render Deployment (No Redis, No Background Worker)

## Prerequisites
- Render account (sign up at https://render.com)
- Your code is on GitHub (already done ✅)

---

## Step 1: Create PostgreSQL Database

1. Go to **Render Dashboard** → Click **New** → **PostgreSQL**
2. Configure:
   - **Name:** `catalog-pipeline-db` (or any name you like)
   - **Database:** `catalogdb` (or any name)
   - **Region:** Choose closest to you (e.g., `Oregon (US West)`)
   - **PostgreSQL Version:** Use default (latest)
3. Click **Create Database**
4. Wait for it to be created (takes ~1 minute)

### Get Database Connection String

1. Once created, click on your database
2. Go to **Connections** tab
3. Find **Internal Database URL** (looks like: `postgresql://user:password@host:port/dbname`)
4. **IMPORTANT:** Copy it and change `postgresql://` to `postgresql+asyncpg://`
   - Example: `postgresql+asyncpg://user:password@host:port/dbname`
5. **Save this URL** - you'll need it in Step 3

---

## Step 2: Create Web Service

1. In Render Dashboard, click **New** → **Web Service**
2. **Connect Repository:**
   - Click **Connect account** if not connected
   - Select **GitHub**
   - Authorize Render
   - Select your repository: `lightyagami2109/catalog-image-processing-`
   - Click **Connect**
3. **Configure Service:**
   - **Name:** `catalog-image-pipeline` (or any name)
   - **Region:** Same as your PostgreSQL (e.g., `Oregon (US West)`)
   - **Branch:** `main` (or `master`)
   - **Root Directory:** Leave empty (or `./`)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install --upgrade pip setuptools wheel && pip install --only-binary :all: pillow pydantic-core asyncpg && pip install -r requirements.txt --prefer-binary --no-cache-dir`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`
   - **Auto-Deploy:** `Yes` (optional - auto-deploys on git push)
4. **DON'T click Create yet!** We need to add environment variables first.

---

## Step 3: Add Environment Variables

**Before clicking Create**, scroll down to **Environment Variables** section:

1. Click **Add Environment Variable** for each:

   **Variable 1:**
   - **Key:** `DATABASE_URL`
   - **Value:** Paste your database URL from Step 1 (with `+asyncpg`)
   - Example: `postgresql+asyncpg://user:pass@host:port/dbname`

   **Variable 2:**
   - **Key:** `STORAGE_PATH`
   - **Value:** `/mnt/storage`

   **Variable 3:**
   - **Key:** `SECRET_KEY`
   - **Value:** Generate a random string:
     - On Mac/Linux: Run `openssl rand -hex 32` in terminal
     - Or use: `python -c "import secrets; print(secrets.token_hex(32))"`
     - Example output: `a1b2c3d4e5f6...` (64 characters)

   **Variable 4:**
   - **Key:** `PURGE_DAYS`
   - **Value:** `30`

   **Variable 5:**
   - **Key:** `ENABLE_WORKER`
   - **Value:** `true`

2. **DO NOT add REDIS_URL** - we're not using Redis

3. Now click **Create Web Service**

---

## Step 4: Wait for Deployment

1. Render will start building your service (takes 2-5 minutes)
2. Watch the **Logs** tab to see progress
3. Look for these success messages:
   ```
   ✓ Database tables created
   ⚠ Redis not configured, using fallback queue
   ✓ Worker started as background task
   ✓ Application started
   ```

---

## Step 5: Verify Deployment

1. Once deployed, you'll see a URL like: `https://catalog-image-pipeline.onrender.com`
2. Test health check:
   ```bash
   curl https://your-service.onrender.com/healthz
   ```
   Should return: `{"status": "healthy", "service": "catalog-image-pipeline"}`

3. Or open in browser: `https://your-service.onrender.com/healthz`

---

## Step 6: Seed Test Data

1. In Render Dashboard, open your Web Service
2. Click **Shell** tab (at the top)
3. Run:
   ```bash
   python app/scripts/seed_corpus.py https://your-service.onrender.com
   ```
   Replace `your-service.onrender.com` with your actual service URL

4. You should see:
   ```
   Seeding test corpus...
   Uploading red_square.jpg...
     ✓ Uploaded: asset_id=1, status=uploaded
   ...
   ✓ Seed corpus completed!
   ```

---

## Step 7: Test Endpoints

Test your API:

```bash
# Get metrics
curl https://your-service.onrender.com/metrics

# Get specific tenant metrics
curl https://your-service.onrender.com/metrics/tenant/test_tenant

# Get asset details
curl https://your-service.onrender.com/retrieve/asset/1
```

---

## ✅ You're Done!

Your pipeline is now deployed and working!

### What's Running:
- ✅ FastAPI Web Service (handles API requests)
- ✅ Worker (processes image jobs in background - same process)
- ✅ PostgreSQL Database (stores all data)

### What's NOT Running:
- ❌ Redis (not needed - using database queue)
- ❌ Separate Background Worker (integrated into Web Service)

---

## Troubleshooting

### Database Connection Error
- Check `DATABASE_URL` has `+asyncpg` (not just `postgresql://`)
- Make sure you're using **Internal Database URL** (not Public)
- Verify database and service are in same region

### Worker Not Processing
- Check logs for: `✓ Worker started as background task`
- Make sure `ENABLE_WORKER=true` is set
- Upload an image and check logs for processing messages

### Health Check Failing
- Check logs for errors
- Verify all environment variables are set correctly
- Make sure database is running

---

## Quick Checklist

- [ ] PostgreSQL database created
- [ ] Database URL copied and converted to `postgresql+asyncpg://`
- [ ] Web Service created
- [ ] All 5 environment variables added:
  - [ ] `DATABASE_URL`
  - [ ] `STORAGE_PATH=/mnt/storage`
  - [ ] `SECRET_KEY=<random-string>`
  - [ ] `PURGE_DAYS=30`
  - [ ] `ENABLE_WORKER=true`
- [ ] Service deployed successfully
- [ ] Health check passing
- [ ] Test data seeded
- [ ] Endpoints working

---

## Next Steps

- Monitor logs in Render Dashboard
- Upload images via API
- Check metrics endpoint
- Customize as needed

Good luck! 🚀

