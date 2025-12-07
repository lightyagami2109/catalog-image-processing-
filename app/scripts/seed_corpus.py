"""Seed corpus script - uploads test images and verifies renditions."""
import asyncio
import sys
from pathlib import Path
import httpx
from PIL import Image
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def seed_corpus(base_url: str = "http://localhost:10000"):
    """Upload test images and verify renditions are created."""
    print("Seeding test corpus...")
    
    # Create simple test images
    test_images = []
    
    # Image 1: Small red square
    img1 = Image.new("RGB", (200, 200), color="red")
    buffer1 = io.BytesIO()
    img1.save(buffer1, format="JPEG")
    test_images.append(("red_square.jpg", buffer1.getvalue()))
    
    # Image 2: Medium blue rectangle
    img2 = Image.new("RGB", (500, 300), color="blue")
    buffer2 = io.BytesIO()
    img2.save(buffer2, format="JPEG")
    test_images.append(("blue_rect.jpg", buffer2.getvalue()))
    
    # Image 3: Large green square
    img3 = Image.new("RGB", (1500, 1500), color="green")
    buffer3 = io.BytesIO()
    img3.save(buffer3, format="JPEG")
    test_images.append(("green_large.jpg", buffer3.getvalue()))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        asset_ids = []
        
        # Upload images
        for filename, content in test_images:
            print(f"Uploading {filename}...")
            files = {"file": (filename, content, "image/jpeg")}
            data = {"tenant_name": "test_tenant"}
            
            response = await client.post(
                f"{base_url}/upload/",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                asset_id = result["asset_id"]
                asset_ids.append(asset_id)
                print(f"  ✓ Uploaded: asset_id={asset_id}, status={result['status']}")
            else:
                print(f"  ✗ Upload failed: {response.status_code} - {response.text}")
                return False
        
        # Wait a bit for processing
        print("\nWaiting for processing...")
        await asyncio.sleep(5)
        
        # Check renditions
        print("\nChecking renditions...")
        for asset_id in asset_ids:
            response = await client.get(f"{base_url}/retrieve/asset/{asset_id}")
            if response.status_code == 200:
                asset = response.json()
                rendition_count = len(asset["renditions"])
                print(f"  Asset {asset_id}: {rendition_count} renditions")
                if rendition_count < 3:
                    print(f"    ⚠ Expected 3 renditions, got {rendition_count}")
            else:
                print(f"  ✗ Failed to retrieve asset {asset_id}")
        
        # Check metrics
        print("\nChecking metrics...")
        response = await client.get(f"{base_url}/metrics/tenant/test_tenant")
        if response.status_code == 200:
            metrics = response.json()
            print(f"  Tenant metrics:")
            print(f"    Assets: {metrics['asset_count']}")
            print(f"    Renditions: {metrics['rendition_count']}")
            print(f"    Total bytes: {metrics['total_bytes']}")
        
        print("\n✓ Seed corpus completed!")
        return True


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:10000"
    asyncio.run(seed_corpus(base_url))

