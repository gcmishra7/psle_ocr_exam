import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import os
import tempfile
from typing import List, Optional, Dict
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
    """Handles OCR processing of PDF files and images, optimized for educational content."""
    
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
            print("✅ pdf2image is available")
        except Exception as e:
            print(f"❌ pdf2image error: {e}")
            print("   Install poppler: brew install poppler (macOS)")
        
        # Test OpenCV
        if OPENCV_AVAILABLE:
            print("✅ OpenCV is available for advanced image processing")
        else:
            print("⚠️  OpenCV not available (will use basic preprocessing)")
    
    def preprocess_educational_image(self, image: Image.Image) -> Image.Image:
        """
        Advanced preprocessing optimized for educational content and diagrams.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object optimized for educational OCR
        """
        try:
            if OPENCV_AVAILABLE:
                return self._opencv_educational_preprocessing(image)
            else:
                return self._basic_educational_preprocessing(image)
        except Exception as e:
            print(f"⚠️  Advanced preprocessing failed: {e}, using basic processing")
            return self._basic_educational_preprocessing(image)
    
    def _opencv_educational_preprocessing(self, image: Image.Image) -> Image.Image:
        """Advanced OpenCV preprocessing for educational content."""
        # Convert PIL to OpenCV
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast for better text recognition
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Noise reduction while preserving text edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Adaptive thresholding optimized for educational content
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to connect text components
        kernel = np.ones((1,1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to PIL
        return Image.fromarray(processed)
    
    def _basic_educational_preprocessing(self, image: Image.Image) -> Image.Image:
        """Basic PIL preprocessing for educational content."""
        # Convert to grayscale
        gray_image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray_image)
        contrast_enhanced = enhancer.enhance(1.5)
        
        # Enhance sharpness for better text recognition
        sharpness_enhancer = ImageEnhance.Sharpness(contrast_enhanced)
        sharp_image = sharpness_enhancer.enhance(2.0)
        
        # Apply a slight blur to reduce noise
        smooth_image = sharp_image.filter(ImageFilter.SMOOTH_MORE)
        
        return smooth_image
    
    def extract_text_with_layout(self, image: Image.Image) -> Dict:
        """
        Extract text with layout information for better MCQ parsing.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with text and layout information
        """
        try:
            # Preprocess image for educational content
            processed_image = self.preprocess_educational_image(image)
            
            # Try multiple OCR configurations optimized for educational content
            configs = [
                # Standard configuration for educational content
                r'--oem 3 --psm 6 -l ' + self.language,
                # Better for single column text (like questions)
                r'--oem 3 --psm 4 -l ' + self.language,  
                # For mixed text and images
                r'--oem 3 --psm 3 -l ' + self.language,
                # For single text blocks
                r'--oem 3 --psm 8 -l ' + self.language,
                # For sparse text (good for MCQ options)
                r'--oem 3 --psm 11 -l ' + self.language,
            ]
            
            best_result = {"text": "", "confidence": 0}
            
            for config in configs:
                try:
                    # Get text with confidence scores
                    data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
                    
                    # Calculate average confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Get text
                    text = pytesseract.image_to_string(processed_image, config=config)
                    
                    if avg_confidence > best_result["confidence"] and text.strip():
                        best_result = {
                            "text": text.strip(),
                            "confidence": avg_confidence,
                            "config": config,
                            "layout_data": data
                        }
                        
                except Exception as e:
                    print(f"⚠️  OCR config failed: {config}, error: {e}")
                    continue
            
            # Fallback: try without custom config
            if not best_result["text"]:
                try:
                    text = pytesseract.image_to_string(processed_image)
                    best_result["text"] = text.strip()
                    best_result["confidence"] = 50  # Default confidence
                except Exception as e:
                    print(f"❌ Fallback OCR failed: {e}")
            
            return best_result
            
        except Exception as e:
            print(f"❌ Error extracting text with layout: {str(e)}")
            return {"text": "", "confidence": 0}
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from a single image using OCR optimized for educational content.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        result = self.extract_text_with_layout(image)
        return result.get("text", "")
    
    def pdf_to_text(self, pdf_path: str) -> str:
        """
        Convert PDF file to text using OCR optimized for educational content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from all pages with enhanced MCQ structure
        """
        try:
            print(f"📄 Converting PDF to images for educational content processing...")
            
            # Try different DPI settings optimized for educational content
            dpi_settings = [300, 200, 150]  # Start with higher DPI for better diagram quality
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
            
            extracted_pages = []
            
            for i, image in enumerate(images):
                print(f"🔍 Processing page {i + 1} of {len(images)} (Educational Content)...")
                
                # Extract text with layout information
                result = self.extract_text_with_layout(image)
                page_text = result.get("text", "")
                confidence = result.get("confidence", 0)
                
                if page_text:
                    page_header = f"--- Page {i + 1} (Confidence: {confidence:.1f}%) ---"
                    extracted_pages.append(f"{page_header}\n{page_text}\n")
                    print(f"✅ Page {i + 1}: Found {len(page_text)} characters (Confidence: {confidence:.1f}%)")
                else:
                    print(f"⚠️  Page {i + 1}: No text found")
            
            result_text = "\n".join(extracted_pages)
            print(f"📝 Total extracted text: {len(result_text)} characters")
            
            # Post-process for better MCQ structure
            enhanced_text = self.enhance_mcq_structure(result_text)
            
            return enhanced_text
            
        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            print("🔧 Troubleshooting tips for educational content:")
            print("   1. Ensure PDF is high quality (300+ DPI recommended)")
            print("   2. Check if PDF contains selectable text vs. scanned images")
            print("   3. For best results with diagrams, use clear, high-contrast images")
            print("   4. Make sure Tesseract and Poppler are properly installed")
            return ""
    
    def enhance_mcq_structure(self, text: str) -> str:
        """
        Post-process text to better structure MCQ questions.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Enhanced text with better MCQ structure
        """
        import re
        
        # Patterns for MCQ options
        option_patterns = [
            r'^\s*\([1-4A-Da-d]\)\s*',  # (1), (2), (A), (B)
            r'^\s*[1-4A-Da-d][\.\)]\s*',  # 1., 2., A., B.
            r'^\s*\([1-4A-Da-d]\s*\)\s*',  # ( 1 ), ( A )
        ]
        
        lines = text.split('\n')
        enhanced_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                enhanced_lines.append('')
                continue
            
            # Check if line is an MCQ option
            is_option = False
            for pattern in option_patterns:
                if re.match(pattern, line):
                    # Ensure proper spacing for options
                    line = f"    {line}"  # Indent options
                    is_option = True
                    break
            
            # Check for question numbers
            if re.match(r'^\s*\d+\.\s*', line) and not is_option:
                # Add extra spacing before questions
                if enhanced_lines and enhanced_lines[-1].strip():
                    enhanced_lines.append('')
                enhanced_lines.append(f"QUESTION {line}")
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def extract_from_uploaded_file(self, uploaded_file) -> str:
        """
        Extract text from uploaded file optimized for educational content.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Extracted text optimized for MCQ parsing
        """
        try:
            print(f"📁 Processing educational content: {uploaded_file.name}")
            print(f"📊 File size: {uploaded_file.size / 1024:.1f} KB")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
                print(f"💾 Saved to temporary file: {tmp_path}")
            
            # Extract text with educational optimizations
            text = self.pdf_to_text(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            print("🗑️  Temporary file cleaned up")
            
            return text
            
        except Exception as e:
            print(f"❌ Error processing uploaded educational file: {str(e)}")
            return ""