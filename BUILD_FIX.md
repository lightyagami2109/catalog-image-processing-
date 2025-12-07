# Fix for Render Build Errors

## Problem
Build fails with "Getting requirements to build wheel" error. This happens because Pillow and imagehash need system dependencies.

## Solution: Update Build Command

In your Render Web Service settings, **change the Build Command** to:

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

This will:
1. Upgrade pip, setuptools, and wheel first
2. Then install all dependencies

## Alternative: If Still Failing

If the above doesn't work, use this more robust build command:

```bash
pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install -r requirements.txt --no-cache-dir
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

