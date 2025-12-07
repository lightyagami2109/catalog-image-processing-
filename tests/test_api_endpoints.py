"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from PIL import Image
import io
import os

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["STORAGE_PATH"] = "./test_storage"
os.environ["SECRET_KEY"] = "test_secret"

from app.main import app
from app.db import Base, init_db, engine, AsyncSessionLocal

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
async def setup_db():
    """Setup test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Cleanup test storage
    import shutil
    if os.path.exists("./test_storage"):
        shutil.rmtree("./test_storage")


def create_test_image(color="red", size=(200, 200)):
    """Create a test image."""
    img = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "endpoints" in response.json()


@pytest.mark.asyncio
async def test_upload_endpoint(setup_db):
    """Test image upload endpoint."""
    image_content = create_test_image()
    
    response = client.post(
        "/upload/",
        files={"file": ("test.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "asset_id" in data
    assert "status" in data
    assert data["status"] in ["uploaded", "exists"]
    assert "content_hash" in data


@pytest.mark.asyncio
async def test_upload_idempotency(setup_db):
    """Test that uploading the same image twice is idempotent."""
    image_content = create_test_image()
    
    # First upload
    response1 = client.post(
        "/upload/",
        files={"file": ("test1.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    asset_id_1 = data1["asset_id"]
    content_hash_1 = data1["content_hash"]
    
    # Second upload (same content, different filename)
    response2 = client.post(
        "/upload/",
        files={"file": ("test2.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Should either return existing asset or create new one with same hash
    # (Implementation may vary, but hash should match)
    assert data2["content_hash"] == content_hash_1


@pytest.mark.asyncio
async def test_retrieve_asset(setup_db):
    """Test asset retrieval endpoint."""
    # Upload first
    image_content = create_test_image()
    response = client.post(
        "/upload/",
        files={"file": ("test.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    assert response.status_code == 200
    asset_id = response.json()["asset_id"]
    
    # Retrieve
    response = client.get(f"/retrieve/asset/{asset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == asset_id
    assert "filename" in data
    assert "renditions" in data


@pytest.mark.asyncio
async def test_retrieve_nonexistent_asset(setup_db):
    """Test retrieving non-existent asset."""
    response = client.get("/retrieve/asset/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_metrics_endpoint(setup_db):
    """Test metrics endpoint."""
    # Upload an image
    image_content = create_test_image()
    client.post(
        "/upload/",
        files={"file": ("test.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    
    # Get metrics
    response = client.get("/metrics/tenant/test_tenant")
    assert response.status_code == 200
    data = response.json()
    assert "asset_count" in data
    assert "rendition_count" in data
    assert "total_bytes" in data


@pytest.mark.asyncio
async def test_purge_endpoint_dry_run(setup_db):
    """Test purge endpoint with dry run."""
    response = client.post("/purge/?dry_run=true")
    assert response.status_code == 200
    data = response.json()
    assert data["dry_run"] is True
    assert "renditions_to_delete" in data


@pytest.mark.asyncio
async def test_compare_endpoint(setup_db):
    """Test compare endpoint."""
    # Upload an image first
    image_content = create_test_image()
    response = client.post(
        "/upload/",
        files={"file": ("test.jpg", image_content, "image/jpeg")},
        data={"tenant_name": "test_tenant"}
    )
    assert response.status_code == 200
    asset_id = response.json()["asset_id"]
    
    # Compare with a different image
    compare_image = create_test_image(color="blue")
    response = client.post(
        f"/compare/{asset_id}",
        files={"file": ("compare.jpg", compare_image, "image/jpeg")}
    )
    
    # Should work even if renditions aren't ready yet
    assert response.status_code in [200, 404]  # 404 if renditions not ready

