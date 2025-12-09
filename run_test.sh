#!/bin/bash
# Quick test script to verify renditions are created

echo "🧪 Testing Rendition Creation"
echo "=============================="
echo ""

# Step 1: Check if server is running
echo "1. Checking server..."
if curl -s http://localhost:10000/healthz > /dev/null 2>&1; then
    echo "   ✅ Server is running"
else
    echo "   ❌ Server is NOT running"
    echo "   💡 Start it with: uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload"
    exit 1
fi

# Step 2: Create test image
echo ""
echo "2. Creating test image..."
python3 -c "from PIL import Image; Image.new('RGB', (800, 600), 'green').save('test_rendition.jpg')" 2>/dev/null
if [ -f test_rendition.jpg ]; then
    echo "   ✅ Test image created"
else
    echo "   ❌ Failed to create test image"
    exit 1
fi

# Step 3: Upload image
echo ""
echo "3. Uploading image..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:10000/upload/" \
  -F "file=@test_rendition.jpg" \
  -F "tenant_name=test")

ASSET_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('asset_id', 'N/A'))" 2>/dev/null)

if [ "$ASSET_ID" != "N/A" ] && [ ! -z "$ASSET_ID" ]; then
    echo "   ✅ Image uploaded successfully"
    echo "   Asset ID: $ASSET_ID"
else
    echo "   ❌ Upload failed"
    echo "   Response: $UPLOAD_RESPONSE"
    exit 1
fi

# Step 4: Wait for processing
echo ""
echo "4. Waiting 20 seconds for worker to process..."
sleep 20

# Step 5: Check renditions
echo ""
echo "5. Checking renditions..."
RENDITION_RESPONSE=$(curl -s "http://localhost:10000/retrieve/asset/$ASSET_ID")

RENDITION_COUNT=$(echo $RENDITION_RESPONSE | python3 -c "import sys, json; r=json.load(sys.stdin).get('renditions', []); print(len(r))" 2>/dev/null)

echo ""
echo "Results:"
echo "--------"
if [ "$RENDITION_COUNT" = "3" ]; then
    echo "   ✅ SUCCESS! All 3 renditions created!"
    echo ""
    echo $RENDITION_RESPONSE | python3 -c "import sys, json; r=json.load(sys.stdin).get('renditions', []); [print(f\"   ✅ {item['preset']:6s} - {item['width']}x{item['height']} ({item['bytes']:,} bytes)\") for item in r]"
else
    echo "   ❌ Only $RENDITION_COUNT/3 renditions created"
    echo ""
    echo "   Full response:"
    echo $RENDITION_RESPONSE | python3 -m json.tool 2>/dev/null || echo $RENDITION_RESPONSE
fi

echo ""
echo "=============================="
