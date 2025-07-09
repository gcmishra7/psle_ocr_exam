#!/usr/bin/env python3
"""
🚀 Quick Install - Enhanced Quiz System

One-file installer that handles pip errors and gets you running immediately.
Minimal dependencies, maximum compatibility.
"""

import sys
import subprocess
import os

def quick_install():
    """Quick installation with error handling."""
    print("🚀 Quick Install - Enhanced Quiz System")
    print("=" * 50)
    
    # Essential packages only
    packages = ["streamlit", "gradio", "Pillow", "pandas"]
    
    print("📦 Installing essential packages...")
    
    for package in packages:
        print(f"\n⏳ Installing {package}...")
        
        # Try different methods
        methods = [
            [sys.executable, "-m", "pip", "install", package, "--no-cache-dir"],
            [sys.executable, "-m", "pip", "install", package, "--user"],
            [sys.executable, "-m", "pip", "install", package, "--force-reinstall"]
        ]
        
        success = False
        for i, cmd in enumerate(methods, 1):
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=180)
                print(f"✅ {package} installed (method {i})")
                success = True
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if i < len(methods):
                    print(f"⚠️  Method {i} failed, trying method {i+1}...")
                continue
        
        if not success:
            print(f"❌ {package} failed - trying to continue...")
    
    # Test what we have
    print("\n🧪 Testing installation...")
    working = []
    
    for package in ["streamlit", "gradio", "PIL", "pandas"]:
        try:
            __import__(package)
            print(f"✅ {package}")
            working.append(package)
        except ImportError:
            print(f"❌ {package}")
    
    # Create basic structure
    print("\n📁 Setting up directories...")
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    # Create basic .env
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("DATABASE_PATH=./data/questions.db\n")
        print("✅ Created .env file")
    
    # Results
    print("\n" + "=" * 50)
    if len(working) >= 2:  # Need at least 2 core packages
        print("🎉 SUCCESS! Basic installation complete!")
        print(f"✅ Working: {', '.join(working)}")
        print("\n🚀 To start:")
        
        if "gradio" in working:
            print("   python -c \"from app.gradio_quiz_app import launch_quiz_app; launch_quiz_app()\"")
        
        if "streamlit" in working:
            print("   python -m streamlit run main.py")
        
        print("\n📚 Or use: python start_quiz.py")
    else:
        print("❌ Installation incomplete")
        print("Try manual installation:")
        print("   pip install streamlit gradio Pillow pandas")
    
    print("=" * 50)

if __name__ == "__main__":
    try:
        quick_install()
    except Exception as e:
        print(f"❌ Quick install failed: {e}")
        print("\nTry manual installation:")
        print("pip install streamlit gradio Pillow pandas")
        sys.exit(1)