#!/usr/bin/env python3
"""
🎓 Enhanced Quiz Application Launcher

A modern, interactive quiz application with smart content extraction and proper image rendering.

Features:
- Gradio-based modern UI
- Smart content extraction (diagrams, tables, equations)
- Interactive quiz navigation
- Proper image display
- Answer tracking and progress monitoring

Usage:
    python quiz_app.py

Requirements:
    pip install -r requirements.txt
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []
    
    try:
        import gradio
    except ImportError:
        missing_deps.append("gradio")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        from pdf2image import convert_from_path
    except ImportError:
        missing_deps.append("pdf2image")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  • {dep}")
        print("\nInstall missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """Set up the application environment."""
    # Create necessary directories
    directories = [
        "data",
        "data/images",
        "data/uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Environment setup completed")

def main():
    """Main application entry point."""
    print("🎓 Enhanced Quiz Application")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All dependencies found")
    
    # Setup environment
    print("🔧 Setting up environment...")
    setup_environment()
    
    # Import and launch the quiz app
    try:
        print("🚀 Launching quiz application...")
        from app.gradio_quiz_app import launch_quiz_app
        
        # Launch the application
        launch_quiz_app()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all components are properly installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Quiz application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()