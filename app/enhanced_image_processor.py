import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

class EnhancedImageProcessor:
    """
    Enhanced image processor that ensures proper image extraction, storage, and path management
    for the quiz application.
    """
    
    def __init__(self):
        """Initialize the enhanced image processor."""
        self.images_dir = Path("data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing parameters
        self.dpi = 300
        self.max_image_width = 1200
        self.min_content_area = 10000
        self.quality = 95
        
    def extract_images_and_content(self, pdf_path: str, source_filename: str) -> Tuple[List[Dict], List[str]]:
        """
        Extract images and content from PDF with proper path management.
        
        Args:
            pdf_path: Path to PDF file
            source_filename: Original filename
            
        Returns:
            Tuple of (image_info_list, image_links_list)
        """
        try:
            print(f"🖼️ Enhanced image extraction from: {source_filename}")
            
            # Create clean subdirectory for this PDF
            pdf_name = Path(source_filename).stem
            pdf_images_dir = self.images_dir / pdf_name
            
            # Clean up existing directory if it exists (for reprocessing)
            if pdf_images_dir.exists():
                print(f"🧹 Cleaning up existing images for: {pdf_name}")
                shutil.rmtree(pdf_images_dir)
            
            pdf_images_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert PDF to images with high quality
            print(f"📄 Converting PDF to images at {self.dpi} DPI...")
            images = convert_from_path(pdf_path, dpi=self.dpi, fmt='PNG')
            
            image_info_list = []
            image_links_list = []
            
            for page_num, pil_image in enumerate(images, 1):
                print(f"🔍 Processing page {page_num}...")
                
                # 1. Save high-quality full page (fallback)
                page_info = self._save_full_page(pil_image, pdf_name, page_num, pdf_images_dir, source_filename)
                if page_info:
                    image_info_list.append(page_info)
                    image_links_list.append(f"/data/images/{pdf_name}/{page_info['stored_filename']}")
                
                # 2. Extract smart content regions
                content_regions = self._extract_smart_content_regions(pil_image, pdf_name, page_num, pdf_images_dir, source_filename)
                image_info_list.extend(content_regions)
                
                for content in content_regions:
                    image_links_list.append(f"/data/images/{pdf_name}/{content['stored_filename']}")
            
            print(f"✅ Enhanced extraction completed: {len(image_info_list)} items saved")
            return image_info_list, image_links_list
            
        except Exception as e:
            print(f"❌ Error in enhanced image extraction: {e}")
            return [], []
    
    def _save_full_page(self, pil_image: Image.Image, pdf_name: str, page_num: int, 
                       pdf_images_dir: Path, source_filename: str) -> Optional[Dict]:
        """Save a high-quality full page image as fallback."""
        try:
            # Optimize the full page image
            optimized_image = self._optimize_image(pil_image)
            
            # Save with descriptive filename
            filename = f"{pdf_name}_page_{page_num}_full.png"
            file_path = pdf_images_dir / filename
            
            optimized_image.save(file_path, "PNG", optimize=True, quality=self.quality)
            
            # Create metadata
            return {
                'original_filename': f"page_{page_num}_full.png",
                'stored_filename': filename,
                'relative_path': f"images/{pdf_name}/{filename}",
                'full_path': str(file_path.absolute()),
                'source_file': source_filename,
                'page_number': page_num,
                'content_type': 'full_page',
                'width': optimized_image.width,
                'height': optimized_image.height,
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }
            
        except Exception as e:
            print(f"⚠️ Error saving full page {page_num}: {e}")
            return None
    
    def _extract_smart_content_regions(self, pil_image: Image.Image, pdf_name: str, 
                                     page_num: int, pdf_images_dir: Path, 
                                     source_filename: str) -> List[Dict]:
        """Extract smart content regions from a page."""
        content_regions = []
        
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 1. Extract diagrams
            diagrams = self._extract_diagrams(cv_image, pil_image, pdf_name, page_num, pdf_images_dir, source_filename)
            content_regions.extend(diagrams)
            
            # 2. Extract tables
            tables = self._extract_tables(cv_image, pil_image, pdf_name, page_num, pdf_images_dir, source_filename)
            content_regions.extend(tables)
            
            # 3. Extract mathematical content
            math_content = self._extract_mathematical_content(cv_image, pil_image, pdf_name, page_num, pdf_images_dir, source_filename)
            content_regions.extend(math_content)
            
            return content_regions
            
        except Exception as e:
            print(f"⚠️ Error extracting smart content from page {page_num}: {e}")
            return []
    
    def _extract_diagrams(self, cv_image: np.ndarray, pil_image: Image.Image, 
                         pdf_name: str, page_num: int, pdf_images_dir: Path, 
                         source_filename: str) -> List[Dict]:
        """Extract diagram regions using advanced computer vision."""
        diagrams = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            diagram_count = 0
            
            for contour in contours:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Filter for diagram-like regions
                if (area > self.min_content_area and 
                    0.2 < aspect_ratio < 8.0 and 
                    w > 100 and h > 100 and
                    w < cv_image.shape[1] * 0.9 and h < cv_image.shape[0] * 0.9):
                    
                    # Add smart padding
                    padding = 15
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract and optimize region
                    region = pil_image.crop((x, y, x + w, y + h))
                    optimized_region = self._optimize_image(region)
                    
                    # Save diagram
                    diagram_count += 1
                    filename = f"{pdf_name}_page_{page_num}_diagram_{diagram_count}.png"
                    file_path = pdf_images_dir / filename
                    
                    optimized_region.save(file_path, "PNG", optimize=True, quality=self.quality)
                    
                    diagrams.append({
                        'original_filename': f"page_{page_num}_diagram_{diagram_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path.absolute()),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'diagram',
                        'width': optimized_region.width,
                        'height': optimized_region.height,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    })
                    
                    print(f"📊 Extracted diagram {diagram_count} from page {page_num}")
            
            return diagrams
            
        except Exception as e:
            print(f"⚠️ Error extracting diagrams: {e}")
            return []
    
    def _extract_tables(self, cv_image: np.ndarray, pil_image: Image.Image, 
                       pdf_name: str, page_num: int, pdf_images_dir: Path, 
                       source_filename: str) -> List[Dict]:
        """Extract table regions using line detection."""
        tables = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find table contours
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            table_count = 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for table-like regions
                if area > 15000 and w > 150 and h > 80:
                    # Add padding
                    padding = 10
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract and optimize table region
                    table_region = pil_image.crop((x, y, x + w, y + h))
                    optimized_table = self._optimize_image(table_region)
                    
                    # Save table
                    table_count += 1
                    filename = f"{pdf_name}_page_{page_num}_table_{table_count}.png"
                    file_path = pdf_images_dir / filename
                    
                    optimized_table.save(file_path, "PNG", optimize=True, quality=self.quality)
                    
                    tables.append({
                        'original_filename': f"page_{page_num}_table_{table_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path.absolute()),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'table',
                        'width': optimized_table.width,
                        'height': optimized_table.height,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    })
                    
                    print(f"📋 Extracted table {table_count} from page {page_num}")
            
            return tables
            
        except Exception as e:
            print(f"⚠️ Error extracting tables: {e}")
            return []
    
    def _extract_mathematical_content(self, cv_image: np.ndarray, pil_image: Image.Image, 
                                    pdf_name: str, page_num: int, pdf_images_dir: Path, 
                                    source_filename: str) -> List[Dict]:
        """Extract mathematical expressions and equations."""
        math_content = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find text contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            math_count = 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Look for equation-like regions
                if (3000 < area < 20000 and 
                    aspect_ratio > 1.5 and 
                    w > 80 and 25 < h < 60):
                    
                    # Add padding
                    padding = 8
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(cv_image.shape[1] - x, w + 2 * padding)
                    h = min(cv_image.shape[0] - y, h + 2 * padding)
                    
                    # Extract and optimize math region
                    math_region = pil_image.crop((x, y, x + w, y + h))
                    optimized_math = self._optimize_image(math_region)
                    
                    # Save math content
                    math_count += 1
                    filename = f"{pdf_name}_page_{page_num}_math_{math_count}.png"
                    file_path = pdf_images_dir / filename
                    
                    optimized_math.save(file_path, "PNG", optimize=True, quality=self.quality)
                    
                    math_content.append({
                        'original_filename': f"page_{page_num}_math_{math_count}.png",
                        'stored_filename': filename,
                        'relative_path': f"images/{pdf_name}/{filename}",
                        'full_path': str(file_path.absolute()),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'content_type': 'math',
                        'width': optimized_math.width,
                        'height': optimized_math.height,
                        'file_size': file_path.stat().st_size,
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    })
                    
                    print(f"🔢 Extracted math content {math_count} from page {page_num}")
            
            return math_content
            
        except Exception as e:
            print(f"⚠️ Error extracting mathematical content: {e}")
            return []
    
    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """Optimize image for web display and storage."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > self.max_image_width:
                ratio = self.max_image_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((self.max_image_width, new_height), Image.Resampling.LANCZOS)
            
            # Enhance image quality
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.05)
            
            return image
            
        except Exception as e:
            print(f"⚠️ Error optimizing image: {e}")
            return image
    
    def get_image_stats(self) -> Dict:
        """Get statistics about stored images."""
        try:
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(self.images_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        file_path = os.path.join(root, file)
                        total_files += 1
                        total_size += os.path.getsize(file_path)
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'images_directory': str(self.images_dir.absolute())
            }
            
        except Exception as e:
            print(f"❌ Error getting image stats: {e}")
            return {'total_files': 0, 'total_size_mb': 0, 'images_directory': str(self.images_dir)}