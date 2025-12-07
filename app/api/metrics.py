"""Metrics endpoint for tenant usage statistics."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Tenant, Asset, Rendition, TenantMetrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/tenant/{tenant_name}")
async def get_tenant_metrics(
    tenant_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get usage metrics for a tenant."""
    # Get tenant
    result = await db.execute(
        select(Tenant).where(Tenant.name == tenant_name)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_name} not found"
        )
    
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
    
    # Sum total bytes (assets + renditions)
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
    
    total_bytes = asset_bytes + rendition_bytes
    
    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "asset_count": asset_count,
        "rendition_count": rendition_count,
        "total_bytes": total_bytes,
        "asset_bytes": asset_bytes,
        "rendition_bytes": rendition_bytes
    }


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

