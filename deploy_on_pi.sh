#!/bin/bash

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    log "Git is not installed. Installing git..."
    sudo apt-get update && sudo apt-get install -y git
fi

# Clone or update the repository
if [ ! -d "shoppy" ]; then
    log "Cloning the repository..."
    git clone https://github.com/jhacksman/shoppy.git
else
    log "Updating the repository..."
    cd shoppy
    git pull
    cd ..
fi

# Navigate to the project directory
cd shoppy

# Check if Python3 and venv are installed
if ! command -v python3 &> /dev/null || ! python3 -m venv --help &> /dev/null; then
    log "Python3 or venv is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y python3 python3-venv
fi

# Set up a Python virtual environment
log "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install the dependencies from the requirements.txt file
log "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the Flask server
log "Starting the Flask server..."
nohup python3 app.py > app.log 2>&1 &

log "Deployment completed successfully!"