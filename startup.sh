#!/bin/bash
# Startup script for VentureAI API

# Ensure environment variables are set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set, trying to find credentials file..."
    # Try to find credentials file
    if [ -f "vc-interview-service-account.json" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="vc-interview-service-account.json"
        echo "Found vc-interview-service-account.json and set it as GOOGLE_APPLICATION_CREDENTIALS"
    fi
fi

# Fix numpy issues
echo "Ensuring correct numpy version..."
pip uninstall -y numpy
pip install numpy==1.24.3

# Check for API key
if [ -z "$API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "Warning: Neither API_KEY nor GOOGLE_API_KEY are set"
else
    if [ -n "$API_KEY" ]; then
        echo "API_KEY is set"
    fi
    if [ -n "$GOOGLE_API_KEY" ]; then
        echo "GOOGLE_API_KEY is set"
    fi
fi

# Check for required directories
for dir in "sessions" "uploads" "data" "keys"; do
    if [ ! -d "$dir" ]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

# Make sure credentials file is readable
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    chmod 644 "$GOOGLE_APPLICATION_CREDENTIALS" 2>/dev/null || true
fi

# Start the application
echo "Starting VentureAI API..."
exec python main.py 