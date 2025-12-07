# Fix for Render Build Errors - Pillow Build Failure

## Problem
Build fails with "Failed to build 'pillow'" error. Pillow requires system libraries (libjpeg, zlib) that aren't available on Render by default.

## Solution: Use Pre-built Wheels

In your Render Web Service settings, **change the Build Command** to:

```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: pillow && pip install -r requirements.txt
```

This will:
1. Upgrade pip, setuptools, and wheel first
2. Install Pillow using pre-built wheels (no compilation needed)
3. Then install all other dependencies

## Alternative: If Still Failing

If the above doesn't work, try this command:

```bash
pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install pillow --only-binary :all: && pip install -r requirements.txt --no-cache-dir
```

Or use this simpler version:

```bash
pip install --upgrade pip && pip install -r requirements.txt --only-binary :all: --no-cache-dir
```

## Steps to Fix in Render

1. Go to your **Web Service** in Render Dashboard
2. Click **Settings** tab
3. Scroll to **Build Command**
4. Replace with:
   ```
   pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
   ```
5. Click **Save Changes**
6. Go to **Manual Deploy** → **Deploy latest commit**

## Why This Works

- `--upgrade pip` ensures latest pip version
- `setuptools` and `wheel` are build tools needed for compilation
- Installing them first ensures they're available when Pillow/imagehash build

## After Fix

Once deployed, check logs for:
```
Successfully installed ...
✓ Database tables created
✓ Application started
```

