# Troubleshooting Guide

## WebRTC Connection Issues

### Symptom: Connection times out with "deadline exceeded while waiting connection"

**Possible causes:**
1. **Network/Firewall blocking ICE/STUN traffic**
   - WebRTC requires UDP ports for ICE candidates
   - Check if ports 8189 (ICE/UDP) and 8000-8001 (RTP/RTCP) are accessible
   
2. **Browser security restrictions**
   - Ensure you're accessing via HTTP (not file://)
   - Try Chrome or Firefox (Safari may have WebRTC restrictions)
   - Check browser console for errors

3. **Localhost networking issues**
   - If using Docker Desktop on Mac/Windows, port forwarding might need configuration
   - Try accessing via your machine's IP instead of localhost

**Solutions:**

1. **Check MediaMTX logs:**
   ```bash
   docker compose logs -f mediamtx
   ```
   Look for WebRTC session creation and ICE candidate exchange

2. **Check browser console:**
   - Open browser DevTools (F12)
   - Look for WebRTC/ICE errors
   - Check Network tab for failed requests

3. **Try accessing via IP instead of localhost:**
   - Find your local IP: `ifconfig` or `ipconfig`
   - Update frontend to use: `http://<your-ip>:8889/live/whip`

4. **Check port accessibility:**
   ```bash
   # Test MediaMTX WebRTC endpoint
   curl -v http://localhost:8889/live/whip
   ```

## FFmpeg Not Starting

### Symptom: Status shows "not_started" even after streaming

**Check:**

1. **Verify trigger is being called:**
   ```bash
   docker compose logs mediamtx | grep -i "runOnReady\|curl\|ffmpeg"
   ```

2. **Test trigger manually:**
   ```bash
   # From MediaMTX container (if possible)
   curl -X POST http://ffmpeg:5000/start/live
   
   # Or from host
   curl -X POST http://localhost:5000/start/live
   ```

3. **Check FFmpeg service:**
   ```bash
   docker compose logs ffmpeg
   curl http://localhost:5000/status
   ```

4. **Verify network connectivity:**
   - MediaMTX and FFmpeg containers must be on same Docker network
   - Check with: `docker network inspect <network_name>`

## FFmpeg Starts but Immediately Stops

### Symptom: FFmpeg status shows "stopped" with return code 1

**Possible causes:**
1. No stream available at MediaMTX RTSP endpoint
2. Cannot connect to Owncast RTMP endpoint
3. Stream path mismatch

**Check:**

1. **Verify stream is available:**
   ```bash
   # Check MediaMTX stream status
   curl http://localhost:8888/live/index.m3u8
   
   # Check RTSP endpoint (from ffmpeg container)
   docker compose exec ffmpeg ffprobe rtsp://mediamtx:8554/live
   ```

2. **Check FFmpeg logs:**
   ```bash
   docker compose logs ffmpeg | grep -i "error\|failed\|connection"
   ```

3. **Verify Owncast URL:**
   ```bash
   docker compose exec ffmpeg printenv OWNCAST_URL
   ```

## MediaMTX Not Detecting Stream

### Symptom: runOnReady never triggers

**Check:**

1. **Verify stream path in MediaMTX:**
   ```bash
   curl http://localhost:8888/live
   ```

2. **Check MediaMTX configuration:**
   - Ensure path name matches: `live`
   - Check if path requires authentication

3. **Verify WebRTC connection completed:**
   - Look for successful WebRTC session in logs
   - Connection should show "connected" state, not timeout

## Quick Diagnostic Commands

```bash
# 1. Check all container status
docker compose ps

# 2. Check MediaMTX logs
docker compose logs --tail=50 mediamtx

# 3. Check FFmpeg logs
docker compose logs --tail=50 ffmpeg

# 4. Test FFmpeg API
curl http://localhost:5000/status

# 5. Test MediaMTX endpoints
curl http://localhost:8888/live/index.m3u8
curl http://localhost:8889/live/whip

# 6. Manually trigger FFmpeg
curl -X POST http://localhost:5000/start/live

# 7. Check if stream is available via RTSP
docker compose exec ffmpeg timeout 5 ffprobe rtsp://mediamtx:8554/live 2>&1 || echo "No stream available"
```

## Common Fixes

1. **Restart everything:**
   ```bash
   docker compose down
   docker compose up -d
   ```

2. **Clear browser cache and try again**

3. **Try different browser** (Chrome recommended for WebRTC)

4. **Check Docker Desktop settings:**
   - Ensure port forwarding is enabled
   - Check if firewall is blocking Docker networking

5. **Verify Owncast is accessible:**
   - Test Owncast URL from your machine
   - Check if stream key is correct

