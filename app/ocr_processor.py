import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile
from typing import List, Optional
from config.settings import settings

# Try to import OpenCV, but make it optional
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️  OpenCV not available, using basic image processing")

class OCRProcessor:
    """Handles OCR processing of PDF files and images."""
    
    def __init__(self):
        """Initialize OCR processor with configuration."""
        self.setup_tesseract()
        self.language = settings.OCR_LANGUAGE
        self.test_dependencies()
    
    def setup_tesseract(self):
        """Setup Tesseract OCR with proper path detection."""
        # Try different common Tesseract paths
        possible_paths = [
            settings.TESSERACT_PATH,
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            'tesseract',  # Assume it's in PATH
        ]
        
        for path in possible_paths:
            if path and self.test_tesseract_path(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract found at: {path}")
                return
        
        print("❌ Tesseract OCR not found. Please install it:")
        print("   macOS: brew install tesseract")
        print("   Ubuntu: sudo apt-get install tesseract-ocr")
    
    def test_tesseract_path(self, path: str) -> bool:
        """Test if Tesseract is available at the given path."""
        try:
            import subprocess
            result = subprocess.run([path, '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def test_dependencies(self):
        """Test all dependencies and print diagnostic information."""
        print("🔧 Testing OCR dependencies...")
        
        # Test Tesseract
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract {version} is working")
        except Exception as e:
            print(f"❌ Tesseract error: {e}")
        
        # Test pdf2image
        try:
            # Create a small test to see if pdf2image works
            print("✅ pdf2image is available")
        except Exception as e:
            print(f"❌ pdf2image error: {e}")
            print("   Install poppler: brew install poppler (macOS)")
        
        # Test OpenCV
        if OPENCV_AVAILABLE:
            print("✅ OpenCV is available")
        else:
            print("⚠️  OpenCV not available (optional)")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        if not OPENCV_AVAILABLE:
            # Basic preprocessing without OpenCV
            return image.convert('L')  # Convert to grayscale
        
        try:
            # Convert PIL image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            return processed_image
        except Exception as e:
            print(f"OpenCV preprocessing failed: {e}, using basic processing")
            return image.convert('L')
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from a single image using OCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Try multiple OCR configurations
            configs = [
                r'--oem 3 --psm 6 -l ' + self.language,
                r'--oem 3 --psm 4 -l ' + self.language,
                r'--oem 3 --psm 3 -l ' + self.language,
                r'--oem 3 --psm 1 -l ' + self.language,
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    if text.strip():
                        return text.strip()
                except Exception as e:
                    print(f"OCR config failed: {config}, error: {e}")
                    continue
            
            # Fallback: try without custom config
            text = pytesseract.image_to_string(processed_image)
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting text from image: {str(e)}")
            return ""
    
    def pdf_to_text(self, pdf_path: str) -> str:
        """
        Convert PDF file to text using OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from all pages
        """
        try:
            print(f"📄 Converting PDF to images...")
            
            # Try different DPI settings
            dpi_settings = [200, 150, 300]
            images = None
            
            for dpi in dpi_settings:
                try:
                    images = convert_from_path(pdf_path, dpi=dpi)
                    print(f"✅ PDF converted to {len(images)} images at {dpi} DPI")
                    break
                except Exception as e:
                    print(f"❌ DPI {dpi} failed: {e}")
                    continue
            
            if not images:
                print("❌ Failed to convert PDF to images")
                return ""
            
            extracted_text = []
            
            for i, image in enumerate(images):
                print(f"🔍 Processing page {i + 1} of {len(images)}...")
                
                # Extract text from image
                page_text = self.extract_text_from_image(image)
                
                if page_text:
                    extracted_text.append(f"--- Page {i + 1} ---\n{page_text}\n")
                    print(f"✅ Page {i + 1}: Found {len(page_text)} characters")
                else:
                    print(f"⚠️  Page {i + 1}: No text found")
            
            result = "\n".join(extracted_text)
            print(f"📝 Total extracted text: {len(result)} characters")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            print("🔧 Troubleshooting tips:")
            print("   1. Make sure Tesseract is installed: brew install tesseract")
            print("   2. Make sure Poppler is installed: brew install poppler")
            print("   3. Check if the PDF is password protected")
            print("   4. Try a different PDF file")
            return ""
    
    def extract_from_uploaded_file(self, uploaded_file) -> str:
        """
        Extract text from uploaded file (for Streamlit integration).
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text
        """
        try:
            print(f"📁 Processing uploaded file: {uploaded_file.name}")
            print(f"📊 File size: {uploaded_file.size / 1024:.1f} KB")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
                print(f"💾 Saved to temporary file: {tmp_path}")
            
            # Extract text
            text = self.pdf_to_text(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            print("🗑️  Temporary file cleaned up")
            
            return text
            
        except Exception as e:
            print(f"❌ Error processing uploaded file: {str(e)}")
            return ""