import google.generativeai as genai
from typing import List, Dict, Optional
import json
import re
from config.settings import settings

class LLMParser:
    """Enhanced LLM parser for extracting structured question paper data with metadata and image support."""
    
    def __init__(self):
        """Initialize the LLM parser with Gemini API."""
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def create_enhanced_prompt(self, question_paper_text: str, image_links: List[str]) -> str:
        """
        Create the enhanced prompt with question paper text and image links.
        
        Args:
            question_paper_text: Raw OCR text from the question paper
            image_links: List of available image links/paths
            
        Returns:
            Formatted prompt for the LLM
        """
        # Convert image links to JSON string
        image_links_json = json.dumps(image_links)
        
        prompt = f"""As an expert OCR Agent, your task is to meticulously parse the provided question paper text and associated image links. Your goal is to extract all relevant information and structure it into a comprehensive JSON object, following the detailed specifications below.

Input:
You will receive two inputs:

{{$question_paper_text}}: The raw text content extracted from the question paper.
{{$image_links}}: A JSON string representing an array of URLs for images that might be referenced in the question paper. Each URL may contain filename information that can help in matching.

Output Structure - JSON Object:

Your output must be a single JSON object. Do not include any conversational text, explanations, or markdown outside of the JSON block.

{{
  "metadata": {{
    "subject": "string | null",
    "school_name": "string | null",
    "booklet_type": "string | null",
    "total_marks": "string | null",
    "time_limit": "string | null",
    "general_instructions": "string | null"
  }},
  "questions": [
    {{
      "question_number": "string",
      "question_text": "string",
      "options": {{
        // "A": "string",
        // "B": "string"
        // ... (if MCQ, keys are option identifiers, values are option text)
      }},
      "marks": "string | null",
      "question_type": "string",
      "image_references_in_text": ["string"],
      "image_links_used": ["URL"]
    }}
    // ... more question objects
  ],
  "unmatched_image_links": ["URL"]
}}

Detailed Extraction Rules and Formatting Guidelines:

1. metadata Object:
* subject: Identify the main subject of the paper (e.g., "Physics", "English Literature", "Algebra"). If not explicitly stated, infer the best possible subject. If unknown, use null.
* school_name: Extract the name of the school, college, or institution. If not found, use null.
* booklet_type: Look for "Set A", "Booklet B", "Code 101", etc. If multiple are present, list the most prominent one or use null.
* total_marks: Find the overall total marks for the paper (e.g., "100 Marks", "Max Marks: 70"). Extract the numerical value and any unit. If not found, use null.
* time_limit: Find the total time duration (e.g., "3 Hours", "90 minutes"). If not found, use null.
* general_instructions: Concatenate all general instructions applicable to the entire paper into a single string. If no general instructions are found, use null.

2. questions Array:
* Each element in this array will be a JSON object representing a single question.
* Process questions sequentially as they appear in the question_paper_text.
* question_number:
  * Extract the leading number or identifier for each question (e.g., "1.", "Q2", "3(a)", "IV."). Be precise.
* question_text:
  * Capture the complete text of the question. This includes any introductory phrases, diagrams, tables, or passages that the question refers to, along with the actual question prompt.
  * Crucially, retain any explicit image references within the text (e.g., "refer to Figure 1.1", "as shown in Diagram A").
* options:
  * If the question is a Multiple Choice Question (MCQ), extract all options.
  * Represent options as a JSON object where keys are the option labels (e.g., "A", "B", "C", "D", "1", "2", "i", "ii") and values are the corresponding option texts.
  * If it's not an MCQ (e.g., short answer, long answer), this field should be an empty JSON object {{}}.
* marks:
  * Extract the marks allocated for the specific question. This is often in parentheses (e.g., "(2)", "[5 marks]", "3m"). Preserve the original string if units are involved, otherwise just the number. If not found, use null.
* question_type:
  * Categorize the question type based on its content and structure. Common types include:
    * "MCQ" (Multiple Choice Question)
    * "Short Answer"
    * "Long Answer" / "Descriptive"
    * "Fill-in-the-Blanks"
    * "True/False"
    * "Match the Following"
    * "Passage-based" (if a significant passage precedes the question)
    * "Diagram-based" (if the question relies heavily on an image)
    * "Assertion-Reason"
    * "Numerical Problem"
    * "Definition"
  * If unsure or a specific type is not covered, use "General".
* image_references_in_text:
  * An array of string references to images found within the question_text (e.g., "Figure 1", "Diagram A", "Table 5.2"). Search for common patterns like "Figure X", "Fig. X", "Diagram X", "Image X", "Illustration X", "Table X".
  * If no image references are found, this should be an empty array [].
* image_links_used:
  * An array of URLs from the {{$image_links}} input that directly correspond to the image_references_in_text for this specific question.
  * Crucially, you must match the extracted image_references_in_text to the provided image_links. Assume image filenames in the URLs often contain variations of the reference (e.g., figure_1_1.png might match "Figure 1.1", diagramA.jpg might match "Diagram A"). Perform fuzzy matching if necessary but prioritize exact matches.
  * Only include links that are explicitly referenced and used in that specific question.
  * If image references are found in the text but no matching link is available in {{$image_links}}, then the image_links_used array for that question should remain empty [].

3. unmatched_image_links Array:
* List any URLs from the original {{$image_links}} array that were not linked to any question in the questions array. This helps identify potentially extraneous images or missed references. If all images are matched, this array should be empty [].

Example of Desired Output Format (Illustrative - your output should be based on the actual input):

{{
  "metadata": {{
    "subject": "Biology",
    "school_name": "Galaxy Academy",
    "booklet_type": "Set R",
    "total_marks": "70",
    "time_limit": "2.5 Hours",
    "general_instructions": "All questions are compulsory. Draw neat and labelled diagrams wherever necessary. Marks for each question are indicated in brackets."
  }},
  "questions": [
    {{
      "question_number": "1",
      "question_text": "Which of the following is the powerhouse of the cell?",
      "options": {{
        "A": "Nucleus",
        "B": "Mitochondria",
        "C": "Cytoplasm",
        "D": "Ribosome"
      }},
      "marks": "1",
      "question_type": "MCQ",
      "image_references_in_text": [],
      "image_links_used": []
    }},
    {{
      "question_number": "2",
      "question_text": "Observe the given figure of a plant cell (Fig. 2.1) and label parts A, B, and C.",
      "options": {{}},
      "marks": "3",
      "question_type": "Diagram-based",
      "image_references_in_text": ["Fig. 2.1"],
      "image_links_used": ["https://example.com/asset/images/fig_2_1_plant_cell.png"]
    }}
  ],
  "unmatched_image_links": [
    "https://example.com/asset/images/school_logo.png",
    "https://example.com/asset/images/header_design.jpg"
  ]
}}

Now, process the following input accordingly:
{question_paper_text}, {image_links_json}"""
        
        return prompt
    
    def parse_questions_enhanced(self, ocr_text: str, image_links: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Parse OCR text using the enhanced prompt structure.
        
        Args:
            ocr_text: Raw text extracted from the question paper
            image_links: List of available image links/paths
            
        Returns:
            Parsed question paper data with metadata and questions, or None if failed
        """
        try:
            if image_links is None:
                image_links = []
            
            print("🧠 Processing with enhanced LLM parser...")
            
            # Create the enhanced prompt
            prompt = self.create_enhanced_prompt(ocr_text, image_links)
            
            # Generate response from Gemini
            print("🤖 Sending request to Gemini API...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json"
                )
            )
            
            if not response or not response.text:
                print("❌ Empty response from Gemini API")
                return None
            
            print("✅ Received response from Gemini API")
            
            # Parse the JSON response
            try:
                parsed_data = json.loads(response.text)
                
                # Validate the structure
                if not self.validate_parsed_data(parsed_data):
                    print("⚠️  Parsed data validation failed")
                    return None
                
                print(f"📊 Successfully parsed: {len(parsed_data.get('questions', []))} questions")
                return parsed_data
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return None
            
        except Exception as e:
            print(f"❌ Error in enhanced LLM parsing: {e}")
            return None
    
    def validate_parsed_data(self, data: Dict) -> bool:
        """
        Validate the structure of parsed data.
        
        Args:
            data: Parsed data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required top-level keys
            required_keys = ['metadata', 'questions', 'unmatched_image_links']
            for key in required_keys:
                if key not in data:
                    print(f"❌ Missing required key: {key}")
                    return False
            
            # Validate metadata structure
            metadata = data['metadata']
            if not isinstance(metadata, dict):
                print("❌ Metadata is not a dictionary")
                return False
            
            # Validate questions structure
            questions = data['questions']
            if not isinstance(questions, list):
                print("❌ Questions is not a list")
                return False
            
            # Validate each question
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    print(f"❌ Question {i} is not a dictionary")
                    return False
                
                required_q_keys = ['question_number', 'question_text', 'options', 
                                 'marks', 'question_type', 'image_references_in_text', 
                                 'image_links_used']
                
                for key in required_q_keys:
                    if key not in question:
                        print(f"❌ Question {i} missing key: {key}")
                        return False
                
                # Validate data types
                if not isinstance(question.get('options'), dict):
                    print(f"❌ Question {i} options is not a dictionary")
                    return False
                
                if not isinstance(question.get('image_references_in_text'), list):
                    print(f"❌ Question {i} image_references_in_text is not a list")
                    return False
                
                if not isinstance(question.get('image_links_used'), list):
                    print(f"❌ Question {i} image_links_used is not a list")
                    return False
            
            # Validate unmatched_image_links
            unmatched = data['unmatched_image_links']
            if not isinstance(unmatched, list):
                print("❌ unmatched_image_links is not a list")
                return False
            
            print("✅ Data validation successful")
            return True
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def extract_image_references_from_questions(self, questions: List[Dict]) -> List[str]:
        """
        Extract all image references mentioned in questions.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            List of unique image references
        """
        image_refs = []
        
        for question in questions:
            refs = question.get('image_references_in_text', [])
            image_refs.extend(refs)
        
        return list(set(image_refs))  # Remove duplicates
    
    def enhance_image_matching(self, parsed_data: Dict, available_images: List[Dict]) -> Dict:
        """
        Enhance image matching by improving the mapping between references and files.
        
        Args:
            parsed_data: Parsed question paper data
            available_images: List of available image information
            
        Returns:
            Enhanced parsed data with better image matching
        """
        try:
            # Create a mapping of image references to files
            from app.image_processor import ImageProcessor
            image_processor = ImageProcessor()
            
            questions = parsed_data.get('questions', [])
            unmatched_links = list(parsed_data.get('unmatched_image_links', []))
            
            for question in questions:
                image_refs = question.get('image_references_in_text', [])
                current_links = question.get('image_links_used', [])
                
                if image_refs and not current_links:
                    # Try to match references to available images
                    mappings = image_processor.match_image_references_to_files(image_refs, available_images)
                    
                    # Update the question with matched links
                    matched_links = list(mappings.values())
                    question['image_links_used'] = matched_links
                    
                    # Remove matched links from unmatched list
                    for link in matched_links:
                        if link in unmatched_links:
                            unmatched_links.remove(link)
            
            # Update unmatched links
            parsed_data['unmatched_image_links'] = unmatched_links
            
            print("🔗 Enhanced image matching completed")
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error enhancing image matching: {e}")
            return parsed_data
    
    def fallback_parse_questions(self, ocr_text: str) -> Optional[Dict]:
        """
        Fallback parsing method if enhanced parsing fails.
        
        Args:
            ocr_text: Raw OCR text
            
        Returns:
            Basic parsed data structure or None
        """
        try:
            print("🔄 Using fallback parsing method...")
            
            # Simple prompt for basic extraction
            fallback_prompt = f"""
Extract questions from this text and format as JSON:

{ocr_text}

Return only a JSON object with this structure:
{{
  "metadata": {{
    "subject": "string or null",
    "school_name": "string or null",
    "booklet_type": "string or null",
    "total_marks": "string or null",
    "time_limit": "string or null",
    "general_instructions": "string or null"
  }},
  "questions": [
    {{
      "question_number": "string",
      "question_text": "string",
      "options": {{}},
      "marks": "string or null",
      "question_type": "string",
      "image_references_in_text": [],
      "image_links_used": []
    }}
  ],
  "unmatched_image_links": []
}}
"""
            
            response = self.model.generate_content(
                fallback_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                    response_mime_type="application/json"
                )
            )
            
            if response and response.text:
                try:
                    parsed_data = json.loads(response.text)
                    if self.validate_parsed_data(parsed_data):
                        print("✅ Fallback parsing successful")
                        return parsed_data
                except json.JSONDecodeError:
                    pass
            
            print("❌ Fallback parsing failed")
            return None
            
        except Exception as e:
            print(f"❌ Fallback parsing error: {e}")
            return None