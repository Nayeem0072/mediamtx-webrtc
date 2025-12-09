# Latency Analysis

## Pipeline Overview

```
Browser (WebRTC encoding)
  ↓ (~100-500ms)
MediaMTX (receives WebRTC)
  ↓ (~50-200ms buffer)
FFmpeg (pulls RTSP, transcodes, pushes RTMP)
  ↓ (~500ms-2s transcoding + buffer)
Owncast (receives RTMP)
  ↓ (~2-5s buffer for HLS)
Viewers (watch stream)
```

## Total Latency Breakdown

### Typical Latency: **3-8 seconds** end-to-end

### Detailed Component Latency

#### 1. Browser → MediaMTX (WebRTC)
- **Latency: 100-500ms**
- WebRTC encoding overhead
- Network transmission
- Minimal buffering
- **Low latency** - WebRTC is designed for real-time

#### 2. MediaMTX Internal Processing
- **Latency: 50-200ms**
- WebRTC to RTSP conversion
- Internal buffering
- Stream relay overhead

#### 3. FFmpeg Transcoding (RTSP → RTMP)
- **Latency: 500ms - 2 seconds** ⚠️ **LARGEST CONTRIBUTOR**
- RTSP stream pull
- Video decode
- Video encode (re-encoding adds latency)
- Audio decode/encode
- RTMP push buffer
- **Keyframe interval** affects latency (currently: default ~2s)

#### 4. Owncast Processing
- **Latency: 2-5 seconds** ⚠️ **LARGEST CONTRIBUTOR**
- RTMP ingest buffer
- HLS segment generation (requires 2-3 segments minimum)
- Segment duration (typically 2-6 seconds per segment)
- **HLS is high latency by design**

#### 5. Viewer Playback
- **Latency: 1-3 seconds**
- HLS player buffering
- Network delay to viewer

## Current Configuration Impact

### FFmpeg Settings (High Latency)

