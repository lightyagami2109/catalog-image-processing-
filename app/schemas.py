from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RenditionResponse(BaseModel):
    preset: str
    file_path: str
    width: int
    height: int
    bytes: int
    quality: Optional[int] = None

class AssetResponse(BaseModel):
    asset_id: int
    filename: str
    content_hash: str
    width: int
    height: int
    bytes: int
    color_space: Optional[str] = None
    created_at: datetime
    renditions: List[RenditionResponse]
