# Testing Guide for Owncast WebRTC Setup

This guide will help you test the MediaMTX + FFmpeg + Owncast streaming setup.

## Prerequisites

- Docker and Docker Compose installed
- All services running (`docker compose up -d`)

## Testing Steps

### 1. Verify Containers are Running

```bash
cd mediamtx-local
docker compose ps
```

You should see both `mediamtx` and `ffmpeg` containers running.

### 2. Check Container Logs

#### MediaMTX logs:
```bash
docker compose logs -f mediamtx
```

#### FFmpeg service logs:
```bash
docker compose logs -f ffmpeg
```

Expected:
- MediaMTX should start without errors
- FFmpeg service should show Flask server starting on port 5000
- When MediaMTX path becomes ready, it should trigger the Python script which calls the FFmpeg API

### 3. Test MediaMTX Web UI

Open in your browser:
```
http://localhost:8888
```

You should see the MediaMTX web interface showing available paths (like `/live`).

### 4. Test FFmpeg API Endpoints

#### Check if FFmpeg service is responding:
```bash
curl http://localhost:5000/status
```

Expected response:
```json
{"status": "not_started"}
```

#### Manually trigger FFmpeg start:
```bash
curl http://localhost:5000/start/live
```

Expected response:
```json
{"status": "success", "message": "FFmpeg started", "pid": <number>}
```

### 5. Test WebRTC Streaming (Frontend)

1. Open `frontend/index.html` in your browser (using a local web server, not `file://`)

   ```bash
   # Option 1: Using Python
   cd ../frontend
   python3 -m http.server 8000
   
   # Option 2: Using Node.js http-server
   npx http-server -p 8000
   ```

2. Open `http://localhost:8000` in your browser

3. Click "Start WHIP Streaming" button
   - Browser will request camera/microphone permissions
   - Video preview should appear
   - Stream should connect to MediaMTX

4. Check MediaMTX logs to confirm connection:
   ```bash
   docker compose logs -f mediamtx | grep -i "whip\|webrtc\|live"
   ```

### 6. Verify Stream Flow

The complete flow should be:

1. **WebRTC Stream** → MediaMTX (via WHIP on port 8889)
2. **MediaMTX** → Detects path ready → Calls `start_ffmpeg.py`
3. **start_ffmpeg.py** → Calls FFmpeg API at `http://ffmpeg:5000/start/live`
4. **FFmpeg Service** → Starts ffmpeg process → Pulls from MediaMTX RTMP → Pushes to Owncast

#### Check if FFmpeg is transcoding:
```bash
docker compose logs -f ffmpeg | grep -i "ffmpeg\|streaming\|error"
```

You should see ffmpeg command output showing the transcoding process.

### 7. Verify Stream in MediaMTX

Once streaming starts, check these URLs:

- **HLS Playback**: `http://localhost:8888/live/index.m3u8`
  - Open in VLC or browser with HLS support
- **WebRTC Playback**: Check MediaMTX web UI for playback options
- **RTSP Playback**: `rtsp://localhost:8554/live`

### 8. Monitor FFmpeg Process Status

```bash
# Check FFmpeg status via API
curl http://localhost:5000/status

# Check running processes in FFmpeg container
docker compose exec ffmpeg ps aux | grep ffmpeg
```

### 9. Test Stream to Owncast

After FFmpeg starts, verify the stream is reaching your Owncast instance:
- Check Owncast dashboard at your instance URL
- Verify stream appears in Owncast
- Check Owncast logs for incoming RTMP connections

## Troubleshooting

### Issue: FFmpeg service not starting

**Check:**
```bash
docker compose logs ffmpeg
```

**Common causes:**
- Python/Flask installation failed
- Port 5000 already in use
- File permissions issue with `start_server.py`

**Solution:**
```bash
docker compose restart ffmpeg
docker compose logs -f ffmpeg
```

### Issue: MediaMTX not triggering FFmpeg

**Check:**
```bash
docker compose logs mediamtx | grep -i "python\|start_ffmpeg\|error"
```

**Verify Python is available in MediaMTX container:**
```bash
docker compose exec mediamtx which python3
docker compose exec mediamtx python3 --version
```

If Python is not available, you may need to use a custom MediaMTX image with Python installed.

### Issue: FFmpeg can't connect to MediaMTX

**Check network connectivity:**
```bash
docker compose exec ffmpeg ping -c 2 mediamtx
docker compose exec ffmpeg wget -O- http://mediamtx:8888
```

### Issue: WebRTC streaming fails

**Check:**
- Browser console for errors
- MediaMTX logs for connection attempts
- Ensure you're accessing the frontend via HTTP (not file://)
- Check browser permissions for camera/microphone

### Issue: FFmpeg can't push to Owncast

**Check:**
- OWNCAST_URL environment variable is correct
- Owncast server is accessible from Docker network
- Owncast RTMP endpoint is correct (including stream key)
- Network firewall rules allow RTMP connections

## Quick Health Check Script

Save this as `test-setup.sh`:

```bash
#!/bin/bash

echo "=== Testing Owncast WebRTC Setup ==="

echo -e "\n1. Checking containers..."
docker compose ps

echo -e "\n2. Checking FFmpeg API..."
curl -s http://localhost:5000/status | jq .

echo -e "\n3. Checking MediaMTX Web UI..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8888

echo -e "\n4. Checking FFmpeg logs (last 5 lines)..."
docker compose logs --tail=5 ffmpeg

echo -e "\n5. Checking MediaMTX logs (last 5 lines)..."
docker compose logs --tail=5 mediamtx

echo -e "\n=== Test Complete ==="
```

Make it executable and run:
```bash
chmod +x test-setup.sh
./test-setup.sh
```

## Next Steps

Once everything is working:
1. Stream from the frontend
2. Verify stream appears in Owncast
3. Monitor CPU/memory usage of containers
4. Adjust ffmpeg encoding parameters if needed (in `start_server.py`)

