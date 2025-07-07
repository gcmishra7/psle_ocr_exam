#!/usr/bin/env python3
"""
Setup script for PDF Question Parser application.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def install_system_dependencies():
    """Install system-level dependencies for OCR"""
    print("🔧 Installing system dependencies...")
    
    # Check if tesseract is installed
    try:
        subprocess.run(["tesseract", "--version"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        print("✅ Tesseract OCR is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Tesseract OCR not found. Please install it manually:")
        print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("   macOS: brew install tesseract")
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        try:
            with open(".env.example", "r") as example:
                content = example.read()
            
            with open(".env", "w") as env:
                env.write(content)
            
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file and add your Gemini API key")
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
    else:
        print("✅ .env file already exists")

def create_data_directory():
    """Create data directory for database"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Data directory created")

def main():
    """Main setup function"""
    print("🚀 Setting up PDF Question Parser...")
    print("=" * 50)
    
    # Install system dependencies
    install_system_dependencies()
    print()
    
    # Install Python dependencies
    if not install_requirements():
        print("❌ Setup failed due to dependency installation error")
        return False
    print()
    
    # Create environment file
    create_env_file()
    print()
    
    # Create data directory
    create_data_directory()
    print()
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Edit the .env file and add your Gemini API key")
    print("2. Run the application: streamlit run main.py")
    print("   or: python main.py")
    print()
    print("🔧 If you encounter issues with OCR, ensure Tesseract is properly installed")
    
    return True

if __name__ == "__main__":
    main()