#!/usr/bin/env python3
"""
🎓 Enhanced Quiz System - Smart Setup Script

This script handles the installation and setup of the quiz system with better error handling.
"""

import sys
import subprocess
import os
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("🎓 Enhanced Quiz System Setup")
    print("=" * 50)
    print("✨ Smart Content Extraction + Modern Quiz Interface")
    print("")

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_essential_packages():
    """Install essential packages one by one with error handling."""
    essential_packages = [
        "streamlit>=1.28.0",
        "gradio>=4.0.0", 
        "Pillow>=10.1.0",
        "pandas>=2.1.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0"
    ]
    
    print("📦 Installing essential packages...")
    
    for package in essential_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Failed to install {package}")
            print(f"     Error: {e}")
            return False
    
    return True

def install_optional_packages():
    """Install optional packages for enhanced functionality."""
    optional_packages = [
        ("pdf2image>=1.17.0", "PDF processing"),
        ("pytesseract>=0.3.10", "OCR functionality"),
        ("opencv-python-headless>=4.8.0", "Smart image extraction"),
        ("scikit-image>=0.21.0", "Image processing")
    ]
    
    print("📦 Installing optional packages...")
    
    for package, description in optional_packages:
        try:
            print(f"  Installing {package} ({description})...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Failed to install {package} - {description} will be limited")

def install_ai_packages():
    """Install AI packages if requested."""
    ai_packages = [
        ("google-generativeai>=0.3.0", "Google Gemini AI"),
        ("openai>=1.0.0", "OpenAI GPT models"),
        ("anthropic>=0.7.0", "Anthropic Claude")
    ]
    
    print("\n🤖 AI packages (optional for enhanced processing):")
    for package, description in ai_packages:
        print(f"  • {description}")
    
    install_ai = input("\nInstall AI packages? (y/N): ").lower().strip()
    
    if install_ai in ['y', 'yes']:
        print("📦 Installing AI packages...")
        for package, description in ai_packages:
            try:
                print(f"  Installing {package}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=True, capture_output=True)
                print(f"  ✅ {package}")
            except subprocess.CalledProcessError as e:
                print(f"  ⚠️  Failed to install {package}")

def setup_directories():
    """Set up necessary directories."""
    directories = [
        "data",
        "data/images", 
        "data/uploads",
        "config"
    ]
    
    print("📁 Setting up directories...")
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {directory}")
        except Exception as e:
            print(f"  ⚠️  Failed to create {directory}: {e}")

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            try:
                env_example.read_text()
                with open(env_file, 'w') as f:
                    f.write(env_example.read_text())
                print("✅ Created .env file from template")
            except Exception as e:
                print(f"⚠️  Could not copy .env.example: {e}")
        else:
            # Create basic .env file
            try:
                with open(env_file, 'w') as f:
                    f.write("""# Enhanced Quiz System Configuration
# Add your API keys here (optional for basic functionality)

# Google Gemini (recommended for AI features)
GEMINI_API_KEY=your_gemini_key_here

# OpenAI (alternative)
OPENAI_API_KEY=your_openai_key_here

# Anthropic Claude (alternative)  
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database path
DATABASE_PATH=./data/questions.db
""")
                print("✅ Created basic .env file")
            except Exception as e:
                print(f"⚠️  Could not create .env file: {e}")
    else:
        print("✅ .env file already exists")

def test_installation():
    """Test if the installation was successful."""
    print("🧪 Testing installation...")
    
    required_modules = [
        ("streamlit", "Streamlit web framework"),
        ("gradio", "Gradio quiz interface"),
        ("PIL", "Image processing")
    ]
    
    all_good = True
    
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ❌ {description} - not available")
            all_good = False
    
    # Test optional modules
    optional_modules = [
        ("cv2", "OpenCV for smart extraction"),
        ("pdf2image", "PDF to image conversion"),
        ("numpy", "Numerical computations")
    ]
    
    for module, description in optional_modules:
        try:
            __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ⚠️  {description} - limited functionality")
    
    return all_good

def print_usage_instructions():
    """Print usage instructions."""
    print("\n🚀 Setup Complete!")
    print("=" * 50)
    print("To start the Enhanced Quiz System:")
    print("")
    print("1. Complete System (Recommended):")
    print("   python enhanced_main.py --mode both")
    print("   • PDF Processing: http://localhost:8501")
    print("   • Quiz Interface: http://localhost:7860")
    print("")
    print("2. Quiz Only:")
    print("   python enhanced_main.py --mode gradio")
    print("   • Quiz Interface: http://localhost:7860")
    print("")
    print("3. PDF Processing Only:")
    print("   python enhanced_main.py --mode streamlit")
    print("   • PDF Processing: http://localhost:8501")
    print("")
    print("📚 For detailed instructions, see: QUICK_START_GUIDE.md")
    print("")

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install packages
    print("\n📦 Installing Dependencies...")
    if not install_essential_packages():
        print("❌ Essential package installation failed")
        print("Try installing manually:")
        print("pip install streamlit gradio Pillow pandas python-dotenv numpy")
        sys.exit(1)
    
    install_optional_packages()
    install_ai_packages()
    
    # Setup environment
    print("\n🔧 Setting up environment...")
    setup_directories()
    create_env_file()
    
    # Test installation
    print("\n🧪 Testing installation...")
    if test_installation():
        print("✅ All essential components installed successfully!")
    else:
        print("⚠️  Some components failed to install - basic functionality available")
    
    print_usage_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)