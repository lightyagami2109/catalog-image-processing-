# VSCode Setup Guide

## One-Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Environment File
```bash
cp example.env .env
```

Edit `.env` if needed (defaults work for local dev).

### 3. Initialize Database
```bash
python -c "from app.db import init_db; import asyncio; asyncio.run(init_db())"
```

This creates the SQLite database and tables.

## Running in VSCode

### Option 1: Two Terminal Panes (Recommended)

**Terminal 1 - FastAPI Server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

**Terminal 2 - Worker:**
```bash
bash app/scripts/run_worker.sh
```

### Option 2: VSCode Tasks (Automated)

Create `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start FastAPI Server",
            "type": "shell",
            "command": "uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload",
            "problemMatcher": [],
            "isBackground": true,
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Start Worker",
            "type": "shell",
            "command": "bash app/scripts/run_worker.sh",
            "problemMatcher": [],
            "isBackground": true,
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Start All",
            "dependsOn": ["Start FastAPI Server", "Start Worker"],
            "problemMatcher": []
        }
    ]
}
```

Then press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → "Tasks: Run Task" → "Start All"

## Testing

Once both are running, test with:

```bash
python app/scripts/seed_corpus.py
```

Or manually:
```bash
curl -X POST "http://localhost:10000/upload/" \
  -F "file=@your-image.jpg" \
  -F "tenant_name=test"
```

## VSCode Terminal Tips

- Split terminal: Click the `+` dropdown → "Split Terminal"
- Or use `Ctrl+Shift+` (backtick) to open new terminal
- Keep both terminals visible side-by-side

