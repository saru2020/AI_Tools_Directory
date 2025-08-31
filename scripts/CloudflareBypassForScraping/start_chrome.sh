#!/bin/bash

# Start Chrome with debugging enabled
echo "Starting Chrome with debugging on port 9222..."

# Close any existing Chrome processes
pkill -f "Google Chrome" 2>/dev/null
sleep 2

# Start Chrome with debugging
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir="/tmp/chrome_debug" \
    --no-first-run \
    --disable-background-mode

echo "Chrome started with debugging on port 9222"
echo "Now run: python test_connection.py"
