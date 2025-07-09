#!/usr/bin/env python3
"""
🎓 Simple Quiz System Launcher

This launcher checks for essential dependencies and starts the quiz system
with graceful fallbacks if some components are missing.
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_and_install_essential():
    """Check for essential packages and offer to install if missing."""
    essential_packages = {
        'streamlit': 'streamlit>=1.28.0',
        'gradio': 'gradio>=4.0.0',
        'PIL': 'Pillow>=10.1.0',
        'pandas': 'pandas>=2.1.0'
    }
    
    missing = []
    
    for module, package in essential_packages.items():
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - not installed")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Missing packages: {', '.join(missing)}")
        install = input("Install missing packages? (y/N): ").lower().strip()
        
        if install in ['y', 'yes']:
            for package in missing:
                try:
                    print(f"Installing {package}...")
                    subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
                    print(f"✅ {package} installed")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to install {package}: {e}")
                    return False
        else:
            print("❌ Cannot start without essential packages")
            return False
    
    return True

def start_gradio_quiz():
    """Start the Gradio quiz interface."""
    try:
        print("🎓 Starting Gradio Quiz Interface...")
        print("📍 URL: http://localhost:7860")
        from app.gradio_quiz_app import launch_quiz_app
        launch_quiz_app()
    except ImportError as e:
        print(f"❌ Cannot start Gradio interface: {e}")
        print("Please run: python setup_quiz_system.py")
        return False
    except Exception as e:
        print(f"❌ Error starting quiz: {e}")
        return False

def start_streamlit_processing():
    """Start the Streamlit PDF processing interface."""
    try:
        print("📊 Starting Streamlit PDF Processing...")
        print("📍 URL: http://localhost:8501")
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'main.py', '--server.port=8501'])
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        return False

def main():
    """Main launcher function."""
    print("🎓 Enhanced Quiz System Launcher")
    print("=" * 40)
    
    # Check essential dependencies
    if not check_and_install_essential():
        print("Setup required. Run: python setup_quiz_system.py")
        sys.exit(1)
    
    # Choose launch mode
    print("\nChoose launch mode:")
    print("1. 🎓 Quiz Interface Only (Gradio)")
    print("2. 📊 PDF Processing Only (Streamlit)")
    print("3. 🔥 Both (Recommended)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        start_gradio_quiz()
    elif choice == "2":
        start_streamlit_processing()
    elif choice == "3":
        # Start both
        import threading
        import time
        
        print("🔥 Starting both interfaces...")
        
        # Start Streamlit in background
        streamlit_thread = threading.Thread(
            target=start_streamlit_processing, 
            daemon=True
        )
        streamlit_thread.start()
        
        # Wait and start Gradio
        time.sleep(3)
        start_gradio_quiz()
    else:
        print("Invalid choice. Starting quiz interface...")
        start_gradio_quiz()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Launcher stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        sys.exit(1)