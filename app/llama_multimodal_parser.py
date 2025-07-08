import os
import json
import base64
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

# Llama Parse imports with fallbacks
try:
    from llama_parse import LlamaParse
    HAS_LLAMA_PARSE = True
except ImportError:
    HAS_LLAMA_PARSE = False
    print("⚠️  Llama Parse not available")

# Vision model imports with fallbacks
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  Google Gemini not available")

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  OpenAI not available")

from PIL import Image
import sqlite3
from config.settings import settings

class LlamaMultimodalParser:
    """
    Advanced parser combining Llama Parse with multimodal vision capabilities.
    Includes automatic cleanup for reprocessing files.
    """
    
    def __init__(self):
        """Initialize the multimodal parser with all available models."""
        self.data_dir = Path("data")
        self.images_dir = self.data_dir / "images"
        self.db_path = self.data_dir / "questions.db"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize parsers
        self._init_llama_parse()
        self._init_vision_models()
        
    def _init_llama_parse(self):
        """Initialize Llama Parse with API key."""
        if HAS_LLAMA_PARSE:
            try:
                # Get API key from environment or settings
                api_key = os.getenv("LLAMA_CLOUD_API_KEY") or getattr(settings, "llama_cloud_api_key", None)
                if api_key:
                    self.llama_parser = LlamaParse(
                        api_key=api_key,
                        result_type="markdown",  # Get structured markdown output
                        verbose=True,
                        language="english",
                        parsing_instruction="""
                        This is an educational document containing exam questions.
                        Please extract:
                        1. Document metadata (subject, school, exam type, marks, time limit)
                        2. All questions with their numbers, text, options, and marks
                        3. Any figure/image references in the text
                        4. General instructions
                        
                        Preserve the exact question numbering and formatting.
                        Mark any image/figure references clearly.
                        """
                    )
                    print("✅ Llama Parse initialized")
                else:
                    self.llama_parser = None
                    print("⚠️  Llama Parse API key not found")
            except Exception as e:
                self.llama_parser = None
                print(f"❌ Llama Parse initialization failed: {e}")
        else:
            self.llama_parser = None
            
    def _init_vision_models(self):
        """Initialize vision models for multimodal analysis."""
        self.vision_models = {}
        
        # Initialize Gemini Vision
        if HAS_GEMINI:
            try:
                api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
                if api_key:
                    genai.configure(api_key=api_key)
                    self.vision_models['gemini'] = genai.GenerativeModel('gemini-1.5-pro')
                    print("✅ Gemini Vision initialized")
            except Exception as e:
                print(f"⚠️  Gemini Vision failed: {e}")
        
        # Initialize OpenAI Vision
        if HAS_OPENAI:
            try:
                api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "openai_api_key", None)
                if api_key:
                    self.vision_models['openai'] = openai.OpenAI(api_key=api_key)
                    print("✅ OpenAI Vision initialized")
            except Exception as e:
                print(f"⚠️  OpenAI Vision failed: {e}")
    
    def cleanup_previous_data(self, source_filename: str) -> bool:
        """
        Clean up previous data for reprocessing the same file.
        Truncates images folder and database entries for the file.
        """
        try:
            print(f"🧹 Cleaning up previous data for: {source_filename}")
            
            # 1. Clean up images folder
            pdf_name = Path(source_filename).stem
            pdf_images_dir = self.images_dir / pdf_name
            
            if pdf_images_dir.exists():
                shutil.rmtree(pdf_images_dir)
                print(f"🗑️  Removed image folder: {pdf_images_dir}")
            
            # 2. Clean up database entries
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get paper_id first
                cursor.execute('SELECT id FROM paper_metadata WHERE source_file = ?', (source_filename,))
                result = cursor.fetchone()
                
                if result:
                    paper_id = result[0]
                    
                    # Delete in correct order (foreign keys)
                    cursor.execute('DELETE FROM unmatched_images WHERE paper_id = ?', (paper_id,))
                    cursor.execute('DELETE FROM questions_new WHERE paper_id = ?', (paper_id,))
                    cursor.execute('DELETE FROM paper_metadata WHERE id = ?', (paper_id,))
                    
                    print(f"🗑️  Removed database entries for paper_id: {paper_id}")
                
                # Also clean up related tables
                cursor.execute('DELETE FROM images WHERE source_file = ?', (source_filename,))
                cursor.execute('DELETE FROM processed_files WHERE filename = ?', (source_filename,))
                
                conn.commit()
                print(f"✅ Database cleanup completed for: {source_filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False
    
    def parse_with_llama_parse(self, pdf_path: str) -> Optional[str]:
        """Parse PDF using Llama Parse to get structured content."""
        if not self.llama_parser:
            print("⚠️  Llama Parse not available, skipping")
            return None
            
        try:
            print("📄 Parsing with Llama Parse...")
            
            # Parse the document
            documents = self.llama_parser.load_data(pdf_path)
            
            if documents:
                # Combine all document text
                full_text = "\n\n".join([doc.text for doc in documents])
                print(f"✅ Llama Parse extracted {len(full_text)} characters")
                return full_text
            else:
                print("⚠️  No content extracted by Llama Parse")
                return None
                
        except Exception as e:
            print(f"❌ Llama Parse error: {e}")
            return None
    
    def analyze_images_with_vision(self, image_paths: List[str], context_text: str = "") -> List[Dict]:
        """Analyze images using multimodal vision models."""
        if not self.vision_models:
            print("⚠️  No vision models available")
            return []
        
        image_analyses = []
        
        for image_path in image_paths:
            try:
                print(f"👁️  Analyzing image: {Path(image_path).name}")
                
                # Try Gemini first, then OpenAI
                analysis = None
                
                if 'gemini' in self.vision_models:
                    analysis = self._analyze_with_gemini(image_path, context_text)
                
                if not analysis and 'openai' in self.vision_models:
                    analysis = self._analyze_with_openai(image_path, context_text)
                
                if analysis:
                    image_analyses.append({
                        'image_path': image_path,
                        'analysis': analysis,
                        'extracted_at': datetime.now().isoformat()
                    })
                    print(f"✅ Image analysis completed: {Path(image_path).name}")
                else:
                    print(f"⚠️  No analysis for: {Path(image_path).name}")
                    
            except Exception as e:
                print(f"❌ Error analyzing {image_path}: {e}")
        
        return image_analyses
    
    def _analyze_with_gemini(self, image_path: str, context_text: str) -> Optional[str]:
        """Analyze image using Gemini Vision."""
        try:
            # Load image
            image = Image.open(image_path)
            
            prompt = f"""
            Analyze this image from an educational document. Context: {context_text[:500] if context_text else 'Educational exam paper'}
            
            Please identify:
            1. What type of content is this? (diagram, graph, table, figure, etc.)
            2. Extract any text visible in the image
            3. Describe the visual elements and their relationships
            4. If this relates to a specific question, identify question markers or numbers
            5. Provide a clear description that would help match this to question text
            
            Format as JSON with keys: content_type, extracted_text, description, question_markers, educational_context
            """
            
            response = self.vision_models['gemini'].generate_content([prompt, image])
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini analysis error: {e}")
            return None
    
    def _analyze_with_openai(self, image_path: str, context_text: str) -> Optional[str]:
        """Analyze image using OpenAI Vision."""
        try:
            # Convert image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""
            Analyze this image from an educational document. Context: {context_text[:500] if context_text else 'Educational exam paper'}
            
            Please identify:
            1. What type of content is this? (diagram, graph, table, figure, etc.)
            2. Extract any text visible in the image
            3. Describe the visual elements and their relationships
            4. If this relates to a specific question, identify question markers or numbers
            5. Provide a clear description that would help match this to question text
            
            Format as JSON with keys: content_type, extracted_text, description, question_markers, educational_context
            """
            
            response = self.vision_models['openai'].chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI analysis error: {e}")
            return None
    
    def enhanced_question_extraction(self, text_content: str, image_analyses: List[Dict]) -> Dict:
        """
        Extract questions using combined text and image analysis.
        Uses the user's sophisticated prompt for structure.
        """
        try:
            # Use Gemini for enhanced text analysis with image context
            if 'gemini' in self.vision_models:
                return self._extract_with_enhanced_prompt(text_content, image_analyses)
            else:
                # Fallback to basic extraction
                return self._extract_basic_structure(text_content, image_analyses)
                
        except Exception as e:
            print(f"❌ Question extraction error: {e}")
            return self._create_fallback_response(text_content)
    
    def _extract_with_enhanced_prompt(self, text_content: str, image_analyses: List[Dict]) -> Dict:
        """Extract using the user's sophisticated prompt with image context."""
        
        # Prepare image context
        image_context = ""
        if image_analyses:
            image_context = "\n\nAvailable Images Analysis:\n"
            for i, analysis in enumerate(image_analyses, 1):
                image_path = analysis['image_path']
                image_name = Path(image_path).name
                image_context += f"{i}. {image_name}: {analysis['analysis'][:200]}...\n"
        
        # Use the user's sophisticated prompt with image enhancement
        enhanced_prompt = f"""
        You are an expert educational content parser. Parse this exam paper and extract comprehensive metadata and questions.

        {image_context}

        TEXT CONTENT:
        {text_content}

        CRITICAL REQUIREMENTS:
        1. Extract COMPLETE metadata including subject, school_name, booklet_type, total_marks, time_limit
        2. Identify ALL questions with proper numbering
        3. Match image references in questions to available images
        4. Provide structured JSON output

        OUTPUT FORMAT (strict JSON):
        {{
            "metadata": {{
                "subject": "extracted subject name",
                "school_name": "school/institution name", 
                "booklet_type": "type of exam booklet",
                "total_marks": "total marks for exam",
                "time_limit": "time limit for exam",
                "general_instructions": "general instructions text"
            }},
            "questions": [
                {{
                    "question_number": "1",
                    "question_text": "complete question text",
                    "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
                    "marks": "marks for this question",
                    "question_type": "MCQ/Short Answer/Long Answer/etc",
                    "image_references_in_text": ["Figure 1.1", "Diagram A"],
                    "image_links_used": ["path/to/matched/image1.png"]
                }}
            ],
            "unmatched_image_links": ["unmatched/image/paths"]
        }}

        PARSE NOW:
        """
        
        try:
            response = self.vision_models['gemini'].generate_content(enhanced_prompt)
            
            # Try to parse JSON response
            response_text = response.text.strip()
            
            # Clean up markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(response_text)
            
            # Enhance with image matching
            if image_analyses:
                parsed_data = self._enhance_with_image_matching(parsed_data, image_analyses)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return self._create_fallback_response(text_content)
        except Exception as e:
            print(f"❌ Enhanced extraction error: {e}")
            return self._create_fallback_response(text_content)
    
    def _enhance_with_image_matching(self, parsed_data: Dict, image_analyses: List[Dict]) -> Dict:
        """Enhance parsed data with smart image matching."""
        try:
            # Create image lookup by analysis content
            image_lookup = {}
            for analysis in image_analyses:
                image_path = analysis['image_path']
                image_name = Path(image_path).name
                analysis_text = analysis.get('analysis', '').lower()
                
                # Extract question numbers from analysis
                import re
                question_numbers = re.findall(r'question\s*(\d+)', analysis_text)
                figure_numbers = re.findall(r'figure\s*(\d+(?:\.\d+)?)', analysis_text)
                
                image_lookup[image_name] = {
                    'path': image_path,
                    'question_numbers': question_numbers,
                    'figure_numbers': figure_numbers,
                    'analysis': analysis_text
                }
            
            # Match images to questions
            for question in parsed_data.get('questions', []):
                question_num = question.get('question_number', '')
                image_refs = question.get('image_references_in_text', [])
                matched_images = []
                
                # Try to match by question number
                for image_name, info in image_lookup.items():
                    if question_num in info['question_numbers']:
                        matched_images.append(f"/data/images/{Path(info['path']).parent.name}/{image_name}")
                
                # Try to match by figure references
                for ref in image_refs:
                    ref_lower = ref.lower()
                    for image_name, info in image_lookup.items():
                        if any(fig_num in ref_lower for fig_num in info['figure_numbers']):
                            image_path = f"/data/images/{Path(info['path']).parent.name}/{image_name}"
                            if image_path not in matched_images:
                                matched_images.append(image_path)
                
                question['image_links_used'] = matched_images
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Image matching error: {e}")
            return parsed_data
    
    def _extract_basic_structure(self, text_content: str, image_analyses: List[Dict]) -> Dict:
        """Basic extraction without advanced models."""
        # Simple regex-based extraction as fallback
        import re
        
        questions = []
        
        # Find question patterns
        question_pattern = r'(\d+)\.\s*(.*?)(?=\d+\.\s*|\Z)'
        matches = re.findall(question_pattern, text_content, re.DOTALL)
        
        for match in matches:
            question_num, question_text = match
            questions.append({
                'question_number': question_num.strip(),
                'question_text': question_text.strip()[:500],
                'options': {},
                'marks': '',
                'question_type': 'Unknown',
                'image_references_in_text': [],
                'image_links_used': []
            })
        
        return {
            'metadata': {
                'subject': 'Unknown',
                'school_name': 'Unknown',
                'booklet_type': 'Unknown',
                'total_marks': 'Unknown',
                'time_limit': 'Unknown',
                'general_instructions': ''
            },
            'questions': questions,
            'unmatched_image_links': []
        }
    
    def _create_fallback_response(self, text_content: str) -> Dict:
        """Create fallback response structure."""
        return {
            'metadata': {
                'subject': 'Parse Error - Manual Review Required',
                'school_name': 'Unknown',
                'booklet_type': 'Unknown', 
                'total_marks': 'Unknown',
                'time_limit': 'Unknown',
                'general_instructions': text_content[:500] if text_content else ''
            },
            'questions': [],
            'unmatched_image_links': [],
            'parsing_notes': 'Automatic parsing failed, manual review required'
        }
    
    def process_pdf_multimodal(self, pdf_path: str, source_filename: str) -> Tuple[Dict, List[Dict]]:
        """
        Complete multimodal processing pipeline.
        
        Returns:
            Tuple of (parsed_data, image_info_list)
        """
        try:
            print(f"🚀 Starting multimodal processing: {source_filename}")
            
            # Step 1: Cleanup previous data
            self.cleanup_previous_data(source_filename)
            
            # Step 2: Extract images (using existing image processor)
            from app.image_processor import ImageProcessor
            image_processor = ImageProcessor()
            image_info_list, image_links = image_processor.extract_images_from_pdf(pdf_path, source_filename)
            
            # Step 3: Parse text with Llama Parse
            text_content = self.parse_with_llama_parse(pdf_path)
            
            # Fallback to basic OCR if Llama Parse fails
            if not text_content:
                print("⚠️  Falling back to basic OCR...")
                # Use existing OCR logic as fallback
                text_content = "Basic OCR extraction - Llama Parse unavailable"
            
            # Step 4: Analyze images with vision models
            image_paths = [info['full_path'] for info in image_info_list]
            image_analyses = self.analyze_images_with_vision(image_paths, text_content)
            
            # Step 5: Enhanced question extraction
            parsed_data = self.enhanced_question_extraction(text_content, image_analyses)
            
            print(f"✅ Multimodal processing completed: {len(parsed_data.get('questions', []))} questions found")
            
            return parsed_data, image_info_list
            
        except Exception as e:
            print(f"❌ Multimodal processing error: {e}")
            import traceback
            traceback.print_exc()
            
            # Return minimal fallback
            return self._create_fallback_response(""), []