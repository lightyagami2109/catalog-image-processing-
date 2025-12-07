"""Storage adapter for local filesystem with S3 hooks."""
import os
from pathlib import Path
from typing import Optional
from app.db import settings


class StorageAdapter:
    """Storage adapter for local filesystem. Includes hooks to swap to S3."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        # Create subdirectories for organization
        (self.base_path / "originals").mkdir(exist_ok=True)
        (self.base_path / "renditions").mkdir(exist_ok=True)
    
    def save_original(self, content: bytes, filename: str) -> str:
        """
        Save original image file.
        Returns: relative file path
        """
        file_path = self.base_path / "originals" / filename
        file_path.write_bytes(content)
        return str(file_path.relative_to(self.base_path))
    
    def save_rendition(self, content: bytes, preset: str, asset_id: int) -> str:
        """
        Save rendition file.
        Returns: relative file path
        """
        filename = f"{asset_id}_{preset}.jpg"
        file_path = self.base_path / "renditions" / filename
        file_path.write_bytes(content)
        return str(file_path.relative_to(self.base_path))
    
    def read_file(self, relative_path: str) -> bytes:
        """Read file from storage."""
        file_path = self.base_path / relative_path
        return file_path.read_bytes()
    
    def delete_file(self, relative_path: str) -> bool:
        """Delete file from storage. Returns True if deleted, False if not found."""
        file_path = self.base_path / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / relative_path).exists()


# S3 adapter hook (commented out - implement when needed)
"""
class S3StorageAdapter:
    \"\"\"S3 storage adapter - implement when needed.\"\"\"
    import boto3
    from botocore.exceptions import ClientError
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.s3_client = boto3.client("s3", region_name=region)
        self.bucket_name = bucket_name
    
    def save_original(self, content: bytes, filename: str) -> str:
        key = f"originals/{filename}"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
        return key
    
    def save_rendition(self, content: bytes, preset: str, asset_id: int) -> str:
        key = f"renditions/{asset_id}_{preset}.jpg"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
        return key
    
    def read_file(self, key: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()
    
    def delete_file(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def file_exists(self, key: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
"""

# Global storage instance
storage = StorageAdapter()

