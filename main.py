#!/usr/bin/env python3
"""
PDF Question Parser - Main Application Entry Point

This is the main entry point for the PDF OCR Question Parser application.
Run this file to start the Streamlit web interface.

Usage:
    streamlit run main.py
    
or

    python main.py
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from config.settings import settings
    from app.streamlit_ui import main
    
    if __name__ == "__main__":
        # Validate settings before starting
        try:
            settings.validate_settings()
            print(f"✅ Starting {settings.APP_TITLE}...")
            print(f"🌐 Access the application at: http://localhost:{settings.APP_PORT}")
            
            # Run the Streamlit app
            main()
            
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("Please check your .env file and ensure all required settings are configured.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Application Error: {e}")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)