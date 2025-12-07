# What to Do Next in Render

## ✅ After Creating Services - Verification Steps

### Step 1: Check Deployment Status

1. **Go to your Web Service** in Render Dashboard
2. **Check the status:**
   - Should show: **Live** (green)
   - If showing "Building" or "Deploying", wait for it to finish

### Step 2: Check Logs

1. Click on your **Web Service**
2. Go to **Logs** tab
3. **Look for these success messages:**
   ```
   Starting up...
   ✓ Database tables created
   ⚠ Redis not configured, using fallback queue
   Starting image processing worker...
   Using fallback database queue
   ✓ Worker started as background task
   ✓ Application started
   ```

4. **If you see errors:**
   - Database connection error → Check `DATABASE_URL` has `+asyncpg`
   - Import errors → Check all dependencies installed
   - Port errors → Should use `$PORT` (already set)

### Step 3: Test Health Check

1. **Get your service URL:**
   - In Web Service dashboard, you'll see: `https://your-service.onrender.com`
   - Copy this URL

2. **Test in browser:**
   - Go to: `https://your-service.onrender.com/healthz`
   - Should see: `{"status": "healthy", "service": "catalog-image-pipeline"}`

3. **Or test with curl:**
   ```bash
   curl https://your-service.onrender.com/healthz
   ```

### Step 4: Test Root Endpoint

1. Go to: `https://your-service.onrender.com/`
2. Should see API information with list of endpoints

### Step 5: Seed Test Data

1. **In Render Dashboard:**
   - Open your **Web Service**
   - Click **Shell** tab (at the top)

2. **Run seed script:**
   ```bash
   python app/scripts/seed_corpus.py https://your-service.onrender.com
   ```
   (Replace with your actual service URL)

3. **Expected output:**
   ```
   Seeding test corpus...
   Uploading red_square.jpg...
     ✓ Uploaded: asset_id=1, status=uploaded
   Uploading blue_rect.jpg...
     ✓ Uploaded: asset_id=2, status=uploaded
   Uploading green_large.jpg...
     ✓ Uploaded: asset_id=3, status=uploaded
   
   Waiting for processing...
   
   Checking renditions...
     Asset 1: 3 renditions
     Asset 2: 3 renditions
     Asset 3: 3 renditions
   
   Checking metrics...
     Tenant metrics:
       Assets: 3
       Renditions: 9
       Total bytes: ...
   
   ✓ Seed corpus completed!
   ```

### Step 6: Verify Worker is Processing

1. **Check logs** after seeding:
   - You should see: `✓ Job X completed for asset X`
   - This confirms worker is processing jobs

2. **If no processing:**
   - Check `ENABLE_WORKER=true` is set
   - Check logs for worker startup messages

### Step 7: Test API Endpoints

**From your local machine or Render Shell:**

```bash
# Get all metrics
curl https://your-service.onrender.com/metrics

# Get tenant metrics
curl https://your-service.onrender.com/metrics/tenant/test_tenant

# Get asset details
curl https://your-service.onrender.com/retrieve/asset/1

# Get rendition (download image)
curl https://your-service.onrender.com/retrieve/rendition/1/thumb -o thumb.jpg
```

### Step 8: Upload Your Own Image

**Using curl:**
```bash
curl -X POST "https://your-service.onrender.com/upload/" \
  -F "file=@/path/to/your/image.jpg" \
  -F "tenant_name=my_tenant"
```

**Using Python:**
```python
import requests

url = "https://your-service.onrender.com/upload/"
files = {"file": open("image.jpg", "rb")}
data = {"tenant_name": "my_tenant"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

## 🔍 Troubleshooting

### If Health Check Fails

1. **Check logs** for errors
2. **Verify environment variables:**
   - `DATABASE_URL` is correct
   - `DATABASE_URL` has `+asyncpg`
   - All 5 variables are set

### If Worker Not Processing

1. **Check logs** for: `✓ Worker started as background task`
2. **Verify:** `ENABLE_WORKER=true` is set
3. **Upload an image** and watch logs for processing

### If Database Connection Fails

1. **Check:** Using **Internal Database URL** (not Public)
2. **Check:** URL format is `postgresql+asyncpg://...`
3. **Check:** Database and service are in same region

### If Build Fails

1. **Check logs** for dependency errors
2. **Verify:** `requirements.txt` is correct
3. **Check:** Python version (should be 3.11+)

---

## 📊 Monitor Your Service

### View Logs
- **Real-time logs:** Web Service → Logs tab
- **Filter logs:** Use search box
- **Download logs:** Click download button

### Check Metrics
- **Service status:** Dashboard shows uptime
- **API metrics:** Use `/metrics` endpoint
- **Database:** PostgreSQL dashboard shows connections

### Set Up Alerts (Optional)
1. Go to Web Service → Settings
2. Add email for deployment notifications
3. Monitor for errors

---

## 🎯 Next Steps After Verification

1. **Customize:**
   - Change `PURGE_DAYS` if needed
   - Adjust rendition presets in `app/utils.py`
   - Add custom endpoints

2. **Production Ready:**
   - Set up custom domain (Render → Settings)
   - Enable HTTPS (automatic on Render)
   - Set up monitoring/alerting

3. **Scale (if needed):**
   - Upgrade to paid tier for always-on
   - Add more workers (if needed)
   - Consider S3 for storage

---

## ✅ Success Checklist

- [ ] Web Service is **Live** (green status)
- [ ] Logs show successful startup
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Test data seeded successfully
- [ ] Worker processing jobs (see logs)
- [ ] Metrics endpoint working
- [ ] Can upload and retrieve images
- [ ] All endpoints responding

---

## 🚀 You're All Set!

Once all checks pass, your pipeline is fully deployed and working!

Need help with any step? Check the logs or refer to `DEPLOY_STEPS.md` for detailed instructions.

