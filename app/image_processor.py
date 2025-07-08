import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw
import tempfile
from pdf2image import convert_from_path
from datetime import datetime
from config.settings import settings

# Try to import numpy, fall back to basic operations if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️  NumPy not available, using basic image processing")

class ImageProcessor:
    """Handles extraction, storage, and management of images from PDF files."""
    
    def __init__(self):
        """Initialize image processor."""
        self.images_dir = Path("data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_images_from_pdf(self, pdf_path: str, source_filename: str) -> Tuple[List[Dict], List[str]]:
        """
        Extract images from a PDF file with enhanced processing for educational content.
        Extracts both full pages and attempts to identify specific diagram regions.
        
        Args:
            pdf_path: Path to the PDF file
            source_filename: Original filename for organization
            
        Returns:
            Tuple of (image_info_list, image_links_list)
        """
        try:
            print(f"📸 Extracting images from PDF: {source_filename}")
            
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300, fmt='PNG')
            
            image_info_list = []
            image_links_list = []
            
            # Create subdirectory for this PDF's images
            pdf_name = Path(source_filename).stem
            pdf_images_dir = self.images_dir / pdf_name
            pdf_images_dir.mkdir(exist_ok=True)
            
            for page_num, image in enumerate(images, 1):
                print(f"📄 Processing page {page_num}...")
                
                # Extract full page image (for reference)
                page_info = self._save_full_page_image(image, pdf_name, page_num, pdf_images_dir, source_filename)
                if page_info:
                    image_info_list.append(page_info)
                    image_links_list.append(f"/images/{pdf_name}/{page_info['stored_filename']}")
                
                # Try to extract specific diagram/figure regions
                diagram_infos = self._extract_diagram_regions(image, pdf_name, page_num, pdf_images_dir, source_filename)
                for diagram_info in diagram_infos:
                    image_info_list.append(diagram_info)
                    image_links_list.append(f"/images/{pdf_name}/{diagram_info['stored_filename']}")
            
            print(f"📸 Extracted {len(image_info_list)} images from {source_filename}")
            return image_info_list, image_links_list
            
        except Exception as e:
            print(f"❌ Error extracting images from PDF: {e}")
            return [], []
    
    def _save_full_page_image(self, image: Image.Image, pdf_name: str, page_num: int, 
                             pdf_images_dir: Path, source_filename: str) -> Optional[Dict]:
        """Save a full page image."""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{pdf_name}_page_{page_num}_{timestamp}.png"
            
            # Save image
            image_path = pdf_images_dir / image_filename
            image.save(image_path, "PNG", optimize=True)
            
            # Get image properties
            width, height = image.size
            file_size = image_path.stat().st_size
            
            # Create relative path for web access
            relative_path = f"images/{pdf_name}/{image_filename}"
            
            # Create image info
            image_info = {
                'original_filename': f"page_{page_num}.png",
                'stored_filename': image_filename,
                'relative_path': relative_path,
                'full_path': str(image_path),
                'source_file': source_filename,
                'page_number': page_num,
                'width': width,
                'height': height,
                'file_size': file_size,
                'image_type': 'full_page'
            }
            
            print(f"✅ Saved full page: page {page_num} -> {relative_path}")
            return image_info
            
        except Exception as e:
            print(f"❌ Error saving full page image: {e}")
            return None
    
    def _extract_diagram_regions(self, image: Image.Image, pdf_name: str, page_num: int, 
                                pdf_images_dir: Path, source_filename: str) -> List[Dict]:
        """
        Extract specific diagram/figure regions from a page.
        Uses simple image processing to identify potential diagram areas.
        """
        try:
            print(f"🔍 Looking for diagrams on page {page_num}...")
            
            if not HAS_NUMPY:
                print(f"⚠️  Skipping diagram extraction (NumPy not available)")
                return []
            
            # Convert to grayscale for analysis
            gray_image = image.convert('L')
            img_array = np.array(gray_image)
            
            # Simple approach: detect regions with high contrast or enclosed areas
            # This is a basic implementation - could be enhanced with ML models
            diagram_regions = self._find_diagram_regions(img_array)
            
            diagram_infos = []
            for i, region in enumerate(diagram_regions):
                x, y, w, h = region
                
                # Extract the region
                cropped = image.crop((x, y, x + w, y + h))
                
                # Only save if region is significant (not too small)
                if w > 100 and h > 100:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    diagram_filename = f"{pdf_name}_page_{page_num}_diagram_{i+1}_{timestamp}.png"
                    
                    # Save diagram
                    diagram_path = pdf_images_dir / diagram_filename
                    cropped.save(diagram_path, "PNG", optimize=True)
                    
                    # Create image info
                    relative_path = f"images/{pdf_name}/{diagram_filename}"
                    diagram_info = {
                        'original_filename': f"page_{page_num}_diagram_{i+1}.png",
                        'stored_filename': diagram_filename,
                        'relative_path': relative_path,
                        'full_path': str(diagram_path),
                        'source_file': source_filename,
                        'page_number': page_num,
                        'width': w,
                        'height': h,
                        'file_size': diagram_path.stat().st_size,
                        'image_type': 'diagram',
                        'region_coords': {'x': x, 'y': y, 'width': w, 'height': h}
                    }
                    
                    diagram_infos.append(diagram_info)
                    print(f"✅ Extracted diagram: page {page_num} diagram {i+1} -> {relative_path}")
            
            return diagram_infos
            
        except Exception as e:
            print(f"❌ Error extracting diagrams from page {page_num}: {e}")
            return []
    
    def _find_diagram_regions(self, img_array) -> List[Tuple[int, int, int, int]]:
        """
        Find potential diagram regions in an image using simple image processing.
        Returns list of (x, y, width, height) tuples.
        """
        try:
            if not HAS_NUMPY:
                return []
                
            # Simple approach: look for rectangular regions with high contrast
            # This is a basic implementation - could be enhanced significantly
            
            # Apply edge detection (simple gradient)
            height, width = img_array.shape
            regions = []
            
            # Look for potential diagram areas by analyzing image statistics
            # Divide image into grid and analyze each section
            grid_size = 50
            
            for y in range(0, height - grid_size, grid_size):
                for x in range(0, width - grid_size, grid_size):
                    # Extract region
                    region = img_array[y:y+grid_size, x:x+grid_size]
                    
                    # Calculate statistics
                    mean_val = np.mean(region)
                    std_val = np.std(region)
                    
                    # Look for regions with high variance (potential diagrams/figures)
                    if std_val > 40 and mean_val < 200:  # High contrast, not pure white
                        # Try to expand the region to capture full diagram
                        expanded_region = self._expand_region(img_array, x, y, grid_size, grid_size)
                        if expanded_region:
                            regions.append(expanded_region)
            
            # Remove overlapping regions and merge adjacent ones
            regions = self._merge_overlapping_regions(regions)
            
            return regions
            
        except Exception as e:
            print(f"❌ Error finding diagram regions: {e}")
            return []
    
    def _expand_region(self, img_array, start_x: int, start_y: int, 
                      initial_w: int, initial_h: int) -> Optional[Tuple[int, int, int, int]]:
        """Expand a region to capture the full diagram."""
        try:
            if not HAS_NUMPY:
                return None
                
            height, width = img_array.shape
            
            # Start with initial region
            x, y, w, h = start_x, start_y, initial_w, initial_h
            
            # Try to expand in all directions
            # This is a simple implementation - could be much more sophisticated
            
            # Expand right
            while x + w < width - 10:
                test_region = img_array[y:y+h, x+w:x+w+10]
                if HAS_NUMPY and np.std(test_region) > 20:  # Still has content
                    w += 10
                else:
                    break
            
            # Expand down
            while y + h < height - 10:
                test_region = img_array[y+h:y+h+10, x:x+w]
                if HAS_NUMPY and np.std(test_region) > 20:  # Still has content
                    h += 10
                else:
                    break
            
            # Only return if region is significant
            if w > 150 and h > 150:
                return (x, y, w, h)
            
            return None
            
        except Exception as e:
            return None
    
    def _merge_overlapping_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Merge overlapping regions to avoid duplicates."""
        if not regions:
            return []
        
        merged = []
        regions = sorted(regions, key=lambda r: r[0] * 10000 + r[1])  # Sort by position
        
        for region in regions:
            x, y, w, h = region
            
            # Check if this region overlaps significantly with any existing merged region
            overlaps = False
            for i, existing in enumerate(merged):
                ex, ey, ew, eh = existing
                
                # Calculate overlap
                overlap_x = max(0, min(x + w, ex + ew) - max(x, ex))
                overlap_y = max(0, min(y + h, ey + eh) - max(y, ey))
                overlap_area = overlap_x * overlap_y
                
                region_area = w * h
                existing_area = ew * eh
                
                # If significant overlap, merge
                if overlap_area > 0.3 * min(region_area, existing_area):
                    # Merge regions
                    new_x = min(x, ex)
                    new_y = min(y, ey)
                    new_w = max(x + w, ex + ew) - new_x
                    new_h = max(y + h, ey + eh) - new_y
                    merged[i] = (new_x, new_y, new_w, new_h)
                    overlaps = True
                    break
            
            if not overlaps:
                merged.append(region)
        
        return merged
    
    def create_image_links_array(self, image_info_list: List[Dict]) -> List[str]:
        """
        Create an array of image links for LLM processing.
        
        Args:
            image_info_list: List of image information dictionaries
            
        Returns:
            List of image links formatted for LLM
        """
        image_links = []
        
        for image_info in image_info_list:
            # Create descriptive filename that LLM can understand
            relative_path = image_info['relative_path']
            page_num = image_info['page_number']
            image_type = image_info.get('image_type', 'full_page')
            
            # Create multiple variations for better matching
            if image_type == 'diagram':
                # For diagrams, create more specific references
                diagram_num = image_info['stored_filename'].split('_diagram_')[1].split('_')[0]
                variations = [
                    f"/data/{relative_path}",
                    f"page_{page_num}_diagram_{diagram_num}.png",
                    f"Page {page_num} Diagram {diagram_num}",
                    f"Figure {diagram_num} (Page {page_num})",
                    f"diagram_{diagram_num}",
                    relative_path
                ]
            else:
                # For full pages
                variations = [
                    f"/data/{relative_path}",
                    f"page_{page_num}.png",
                    f"Page {page_num}",
                    f"page{page_num}",
                    relative_path
                ]
            
            image_links.extend(variations)
        
        return list(set(image_links))  # Remove duplicates
    
    def match_image_references_to_files(self, 
                                      image_references: List[str], 
                                      available_images: List[Dict]) -> Dict[str, str]:
        """
        Match image references found in text to actual stored image files.
        
        Args:
            image_references: List of image references found in text
            available_images: List of available image information
            
        Returns:
            Dictionary mapping references to actual file paths
        """
        mappings = {}
        
        for ref in image_references:
            ref_lower = ref.lower().strip()
            
            # Try to extract page number or figure identifier
            best_match = None
            best_score = 0
            
            for image_info in available_images:
                page_num = image_info['page_number']
                relative_path = image_info['relative_path']
                
                # Direct page number matching
                if f"page {page_num}" in ref_lower or f"page{page_num}" in ref_lower:
                    best_match = relative_path
                    best_score = 100
                    break
                
                # Figure/diagram matching with page context
                if any(keyword in ref_lower for keyword in ['figure', 'fig', 'diagram', 'image']):
                    # Extract numbers from reference
                    import re
                    numbers = re.findall(r'\d+', ref)
                    if numbers:
                        ref_num = int(numbers[0])
                        if ref_num == page_num and best_score < 80:
                            best_match = relative_path
                            best_score = 80
                
                # Partial matching
                if ref_lower in relative_path.lower() and best_score < 60:
                    best_match = relative_path
                    best_score = 60
            
            if best_match:
                mappings[ref] = f"/data/{best_match}"
                print(f"🔗 Matched '{ref}' -> {best_match}")
            else:
                print(f"⚠️  No match found for image reference: '{ref}'")
        
        return mappings
    
    def create_web_accessible_path(self, relative_path: str) -> str:
        """
        Create a web-accessible path for an image.
        
        Args:
            relative_path: Relative path to the image
            
        Returns:
            Web-accessible path
        """
        # Ensure the path starts with /data/ for web access
        if not relative_path.startswith('/data/'):
            if relative_path.startswith('images/'):
                return f"/data/{relative_path}"
            else:
                return f"/data/images/{relative_path}"
        return relative_path
    
    def get_image_file_path(self, relative_path: str) -> Optional[str]:
        """
        Get the actual file system path for an image.
        
        Args:
            relative_path: Relative path from the database
            
        Returns:
            Full file system path or None if not found
        """
        # Clean the relative path
        clean_path = relative_path.replace('/data/', '').replace('images/', '')
        
        # Construct full path
        full_path = self.images_dir / clean_path
        
        if full_path.exists():
            return str(full_path)
        
        # Try alternative paths
        alternative_paths = [
            self.images_dir / relative_path.lstrip('/'),
            Path("data") / relative_path.lstrip('/'),
            Path(relative_path.lstrip('/'))
        ]
        
        for alt_path in alternative_paths:
            if alt_path.exists():
                return str(alt_path)
        
        return None
    
    def optimize_image_for_web(self, image_path: str, max_width: int = 800) -> bool:
        """
        Optimize an image for web display.
        
        Args:
            image_path: Path to the image file
            max_width: Maximum width for optimization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                # Calculate new dimensions
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    
                    # Resize image
                    img_resized = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save optimized version
                    img_resized.save(image_path, "PNG", optimize=True, quality=85)
                    print(f"🔧 Optimized image: {image_path} -> {max_width}x{new_height}")
                
                return True
                
        except Exception as e:
            print(f"❌ Error optimizing image {image_path}: {e}")
            return False
    
    def cleanup_old_images(self, source_filename: str) -> bool:
        """
        Clean up old images for a specific PDF file.
        
        Args:
            source_filename: Name of the source PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_name = Path(source_filename).stem
            pdf_images_dir = self.images_dir / pdf_name
            
            if pdf_images_dir.exists():
                shutil.rmtree(pdf_images_dir)
                print(f"🗑️  Cleaned up old images for: {source_filename}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up images: {e}")
            return False
    
    def get_image_stats(self) -> Dict:
        """
        Get statistics about stored images.
        
        Returns:
            Dictionary with image statistics
        """
        try:
            total_images = 0
            total_size = 0
            pdf_folders = []
            
            if self.images_dir.exists():
                for pdf_folder in self.images_dir.iterdir():
                    if pdf_folder.is_dir():
                        pdf_folders.append(pdf_folder.name)
                        folder_images = list(pdf_folder.glob("*.png"))
                        total_images += len(folder_images)
                        
                        for img_file in folder_images:
                            total_size += img_file.stat().st_size
            
            return {
                'total_images': total_images,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'pdf_folders': len(pdf_folders),
                'folder_names': pdf_folders
            }
            
        except Exception as e:
            print(f"❌ Error getting image stats: {e}")
            return {
                'total_images': 0,
                'total_size_mb': 0,
                'pdf_folders': 0,
                'folder_names': []
            }