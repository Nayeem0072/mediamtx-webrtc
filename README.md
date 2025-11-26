# Owncast WebRTC Streaming Setup

A complete solution for streaming video from a browser (WebRTC) to [Owncast](https://owncast.online/) via [MediaMTX](https://github.com/bluenviron/mediamtx) with automatic transcoding.

## Overview

This setup enables you to:
- Stream live video/audio directly from a web browser using WebRTC (WHIP protocol)
- Automatically transcode and forward streams to your Owncast instance
- Handle low bandwidth situations with automatic quality adjustment

### Architecture

```
Browser (WebRTC/WHIP)
    ↓
MediaMTX (receives WebRTC stream)
    ↓
FFmpeg Service (transcodes RTSP → RTMP)
    ↓
Owncast Server (receives RTMP stream)
```

## Features

- ✅ **WebRTC Streaming**: Stream directly from browser using WHIP protocol
- ✅ **Automatic Transcoding**: FFmpeg automatically transcodes and forwards to Owncast
- ✅ **Bandwidth Adaptation**: WebRTC automatically adjusts quality based on network conditions
- ✅ **Secure Configuration**: Sensitive credentials stored in `.env` file (not in git)
- ✅ **Docker-based**: Easy setup with Docker Compose

## Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- An Owncast server instance with RTMP ingest enabled
- Modern web browser with WebRTC support (Chrome, Firefox, Edge)

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd owncast-webrtc
```

### 2. Configure Owncast URL

```bash
cd mediamtx-local
cp .env.example .env
```

Edit `.env` file with your Owncast RTMP URL:

```bash
OWNCAST_URL=rtmp://your-owncast-server.com:1935/live/$$your-stream-key
```

**Note**: Use `$$` to escape `$` in the stream key (e.g., `$$key123` becomes `$key123`)

### 3. Start Services

```bash
docker compose up -d
```

### 4. Serve the Frontend

Open a new terminal and start a local web server:

```bash
cd frontend
python3 -m http.server 8000
```

Or use Node.js:

```bash
npx http-server -p 8000
```

### 5. Start Streaming

1. Open `http://localhost:8000` in your browser
2. Click "Start WHIP Streaming"
3. Allow camera/microphone permissions when prompted
4. Your stream will automatically be forwarded to Owncast!

## Configuration

### Environment Variables

Create a `.env` file in `mediamtx-local/` directory:

```bash
OWNCAST_URL=rtmp://your-server:1935/live/$$stream-key
```

### MediaMTX Configuration

Edit `mediamtx-local/mediamtx.yml` to customize:
- Stream paths
- Authentication
- WebRTC settings

### FFmpeg Settings

Edit `mediamtx-local/start_server.py` to customize:
- Video codec and bitrate
- Audio codec and bitrate
- Encoding presets

## Project Structure

```
owncast-webrtc/
├── frontend/
│   └── index.html          # WebRTC streaming client
├── mediamtx-local/
│   ├── docker-compose.yml  # Docker services configuration
│   ├── mediamtx.yml        # MediaMTX configuration
│   ├── start_server.py     # FFmpeg control API (Flask)
│   ├── startup.sh          # FFmpeg container startup script
│   ├── start_ffmpeg.py     # Trigger script (not used, legacy)
│   ├── .env                # Your credentials (NOT in git)
│   ├── .env.example        # Example configuration
│   ├── TESTING.md          # Testing guide
│   └── TROUBLESHOOTING.md  # Troubleshooting guide
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## How It Works

### 1. WebRTC Connection
- Browser establishes WebRTC connection to MediaMTX via WHIP (WebRTC-HTTP Ingestion Protocol)
- Video/audio tracks are sent over WebRTC
- Connection automatically adapts to bandwidth constraints

### 2. MediaMTX Processing
- MediaMTX receives WebRTC stream on port 8889
- Makes stream available via RTSP (port 8554), HLS (port 8888), and other protocols

### 3. Automatic Transcoding
- When WebRTC connection is established, frontend triggers FFmpeg service
- FFmpeg pulls stream from MediaMTX via RTSP
- Transcodes video/audio and pushes to Owncast via RTMP

### 4. Owncast Delivery
- Owncast receives RTMP stream
- Can be viewed by your audience through Owncast's web interface

## Ports

- **8889**: WHIP/WebRTC HTTP endpoint (for browser streaming)
- **8189**: WebRTC ICE/UDP
- **8000-8001**: RTP/RTCP
- **8554**: RTSP (for pulling streams)
- **8888**: HLS/MediaMTX Web UI
- **1935**: RTMP (if publishing via RTMP)
- **5000**: FFmpeg API (for triggering transcoding)

## Troubleshooting

### WebRTC Connection Issues

See [TROUBLESHOOTING.md](mediamtx-local/TROUBLESHOOTING.md) for detailed troubleshooting steps.

**Common issues:**
- Connection timeout: Check UDP ports are accessible
- ICE connection fails: Ensure ports 8189, 8000-8001 are open
- CORS errors: FFmpeg service should have CORS enabled (already configured)

### FFmpeg Not Starting

1. Check FFmpeg service logs:
   ```bash
   docker compose logs ffmpeg
   ```

2. Check FFmpeg status:
   ```bash
   curl http://localhost:5000/status
   ```

3. Manually trigger FFmpeg:
   ```bash
   curl -X POST http://localhost:5000/start/live
   ```

### Stream Not Appearing in Owncast

1. Verify Owncast URL is correct in `.env` file
2. Check Owncast logs for incoming RTMP connections
3. Verify stream key is correct
4. Check network connectivity from Docker containers to Owncast server

## Testing

Use the provided test script:

```bash
cd mediamtx-local
./test-stream.sh
```

See [TESTING.md](mediamtx-local/TESTING.md) for detailed testing procedures.

## Security Notes

- **Never commit `.env` file** - It contains your Owncast credentials
- `.env` is already in `.gitignore`
- Use `.env.example` as a template for others
- Change stream keys regularly

## Bandwidth Handling

WebRTC automatically adjusts video quality based on available bandwidth:
- **Good bandwidth**: Streams at full quality (720p-1080p)
- **Low bandwidth**: Automatically reduces to 480p or lower
- **Very low bandwidth**: Connection may become unstable

The frontend includes quality constraints to start at reasonable settings (720p @ 30fps ideal).

## Monitoring

### Check Service Status

```bash
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mediamtx
docker compose logs -f ffmpeg
```

### Check Stream Status

```bash
# Check FFmpeg API
curl http://localhost:5000/status

# Check MediaMTX HLS stream
curl http://localhost:8888/live/index.m3u8
```

## Development

### Modifying FFmpeg Transcoding

Edit `mediamtx-local/start_server.py` to change:
- Video codec, bitrate, preset
- Audio codec, bitrate
- Reconnection settings

### Modifying Frontend

Edit `frontend/index.html` to:
- Change UI/UX
- Add quality controls
- Add bandwidth monitoring

### Custom MediaMTX Configuration

Edit `mediamtx-local/mediamtx.yml` for:
- Different stream paths
- Authentication
- WebRTC settings
- Path-specific configurations

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Modern browser with WebRTC support
- Owncast server with RTMP ingest enabled

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](mediamtx-local/TROUBLESHOOTING.md)
2. Check MediaMTX documentation: https://github.com/bluenviron/mediamtx
3. Check Owncast documentation: https://owncast.online/docs/

## Acknowledgments

- [MediaMTX](https://github.com/bluenviron/mediamtx) - Media server
- [Owncast](https://owncast.online/) - Self-hosted live streaming platform
- [FFmpeg](https://ffmpeg.org/) - Video transcoding

