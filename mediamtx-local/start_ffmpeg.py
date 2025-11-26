#!/usr/bin/env python3
"""
Python script to start sidecar ffmpeg service.
Called by mediamtx when the live path becomes ready.
"""
import time
import sys
import urllib.request
import urllib.error

FFMPEG_URL = "http://ffmpeg:5000/start/live"
SLEEP_DURATION = 1


def main():
    """Start the ffmpeg sidecar service."""
    # Wait a moment before making the request
    time.sleep(SLEEP_DURATION)
    
    try:
        # Make the HTTP request to start ffmpeg
        request = urllib.request.Request(FFMPEG_URL)
        response = urllib.request.urlopen(request, timeout=10)
        
        status_code = response.getcode()
        response_data = response.read().decode('utf-8')
        
        print(f"Successfully started ffmpeg: {status_code} - {response_data}", file=sys.stdout)
        sys.exit(0)
        
    except urllib.error.HTTPError as e:
        print(f"HTTP error starting ffmpeg: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL error starting ffmpeg: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error starting ffmpeg: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

