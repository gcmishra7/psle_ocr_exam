import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import tempfile
from pdf2image import convert_from_path
from datetime import datetime
from config.settings import settings

class ImageProcessor:
    """Handles extraction, storage, and management of images from PDF files."""
    
    def __init__(self):
        """Initialize image processor."""
        self.images_dir = Path("data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_images_from_pdf(self, pdf_path: str, source_filename: str) -> Tuple[List[Dict], List[str]]:
        """
        Extract all images from a PDF file and save them to the images directory.
        
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
                    'file_size': file_size
                }
                
                image_info_list.append(image_info)
                
                # Create web-accessible URL/path
                image_link = f"/images/{pdf_name}/{image_filename}"
                image_links_list.append(image_link)
                
                print(f"✅ Saved image: page {page_num} -> {relative_path}")
            
            print(f"📸 Extracted {len(image_info_list)} images from {source_filename}")
            return image_info_list, image_links_list
            
        except Exception as e:
            print(f"❌ Error extracting images from PDF: {e}")
            return [], []
    
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
            
            # Create multiple variations for better matching
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