#!/usr/bin/env python3
"""
🎓 Enhanced Quiz System - Complete Application

This application provides both PDF processing capabilities and a modern quiz interface.

Features:
- PDF processing with smart content extraction
- Modern Gradio-based quiz interface
- Streamlit admin interface for processing
- Automatic image path fixing and optimization

Usage:
    python enhanced_main.py --mode [streamlit|gradio|both]
"""

import argparse
import sys
import subprocess
import threading
import time
from pathlib import Path

def launch_streamlit():
    """Launch the Streamlit PDF processing interface."""
    print("🚀 Starting Streamlit PDF Processing Interface...")
    print("📍 URL: http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py", "--server.port=8501"])

def launch_gradio():
    """Launch the Gradio quiz interface."""
    print("🎓 Starting Gradio Quiz Interface...")
    print("📍 URL: http://localhost:7860")
    subprocess.run([sys.executable, "quiz_app.py"])

def launch_both():
    """Launch both interfaces simultaneously."""
    print("🔥 Starting Enhanced Quiz System with Both Interfaces...")
    print("📊 Streamlit (PDF Processing): http://localhost:8501")
    print("🎓 Gradio (Quiz): http://localhost:7860")
    print("=" * 60)
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=launch_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Wait a moment for Streamlit to start
    time.sleep(3)
    
    # Start Gradio in main thread
    launch_gradio()

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Enhanced Quiz System")
    parser.add_argument(
        "--mode", 
        choices=["streamlit", "gradio", "both"], 
        default="both",
        help="Launch mode: streamlit (PDF processing), gradio (quiz), or both"
    )
    
    args = parser.parse_args()
    
    print("🎓 Enhanced Quiz System")
    print("=" * 50)
    print("✨ Smart Content Extraction + Modern Quiz Interface")
    print("")
    
    if args.mode == "streamlit":
        print("📊 PDF Processing Mode")
        launch_streamlit()
    elif args.mode == "gradio":
        print("🎓 Quiz Mode")
        launch_gradio()
    else:
        print("🔥 Complete System Mode")
        launch_both()

if __name__ == "__main__":
    main()