Current FFmpeg command:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-rtsp_transport', 'tcp',
    '-i', MEDIAMTX_SOURCE,
    '-c:v', 'libx264',
    '-preset', 'veryfast',      # Good for CPU, but not latency
    '-c:a', 'aac',
    '-b:a', '128k',
    '-f', 'flv',
    # No keyframe interval specified (defaults to ~2s)
    # No buffer size limits
]
```

**Issues:**
- No explicit keyframe interval (defaults to ~2 seconds)
- No low-latency tuning
- Default buffer sizes add latency
- Re-encoding adds processing delay

### Owncast HLS Latency

Owncast uses HLS for delivery:
- **Segment duration**: Typically 2-6 seconds
- **Minimum segments before playback**: 2-3 segments
- **Total delay**: 4-18 seconds just for HLS
- **HLS is NOT designed for low latency** - it's for reliability

## Minimizing Latency

### Option 1: Optimize FFmpeg for Low Latency

Add low-latency flags:

```python
ffmpeg_cmd = [
    'ffmpeg',
    '-rtsp_transport', 'tcp',
    '-fflags', 'nobuffer',           # Reduce buffering
    '-flags', 'low_delay',            # Low delay flag
    '-strict', 'experimental',
    '-i', MEDIAMTX_SOURCE,
    '-c:v', 'libx264',
    '-preset', 'ultrafast',           # Faster encoding (lower latency)
    '-tune', 'zerolatency',           # Zero latency tuning
    '-g', '30',                       # Keyframe every 30 frames (1s @ 30fps)
    '-sc_threshold', '0',             # Disable scene change detection
    '-c:a', 'aac',
    '-b:a', '128k',
    '-f', 'flv',
    '-flush_packets', '1',            # Flush packets immediately
    '-fflags', '+genpts',             # Generate PTS immediately
    OWNCAST_URL
]
```

**Expected improvement: 1-2 seconds**

### Option 2: Use Owncast WebRTC Delivery (Low Latency)

**Best option** - Use Owncast's WebRTC delivery instead of HLS:
- **Latency: 200-800ms** instead of 4-8 seconds
- Direct WebRTC to viewers (bypass HLS)
- Requires Owncast configuration for WebRTC output

### Option 3: Reduce Owncast HLS Segment Duration

Configure Owncast for shorter segments:
- Reduce segment duration to 1-2 seconds
- **Trade-off**: More segments = more overhead, but lower latency

### Option 4: Use WebRTC Direct (Bypass Owncast)

Stream directly from MediaMTX to viewers via WebRTC:
- **Latency: 200-500ms** (very low)
- Bypasses FFmpeg and Owncast entirely
- **Trade-off**: Lose Owncast features (chat, branding, etc.)

## Latency Comparison

| Configuration | Typical Latency |
|---------------|----------------|
| **Current Setup** (HLS via Owncast) | **3-8 seconds** |
| Optimized FFmpeg + Owncast HLS | **2-6 seconds** |
| FFmpeg + Owncast WebRTC | **0.5-1.5 seconds** |
| Direct MediaMTX WebRTC | **0.2-0.5 seconds** |

## Real-World Expectations

### Current Setup (Not Optimized)

**Typical viewers will experience:**
- **5-10 seconds delay** from live action
- Delay can increase during:
  - Network congestion
  - High CPU usage
  - Buffering events

**This is normal for HLS-based streaming** - it prioritizes reliability over low latency.

### Optimized Setup

With low-latency optimizations:
- **2-4 seconds delay** (still HLS)
- Or **<1 second** with WebRTC delivery

## Where Latency is Added

### ✅ Low Latency Components

1. **Browser WebRTC encoding**: ~100-300ms
2. **MediaMTX relay**: ~50-200ms
3. **Network transmission**: ~50-200ms

### ⚠️ High Latency Components

1. **FFmpeg transcoding**: **500ms - 2s**
   - Video re-encoding is expensive
   - Buffer accumulation
   - Keyframe intervals

2. **Owncast HLS**: **2-5s** 
   - Segment generation
   - Minimum segment buffer
   - HLS protocol design

### Total Breakdown (Current)

```
Browser encoding:        ~200ms
Network (Browser→MTX):   ~100ms
MediaMTX processing:     ~100ms
FFmpeg transcoding:      ~1000ms ⚠️
Network (FFmpeg→Owncast): ~50ms
Owncast HLS:             ~3000ms ⚠️
────────────────────────────────
TOTAL:                   ~4500ms (4.5 seconds minimum)
```

## Minimizing Latency - Practical Steps

### Step 1: Optimize FFmpeg (Easiest)

Modify `mediamtx-local/start_server.py`:

```python
ffmpeg_cmd = [
    'ffmpeg',
    '-rtsp_transport', 'tcp',
    '-fflags', 'nobuffer',
    '-flags', 'low_delay',
    '-i', MEDIAMTX_SOURCE,
    '-c:v', 'libx264',
    '-preset', 'ultrafast',      # Changed from 'veryfast'
    '-tune', 'zerolatency',      # ADD THIS
    '-g', '30',                  # ADD THIS (1 second keyframes)
    '-c:a', 'aac',
    '-b:a', '128k',
    '-f', 'flv',
    '-flush_packets', '1',       # ADD THIS
    OWNCAST_URL
]
```

### Step 2: Configure Owncast for Lower Latency

In Owncast configuration:
- Reduce HLS segment duration
- Enable WebRTC delivery (if available)
- Minimize buffer sizes

### Step 3: Monitor Latency

Add latency monitoring:
- Track timestamps through pipeline
- Log delay metrics
- Alert on high latency

## Trade-offs

### Low Latency = Lower Reliability

- More dropped frames
- Higher CPU usage
- More network overhead
- Potential playback issues

### Higher Latency = Higher Reliability

- Better buffering
- Smoother playback
- Better error recovery
- Lower CPU usage

## Recommendations

### For Interactive Streaming (Gaming, Chat)

**Use WebRTC delivery:**
- Configure Owncast for WebRTC output
- Or stream directly from MediaMTX
- **Latency: <1 second**

### For General Broadcasting

**Current setup is fine:**
- 5-10 seconds is acceptable
- Prioritizes reliability
- Works well for most use cases

### For Live Events

**Optimize FFmpeg + shorten Owncast segments:**
- Reduce to 2-3 seconds total
- Good balance of latency and reliability

## Current Status

Your current setup:
- ✅ **Functional and reliable**
- ⚠️ **Not optimized for low latency**
- ✅ **Good for general broadcasting**
- ❌ **Not ideal for real-time interaction**

**Typical latency: 3-8 seconds** (normal for HLS-based streaming)

