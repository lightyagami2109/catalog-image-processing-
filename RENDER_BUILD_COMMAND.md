# Render Build Command - Final Fix (All Binary Wheels)

## Use This Build Command in Render

Copy and paste this **exact** command into Render's Build Command field:

```
pip install --upgrade pip setuptools wheel && pip install --only-binary :all: pillow pydantic-core asyncpg && pip install -r requirements.txt --prefer-binary --no-cache-dir
```

## What This Does

- `pip install --upgrade pip setuptools wheel` - Upgrades build tools
- `pip install --only-binary :all: pillow pydantic-core asyncpg` - Installs problematic packages from binary wheels ONLY (no compilation)
- `pip install -r requirements.txt --prefer-binary --no-cache-dir` - Installs rest with binary preference, no cache

## Why This Works

- Pillow, pydantic-core, and asyncpg all need compilation (C/Rust)
- Installing them from binary wheels avoids compilation errors
- Python 3.11 (specified in runtime.txt) has pre-built wheels for all these packages

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


## Important: Python Version

Make sure Render is using Python 3.11 (not 3.13). The `runtime.txt` file in the repo specifies this.

If Render still uses Python 3.13, add this to your Build Command at the very start:

```
python --version && pip install --upgrade pip setuptools wheel && pip install --only-binary :all: pillow pydantic-core asyncpg && pip install -r requirements.txt --prefer-binary --no-cache-dir
```

## If This Still Fails

Try this alternative (forces Python 3.11):

```
python3.11 -m pip install --upgrade pip setuptools wheel && python3.11 -m pip install --only-binary :all: pillow pydantic-core asyncpg && python3.11 -m pip install -r requirements.txt --prefer-binary --no-cache-dir
```

## Verify It Works

After deployment, check logs for:
```
Successfully installed pillow ...
Successfully installed fastapi ...
✓ Database tables created
✓ Application started
```

