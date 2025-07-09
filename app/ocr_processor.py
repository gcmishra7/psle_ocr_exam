import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image, ImageEnhance, ImageFilter
import os
import tempfile
from typing import List, Optional, Dict, Tuple
from config.settings import settings
import logging
from pathlib import Path
from app.llm_parser import LLMParser
from app.database_manager import DatabaseManager
from app.image_processor import ImageProcessor

# Try to import OpenCV, but make it optional
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️  OpenCV not available, using basic image processing")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """Enhanced OCR processor with image extraction and advanced question paper parsing."""
    
    def __init__(self):
        """Initialize OCR processor with all components."""
        print("🔧 Initializing OCR processor with dependency handling...")
        
        # Always try SimpleDatabaseManager first to avoid dependency issues
        try:
            from app.simple_database_manager import SimpleDatabaseManager
            self.db_manager = SimpleDatabaseManager()
            print("✅ Using SimpleDatabaseManager (dependency-free)")
        except Exception as e:
            print(f"❌ SimpleDatabaseManager failed: {e}")
            try:
                self.db_manager = DatabaseManager()
                print("✅ Using full DatabaseManager")
            except Exception as e2:
                print(f"❌ Both database managers failed: {e2}")
                raise
        
        # Try to initialize other components with fallbacks
        try:
            self.llm_parser = LLMParser()
            print("✅ LLM parser initialized")
        except Exception as e:
            print(f"⚠️  LLM parser failed ({e}), will use fallback parsing")
            self.llm_parser = None
        
        try:
            self.image_processor = ImageProcessor()
            print("✅ Image processor initialized")
        except Exception as e:
            print(f"⚠️  Image processor failed ({e}), will use basic image handling")
            self.image_processor = None
        
        # OCR settings for educational content with fallback configs
        self.ocr_configs = [
            {
                'name': 'Standard Educational',
                'lang': 'eng',
                'config': '--oem 3 --psm 6'
            },
            {
                'name': 'Single Column Text',
                'lang': 'eng', 
                'config': '--oem 3 --psm 4'
            },
            {
                'name': 'Mixed Text and Images',
                'lang': 'eng',
                'config': '--oem 3 --psm 3'
            },
            {
                'name': 'Sparse Text',
                'lang': 'eng',
                'config': '--oem 3 --psm 11'
            }
        ]
        
        # Default configuration
        self.current_ocr_config = self.ocr_configs[0]
        
        self.dpi = 300
        self.processing_stats = {
            'pages_processed': 0,
            'images_extracted': 0,
            'questions_found': 0,
            'processing_time': 0
        }
    
    def process_pdf_comprehensive(self, pdf_path: str, source_filename: Optional[str] = None) -> bool:
        """
        Comprehensive PDF processing with image extraction and enhanced parsing.
        
        Args:
            pdf_path: Path to the PDF file
            source_filename: Original filename for organization
            
        Returns:
            True if processing successful, False otherwise
        """
        import time
        start_time = time.time()
        
        try:
            if source_filename is None:
                source_filename = Path(pdf_path).name
            
            print(f"\n🚀 Starting comprehensive processing of: {source_filename}")
            print("=" * 80)
            
            # Step 1: Extract images from PDF
            print("📸 STEP 1: Extracting images from PDF...")
            if self.image_processor is not None:
                image_info_list, image_links_list = self.image_processor.extract_images_from_pdf(
                    pdf_path, source_filename
                )
                
                self.processing_stats['images_extracted'] = len(image_info_list)
                
                # Save image information to database
                for image_info in image_info_list:
                    self.db_manager.save_image_info(image_info)
            else:
                print("⚠️  Image processing disabled - skipping image extraction")
                image_info_list, image_links_list = [], []
                self.processing_stats['images_extracted'] = 0
            
            # Step 2: Perform OCR on the PDF
            print("\n🔍 STEP 2: Performing OCR extraction...")
            extracted_text = self.extract_text_from_pdf(pdf_path)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                print("❌ Insufficient text extracted from PDF")
                return False
            
            print(f"✅ Extracted {len(extracted_text)} characters of text")
            
            # Step 3: Create image links for LLM processing
            print("\n🔗 STEP 3: Preparing image links for LLM...")
            if self.image_processor is not None:
                formatted_image_links = self.image_processor.create_image_links_array(image_info_list)
                print(f"📋 Created {len(formatted_image_links)} image link variations")
            else:
                formatted_image_links = []
                print("⚠️  Image processing disabled - no image links created")
            
            # Step 4: Parse with enhanced LLM
            print("\n🧠 STEP 4: Enhanced LLM parsing with image support...")
            if self.llm_parser is not None:
                parsed_data = self.llm_parser.parse_questions_enhanced(
                    extracted_text, 
                    formatted_image_links
                )
                
                if not parsed_data:
                    print("⚠️  Enhanced parsing failed, trying fallback...")
                    parsed_data = self.llm_parser.fallback_parse_questions(extracted_text)
            else:
                print("⚠️  LLM processing disabled - creating basic parsed data structure")
                parsed_data = self.create_basic_parsed_data(extracted_text, source_filename)
            
            if not parsed_data:
                print("❌ All parsing methods failed")
                return False
            
            # Step 5: Enhance image matching
            print("\n🔍 STEP 5: Enhancing image reference matching...")
            if self.llm_parser is not None:
                parsed_data = self.llm_parser.enhance_image_matching(parsed_data, image_info_list)
            else:
                print("⚠️  LLM processing disabled - skipping image matching enhancement")
            
            # Step 6: Create image mappings for database storage
            print("\n💾 STEP 6: Creating image mappings...")
            image_mappings = self.create_image_mappings(parsed_data, image_info_list)
            
            # Step 7: Save to database
            print("\n💾 STEP 7: Saving to enhanced database...")
            success = self.db_manager.save_enhanced_paper_data(
                parsed_data, 
                source_filename, 
                image_mappings
            )
            
            if not success:
                print("❌ Failed to save to database")
                return False
            
            # Update processing stats
            self.processing_stats['questions_found'] = len(parsed_data.get('questions', []))
            self.processing_stats['processing_time'] = int(time.time() - start_time)
            
            # Print summary
            self.print_processing_summary(source_filename, parsed_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Error in comprehensive PDF processing: {e}")
            logger.error(f"Comprehensive processing error: {e}", exc_info=True)
            return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF with optimized settings for question papers.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            print(f"📖 Converting PDF to images for OCR...")
            
            # Get PDF info
            pdf_info = pdfinfo_from_path(pdf_path)
            total_pages = pdf_info['Pages']
            self.processing_stats['pages_processed'] = total_pages
            
            print(f"📄 Processing {total_pages} pages at {self.dpi} DPI...")
            
            # Convert PDF to images
            images = convert_from_path(
                pdf_path, 
                dpi=self.dpi,
                fmt='PNG',
                thread_count=2
            )
            
            all_text = []
            
            for page_num, image in enumerate(images, 1):
                print(f"🔍 Processing page {page_num}/{total_pages}...")
                
                # Enhance image for better OCR
                enhanced_image = self.enhance_image_for_ocr(image)
                
                # Perform OCR with robust error handling
                page_text = self.extract_text_with_fallback(enhanced_image)
                
                if page_text.strip():
                    all_text.append(f"\n--- PAGE {page_num} ---\n")
                    all_text.append(page_text)
                    all_text.append(f"\n--- END PAGE {page_num} ---\n")
            
            combined_text = '\n'.join(all_text)
            print(f"✅ OCR completed. Extracted {len(combined_text)} characters total")
            
            return combined_text
            
        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            logger.error(f"Text extraction error: {e}", exc_info=True)
            return ""
    
    def extract_text_with_fallback(self, image: Image.Image) -> str:
        """
        Extract text from image with fallback OCR configurations.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text string
        """
        for config in self.ocr_configs:
            try:
                print(f"🔍 Trying OCR config: {config['name']}")
                
                text = pytesseract.image_to_string(
                    image,
                    lang=config['lang'],
                    config=config['config']
                )
                
                if text and text.strip():
                    print(f"✅ OCR successful with {config['name']}")
                    return text
                    
            except Exception as e:
                print(f"⚠️  OCR config '{config['name']}' failed: {e}")
                continue
        
        # If all configs fail, try basic OCR without config
        try:
            print("🔄 Trying basic OCR without specific config...")
            text = pytesseract.image_to_string(image, lang='eng')
            return text if text else ""
        except Exception as e:
            print(f"❌ All OCR attempts failed: {e}")
            return ""
    
    def enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Enhance image quality for better OCR results on educational content.
        
        Args:
            image: PIL Image object
            
        Returns:
            Enhanced PIL Image
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small
            width, height = image.size
            if width < 1000:
                ratio = 1000 / width
                new_height = int(height * ratio)
                image = image.resize((1000, new_height), Image.Resampling.LANCZOS)
            
            # Enhance contrast for better text recognition
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return image
            
        except Exception as e:
            print(f"⚠️  Image enhancement failed: {e}")
            return image  # Return original if enhancement fails
    
    def create_image_mappings(self, parsed_data: Dict, image_info_list: List[Dict]) -> Dict[str, str]:
        """
        Create mappings between image references in questions and actual stored files.
        
        Args:
            parsed_data: Parsed question paper data
            image_info_list: List of extracted image information
            
        Returns:
            Dictionary mapping references to stored file paths
        """
        mappings = {}
        
        try:
            questions = parsed_data.get('questions', [])
            
            for question in questions:
                image_links = question.get('image_links_used', [])
                
                for link in image_links:
                    # Find corresponding image info
                    for image_info in image_info_list:
                        relative_path = image_info['relative_path']
                        
                        # Check if this link matches this image
                        if self.is_link_match(link, image_info):
                            web_path = f"/data/{relative_path}"
                            mappings[link] = web_path
                            print(f"🔗 Mapped: {link} -> {web_path}")
                            break
            
            return mappings
            
        except Exception as e:
            print(f"❌ Error creating image mappings: {e}")
            return {}
    
    def is_link_match(self, link: str, image_info: Dict) -> bool:
        """
        Check if a link matches an image based on various criteria.
        
        Args:
            link: Image link from LLM parsing
            image_info: Image information dictionary
            
        Returns:
            True if they match, False otherwise
        """
        try:
            page_num = image_info['page_number']
            relative_path = image_info['relative_path']
            stored_filename = image_info['stored_filename']
            
            link_lower = link.lower()
            
            # Direct path matching
            if relative_path.lower() in link_lower or stored_filename.lower() in link_lower:
                return True
            
            # Page number matching
            if f"page_{page_num}" in link_lower or f"page{page_num}" in link_lower:
                return True
            
            # Figure/diagram matching with page number
            if any(keyword in link_lower for keyword in ['figure', 'fig', 'diagram', 'image']):
                import re
                numbers = re.findall(r'\d+', link)
                if numbers and int(numbers[0]) == page_num:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def print_processing_summary(self, source_filename: str, parsed_data: Dict):
        """
        Print a comprehensive summary of the processing results.
        
        Args:
            source_filename: Name of the processed file
            parsed_data: Parsed question paper data
        """
        print("\n" + "=" * 80)
        print("📊 PROCESSING SUMMARY")
        print("=" * 80)
        
        metadata = parsed_data.get('metadata', {})
        questions = parsed_data.get('questions', [])
        unmatched_images = parsed_data.get('unmatched_image_links', [])
        
        print(f"📄 File: {source_filename}")
        print(f"⏱️  Processing Time: {self.processing_stats['processing_time']:.2f} seconds")
        print(f"📖 Pages Processed: {self.processing_stats['pages_processed']}")
        print(f"🖼️  Images Extracted: {self.processing_stats['images_extracted']}")
        print(f"❓ Questions Found: {len(questions)}")
        
        print("\n📋 METADATA:")
        for key, value in metadata.items():
            if value:
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n❓ QUESTIONS BREAKDOWN:")
        question_types = {}
        questions_with_images = 0
        
        for question in questions:
            q_type = question.get('question_type', 'Unknown')
            question_types[q_type] = question_types.get(q_type, 0) + 1
            
            if question.get('image_references_in_text') or question.get('image_links_used'):
                questions_with_images += 1
        
        for q_type, count in question_types.items():
            print(f"  • {q_type}: {count}")
        
        print(f"  • Questions with Images: {questions_with_images}")
        
        if unmatched_images:
            print(f"\n⚠️  UNMATCHED IMAGES: {len(unmatched_images)}")
            for img in unmatched_images[:3]:  # Show first 3
                print(f"  • {img}")
            if len(unmatched_images) > 3:
                print(f"  • ... and {len(unmatched_images) - 3} more")
        
        print("\n" + "=" * 80)
        print("✅ PROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'pages_processed': 0,
            'images_extracted': 0,
            'questions_found': 0,
            'processing_time': 0
        }
    
    def process_pdf(self, pdf_path: str, source_filename: Optional[str] = None) -> bool:
        """
        Main PDF processing method - uses smart content extraction with multimodal AI.
        Includes automatic cleanup for reprocessing files.
        
        Args:
            pdf_path: Path to the PDF file
            source_filename: Original filename
            
        Returns:
            True if successful, False otherwise
        """
        if source_filename is None:
            source_filename = Path(pdf_path).name
            
        try:
            print(f"\n🚀 STARTING ENHANCED PDF PROCESSING: {source_filename}")
            print("=" * 80)
            
            # Step 1: Smart content extraction
            print("🔍 Step 1: Smart Content Extraction...")
            try:
                from app.smart_content_extractor import SmartContentExtractor
                smart_extractor = SmartContentExtractor()
                image_info_list, image_links = smart_extractor.extract_smart_content(pdf_path, source_filename)
                print(f"✅ Smart extraction completed: {len(image_info_list)} content items found")
            except ImportError:
                print("⚠️  Smart content extractor not available, using basic image extraction...")
                if self.image_processor:
                    image_info_list, image_links = self.image_processor.extract_images_from_pdf(pdf_path, source_filename)
                else:
                    image_info_list, image_links = [], []
            except Exception as e:
                print(f"⚠️  Smart extraction failed ({e}), falling back to basic extraction...")
                if self.image_processor:
                    image_info_list, image_links = self.image_processor.extract_images_from_pdf(pdf_path, source_filename)
                else:
                    image_info_list, image_links = [], []

            # Step 2: Try multimodal parsing
            print("🎯 Step 2: Advanced Text Processing...")
            try:
                from app.llama_multimodal_parser import LlamaMultimodalParser
                multimodal_parser = LlamaMultimodalParser()
                parsed_data, _ = multimodal_parser.process_pdf_multimodal(pdf_path, source_filename)
                
                if parsed_data and parsed_data.get('questions'):
                    print(f"✅ Multimodal text processing completed: {len(parsed_data['questions'])} questions")
                else:
                    print("⚠️  Multimodal processing yielded no results, using fallback...")
                    parsed_data = self._fallback_text_processing(pdf_path, source_filename)
                    
            except ImportError:
                print("⚠️  Multimodal parser not available, using fallback processing...")
                parsed_data = self._fallback_text_processing(pdf_path, source_filename)
            except Exception as e:
                print(f"⚠️  Multimodal processing failed ({e}), using fallback...")
                parsed_data = self._fallback_text_processing(pdf_path, source_filename)

            # Step 3: Enhance with smart content
            if parsed_data:
                print("🔗 Step 3: Enhancing questions with smart content...")
                self._enhance_questions_with_smart_content(parsed_data, image_info_list)
            
            # Step 4: Save to database
            print("💾 Step 4: Saving to enhanced database...")
            if parsed_data:
                success = self.db_manager.save_enhanced_paper_data(parsed_data, source_filename, None)
                
                if success:
                    # Save image info
                    if hasattr(self.db_manager, 'save_image_info'):
                        for image_info in image_info_list:
                            self.db_manager.save_image_info(image_info)
                    
                    self._print_enhanced_summary(source_filename, parsed_data, image_info_list)
                    return True
                else:
                    print("❌ Failed to save to database")
                    return False
            else:
                print("❌ No parsed data to save")
                return False
                
        except Exception as e:
            print(f"❌ Error in PDF processing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fallback_text_processing(self, pdf_path: str, source_filename: str) -> Optional[Dict]:
        """Fallback text processing when multimodal parsing fails."""
        try:
            # Extract text using basic OCR
            text_content = self.extract_text_from_pdf(pdf_path)
            
            if not text_content:
                print("❌ No text content extracted")
                return None
            
            # Use LLM parser if available
            if self.llm_parser:
                parsed_data = self.llm_parser.parse_questions_enhanced(text_content, [])
                
                if not parsed_data:
                    parsed_data = self.create_basic_parsed_data(text_content, source_filename)
            else:
                parsed_data = self.create_basic_parsed_data(text_content, source_filename)
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error in fallback text processing: {e}")
            return None
    
    def _enhance_questions_with_smart_content(self, parsed_data: Dict, image_info_list: List[Dict]):
        """Enhance parsed questions with smart content extraction results."""
        try:
            questions = parsed_data.get('questions', [])
            
            if not image_info_list:
                return
            
            # Create mapping of content by page and type
            content_by_page = {}
            for content in image_info_list:
                page_num = content.get('page_number', 0)
                if page_num not in content_by_page:
                    content_by_page[page_num] = []
                content_by_page[page_num].append(content)
            
            # Enhanced matching for questions
            enhanced_count = 0
            for question in questions:
                question_num = question.get('question_number', '')
                existing_links = question.get('image_links_used', [])
                new_links = []
                
                # Add smart content based on different strategies
                for page_num, page_content in content_by_page.items():
                    for content in page_content:
                        content_type = content.get('content_type', '')
                        content_path = f"/data/{content['relative_path']}"
                        
                        # Add high-value content (diagrams, tables, equations)
                        if content_type in ['diagram', 'table', 'equation'] and content_path not in existing_links:
                            new_links.append(content_path)
                
                # Update question with enhanced content
                if new_links:
                    all_links = existing_links + new_links
                    question['image_links_used'] = list(set(all_links))  # Remove duplicates
                    enhanced_count += 1
                    print(f"🔗 Enhanced Q{question_num} with {len(new_links)} smart content items")
            
            if enhanced_count > 0:
                print(f"✅ Enhanced {enhanced_count} questions with smart content")
            
        except Exception as e:
            print(f"⚠️  Error enhancing questions with smart content: {e}")
    
    def _print_enhanced_summary(self, source_filename: str, parsed_data: Dict, image_info_list: List[Dict]):
        """Print enhanced summary with smart content information."""
        print("\n" + "=" * 80)
        print("🎉 ENHANCED PROCESSING COMPLETED!")
        print("=" * 80)
        
        metadata = parsed_data.get('metadata', {})
        questions = parsed_data.get('questions', [])
        
        print(f"📄 File: {source_filename}")
        print(f"🧠 Method: Smart Content + Multimodal AI")
        print(f"📊 Questions: {len(questions)}")
        print(f"📸 Smart Content Items: {len(image_info_list)}")
        
        # Content type breakdown
        content_types = {}
        for content in image_info_list:
            content_type = content.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        if content_types:
            print(f"🔍 Content Types Found:")
            for content_type, count in content_types.items():
                print(f"  • {content_type.title()}: {count}")
        
        # Metadata
        print("\n📋 EXTRACTED METADATA:")
        for key, value in metadata.items():
            if value and str(value) != 'Unknown':
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Questions with smart content
        questions_with_content = sum(1 for q in questions if q.get('image_links_used'))
        
        print(f"\n❓ QUESTIONS BREAKDOWN:")
        question_types = {}
        for question in questions:
            q_type = question.get('question_type', 'Unknown')
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        for q_type, count in question_types.items():
            print(f"  • {q_type}: {count}")
        print(f"  • Questions with Smart Content: {questions_with_content}")
        
        print("=" * 80)
    
    def _print_multimodal_summary(self, source_filename: str, parsed_data: Dict, image_info_list: List[Dict]):
        """Print summary for multimodal processing results."""
        print("\n" + "=" * 80)
        print("🎉 MULTIMODAL PROCESSING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        metadata = parsed_data.get('metadata', {})
        questions = parsed_data.get('questions', [])
        
        print(f"📄 File: {source_filename}")
        print(f"🧠 Method: Llama Parse + Vision Models")
        print(f"📊 Questions: {len(questions)}")
        print(f"📸 Images: {len(image_info_list)}")
        
        print("\n📋 EXTRACTED METADATA:")
        for key, value in metadata.items():
            if value and value != 'Unknown':
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Question type breakdown
        question_types = {}
        questions_with_images = 0
        
        for question in questions:
            q_type = question.get('question_type', 'Unknown')
            question_types[q_type] = question_types.get(q_type, 0) + 1
            
            if question.get('image_references_in_text') or question.get('image_links_used'):
                questions_with_images += 1
        
        print(f"\n❓ QUESTIONS BREAKDOWN:")
        for q_type, count in question_types.items():
            print(f"  • {q_type}: {count}")
        print(f"  • Questions with Images: {questions_with_images}")
        
        print("=" * 80)
    
    def create_basic_parsed_data(self, extracted_text: str, source_filename: str) -> Dict:
        """
        Create basic parsed data structure when LLM processing is unavailable.
        
        Args:
            extracted_text: Raw text from OCR
            source_filename: Name of the source file
            
        Returns:
            Basic parsed data structure
        """
        try:
            # Create a basic structure when LLM is not available
            basic_data = {
                'metadata': {
                    'subject': None,
                    'school_name': None,
                    'booklet_type': None,
                    'total_marks': None,
                    'time_limit': None,
                    'general_instructions': extracted_text[:500] if extracted_text else None  # First 500 chars as instructions
                },
                'questions': [
                    {
                        'question_number': '1',
                        'question_text': extracted_text if extracted_text else 'No text extracted',
                        'options': {},
                        'marks': None,
                        'question_type': 'General',
                        'image_references_in_text': [],
                        'image_links_used': []
                    }
                ],
                'unmatched_image_links': []
            }
            
            print(f"📋 Created basic parsed data structure (LLM unavailable)")
            return basic_data
            
        except Exception as e:
            print(f"❌ Error creating basic parsed data: {e}")
            return {
                'metadata': {},
                'questions': [],
                'unmatched_image_links': []
            }
    
    def extract_text_with_confidence(self, pdf_path: str) -> Tuple[str, float]:
        """
        Extract text and return confidence score.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            text = self.extract_text_from_pdf(pdf_path)
            
            # Calculate confidence based on various factors
            confidence = 0.0
            
            if text:
                # Text length factor
                length_factor = min(len(text) / 1000, 1.0)  # Max 1.0 for 1000+ chars
                
                # Word count factor
                words = text.split()
                word_factor = min(len(words) / 100, 1.0)  # Max 1.0 for 100+ words
                
                # Special character ratio (lower is better for clean text)
                import string
                special_chars = sum(1 for c in text if c in string.punctuation)
                special_ratio = special_chars / len(text) if text else 1
                special_factor = max(0, 1 - special_ratio * 5)  # Penalty for too many special chars
                
                # Combine factors
                confidence = (length_factor * 0.4 + word_factor * 0.4 + special_factor * 0.2) * 100
            
            return text, min(confidence, 100.0)
            
        except Exception as e:
            print(f"❌ Error in text extraction with confidence: {e}")
            return "", 0.0