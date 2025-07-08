#!/usr/bin/env python3
"""
Enhanced OCR System Diagnostic Script
=====================================
This script tests all components to identify processing failures.
"""

import sys
import os
import tempfile
from pathlib import Path
import traceback

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_basic_imports():
    """Test basic Python imports."""
    print_section("TESTING BASIC IMPORTS")
    
    imports = [
        ('os', 'Built-in OS module'),
        ('sys', 'Built-in System module'),
        ('pathlib', 'Built-in Path module'),
        ('tempfile', 'Built-in Temporary file module'),
        ('json', 'Built-in JSON module'),
    ]
    
    for module, description in imports:
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError as e:
            print(f"❌ {module}: Failed - {e}")
            return False
    
    return True

def test_external_dependencies():
    """Test external package imports."""
    print_section("TESTING EXTERNAL DEPENDENCIES")
    
    dependencies = [
        ('PIL', 'Pillow - Image processing'),
        ('pdf2image', 'PDF to image conversion'),
        ('pytesseract', 'Tesseract OCR wrapper'),
        ('google.generativeai', 'Google Gemini AI'),
        ('streamlit', 'Web framework'),
        ('pandas', 'Data manipulation'),
        ('sqlite3', 'Database support'),
    ]
    
    failed_imports = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError as e:
            print(f"❌ {module}: Failed - {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n🔧 To fix missing dependencies, run:")
        print(f"pip install {' '.join(failed_imports)}")
        return False
    
    return True

def test_system_commands():
    """Test system command availability."""
    print_section("TESTING SYSTEM COMMANDS")
    
    commands = [
        ('tesseract', 'tesseract --version'),
        ('poppler', 'pdftoppm -h'),
    ]
    
    import subprocess
    
    for name, command in commands:
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {name}: Available")
            else:
                print(f"❌ {name}: Command failed")
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ {name}: Command timeout")
            return False
        except FileNotFoundError:
            print(f"❌ {name}: Not found")
            print(f"   Install with: brew install {name} (macOS) or apt-get install {name}-ocr (Ubuntu)")
            return False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            return False
    
    return True

def test_configuration():
    """Test configuration and environment setup."""
    print_section("TESTING CONFIGURATION")
    
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        from config.settings import settings
        print("✅ Settings module imported successfully")
        
        # Check API key
        if settings.GEMINI_API_KEY:
            print("✅ Gemini API key is configured")
        else:
            print("❌ Gemini API key not found")
            print("   Add GEMINI_API_KEY to your .env file")
            return False
        
        # Check database path
        db_path = Path(settings.DATABASE_PATH)
        db_dir = db_path.parent
        
        if db_dir.exists():
            print(f"✅ Database directory exists: {db_dir}")
        else:
            print(f"🔧 Creating database directory: {db_dir}")
            db_dir.mkdir(parents=True, exist_ok=True)
        
        # Check images directory
        images_dir = Path("data/images")
        if images_dir.exists():
            print(f"✅ Images directory exists: {images_dir}")
        else:
            print(f"🔧 Creating images directory: {images_dir}")
            images_dir.mkdir(parents=True, exist_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connectivity."""
    print_section("TESTING DATABASE CONNECTION")
    
    try:
        from app.database_manager import DatabaseManager
        
        print("✅ DatabaseManager imported successfully")
        
        db = DatabaseManager()
        print("✅ Database connection established")
        
        # Test basic operations
        stats = db.get_statistics()
        print(f"✅ Database statistics retrieved: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        traceback.print_exc()
        return False

def test_image_processor():
    """Test image processing functionality."""
    print_section("TESTING IMAGE PROCESSOR")
    
    try:
        from app.image_processor import ImageProcessor
        
        print("✅ ImageProcessor imported successfully")
        
        processor = ImageProcessor()
        print("✅ ImageProcessor initialized")
        
        # Test image stats
        stats = processor.get_image_stats()
        print(f"✅ Image statistics retrieved: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Image processor error: {e}")
        traceback.print_exc()
        return False

def test_llm_parser():
    """Test LLM parser functionality."""
    print_section("TESTING LLM PARSER")
    
    try:
        from app.llm_parser import LLMParser
        
        print("✅ LLMParser imported successfully")
        
        parser = LLMParser()
        print("✅ LLMParser initialized (Gemini connection OK)")
        
        # Test basic validation
        test_data = {
            'metadata': {'subject': 'Test'},
            'questions': [],
            'unmatched_image_links': []
        }
        
        is_valid = parser.validate_parsed_data(test_data)
        print(f"✅ Data validation working: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM parser error: {e}")
        traceback.print_exc()
        return False

def test_ocr_processor():
    """Test OCR processor functionality."""
    print_section("TESTING OCR PROCESSOR")
    
    try:
        from app.ocr_processor import OCRProcessor
        
        print("✅ OCRProcessor imported successfully")
        
        processor = OCRProcessor()
        print("✅ OCRProcessor initialized")
        
        # Test stats
        stats = processor.get_processing_stats()
        print(f"✅ Processing statistics retrieved: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR processor error: {e}")
        traceback.print_exc()
        return False

def test_pdf_processing():
    """Test PDF processing with a simple test."""
    print_section("TESTING PDF PROCESSING")
    
    # Note: This test requires a PDF file to work
    # For now, we'll just test the import and initialization
    try:
        from pdf2image import convert_from_path, pdfinfo_from_path
        print("✅ PDF processing modules imported")
        
        # Test if we can create a simple test
        print("ℹ️  PDF processing test requires an actual PDF file")
        print("   Upload a PDF through the web interface to test full processing")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processing error: {e}")
        traceback.print_exc()
        return False

def test_streamlit_compatibility():
    """Test Streamlit compatibility."""
    print_section("TESTING STREAMLIT COMPATIBILITY")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Test if we're in a Streamlit context
        try:
            st.get_option("server.port")
            print("✅ Running in Streamlit context")
        except:
            print("ℹ️  Not currently running in Streamlit context (normal for debugging)")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit error: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🔍 Enhanced OCR System Diagnostic Tool")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("External Dependencies", test_external_dependencies),
        ("System Commands", test_system_commands),
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Image Processor", test_image_processor),
        ("LLM Parser", test_llm_parser),
        ("OCR Processor", test_ocr_processor),
        ("PDF Processing", test_pdf_processing),
        ("Streamlit Compatibility", test_streamlit_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            results.append((test_name, False))
    
    # Print summary
    print_section("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print()
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    if passed == total:
        print(f"\n🎉 All tests passed! Your system should be working correctly.")
        print(f"If you're still experiencing issues, the problem might be:")
        print(f"   • PDF file quality or format")
        print(f"   • Network connectivity for Gemini API")
        print(f"   • File permissions")
    else:
        print(f"\n🔧 Please fix the failing tests above and try again.")
        print(f"Common fixes:")
        print(f"   • pip install -r requirements.txt")
        print(f"   • brew install tesseract poppler (macOS)")
        print(f"   • sudo apt-get install tesseract-ocr poppler-utils (Ubuntu)")
        print(f"   • Add GEMINI_API_KEY to .env file")

if __name__ == "__main__":
    run_comprehensive_test()