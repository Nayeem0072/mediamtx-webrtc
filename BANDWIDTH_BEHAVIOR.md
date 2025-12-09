# Bandwidth Behavior with Low Network Conditions

## Current Setup Behavior

### What Happens Automatically

**WebRTC has built-in Adaptive Bitrate (ABR)** - it automatically adjusts quality based on available bandwidth:

1. **Automatic Quality Reduction**
   - Resolution decreases (e.g., 1080p → 720p → 480p)
   - Frame rate may drop (e.g., 30fps → 24fps → 15fps)
   - Bitrate automatically reduces

2. **Connection State Changes**
   - Connection may fluctuate between "connected" and "connecting"
   - ICE connection state may show "disconnected" intermittently
   - Stream continues but quality degrades

3. **Data Flow**
   ```
   Browser (low bandwidth)
     ↓ (WebRTC automatically reduces quality)
   MediaMTX (receives lower quality stream)
     ↓ (FFmpeg transcodes whatever it receives)
   Owncast (receives lower quality transcoded stream)
   ```

## Detailed Scenarios

### Scenario 1: Slightly Low Bandwidth (70-90% of required)

**What Happens:**
- ✅ Stream continues normally
- ⚠️ Resolution may drop from 1080p → 720p
- ⚠️ Frame rate may reduce from 30fps → 24fps
- ⚠️ Slight increase in compression artifacts

**User Experience:**
- Stream remains watchable
- Occasional quality dips
- No disconnections

**Owncast Viewers:**
- Receive lower quality but stable stream
- Stream remains live

### Scenario 2: Very Low Bandwidth (30-70% of required)

**What Happens:**
- ⚠️ Significant quality reduction (720p → 480p or lower)
- ⚠️ Frequent frame drops
- ⚠️ Audio may become choppy
- ⚠️ Connection may become unstable
- ⚠️ High latency/buffering

**User Experience:**
- Pixelated/blurry video
- Choppy audio
- Connection may drop and reconnect
- Stream may pause/buffer

**Owncast Viewers:**
- Receive very low quality stream
- Stream may be intermittent
- Audio may cut out

### Scenario 3: Extremely Low Bandwidth (<30% of required)

**What Happens:**
- ❌ Connection may fail completely
- ❌ WebRTC disconnects
- ❌ FFmpeg may timeout waiting for input
- ❌ Stream to Owncast breaks

**User Experience:**
- Connection fails
- "Connection failed" or "disconnected" status
- Need to reconnect

**Owncast Viewers:**
- Stream stops completely
- No video/audio

## Current Limitations

### What's NOT Handled Well

1. **No Explicit Bitrate Limits in FFmpeg**
   - FFmpeg transcodes whatever quality MediaMTX receives
   - No minimum quality threshold
   - No maximum bitrate cap for Owncast

2. **No User Feedback**
   - No warning when bandwidth is low
   - No quality indicators
   - No way to manually adjust quality

3. **No Graceful Degradation**
   - Stream may fail completely instead of maintaining minimum quality
   - No fallback to audio-only mode

4. **No Bandwidth Monitoring**
   - Can't detect bandwidth issues before they cause problems
   - No statistics about connection quality

## What WebRTC Does Automatically

WebRTC's built-in adaptation includes:

1. **Bitrate Estimation**
   - Continuously monitors network conditions
   - Estimates available bandwidth
   - Adjusts encoder settings accordingly

2. **Packet Loss Handling**
   - Detects lost packets
   - Requests retransmission if possible
   - Reduces bitrate if packet loss is high

3. **Latency Monitoring**
   - Tracks round-trip time
   - Adjusts buffer sizes
   - May reduce quality if latency is high

4. **Dynamic Adaptation**
   - Changes resolution in real-time
   - Adjusts frame rate dynamically
   - Varies bitrate based on network

## FFmpeg Behavior

### Current Configuration

FFmpeg currently:
- ✅ Reconnects automatically if connection drops
- ✅ Handles stream interruptions gracefully
- ❌ **No bitrate limits** - passes through whatever quality it receives
- ❌ **No quality guarantees** - could send very low quality to Owncast

### What Happens to Owncast

- Receives the same quality that MediaMTX receives
- If WebRTC reduces to 480p, Owncast gets 480p
- If stream becomes unstable, Owncast stream is unstable
- If connection fails, Owncast stream stops

## Recommendations

### Immediate Improvements

1. **Add Video Constraints in Frontend**
   ```javascript
   stream = await navigator.mediaDevices.getUserMedia({
     video: {
       width: { ideal: 1280, max: 1920 },
       height: { ideal: 720, max: 1080 },
       frameRate: { ideal: 30, max: 60 }
     }
   });
   ```

2. **Add FFmpeg Bitrate Limits**
   ```python
   '-b:v', '2M',      # Target: 2 Mbps
   '-maxrate', '2.5M', # Max: 2.5 Mbps
   '-bufsize', '4M'    # Buffer size
   ```

3. **Add Bandwidth Monitoring**
   - Track WebRTC statistics
   - Log quality changes
   - Alert on persistent low bandwidth

### Advanced Improvements

1. **Multiple Quality Streams**
   - Transcode to multiple bitrates
   - Allow viewers to select quality

2. **Quality Selection UI**
   - Let user choose quality before streaming
   - Show current bandwidth estimate

3. **Fallback Mechanisms**
   - Audio-only mode for very low bandwidth
   - Static image with audio as last resort

## Monitoring Low Bandwidth

### Check WebRTC Stats

```javascript
// In browser console or frontend code
pc.getStats().then(stats => {
  stats.forEach(report => {
    if (report.type === 'outbound-rtp') {
      console.log('Bitrate:', report.bytesSent);
      console.log('Packets lost:', report.packetsLost);
    }
  });
});
```

### Check Connection Quality

Watch for these indicators:
- Frequent resolution changes
- Frame drops
- High latency
- Packet loss
- Connection state changes

## Summary

**Current Behavior:**
- ✅ WebRTC automatically adapts quality
- ✅ Stream continues at lower quality when bandwidth is limited
- ⚠️ No explicit controls or limits
- ⚠️ Stream may fail if bandwidth is extremely low

**Best Practices:**
- Monitor bandwidth during streaming
- Set realistic quality targets
- Provide user feedback on connection quality
- Consider bitrate limits for consistent output quality

