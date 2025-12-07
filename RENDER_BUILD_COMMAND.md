# Render Build Command - Final Fix

## Use This Build Command in Render

Copy and paste this **exact** command into Render's Build Command field:

```
pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install pillow --only-binary :all: && pip install pydantic-core --only-binary :all: && pip install -r requirements.txt --prefer-binary
```

## Step-by-Step Instructions

1. **Go to Render Dashboard**
2. **Open your Web Service**
3. **Click Settings tab**
4. **Scroll to "Build Command"**
5. **Delete the old command**
6. **Paste this new command:**
   ```
   pip install --upgrade pip && pip install pillow --only-binary :all: && pip install -r requirements.txt
   ```
7. **Click "Save Changes"**
8. **Go to "Manual Deploy" tab**
9. **Click "Deploy latest commit"**

## What This Does

- `pip install --upgrade pip` - Ensures latest pip
- `pip install --upgrade setuptools wheel` - Ensures build tools are latest
- `pip install pillow --only-binary :all:` - Installs Pillow from pre-built wheel (no compilation)
- `pip install pydantic-core --only-binary :all:` - Installs pydantic-core from pre-built wheel (no Rust compilation)
- `pip install -r requirements.txt --prefer-binary` - Installs all other packages, preferring binary wheels

## If This Still Fails

Try this alternative (simpler):

```
pip install --upgrade pip && pip install -r requirements.txt --prefer-binary --no-cache-dir
```

Or this more explicit version:

```
pip install --upgrade pip setuptools wheel && pip install pillow pydantic-core --only-binary :all: && pip install -r requirements.txt --prefer-binary
```

## Verify It Works

After deployment, check logs for:
```
Successfully installed pillow ...
Successfully installed fastapi ...
✓ Database tables created
✓ Application started
```

