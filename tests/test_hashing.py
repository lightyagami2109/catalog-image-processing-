"""Tests for hashing utilities."""
import pytest
from PIL import Image
import io

from app.hashing import (
    compute_sha256,
    compute_perceptual_hash,
    compute_content_hash,
    hash_distance
)


def test_compute_sha256():
    """Test SHA256 computation."""
    content = b"test content"
    hash1 = compute_sha256(content)
    hash2 = compute_sha256(content)
    
    # Same content should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex is 64 chars
    
    # Different content should produce different hash
    hash3 = compute_sha256(b"different content")
    assert hash1 != hash3


def test_compute_perceptual_hash():
    """Test perceptual hash computation."""
    # Create two identical images
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="red")
    
    hash1 = compute_perceptual_hash(img1)
    hash2 = compute_perceptual_hash(img2)
    
    # Identical images should have same perceptual hash
    assert hash1 == hash2
    
    # Different images should have different hashes
    img3 = Image.new("RGB", (100, 100), color="blue")
    hash3 = compute_perceptual_hash(img3)
    assert hash1 != hash3


def test_compute_content_hash():
    """Test combined content hash computation."""
    img = Image.new("RGB", (100, 100), color="red")
    content = b"test image bytes"
    
    sha256, perceptual = compute_content_hash(img, content)
    
    assert len(sha256) == 64
    assert len(perceptual) > 0
    
    # Same inputs should produce same hashes
    sha256_2, perceptual_2 = compute_content_hash(img, content)
    assert sha256 == sha256_2
    assert perceptual == perceptual_2


def test_hash_distance():
    """Test perceptual hash distance computation."""
    # Same hash should have distance 0
    hash1 = "a1b2c3d4"
    assert hash_distance(hash1, hash1) == 0
    
    # Different hashes should have positive distance
    hash2 = "a1b2c3d5"  # One bit different
    distance = hash_distance(hash1, hash2)
    assert distance > 0
    
    # Create images and test
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="red")
    img3 = Image.new("RGB", (100, 100), color="blue")
    
    hash1 = compute_perceptual_hash(img1)
    hash2 = compute_perceptual_hash(img2)
    hash3 = compute_perceptual_hash(img3)
    
    # Identical images should have distance 0
    assert hash_distance(hash1, hash2) == 0
    
    # Different images should have positive distance
    assert hash_distance(hash1, hash3) > 0

