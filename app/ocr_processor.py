import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
import os
import tempfile
from typing import List, Optional
from config.settings import settings

class OCRProcessor:
    """Handles OCR processing of PDF files and images."""
    
    def __init__(self):
        """Initialize OCR processor with configuration."""
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
        self.language = settings.OCR_LANGUAGE
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
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
            
            # Configure OCR settings
            custom_config = r'--oem 3 --psm 6 -l ' + self.language
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)
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
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200)
            
            extracted_text = []
            
            for i, image in enumerate(images):
                print(f"Processing page {i + 1} of {len(images)}...")
                
                # Extract text from image
                page_text = self.extract_text_from_image(image)
                
                if page_text:
                    extracted_text.append(f"--- Page {i + 1} ---\n{page_text}\n")
            
            return "\n".join(extracted_text)
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
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
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract text
            text = self.pdf_to_text(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return text
            
        except Exception as e:
            print(f"Error processing uploaded file: {str(e)}")
            return ""