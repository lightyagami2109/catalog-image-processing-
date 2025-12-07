# Render Free Tier Deployment (No Background Worker)

Since Render's Background Worker requires a paid plan, here's how to deploy using only the **free Web Service** tier.

## Solution: Run Worker in Same Process

The worker now runs as a background task in the same Web Service process. This works perfectly for the free tier!

## Updated Deployment Steps

### Step 1: Create Web Service (Same as Before)

1. Go to Render Dashboard
2. Click **New** → **Web Service**
3. Connect your repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/healthz`

### Step 2: Create PostgreSQL (Same as Before)

1. Click **New** → **PostgreSQL**
2. Copy **Internal Database URL**
3. Convert to: `postgresql+asyncpg://user:pass@host:port/dbname`

### Step 3: Add Environment Variables

Add to Web Service:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
STORAGE_PATH=/mnt/storage
SECRET_KEY=<generate-random-string>
PURGE_DAYS=30
ENABLE_WORKER=true
```

**Note:** `ENABLE_WORKER=true` starts the worker in the same process. Set to `false` if you want to disable it.

### Step 4: (Optional) Redis

If you want Redis (still optional):
1. Create Redis instance
2. Add: `REDIS_URL=redis://:password@host:port`

### Step 5: Deploy!

That's it! No separate Background Worker needed. The worker runs automatically in the same process.

## How It Works

- The FastAPI app starts the worker as a background `asyncio` task on startup
- Worker processes jobs from the database queue (or Redis if configured)
- Both API and worker run in the same process (free tier friendly!)

## Verify It's Working

1. Check logs - you should see:
   ```
   Starting image processing worker...
   Using fallback database queue (or ✓ Connected to Redis)
   ✓ Worker started as background task
   ✓ Application started
   ```

2. Upload an image via API
3. Check logs - you should see worker processing the job:
   ```
   ✓ Job 1 completed for asset 1
   ```

## Alternative: Run Worker Locally

If you prefer to keep worker separate (for development):

1. Deploy only the Web Service to Render
2. Run worker locally on your machine:
   ```bash
   bash app/scripts/run_worker.sh
   ```
3. Make sure your local `.env` points to Render's database:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@render-host:port/dbname
   ```

## Other Free Alternatives

If Render doesn't work for you:

### Railway.app
- Free tier includes both Web Service and Worker
- Similar setup to Render

### Fly.io
- Generous free tier
- Can deploy both services

### Heroku
- Free tier available (with limitations)
- Can use worker dynos

## Cost Comparison

| Service | Web Service | Background Worker | Total |
|---------|-------------|-------------------|-------|
| Render (Free) | ✅ Free | ❌ Paid | **Free** (with integrated worker) |
| Railway | ✅ Free | ✅ Free | Free |
| Fly.io | ✅ Free | ✅ Free | Free |

The integrated worker solution (Option 1) is the best for Render's free tier!

