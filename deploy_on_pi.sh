#!/bin/bash

# Clone the repository
git clone https://github.com/jhacksman/shoppy.git

# Navigate to the project directory
cd shoppy

# Set up a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the dependencies from the requirements.txt file
pip install -r requirements.txt

# Start the Flask server
python3 app.py