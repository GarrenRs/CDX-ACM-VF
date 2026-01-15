#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p static/assets/uploads

echo "Build completed successfully!"
