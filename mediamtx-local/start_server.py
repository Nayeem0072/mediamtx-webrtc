#!/usr/bin/env python3
"""
Flask server to control ffmpeg sidecar.
Provides API endpoint to start ffmpeg transcoding from mediamtx to Owncast.
"""
import os
import subprocess
import signal
import sys
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes to allow frontend to call the API
CORS(app)
ffmpeg_process = None

# Get Owncast URL from environment variable
OWNCAST_URL = os.getenv('OWNCAST_URL', 'rtmp://streamdev.convay.com:1935/live/$tr3amD3v')
# MediaMTX RTSP source URL (internal Docker network) - RTSP works better for pulling streams
MEDIAMTX_SOURCE = 'rtsp://mediamtx:8554/live'


def start_ffmpeg():
    """Start ffmpeg process to transcode from mediamtx to Owncast."""
    global ffmpeg_process
    
    # Stop existing ffmpeg process if running
    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("Stopping existing ffmpeg process...", file=sys.stderr)
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
    
    # Build ffmpeg command
    # Pull RTSP stream from mediamtx and push to Owncast
    # Using RTSP instead of RTMP as it's more reliable for pulling streams
    ffmpeg_cmd = [
        'ffmpeg',
        '-rtsp_transport', 'tcp',        # Use TCP for RTSP (more reliable)
        '-i', MEDIAMTX_SOURCE,           # Input from mediamtx (RTSP)
        '-c:v', 'libx264',               # Video codec
        '-preset', 'veryfast',           # Encoding preset
        '-c:a', 'aac',                   # Audio codec
        '-b:a', '128k',                  # Audio bitrate
        '-f', 'flv',                     # Output format
        '-y',                            # Overwrite output files
        '-reconnect', '1',               # Reconnect on errors
        '-reconnect_at_eof', '1',        # Reconnect at end of file
        '-reconnect_streamed', '1',      # Reconnect streamed non-file inputs
        '-reconnect_delay_max', '2',     # Max delay between reconnect attempts
        OWNCAST_URL                      # Output to Owncast
    ]
    
    # Log the command (without sensitive parts)
    safe_cmd = ' '.join(ffmpeg_cmd[:-1]) + ' [OWNCAST_URL]'
    print(f"Starting ffmpeg command: {safe_cmd}", file=sys.stderr)
    print(f"OWNCAST_URL length: {len(OWNCAST_URL)}", file=sys.stderr)
    
    # Start ffmpeg process
    try:
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # Use binary mode for stderr to capture all output
        )
        print(f"FFmpeg started with PID: {ffmpeg_process.pid}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error starting ffmpeg: {str(e)}", file=sys.stderr)
        import traceback
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return False


@app.route('/start/live', methods=['GET', 'POST'])
def start_live():
    """API endpoint to start ffmpeg transcoding."""
    success = start_ffmpeg()
    
    if success and ffmpeg_process:
        return jsonify({
            'status': 'success',
            'message': 'FFmpeg started',
            'pid': ffmpeg_process.pid
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to start ffmpeg'
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """Check ffmpeg process status."""
    if ffmpeg_process is None:
        return jsonify({'status': 'not_started'}), 200
    
    if ffmpeg_process.poll() is None:
        return jsonify({
            'status': 'running',
            'pid': ffmpeg_process.pid
        }), 200
    else:
        return jsonify({
            'status': 'stopped',
            'return_code': ffmpeg_process.returncode
        }), 200


@app.route('/stop', methods=['POST'])
def stop():
    """Stop ffmpeg process."""
    global ffmpeg_process
    
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=5)
            return jsonify({'status': 'stopped'}), 200
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
            return jsonify({'status': 'killed'}), 200
    
    return jsonify({'status': 'not_running'}), 200


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("\nShutting down ffmpeg...", file=sys.stderr)
        ffmpeg_process.terminate()
        ffmpeg_process.wait()
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Starting Flask server on port 5000...", file=sys.stderr)
    print(f"Owncast URL from env: {os.getenv('OWNCAST_URL', 'NOT SET')}", file=sys.stderr)
    print(f"Owncast URL variable: {OWNCAST_URL}", file=sys.stderr)
    print(f"MediaMTX source: {MEDIAMTX_SOURCE}", file=sys.stderr)
    
    # Validate OWNCAST_URL format
    if not OWNCAST_URL.startswith('rtmp://'):
        print(f"WARNING: OWNCAST_URL doesn't start with 'rtmp://': {OWNCAST_URL}", file=sys.stderr)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)

