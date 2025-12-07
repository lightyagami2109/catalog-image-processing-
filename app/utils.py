"""Image processing utilities and quality metrics."""
import io
from PIL import Image
import numpy as np
from app.hashing import hash_distance


# Rendition presets
RENDITION_PRESETS = {
    "thumb": {"size": (100, 100), "fit": True},
    "card": {"size": (400, 400), "fit": True},
    "zoom": {"size": (1200, 1200), "fit": False},  # max dimension
}


def create_rendition(image: Image.Image, preset: str) -> Image.Image:
    """
    Create a rendition from original image based on preset.
    - thumb: 100x100 fit (maintains aspect ratio)
    - card: 400x400 fit (maintains aspect ratio)
    - zoom: max 1200px on longer edge (maintains aspect ratio)
    """
    config = RENDITION_PRESETS[preset]
    size = config["size"]
    fit = config["fit"]
    
    if fit:
        # Fit within dimensions while maintaining aspect ratio
        image.thumbnail(size, Image.Resampling.LANCZOS)
    else:
        # Max dimension (zoom: max 1200px on longer edge)
        max_dim = max(size)
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    
    return image


def save_rendition(image: Image.Image, format: str = "JPEG", quality: int = 85) -> bytes:
    """Save image to bytes with specified format and quality."""
    buffer = io.BytesIO()
    image.save(buffer, format=format, quality=quality, optimize=True)
    return buffer.getvalue()


def compute_psnr(image1: Image.Image, image2: Image.Image) -> float:
    """
    Compute Peak Signal-to-Noise Ratio (PSNR) between two images.
    Higher PSNR = better quality (typically > 30 dB is good).
    Returns PSNR in decibels.
    """
    # Convert to RGB if needed
    img1 = image1.convert("RGB")
    img2 = image2.convert("RGB")
    
    # Convert to numpy arrays
    arr1 = np.array(img1, dtype=np.float64)
    arr2 = np.array(img2, dtype=np.float64)
    
    # Ensure same dimensions
    if arr1.shape != arr2.shape:
        # Resize image2 to match image1
        img2_resized = img2.resize(img1.size, Image.Resampling.LANCZOS)
        arr2 = np.array(img2_resized, dtype=np.float64)
    
    # Compute MSE (Mean Squared Error)
    mse = np.mean((arr1 - arr2) ** 2)
    
    if mse == 0:
        return float("inf")  # Images are identical
    
    # PSNR = 20 * log10(MAX_PIXEL_VALUE / sqrt(MSE))
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return float(psnr)


def compare_images(original: Image.Image, rendition: Image.Image, 
                  original_hash: str, rendition_hash: str) -> dict:
    """
    Compare original and rendition images.
    Returns dict with file size, PSNR, and perceptual hash distance.
    """
    # Convert rendition to bytes to get file size
    rendition_bytes = save_rendition(rendition)
    
    # Compute PSNR
    psnr = compute_psnr(original, rendition)
    
    # Compute perceptual hash distance
    phash_dist = hash_distance(original_hash, rendition_hash)
    
    return {
        "file_size_bytes": len(rendition_bytes),
        "psnr_db": psnr,
        "perceptual_hash_distance": phash_dist,
        "note": "PSNR > 30 dB is good quality. Lower hash distance = more similar."
    }

