# Step-by-Step Render Deployment Guide

## Prerequisites
- GitHub account (free)
- Render account (sign up at https://render.com - free tier available)

---

## Step 1: Push Code to GitHub

### 1.1 Initialize Git (if not already done)
```bash
cd "/Users/anshmansingh/Desktop/ojt 4 tyr"
git init
git add .
git commit -m "Initial commit: Catalog Image Processing Pipeline"
```

### 1.2 Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `catalog-image-pipeline` (or your choice)
3. Make it **Public** (or Private if you have GitHub Pro)
4. **Don't** initialize with README (we already have one)
5. Click **Create repository**

### 1.3 Push to GitHub
GitHub will show you commands. Run these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/catalog-image-pipeline.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## Step 2: Create Render Account & Connect GitHub

### 2.1 Sign Up for Render
1. Go to https://render.com
2. Click **Get Started for Free**
3. Sign up with GitHub (recommended) or email

### 2.2 Connect GitHub Account
1. If you signed up with email, go to **Account Settings** → **Connected Accounts**
2. Click **Connect GitHub**
3. Authorize Render to access your repositories

---

## Step 3: Create PostgreSQL Database

### 3.1 Create Database
1. In Render Dashboard, click **New +** → **PostgreSQL**
2. Configure:
   - **Name:** `catalog-pipeline-db`
   - **Database:** `catalogdb`
   - **User:** (auto-generated)
   - **Region:** Choose closest to you (e.g., `Oregon (US West)`)
   - **PostgreSQL Version:** Latest (15 or 16)
   - **Plan:** Free (or paid if needed)
3. Click **Create Database**

### 3.2 Get Database URL
1. Wait for database to be created (~1 minute)
2. Click on the database name
3. Go to **Connections** tab
4. Copy the **Internal Database URL**
   - Format: `postgresql://user:password@host:port/dbname`
   - **Important:** We need to convert this for asyncpg

### 3.3 Convert to Async Format
Change `postgresql://` to `postgresql+asyncpg://`

Example:
- Original: `postgresql://user:pass@dpg-xxx-a.oregon-postgres.render.com:5432/catalogdb`
- Converted: `postgresql+asyncpg://user:pass@dpg-xxx-a.oregon-postgres.render.com:5432/catalogdb`

**Save this converted URL** - you'll need it in Step 5.

---

## Step 4: (Optional) Create Redis Instance

### 4.1 Create Redis
1. Click **New +** → **Redis**
2. Configure:
   - **Name:** `catalog-pipeline-redis`
   - **Region:** Same as PostgreSQL
   - **Plan:** Free (or paid)
3. Click **Create Redis**

### 4.2 Get Redis URL
1. Wait for Redis to be created
2. Click on Redis instance
3. Go to **Connections** tab
4. Copy the **Internal Redis URL**
   - Format: `redis://:password@host:port`

**Save this URL** - you'll need it in Step 5.

**Note:** If you skip Redis, the worker will use database polling (works fine for small scale).

---

## Step 5: Create Web Service

### 5.1 Create Web Service
1. In Render Dashboard, click **New +** → **Web Service**
2. Click **Connect account** if GitHub isn't connected
3. Select your repository: `catalog-image-pipeline`
4. Click **Connect**

### 5.2 Configure Web Service

**Basic Settings:**
- **Name:** `catalog-image-pipeline` (or your choice)
- **Region:** Same as PostgreSQL
- **Branch:** `main` (or your default branch)
- **Root Directory:** (leave empty)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Advanced Settings:**
- **Health Check Path:** `/healthz`
- **Auto-Deploy:** `Yes` (deploys on every git push)

### 5.3 Add Environment Variables

Click **Add Environment Variable** and add these one by one:

1. **DATABASE_URL**
   - Value: The converted asyncpg URL from Step 3.3
   - Example: `postgresql+asyncpg://user:pass@host:port/dbname`

2. **STORAGE_PATH**
   - Value: `/mnt/storage`
   - (Render provides persistent disk at this path)

3. **SECRET_KEY**
   - Value: Generate a random string
   - Run this locally: `openssl rand -hex 32`
   - Or use: `python -c "import secrets; print(secrets.token_hex(32))"`

4. **PURGE_DAYS**
   - Value: `30`

5. **REDIS_URL** (only if you created Redis in Step 4)
   - Value: The Redis URL from Step 4.2
   - Example: `redis://:password@host:port`

### 5.4 Create Web Service
Click **Create Web Service**

Render will start building and deploying. This takes 2-5 minutes.

---

## Step 6: Create Background Worker

### 6.1 Create Worker
1. Click **New +** → **Background Worker**
2. Select the same repository: `catalog-image-pipeline`
3. Click **Connect**

### 6.2 Configure Worker

**Basic Settings:**
- **Name:** `catalog-image-worker`
- **Region:** Same as Web Service
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `bash app/scripts/run_worker.sh`

### 6.3 Add Environment Variables

**Copy ALL environment variables from Web Service:**
- `DATABASE_URL` (same value)
- `REDIS_URL` (same value, if you set it)
- `STORAGE_PATH` (same value)
- `SECRET_KEY` (same value)
- `PURGE_DAYS` (same value)

**Important:** Worker needs the same database and Redis URLs to work!

### 6.4 Create Worker
Click **Create Background Worker**

---

## Step 7: Verify Deployment

### 7.1 Check Web Service Logs
1. Open your Web Service in Render
2. Go to **Logs** tab
3. Look for:
   ```
   ✓ Database tables created
   ✓ Redis connected
   ✓ Application started
   ```
   Or if no Redis:
   ```
   ⚠ Redis not configured, using fallback queue
   ```

### 7.2 Check Worker Logs
1. Open your Background Worker
2. Go to **Logs** tab
3. Look for:
   ```
   Starting image processing worker...
   ✓ Connected to Redis
   ```
   Or:
   ```
   Using fallback database queue
   ```

### 7.3 Test Health Check
Get your Web Service URL (format: `https://catalog-image-pipeline.onrender.com`)

Test in browser or terminal:
```bash
curl https://your-service-name.onrender.com/healthz
```

Expected response:
```json
{"status": "healthy", "service": "catalog-image-pipeline"}
```

### 7.4 Test API
```bash
# Get your service URL from Render dashboard
SERVICE_URL="https://your-service-name.onrender.com"

# Test root endpoint
curl $SERVICE_URL/

# Test metrics
curl $SERVICE_URL/metrics
```

---

## Step 8: Seed Test Data

### Option 1: Using Render Shell
1. Open Web Service in Render
2. Go to **Shell** tab
3. Run:
   ```bash
   python app/scripts/seed_corpus.py https://your-service-name.onrender.com
   ```

### Option 2: From Your Local Machine
```bash
python app/scripts/seed_corpus.py https://your-service-name.onrender.com
```

### Verify It Worked
```bash
curl https://your-service-name.onrender.com/metrics
```

You should see asset and rendition counts.

---

## Troubleshooting

### Database Connection Failed
- **Check:** `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
- **Check:** Using Internal Database URL (not Public URL)
- **Check:** Database is in same region as Web Service

### Worker Not Processing Jobs
- **Check:** Worker has same `DATABASE_URL` as Web Service
- **Check:** Worker logs for errors
- **Check:** Jobs are being created (query database or check logs)

### Build Failed
- **Check:** `requirements.txt` is in root directory
- **Check:** Python version (should be 3.11+)
- **Check:** Build logs for specific error

### Health Check Failing
- **Check:** `/healthz` endpoint exists in `app/main.py`
- **Check:** Application logs for startup errors
- **Check:** Database connection is working

### Storage Issues
- **Check:** `STORAGE_PATH=/mnt/storage` is set
- **Check:** Render provides `/mnt/storage` for persistent disk
- **Note:** Free tier has limited disk space

---

## Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] PostgreSQL database created
- [ ] Database URL converted to `postgresql+asyncpg://` format
- [ ] (Optional) Redis created
- [ ] Web Service created with correct build/start commands
- [ ] All environment variables added to Web Service
- [ ] Background Worker created
- [ ] All environment variables copied to Worker
- [ ] Both services deployed successfully
- [ ] Health check passing (`/healthz`)
- [ ] Test data seeded
- [ ] Metrics endpoint working

---

## Cost Notes

**Free Tier Includes:**
- Web Service (sleeps after 15 min inactivity)
- PostgreSQL (90 days free, then $7/month)
- Redis (30 days free, then $10/month)
- Background Worker (sleeps with Web Service)

**For Production:**
- Upgrade to paid plans for always-on services
- More storage and memory
- Better performance

---

## Next Steps After Deployment

1. **Set up custom domain** (optional)
2. **Configure monitoring/alerting**
3. **Set up CI/CD** (auto-deploy on git push - already enabled if you set Auto-Deploy)
4. **Review logs** regularly
5. **Monitor usage** in Render dashboard

---

## Need Help?

- Check Render logs for specific errors
- Review `render/render.md` for detailed technical notes
- Check `README.md` for API documentation

