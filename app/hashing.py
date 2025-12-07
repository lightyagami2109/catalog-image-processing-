"""Content hashing utilities for idempotency."""
import hashlib
from PIL import Image
import imagehash


def compute_sha256(content: bytes) -> str:
    """Compute SHA256 hash of content bytes."""
    return hashlib.sha256(content).hexdigest()


def compute_perceptual_hash(image: Image.Image) -> str:
    """Compute perceptual hash (pHash) of image using average hash."""
    # Using average hash (8x8) for simplicity; can swap to perceptual hash if needed
    phash = imagehash.average_hash(image)
    return str(phash)


def compute_content_hash(image: Image.Image, content_bytes: bytes) -> tuple[str, str]:
    """
    Compute both SHA256 and perceptual hash for idempotency.
    Returns: (sha256_hex, perceptual_hash_hex)
    """
    sha256 = compute_sha256(content_bytes)
    perceptual = compute_perceptual_hash(image)
    return sha256, perceptual


def hash_distance(hash1: str, hash2: str) -> int:
    """
    Compute Hamming distance between two perceptual hashes.
    Lower distance = more similar images.
    """
    # Convert hex strings to integers and compute Hamming distance
    h1 = int(hash1, 16)
    h2 = int(hash2, 16)
    return bin(h1 ^ h2).count("1")

