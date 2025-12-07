# Local PostgreSQL Setup Guide

This guide will help you connect the application to your local PostgreSQL database.

## Prerequisites

- PostgreSQL installed and running
- PostgreSQL user credentials (default: `postgres` user)
- Python package `asyncpg` installed (included in requirements.txt)

## Step 1: Check PostgreSQL is Running

### On macOS:
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Or start it if not running
brew services start postgresql
```

### On Linux:
```bash
# Check status
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### On Windows:
- Check Services (services.msc) for "PostgreSQL" service
- Or use pgAdmin to verify connection

## Step 2: Create Database

### Option A: Using Python Script (Recommended)

```bash
python app/scripts/setup_postgres.py
```

This will:
1. Prompt for your PostgreSQL password
2. Create the database `catalogdb` (if it doesn't exist)
3. Initialize all tables
4. Show you the DATABASE_URL to add to `.env`

### Option B: Using Bash Script

```bash
# Set your PostgreSQL password
export DB_PASSWORD=your_password

# Run setup script
bash app/scripts/setup_postgres.sh
```

### Option C: Manual Setup

1. **Connect to PostgreSQL:**
   ```bash
   psql -U postgres
   ```

2. **Create database:**
   ```sql
   CREATE DATABASE catalogdb;
   ```

3. **Exit psql:**
   ```sql
   \q
   ```

4. **Initialize tables:**
   ```bash
   python -c "from app.db import init_db; import asyncio; asyncio.run(init_db())"
   ```

## Step 3: Configure .env File

Create or update your `.env` file:

```bash
cp example.env .env
```

Edit `.env` and update the `DATABASE_URL`:

```env
# Replace with your actual credentials
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/catalogdb
```

**Format breakdown:**
- `postgresql+asyncpg://` - Protocol (asyncpg driver)
- `postgres` - Username
- `your_password` - Your PostgreSQL password
- `localhost` - Host (or `127.0.0.1`)
- `5432` - Port (default PostgreSQL port)
- `catalogdb` - Database name

## Step 4: Test Connection

### Test 1: Initialize Database
```bash
python -c "from app.db import init_db; import asyncio; asyncio.run(init_db())"
```

You should see:
```
✓ Database tables created
```

### Test 2: Start Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

Check logs for:
```
✓ Database tables created
✓ Application started
```

### Test 3: Check Database
```bash
psql -U postgres -d catalogdb -c "\dt"
```

You should see tables:
- tenants
- assets
- renditions
- jobs
- poison_jobs
- tenant_metrics

## Common Issues

### Issue 1: "password authentication failed"

**Solution:**
- Verify password in `.env` file
- Try resetting PostgreSQL password:
  ```bash
  psql -U postgres -c "ALTER USER postgres PASSWORD 'new_password';"
  ```

### Issue 2: "could not connect to server"

**Solution:**
- Check PostgreSQL is running:
  ```bash
  # macOS
  brew services list | grep postgresql
  
  # Linux
  sudo systemctl status postgresql
  ```
- Verify port (default is 5432)
- Check if PostgreSQL is listening on localhost:
  ```bash
  lsof -i :5432
  ```

### Issue 3: "database does not exist"

**Solution:**
- Create database manually:
  ```sql
  psql -U postgres -c "CREATE DATABASE catalogdb;"
  ```
- Or run the setup script again

### Issue 4: "role does not exist"

**Solution:**
- Create user/role:
  ```sql
  psql -U postgres -c "CREATE USER postgres WITH PASSWORD 'password';"
  psql -U postgres -c "ALTER USER postgres CREATEDB;"
  ```

### Issue 5: "asyncpg module not found"

**Solution:**
```bash
pip install -r requirements.txt
```

## Switching Between SQLite and PostgreSQL

### Use PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/catalogdb
```

### Use SQLite (fallback):
```env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
```

The application automatically detects which database to use based on the URL.

## Verify Tables Created

```bash
psql -U postgres -d catalogdb -c "\d+ assets"
psql -U postgres -d catalogdb -c "\d+ renditions"
psql -U postgres -d catalogdb -c "\d+ jobs"
```

## Next Steps

Once PostgreSQL is connected:
1. Start the FastAPI server: `uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload`
2. Start the worker: `bash app/scripts/run_worker.sh`
3. Seed test data: `python app/scripts/seed_corpus.py`

## Production Notes

For production (Render deployment):
- Use the same `postgresql+asyncpg://` format
- Use Render's Internal Database URL (convert to asyncpg format)
- Never commit `.env` file with real passwords to git

