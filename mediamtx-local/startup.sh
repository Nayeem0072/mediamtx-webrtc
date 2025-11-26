#!/bin/sh
set -e

# Check if Python is installed, if not install it
if ! command -v python3 >/dev/null 2>&1; then
    echo "Installing Python and pip..."
    apk add --no-cache python3 py3-pip
else
    echo "Python already installed"
fi

# Check if Flask is installed, if not install it
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask and flask-cors..."
    pip install flask flask-cors
else
    echo "Flask already installed"
fi

# Check if flask-cors is installed, if not install it
if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo "Installing flask-cors..."
    pip install flask-cors
else
    echo "flask-cors already installed"
fi

echo "Starting Flask server..."
exec python3 /start_server.py

