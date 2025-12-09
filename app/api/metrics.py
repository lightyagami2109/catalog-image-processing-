"""Metrics endpoint for tenant usage statistics."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Tenant, Asset, Rendition, TenantMetrics

router = APIRouter(prefix="/metrics", tags=["metrics"])





@router.get("/")
async def get_all_metrics(
    db: AsyncSession = Depends(get_db)
):
    """Get metrics for all tenants."""
    # Get all tenants
    result = await db.execute(select(Tenant))
    tenants = result.scalars().all()
    
    metrics = []
    for tenant in tenants:
        # Count assets
        result = await db.execute(
            select(func.count(Asset.id)).where(Asset.tenant_id == tenant.id)
        )
        asset_count = result.scalar_one()
        
        # Count renditions
        result = await db.execute(
            select(func.count(Rendition.id))
            .join(Asset)
            .where(Asset.tenant_id == tenant.id)
        )
        rendition_count = result.scalar_one()
        
        # Sum bytes
        result = await db.execute(
            select(func.sum(Asset.original_bytes)).where(Asset.tenant_id == tenant.id)
        )
        asset_bytes = result.scalar_one() or 0
        
        result = await db.execute(
            select(func.sum(Rendition.bytes))
            .join(Asset)
            .where(Asset.tenant_id == tenant.id)
        )
        rendition_bytes = result.scalar_one() or 0
        
        metrics.append({
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "asset_count": asset_count,
            "rendition_count": rendition_count,
            "total_bytes": asset_bytes + rendition_bytes
        })
    
    return {"tenants": metrics}

