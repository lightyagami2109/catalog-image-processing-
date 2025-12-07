# Render Deployment Guide (Non-Docker)

This guide provides step-by-step instructions for deploying the Catalog Image Processing Pipeline to Render without Docker.

## Prerequisites

- Render account (sign up at https://render.com)
- Git repository with the code pushed
- Basic understanding of environment variables

## Step 1: Create Web Service

1. Log in to Render Dashboard
2. Click **New** → **Web Service**
3. Connect your repository (GitHub/GitLab/Bitbucket)
4. Select the repository and branch

### Web Service Configuration

**Name:** `catalog-image-pipeline` (or your choice)

**Environment:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Health Check Path:** `/healthz`

**Auto-Deploy:** `Yes` (optional, for automatic deployments on git push)

Click **Create Web Service**.

## Step 2: Provision PostgreSQL Database

1. In Render Dashboard, click **New** → **PostgreSQL**
2. Configure:
   - **Name:** `catalog-pipeline-db`
   - **Database:** `catalogdb` (or your choice)
   - **User:** Auto-generated
   - **Region:** Same as Web Service
3. Click **Create Database**

### Get Database URL

1. Open the PostgreSQL instance
2. Go to **Connections** tab
3. Copy the **Internal Database URL** (format: `postgresql://user:pass@host:port/dbname`)

### Update for Async

Convert the URL to asyncpg format:
```
postgresql+asyncpg://user:pass@host:port/dbname
```

## Step 3: Add Environment Variables to Web Service

In your Web Service settings, go to **Environment** section and add:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
STORAGE_PATH=/mnt/storage
SECRET_KEY=<generate-a-random-string-here>
PURGE_DAYS=30
```

**Note:** Replace `<generate-a-random-string-here>` with a secure random string (e.g., use `openssl rand -hex 32`)

## Step 4: (Optional) Provision Redis

1. Click **New** → **Redis**
2. Configure:
   - **Name:** `catalog-pipeline-redis`
   - **Region:** Same as Web Service
3. Click **Create Redis**

### Get Redis URL

1. Open the Redis instance
2. Go to **Connections** tab
3. Copy the **Internal Redis URL** (format: `redis://:password@host:port`)

### Add to Environment Variables

Add to Web Service environment:
```
REDIS_URL=redis://:password@host:port
```

**Note:** If Redis is not set, the worker will use database polling fallback.

## Step 5: Create Background Worker

1. Click **New** → **Background Worker**
2. Connect the same repository
3. Configure:

**Name:** `catalog-image-worker`

**Start Command:**
```bash
bash app/scripts/run_worker.sh
```

**Environment Variables:** Copy all from Web Service:
- `DATABASE_URL`
- `REDIS_URL` (if set)
- `STORAGE_PATH`
- `SECRET_KEY`
- `PURGE_DAYS`

Click **Create Background Worker**.

## Step 6: Deploy and Verify

### Initial Deployment

1. Both services will start deploying automatically
2. Monitor logs in Render Dashboard

### Check Web Service Logs

Look for:
```
✓ Database tables created
✓ Redis connected
✓ Application started
```

If Redis is not configured, you'll see:
```
⚠ Redis not configured, using fallback queue
```

### Check Worker Logs

Look for:
```
Starting image processing worker...
✓ Connected to Redis
```
or
```
Using fallback database queue
```

### Test Health Check

```bash
curl https://your-service.onrender.com/healthz
```

Expected response:
```json
{"status": "healthy", "service": "catalog-image-pipeline"}
```

## Step 7: Seed Test Data

### Option 1: From Render Shell

1. Open Web Service
2. Go to **Shell** tab
3. Run:
```bash
python app/scripts/seed_corpus.py https://your-service.onrender.com
```

### Option 2: From Local Machine

```bash
python app/scripts/seed_corpus.py https://your-service.onrender.com
```

### Verify

```bash
# Check metrics
curl https://your-service.onrender.com/metrics

# Check asset
curl https://your-service.onrender.com/retrieve/asset/1
```

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
- Check that PostgreSQL is in the same region as Web Service
- Use Internal Database URL (not Public URL)

### Worker Not Processing Jobs

- Check worker logs for errors
- Verify `DATABASE_URL` matches Web Service
- If using Redis, verify `REDIS_URL` is correct
- Check that jobs are being created (query database)

### Storage Issues

- Render provides `/mnt/storage` for persistent disk
- Ensure `STORAGE_PATH=/mnt/storage` is set
- Check file permissions

### Health Check Failing

- Verify `/healthz` endpoint returns 200
- Check application logs for startup errors
- Ensure database connection is working

## Render Checklist

- [ ] Web Service created with correct build/start commands
- [ ] PostgreSQL database provisioned
- [ ] `DATABASE_URL` set (with `+asyncpg`)
- [ ] `STORAGE_PATH` set to `/mnt/storage`
- [ ] `SECRET_KEY` set (random string)
- [ ] `PURGE_DAYS` set (optional, defaults to 30)
- [ ] Redis provisioned (optional)
- [ ] `REDIS_URL` set (if using Redis)
- [ ] Background Worker created
- [ ] Worker environment variables match Web Service
- [ ] Health check passing (`/healthz`)
- [ ] Test data seeded
- [ ] Metrics endpoint working

## Cost Considerations

- **Web Service:** Free tier available (sleeps after inactivity)
- **PostgreSQL:** Free tier available (limited storage)
- **Redis:** Free tier available (limited memory)
- **Background Worker:** Free tier available (sleeps with Web Service)

For production, consider paid tiers for:
- Always-on services
- More storage/memory
- Better performance

## Next Steps

- Set up monitoring/alerting
- Configure custom domain
- Set up CI/CD for automatic deployments
- Review and optimize database queries
- Consider S3 for storage (see `app/storage.py`)

