"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

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
    
    print("✓ Application started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await close_db()
    print("Application shut down")


@app.get("/healthz")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy", "service": "catalog-image-pipeline"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Catalog Image Processing Pipeline",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "retrieve": "/retrieve/asset/{asset_id}",
            "compare": "/compare/{asset_id}",
            "metrics": "/metrics",
            "purge": "/purge"
        }
    }

