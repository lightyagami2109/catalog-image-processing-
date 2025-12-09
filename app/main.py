"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

from app.db import init_db, close_db, settings
from app.api import upload, retrieve, compare, metrics, purge

# Create FastAPI app
app = FastAPI(
    title="Catalog Image Processing Pipeline",
    description="Async image processing pipeline with idempotency and renditions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(retrieve.router)
app.include_router(compare.router)
app.include_router(metrics.router)
app.include_router(purge.router)


# Background task for worker (runs in same process)
worker_task = None

async def run_worker_background():
    """Run worker in background task (for free tier - no separate worker service needed)."""
    from app.workers import main as worker_main
    try:
        # Skip init_db since it's already called in startup_event
        await worker_main(skip_init_db=True)
    except Exception as e:
        print(f"Worker error: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and check connections on startup."""
    print("Starting up...")
    
    # Initialize database
    await init_db()
    
    # Check Redis connection if available
    try:
        if settings.redis_url:
            import aioredis
            redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
            await redis.ping()
            await redis.close()
            print("✓ Redis connected")
        else:
            print("⚠ Redis not configured, using fallback queue")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}. Using fallback queue.")
    
    # Start worker as background task (only if ENABLE_WORKER env is not "false")
    # This allows running worker in same process for free tier
    if os.getenv("ENABLE_WORKER", "true").lower() != "false":
        global worker_task
        worker_task = asyncio.create_task(run_worker_background())
        print("✓ Worker started as background task")
    
    print("✓ Application started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Cancel worker task if running
    global worker_task
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    
    await close_db()
    print("Application shut down")


@app.get("/healthz")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy", "service": "catalog-image-pipeline"}




