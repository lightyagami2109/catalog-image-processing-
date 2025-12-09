import pytest
from app.schemas import AssetResponse, RenditionResponse
from datetime import datetime

def test_asset_response_schema():
    """Verify AssetResponse schema structure."""
    data = {
        "asset_id": 1,
        "filename": "test.jpg",
        "content_hash": "hash123",
        "width": 100,
        "height": 100,
        "bytes": 1024,
        "color_space": "RGB",
        "created_at": datetime.now(),
        "renditions": [
            {
                "preset": "thumb",
                "file_path": "path/to/thumb.jpg",
                "width": 50,
                "height": 50,
                "bytes": 512,
                "quality": 80
            }
        ]
    }
    asset = AssetResponse(**data)
    assert asset.asset_id == 1
    assert asset.filename == "test.jpg"
    assert len(asset.renditions) == 1
    assert asset.renditions[0].preset == "thumb"


