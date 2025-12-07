"""Tests for idempotency behavior."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from PIL import Image
import io

from app.models import Asset, Tenant
from app.db import Base, init_db
from app.hashing import compute_content_hash
from app.storage import StorageAdapter

# Test database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session():
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_image():
    """Create a test image."""
    img = Image.new("RGB", (200, 200), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return img, buffer.getvalue()


@pytest.mark.asyncio
async def test_idempotent_upload(db_session, test_image):
    """Test that uploading the same image twice returns existing asset."""
    from sqlalchemy import select
    
    img, content = test_image
    sha256, perceptual = compute_content_hash(img, content)
    
    # Create tenant
    tenant = Tenant(name="test_tenant")
    db_session.add(tenant)
    await db_session.flush()
    
    # Create first asset
    asset1 = Asset(
        tenant_id=tenant.id,
        filename="test.jpg",
        content_hash=sha256,
        perceptual_hash=perceptual,
        original_bytes=len(content),
        width=img.width,
        height=img.height,
        color_space=img.mode
    )
    db_session.add(asset1)
    await db_session.commit()
    
    # Try to create second asset with same content hash
    result = await db_session.execute(
        select(Asset).where(Asset.content_hash == sha256)
    )
    existing_asset = result.scalar_one_or_none()
    
    # Should find existing asset
    assert existing_asset is not None
    assert existing_asset.id == asset1.id
    assert existing_asset.content_hash == sha256


@pytest.mark.asyncio
async def test_different_images_different_hashes(db_session, test_image):
    """Test that different images produce different hashes."""
    from sqlalchemy import select
    
    img1, content1 = test_image
    sha256_1, perceptual_1 = compute_content_hash(img1, content1)
    
    # Create different image
    img2 = Image.new("RGB", (200, 200), color="blue")
    buffer2 = io.BytesIO()
    img2.save(buffer2, format="JPEG")
    content2 = buffer2.getvalue()
    sha256_2, perceptual_2 = compute_content_hash(img2, content2)
    
    # Hashes should be different
    assert sha256_1 != sha256_2
    assert perceptual_1 != perceptual_2
    
    # Create tenant
    tenant = Tenant(name="test_tenant")
    db_session.add(tenant)
    await db_session.flush()
    
    # Create both assets
    asset1 = Asset(
        tenant_id=tenant.id,
        filename="test1.jpg",
        content_hash=sha256_1,
        perceptual_hash=perceptual_1,
        original_bytes=len(content1),
        width=img1.width,
        height=img1.height,
        color_space=img1.mode
    )
    asset2 = Asset(
        tenant_id=tenant.id,
        filename="test2.jpg",
        content_hash=sha256_2,
        perceptual_hash=perceptual_2,
        original_bytes=len(content2),
        width=img2.width,
        height=img2.height,
        color_space=img2.mode
    )
    db_session.add(asset1)
    db_session.add(asset2)
    await db_session.commit()
    
    # Both should exist
    result = await db_session.execute(select(Asset))
    assets = result.scalars().all()
    assert len(assets) == 2

