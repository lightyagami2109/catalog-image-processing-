"""SQLAlchemy async models for the catalog image pipeline."""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Tenant(Base):
    """Tenant/organization model."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assets = relationship("Asset", back_populates="tenant", cascade="all, delete-orphan")


class Asset(Base):
    """Original image asset model."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 hex
    perceptual_hash = Column(String(16), nullable=False, index=True)  # perceptual hash hex
    original_bytes = Column(BigInteger, nullable=False)  # file size in bytes
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    color_space = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="assets")
    renditions = relationship("Rendition", back_populates="asset", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="asset", cascade="all, delete-orphan")


class Rendition(Base):
    """Processed image rendition model."""
    __tablename__ = "renditions"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    preset = Column(String(32), nullable=False, index=True)  # thumb, card, zoom
    file_path = Column(String(1024), nullable=False, unique=True)
    bytes = Column(BigInteger, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    quality = Column(Integer, nullable=True)  # JPEG quality if applicable
    color_space = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="renditions")


class Job(Base):
    """Processing job queue model."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="jobs")


class PoisonJob(Base):
    """Permanently failed jobs moved here after max retries."""
    __tablename__ = "poison_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, nullable=False, index=True)
    original_job_id = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=False)
    retry_count = Column(Integer, nullable=False)
    failed_at = Column(DateTime(timezone=True), server_default=func.now())


class TenantMetrics(Base):
    """Aggregated tenant usage metrics (can be materialized view or table)."""
    __tablename__ = "tenant_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), unique=True, nullable=False, index=True)
    asset_count = Column(Integer, default=0, nullable=False)
    rendition_count = Column(Integer, default=0, nullable=False)
    total_bytes = Column(BigInteger, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    tenant = relationship("Tenant")

