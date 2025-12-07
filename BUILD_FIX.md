# Fix for Render Build Errors - Pillow Build Failure

## Problem
Build fails with "Failed to build 'pillow'" error. Pillow requires system libraries (libjpeg, zlib) that aren't available on Render by default.

## Solution: Install Pillow First with Binary Wheels

In your Render Web Service settings, **change the Build Command** to:

```bash
pip install --upgrade pip setuptools wheel && pip install --upgrade pip && pip install pillow --only-binary :all: --no-cache-dir && pip install -r requirements.txt --no-cache-dir
```

**OR try this simpler version (recommended):**

```bash
pip install --upgrade pip && pip install pillow --only-binary :all: && pip install -r requirements.txt
```

## Alternative: If Still Failing - Use Latest Pillow

If the above doesn't work, try installing latest Pillow explicitly:

```bash
pip install --upgrade pip setuptools wheel && pip install --upgrade pillow --only-binary :all: && pip install -r requirements.txt --no-cache-dir
```

## Last Resort: Skip Pillow Build

If nothing works, try this (installs from PyPI wheels only):

```bash
pip install --upgrade pip && pip install -r requirements.txt --prefer-binary --no-cache-dir
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

