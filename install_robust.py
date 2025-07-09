#!/usr/bin/env python3
"""
🎓 Robust Quiz System Installer

This installer handles common pip/network errors and provides multiple
installation methods to ensure successful setup.
"""

import sys
import subprocess
import time
import os
from pathlib import Path

def print_banner():
    """Print installation banner."""
    print("🎓 Robust Quiz System Installer")
    print("=" * 50)
    print("🔧 Handles pip errors and network issues")
    print("✨ Multiple installation methods")
    print("")

def upgrade_pip():
    """Upgrade pip to latest version to avoid common issues."""
    print("🔄 Upgrading pip to latest version...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, capture_output=True, text=True)
        print("✅ Pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("⚠️  Pip upgrade failed, continuing with current version...")
        return False

def install_package_with_retry(package, max_retries=3):
    """Install a package with retry logic and different methods."""
    
    # Different installation methods to try
    methods = [
        # Method 1: Standard installation
        [sys.executable, "-m", "pip", "install", package],
        
        # Method 2: With no cache
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", package],
        
        # Method 3: With user flag
        [sys.executable, "-m", "pip", "install", "--user", package],
        
        # Method 4: Force reinstall
        [sys.executable, "-m", "pip", "install", "--force-reinstall", package],
        
        # Method 5: With different index
        [sys.executable, "-m", "pip", "install", "--index-url", "https://pypi.org/simple/", package]
    ]
    
    for method_num, cmd in enumerate(methods, 1):
        for attempt in range(max_retries):
            try:
                print(f"  Method {method_num}, Attempt {attempt + 1}: Installing {package}...")
                
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                print(f"  ✅ {package} installed successfully")
                return True
                
            except subprocess.TimeoutExpired:
                print(f"  ⏰ Installation timeout for {package}")
                continue
                
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Method {method_num}, Attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    print("  🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                continue
                
            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                continue
    
    print(f"  ❌ All installation methods failed for {package}")
    return False

def install_essential_packages():
    """Install essential packages with robust error handling."""
    
    # Core packages needed for the quiz system
    essential_packages = [
        "setuptools",  # Install setuptools first
        "wheel",       # Install wheel for better package building
        "streamlit>=1.28.0",
        "gradio>=4.0.0",
        "Pillow>=10.1.0",
        "pandas>=2.1.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0"
    ]
    
    print("📦 Installing essential packages...")
    
    failed_packages = []
    
    for package in essential_packages:
        print(f"\n📦 Installing {package}...")
        
        if install_package_with_retry(package):
            print(f"✅ {package} - SUCCESS")
        else:
            print(f"❌ {package} - FAILED")
            failed_packages.append(package)
    
    return failed_packages

def install_optional_packages():
    """Install optional packages for enhanced functionality."""
    
    optional_packages = [
        ("pdf2image>=1.17.0", "PDF to image conversion"),
        ("pytesseract>=0.3.10", "OCR functionality"),
        ("opencv-python-headless>=4.8.0", "Smart image extraction"),
        ("scikit-image>=0.21.0", "Advanced image processing")
    ]
    
    print("\n📦 Installing optional packages...")
    
    for package, description in optional_packages:
        print(f"\n📦 Installing {package} ({description})...")
        
        if install_package_with_retry(package, max_retries=2):
            print(f"✅ {package} - SUCCESS")
        else:
            print(f"⚠️  {package} - FAILED (optional, continuing...)")

def test_installation():
    """Test if core packages are working."""
    print("\n🧪 Testing installation...")
    
    tests = [
        ("streamlit", "Streamlit web framework"),
        ("gradio", "Gradio quiz interface"),
        ("PIL", "Image processing (Pillow)"),
        ("pandas", "Data handling"),
        ("numpy", "Numerical computing")
    ]
    
    working = []
    failed = []
    
    for module, description in tests:
        try:
            __import__(module)
            print(f"  ✅ {description}")
            working.append(module)
        except ImportError:
            print(f"  ❌ {description} - Not available")
            failed.append(module)
    
    return working, failed

def create_directories():
    """Create necessary directories."""
    directories = [
        "data",
        "data/images",
        "data/uploads",
        "config"
    ]
    
    print("\n📁 Creating directories...")
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {directory}")
        except Exception as e:
            print(f"  ❌ {directory}: {e}")

def create_basic_env():
    """Create a basic .env file."""
    env_content = """# Enhanced Quiz System Configuration
# Basic configuration for local development

# Database (using SQLite - no additional setup needed)
DATABASE_PATH=./data/questions.db

# Optional: Add API keys for enhanced AI features
# GEMINI_API_KEY=your_gemini_key_here
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Server settings
APP_PORT=8501
QUIZ_PORT=7860
"""
    
    try:
        if not Path(".env").exists():
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Created .env configuration file")
        else:
            print("✅ .env file already exists")
    except Exception as e:
        print(f"⚠️  Could not create .env file: {e}")

def provide_manual_instructions():
    """Provide manual installation instructions."""
    print("\n" + "=" * 60)
    print("📖 MANUAL INSTALLATION INSTRUCTIONS")
    print("=" * 60)
    print()
    print("If the automatic installation failed, try these manual steps:")
    print()
    print("1. Upgrade pip:")
    print("   pip install --upgrade pip")
    print()
    print("2. Install packages individually:")
    print("   pip install streamlit")
    print("   pip install gradio")
    print("   pip install Pillow")
    print("   pip install pandas")
    print("   pip install python-dotenv")
    print("   pip install numpy")
    print()
    print("3. Test installation:")
    print("   python -c \"import streamlit, gradio, PIL; print('Success!')\"")
    print()
    print("4. Start the quiz system:")
    print("   python start_quiz.py")
    print()
    print("=" * 60)

def main():
    """Main installation function."""
    print_banner()
    
    # Step 1: Upgrade pip
    upgrade_pip()
    
    # Step 2: Install essential packages
    failed_packages = install_essential_packages()
    
    # Step 3: Install optional packages
    install_optional_packages()
    
    # Step 4: Test installation
    working, failed = test_installation()
    
    # Step 5: Setup environment
    print("\n🔧 Setting up environment...")
    create_directories()
    create_basic_env()
    
    # Step 6: Report results
    print("\n" + "=" * 60)
    print("📊 INSTALLATION SUMMARY")
    print("=" * 60)
    
    if len(working) >= 4:  # Need at least streamlit, gradio, PIL, pandas
        print("🎉 SUCCESS! Core components installed successfully!")
        print()
        print("✅ Working components:")
        for module in working:
            print(f"  • {module}")
        
        if failed:
            print("\n⚠️  Optional components that failed:")
            for module in failed:
                print(f"  • {module}")
        
        print("\n🚀 To start the quiz system:")
        print("   python start_quiz.py")
        print()
        print("Or run individual components:")
        print("   python enhanced_main.py --mode gradio    # Quiz interface")
        print("   python enhanced_main.py --mode streamlit # PDF processing")
        print()
        
    else:
        print("❌ Installation incomplete. Essential components missing.")
        print()
        print("✅ Successfully installed:")
        for module in working:
            print(f"  • {module}")
        
        print("\n❌ Failed to install:")
        for module in failed:
            print(f"  • {module}")
        
        provide_manual_instructions()
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Installation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        import traceback
        traceback.print_exc()
        provide_manual_instructions()
        sys.exit(1)