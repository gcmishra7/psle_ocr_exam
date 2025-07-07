#!/bin/bash

# PDF Question Parser - Startup Script
# This script sets up and runs the PDF Question Parser application

echo "🚀 Starting PDF Question Parser..."
echo "================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed or not in PATH"
    echo "Please install pip and try again"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Install/upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please check requirements.txt and try again"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created"
        echo "⚠️  Please edit .env file and add your Gemini API key before continuing"
        echo "You can continue now and add the API key later through the web interface"
    else
        echo "❌ .env.example file not found"
        exit 1
    fi
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR not found. OCR functionality may not work properly."
    echo "To install Tesseract:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    echo "You can continue without Tesseract, but PDF processing may fail."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please install Tesseract and try again"
        exit 1
    fi
else
    echo "✅ Tesseract OCR found"
fi

# Check for Gemini API key
if grep -q "your_gemini_api_key_here" .env; then
    echo "⚠️  Gemini API key not configured in .env file"
    echo "The application will start but PDF processing will fail until you add your API key"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
fi

echo ""
echo "================================="
echo "✅ Setup completed successfully!"
echo ""
echo "🌐 Starting Streamlit application..."
echo "📝 Access the application at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo "================================="
echo ""

# Start the application
python main.py

# Deactivate virtual environment on exit
deactivate