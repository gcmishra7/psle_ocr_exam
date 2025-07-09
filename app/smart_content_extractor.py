import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tempfile
import os
from pdf2image import convert_from_path

class SmartContentExtractor:
    """
    Smart content extractor that identifies and extracts specific content regions
    like diagrams, tables, and figures instead of whole pages.
    """
    
    def __init__(self):
        """Initialize the smart content extractor."""
        self.images_dir = Path("data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Parameters for content detection
        self.min_content_area = 15000  # Minimum area for content regions
        self.min_aspect_ratio = 0.3   # Minimum width/height ratio
        self.max_aspect_ratio = 5.0   # Maximum width/height ratio
        
    def extract_smart_content(self, pdf_path: str, source_filename: str) -> Tuple[List[Dict], List[str]]:
        """
        Extract smart content from PDF including diagrams, tables, and figures.
        
        Args:
            pdf_path: Path to PDF file
            source_filename: Original filename
            
        Returns:
            Tuple of (content_info_list, content_links_list)
        """
        try:
            print(f"🔍 Smart content extraction from: {source_filename}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300, fmt='PNG')
            
            content_info_list = []
            content_links_list = []
            
            # Create subdirectory for this PDF's content
            pdf_name = Path(source_filename).stem
            pdf_content_dir = self.images_dir / pdf_name
            pdf_content_dir.mkdir(exist_ok=True)
            
            for page_num, pil_image in enumerate(images, 1):
                print(f"📄 Analyzing page {page_num} for content...")
                
                # Convert PIL to OpenCV format
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                
                # Extract different types of content
                page_contents = self._extract_page_content(cv_image, pil_image, pdf_name, page_num, pdf_content_dir, source_filename)
                
                for content in page_contents:
                    content_info_list.append(content)
                    content_links_list.append(f"/images/{pdf_name}/{content['stored_filename']}")
            
            print(f"✅ Smart extraction completed: {len(content_info_list)} content items found")
            return content_info_list, content_links_list
            
        except Exception as e:
            print(f"❌ Error in smart content extraction: {e}")
            return [], []
    
    def _extract_page_content(self, cv_image: np.ndarray, pil_image: Image.Image, 
                             pdf_name: str, page_num: int, pdf_content_dir: Path, 
                             source_filename: str) -> List[Dict]:
        """Extract different types of content from a page."""
        content_list = []
        
        # 1. Extract diagrams and figures
        diagrams = self._extract_diagrams(cv_image, pil_image, pdf_name, page_num, pdf_content_dir, source_filename)
        content_list.extend(diagrams)
        
        # 2. Extract tables
        tables = self._extract_tables(cv_image, pil_image, pdf_name, page_num, pdf_content_dir, source_filename)
        content_list.extend(tables)
        
        # 3. Extract mathematical expressions/equations
        equations = self._extract_equations(cv_image, pil_image, pdf_name, page_num, pdf_content_dir, source_filename)
        content_list.extend(equations)
        
        # 4. If no specific content found, save a representative crop (not full page)
        if not content_list:
            representative = self._extract_representative_content(cv_image, pil_image, pdf_name, page_num, pdf_content_dir, source_filename)
            if representative:
                content_list.append(representative)
        
        return content_list
    
    def _extract_diagrams(self, cv_image: np.ndarray, pil_image: Image.Image, 
                         pdf_name: str, page_num: int, pdf_content_dir: Path, 
                         source_filename: str) -> List[Dict]:
        """Extract diagram regions using contour detection."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            diagrams = []
            diagram_count = 0
            
            for contour in contours:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Filter based on size and aspect ratio
                if (area > self.min_content_area and 
                    self.min_aspect_ratio < aspect_ratio < self.max_aspect_ratio and
                    w > 150 and h > 150):
                    
                    # Add padding
                    padding = 20
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract region
                    region = pil_image.crop((x, y, x + w, y + h))
                    
                    # Save diagram
                    diagram_count += 1
                    filename = f"{pdf_name}_page_{page_num}_diagram_{diagram_count}.png"
                    file_path = pdf_content_dir / filename
                    region.save(file_path, "PNG", optimize=True)
                    
                    # Create content info
                    content_info = {
                        'original_filename': f"page_{page_num}_diagram_{diagram_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'diagram',
                        'width': w,
                        'height': h,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    }
                    
                    diagrams.append(content_info)
                    print(f"📊 Extracted diagram {diagram_count} from page {page_num}")
            
            return diagrams
            
        except Exception as e:
            print(f"❌ Error extracting diagrams: {e}")
            return []
    
    def _extract_tables(self, cv_image: np.ndarray, pil_image: Image.Image, 
                       pdf_name: str, page_num: int, pdf_content_dir: Path, 
                       source_filename: str) -> List[Dict]:
        """Extract table regions using line detection."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines to find table structure
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours of potential tables
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tables = []
            table_count = 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for table-like regions
                if area > 20000 and w > 200 and h > 100:
                    # Add padding
                    padding = 15
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract table region
                    table_region = pil_image.crop((x, y, x + w, y + h))
                    
                    # Save table
                    table_count += 1
                    filename = f"{pdf_name}_page_{page_num}_table_{table_count}.png"
                    file_path = pdf_content_dir / filename
                    table_region.save(file_path, "PNG", optimize=True)
                    
                    # Create content info
                    content_info = {
                        'original_filename': f"page_{page_num}_table_{table_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'table',
                        'width': w,
                        'height': h,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    }
                    
                    tables.append(content_info)
                    print(f"📋 Extracted table {table_count} from page {page_num}")
            
            return tables
            
        except Exception as e:
            print(f"❌ Error extracting tables: {e}")
            return []
    
    def _extract_equations(self, cv_image: np.ndarray, pil_image: Image.Image, 
                          pdf_name: str, page_num: int, pdf_content_dir: Path, 
                          source_filename: str) -> List[Dict]:
        """Extract mathematical equation regions."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to find text regions
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find text contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            equations = []
            equation_count = 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Look for equation-like regions (horizontal, moderate size)
                if (5000 < area < 30000 and 
                    aspect_ratio > 2.0 and 
                    w > 100 and 30 < h < 80):
                    
                    # Add padding
                    padding = 10
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract equation region
                    equation_region = pil_image.crop((x, y, x + w, y + h))
                    
                    # Save equation
                    equation_count += 1
                    filename = f"{pdf_name}_page_{page_num}_equation_{equation_count}.png"
                    file_path = pdf_content_dir / filename
                    equation_region.save(file_path, "PNG", optimize=True)
                    
                    # Create content info
                    content_info = {
                        'original_filename': f"page_{page_num}_equation_{equation_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'equation',
                        'width': w,
                        'height': h,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    }
                    
                    equations.append(content_info)
                    print(f"🔢 Extracted equation {equation_count} from page {page_num}")
            
            return equations
            
        except Exception as e:
            print(f"❌ Error extracting equations: {e}")
            return []
    
    def _extract_representative_content(self, cv_image: np.ndarray, pil_image: Image.Image, 
                                      pdf_name: str, page_num: int, pdf_content_dir: Path, 
                                      source_filename: str) -> Optional[Dict]:
        """Extract a representative content region if no specific content found."""
        try:
            # Find the main content area (exclude margins)
            height, width = cv_image.shape[:2]
            
            # Define content area (exclude typical margins)
            margin_top = int(height * 0.1)
            margin_bottom = int(height * 0.9)
            margin_left = int(width * 0.1)
            margin_right = int(width * 0.9)
            
            # Extract main content area
            content_region = pil_image.crop((margin_left, margin_top, margin_right, margin_bottom))
            
            # Save representative content
            filename = f"{pdf_name}_page_{page_num}_content.png"
            file_path = pdf_content_dir / filename
            content_region.save(file_path, "PNG", optimize=True)
            
            # Create content info
            content_info = {
                'original_filename': f"page_{page_num}_content.png",
                'stored_filename': filename,
                'relative_path': f"images/{pdf_name}/{filename}",
                'full_path': str(file_path),
                'source_file': source_filename,
                'page_number': page_num,
                'content_type': 'content',
                'width': margin_right - margin_left,
                'height': margin_bottom - margin_top,
                'file_size': file_path.stat().st_size,
                'region_coords': {
                    'x': margin_left, 
                    'y': margin_top, 
                    'width': margin_right - margin_left, 
                    'height': margin_bottom - margin_top
                }
            }
            
            print(f"📄 Extracted representative content from page {page_num}")
            return content_info
            
        except Exception as e:
            print(f"❌ Error extracting representative content: {e}")
            return None