#!/usr/bin/env python3
"""Test script to upload image and check renditions locally."""
import requests
import time
import sys

BASE_URL = "http://localhost:10000"

def test_upload_and_renditions():
    """Test uploading an image and checking renditions."""
    
    print("🧪 Testing Local Server\n")
    
    # Step 1: Check server is running
    print("1. Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Server is not running!")
        print("   💡 Start it with: uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Step 2: Create a test image
    print("\n2. Creating test image...")
    try:
        from PIL import Image
        import io
        
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        test_image = ('test.jpg', buffer, 'image/jpeg')
        print("   ✅ Test image created (800x600 red image)")
    except Exception as e:
        print(f"   ❌ Error creating test image: {e}")
        return False
    
    # Step 3: Upload image
    print("\n3. Uploading image...")
    try:
        files = {'file': test_image}
        data = {'tenant_name': 'test_tenant'}
        
        response = requests.post(f"{BASE_URL}/upload/", files=files, data=data, timeout=30)
        
        if response.status_code != 200:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        asset_id = result.get('asset_id')
        job_id = result.get('job_id')
        
        print(f"   ✅ Image uploaded successfully")
        print(f"   Asset ID: {asset_id}")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {result.get('status')}")
        
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Wait for processing
    print("\n4. Waiting for worker to process (15 seconds)...")
    time.sleep(15)
    
    # Step 5: Check renditions
    print("\n5. Checking renditions...")
    try:
        response = requests.get(f"{BASE_URL}/retrieve/asset/{asset_id}", timeout=10)
        
        if response.status_code != 200:
            print(f"   ❌ Failed to retrieve asset: {response.status_code}")
            return False
        
        asset_data = response.json()
        renditions = asset_data.get('renditions', [])
        
        print(f"   Found {len(renditions)} rendition(s)")
        
        expected_presets = ['thumb', 'card', 'zoom']
        found_presets = [r['preset'] for r in renditions]
        
        print("\n   Rendition Status:")
        for preset in expected_presets:
            if preset in found_presets:
                r = next(r for r in renditions if r['preset'] == preset)
                print(f"   ✅ {preset:6s} - {r['width']}x{r['height']} ({r['bytes']:,} bytes)")
            else:
                print(f"   ❌ {preset:6s} - MISSING")
        
        if len(renditions) == 3:
            print("\n   🎉 SUCCESS! All 3 renditions created!")
            return True
        else:
            print(f"\n   ⚠️  WARNING: Only {len(renditions)}/3 renditions created")
            print("   💡 Check worker logs for errors")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking renditions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    success = test_upload_and_renditions()
    print("=" * 60)
    
    if success:
        print("\n✅ Test PASSED - Renditions are working locally!")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED - Check the issues above")
        sys.exit(1)
