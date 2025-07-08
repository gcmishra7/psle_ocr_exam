#!/usr/bin/env python3
"""
Test script to diagnose OCR issues.
"""

import sys
import os
from pathlib import Path

def test_dependencies():
    """Test all OCR dependencies."""
    print("🔧 Testing OCR Dependencies...")
    print("=" * 50)
    
    # Test 1: Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract {version} is working")
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        print("   Solution: brew install tesseract")
        return False
    
    # Test 2: pdf2image
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image is available")
    except Exception as e:
        print(f"❌ pdf2image error: {e}")
        print("   Solution: brew install poppler")
        return False
    
    # Test 3: PIL
    try:
        from PIL import Image
        print("✅ PIL (Pillow) is available")
    except Exception as e:
        print(f"❌ PIL error: {e}")
        print("   Solution: pip3 install Pillow")
        return False
    
    return True

def test_simple_ocr():
    """Test OCR with a simple text image."""
    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Use default font
        try:
            # Try to use a better font if available
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), "Hello World Test", fill='black', font=font)
        
        # Test OCR on this simple image
        text = pytesseract.image_to_string(img)
        
        if "Hello" in text or "World" in text:
            print("✅ Basic OCR is working")
            print(f"   Extracted text: '{text.strip()}'")
            return True
        else:
            print(f"⚠️  OCR extracted: '{text.strip()}' (should contain 'Hello World')")
            return False
            
    except Exception as e:
        print(f"❌ Basic OCR test failed: {e}")
        return False

def test_pdf_conversion(pdf_path):
    """Test PDF to image conversion."""
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    try:
        from pdf2image import convert_from_path
        
        print(f"📄 Testing PDF conversion: {pdf_path}")
        
        # Try to convert first page only
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        
        if images:
            print(f"✅ PDF converted to {len(images)} image(s)")
            print(f"   Image size: {images[0].size}")
            
            # Test OCR on the first image
            import pytesseract
            text = pytesseract.image_to_string(images[0])
            
            if text.strip():
                print(f"✅ OCR extracted text from PDF")
                print(f"   Text length: {len(text)} characters")
                print(f"   First 100 chars: {text[:100]}...")
                return True
            else:
                print("❌ No text extracted from PDF image")
                print("   This might be an image-only PDF or low quality scan")
                return False
        else:
            print("❌ No images generated from PDF")
            return False
            
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 OCR Diagnostic Tool")
    print("=" * 50)
    
    # Test 1: Dependencies
    if not test_dependencies():
        print("\n❌ Dependencies test failed. Install missing components and try again.")
        return
    
    print("\n" + "=" * 50)
    
    # Test 2: Basic OCR
    if not test_simple_ocr():
        print("\n⚠️  Basic OCR test failed. There might be a Tesseract configuration issue.")
    
    print("\n" + "=" * 50)
    
    # Test 3: PDF file (if provided)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_pdf_conversion(pdf_path)
    else:
        print("💡 To test a specific PDF file, run:")
        print("   python3 test_ocr.py /path/to/your/file.pdf")
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete!")

if __name__ == "__main__":
    main()