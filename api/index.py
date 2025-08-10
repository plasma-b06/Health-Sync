import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from app.py
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import the Flask app
from app import app

# This file should be placed in an 'api' folder
# Vercel will use this as the entry point for serverless functions