"""Purge endpoint for safe deletion of old renditions."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.db import get_db, settings
from app.models import Rendition, Asset
from app.storage import storage

router = APIRouter(prefix="/purge", tags=["purge"])


@router.post("/")
async def purge_renditions(
    dry_run: bool = Query(True, description="If true, only report what would be deleted"),
    days: int = Query(None, description="Purge renditions older than N days (defaults to PURGE_DAYS env)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Safely purge unreferenced renditions older than specified days.
    Only deletes renditions that are not referenced by any asset.
    """
    purge_days = days or settings.purge_days
    cutoff_date = datetime.utcnow() - timedelta(days=purge_days)
    
    # Find renditions older than cutoff that are not referenced
    # (In a real system, you'd check for references, but here we'll check if asset exists)
    result = await db.execute(
        select(Rendition).where(
            Rendition.created_at < cutoff_date
        )
    )
    old_renditions = result.scalars().all()
    
    # Filter to only unreferenced renditions (check if asset exists)
    to_delete = []
    for rendition in old_renditions:
        result = await db.execute(
            select(Asset).where(Asset.id == rendition.asset_id)
        )
        asset = result.scalar_one_or_none()
        
        # Only delete if asset doesn't exist (unreferenced)
        if not asset:
            to_delete.append(rendition)
    
    deleted_count = 0
    deleted_bytes = 0
    errors = []
    
    if not dry_run:
        for rendition in to_delete:
            try:
                # Delete file from storage
                if storage.delete_file(rendition.file_path):
                    deleted_bytes += rendition.bytes
                
                # Delete database record
                await db.delete(rendition)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Error deleting rendition {rendition.id}: {str(e)}")
        
        await db.commit()
    else:
        # Dry run - just calculate
        deleted_count = len(to_delete)
        deleted_bytes = sum(r.bytes for r in to_delete)
    
    return {
        "dry_run": dry_run,
        "purge_days": purge_days,
        "cutoff_date": cutoff_date.isoformat(),
        "renditions_found": len(old_renditions),
        "renditions_to_delete": len(to_delete),
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "errors": errors if errors else None
    }

