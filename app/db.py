"""Database connection and session management."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pydantic_settings import BaseSettings

# Base class for SQLAlchemy models
Base = declarative_base()


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    redis_url: str = os.getenv("REDIS_URL", "")
    storage_path: str = os.getenv("STORAGE_PATH", "./storage")
    secret_key: str = os.getenv("SECRET_KEY", "change_me")
    purge_days: int = int(os.getenv("PURGE_DAYS", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields like PORT


settings = Settings()

# Create async engine
# For SQLite, use aiosqlite; for PostgreSQL, use asyncpg
# The URL format determines which driver to use:
# - sqlite+aiosqlite:///path/to/db.db
# - postgresql+asyncpg://user:pass@host:port/dbname
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (call after importing all models)."""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print(f"  Check your DATABASE_URL: {settings.database_url[:50]}...")
        raise


async def close_db():
    """Close database connections."""
    await engine.dispose()

