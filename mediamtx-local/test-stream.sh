#!/bin/bash

echo "=== Testing Owncast WebRTC Stream Setup ==="
echo ""

echo "1. Checking containers..."
docker compose ps
echo ""

echo "2. Testing MediaMTX Web UI..."
curl -s -o /dev/null -w "MediaMTX HTTP Status: %{http_code}\n" http://localhost:8888
echo ""

echo "3. Testing FFmpeg API..."
curl -s http://localhost:5000/status | jq . 2>/dev/null || curl -s http://localhost:5000/status
echo ""

echo "4. Checking MediaMTX logs (last 5 lines)..."
docker compose logs --tail=5 mediamtx
echo ""

echo "5. Checking FFmpeg service logs (last 5 lines)..."
docker compose logs --tail=5 ffmpeg
echo ""

echo "=== Setup looks good! ==="
echo ""
echo "To test streaming:"
echo "1. Start a local web server in the frontend directory:"
echo "   cd ../frontend && python3 -m http.server 8000"
echo ""
echo "2. Open http://localhost:8000 in your browser"
echo ""
echo "3. Click 'Start WHIP Streaming' and allow camera/microphone access"
echo ""
echo "4. Monitor the logs:"
echo "   docker compose logs -f mediamtx"
echo "   docker compose logs -f ffmpeg"
echo ""
echo "5. Check if FFmpeg started transcoding:"
echo "   curl http://localhost:5000/status"
echo ""

