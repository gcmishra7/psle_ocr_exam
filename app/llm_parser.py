import google.generativeai as genai
from typing import List, Dict, Optional
import json
import re
from config.settings import settings

class LLMParser:
    """Handles parsing of extracted text using Gemini LLM, optimized for educational MCQ content."""
    
    def __init__(self):
        """Initialize LLM parser with Gemini configuration."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
    
    def create_mcq_parsing_prompt(self, text: str) -> str:
        """
        Create a specialized prompt for parsing MCQ questions from educational content.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Formatted prompt optimized for MCQ parsing
        """
        prompt = f"""
You are an expert at parsing Multiple Choice Questions (MCQ) from educational content. 
The text below contains questions extracted from an educational document that may include:
- Questions with diagrams or images (referenced in the question text)
- Multiple choice options numbered (1), (2), (3), (4) or lettered (A), (B), (C), (D)
- Questions that span multiple lines
- Mixed content with both question text and option text

For each question found, provide a JSON object with this structure:
{{
    "question_id": "sequential number starting from 1",
    "question_text": "the complete question text including any references to diagrams/images",
    "question_type": "multiple_choice",
    "options": [
        "option 1 text",
        "option 2 text", 
        "option 3 text",
        "option 4 text"
    ],
    "correct_answer": "correct answer if mentioned, otherwise empty string",
    "difficulty_level": "easy, medium, hard, or unknown",
    "subject_area": "the subject (science, math, english, etc.)",
    "page_number": "page number if mentioned",
    "has_diagram": true/false,
    "diagram_description": "brief description of any diagram/image referenced"
}}

IMPORTANT PARSING RULES:
1. Look for question patterns like "Study the diagram...", "Look at the figure...", "Which of the following..."
2. Group options that follow a question (numbered 1-4 or lettered A-D)
3. If a question references a diagram/image, set "has_diagram": true
4. Keep the complete question text, including setup/context
5. Clean up OCR artifacts but preserve meaning
6. If options are split across lines, combine them properly
7. Handle both numbered (1), (2), (3), (4) and lettered (A), (B), (C), (D) options

Text to analyze:
{text}

Return a JSON array of questions. If no questions are found, return an empty array [].
Focus on educational content and be thorough in capturing complete questions with all their options.
"""
        return prompt
    
    def preprocess_mcq_text(self, text: str) -> str:
        """
        Preprocess OCR text to improve MCQ parsing.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned and structured text
        """
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Fix common OCR errors in MCQ format
            line = re.sub(r'\(\s*([1-4A-Da-d])\s*\)', r'(\1)', line)  # Fix spaced parentheses
            line = re.sub(r'([1-4A-Da-d])\s*[\.\)]\s*', r'(\1) ', line)  # Normalize option format
            
            # Fix common words that get OCR'd incorrectly
            line = re.sub(r'\b[Ww]hich\b', 'Which', line)
            line = re.sub(r'\b[Tt]he\b', 'the', line)
            line = re.sub(r'\b[Oo]f\b', 'of', line)
            line = re.sub(r'\b[Ff]ollowing\b', 'following', line)
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def parse_questions(self, text: str) -> List[Dict]:
        """
        Parse MCQ questions from extracted text using Gemini LLM.
        
        Args:
            text: Raw text from OCR
            
        Returns:
            List of parsed questions as dictionaries
        """
        try:
            # Preprocess text for better MCQ parsing
            processed_text = self.preprocess_mcq_text(text)
            
            prompt = self.create_mcq_parsing_prompt(processed_text)
            
            print("🤖 Parsing educational content with Gemini LLM...")
            
            # Generate response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens,
                        )
                    )
                    
                    # Extract and parse JSON response
                    response_text = response.text.strip()
                    print(f"📝 Received response from Gemini (attempt {attempt + 1})")
                    
                    # Try to extract JSON from response
                    questions = self._extract_json_from_response(response_text)
                    
                    if questions:
                        print(f"✅ Successfully parsed {len(questions)} MCQ questions")
                        return self._validate_and_clean_questions(questions)
                    
                except Exception as e:
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise e
            
            # If all retries failed, try fallback parsing
            print("🔄 Trying fallback MCQ parsing...")
            return self._fallback_mcq_parse(processed_text)
                
        except Exception as e:
            print(f"❌ Error calling Gemini API: {e}")
            return self._fallback_mcq_parse(text)
    
    def _extract_json_from_response(self, response_text: str) -> List[Dict]:
        """Extract JSON array from Gemini response."""
        # Try to find JSON array in response
        json_patterns = [
            r'\[.*?\]',  # Look for array
            r'\{.*?\}',  # Look for single object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict):
                        return [parsed]
                except json.JSONDecodeError:
                    continue
        
        # Try parsing the entire response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return []
    
    def _validate_and_clean_questions(self, questions: List[Dict]) -> List[Dict]:
        """Validate and clean parsed questions."""
        cleaned_questions = []
        
        for i, question in enumerate(questions, 1):
            if not isinstance(question, dict):
                continue
            
            # Ensure required fields
            cleaned_question = {
                "question_id": str(question.get("question_id", i)),
                "question_text": str(question.get("question_text", "")).strip(),
                "question_type": question.get("question_type", "multiple_choice"),
                "options": question.get("options", []),
                "correct_answer": str(question.get("correct_answer", "")).strip(),
                "difficulty_level": question.get("difficulty_level", "unknown"),
                "subject_area": question.get("subject_area", "unknown"),
                "page_number": str(question.get("page_number", "unknown")),
                "has_diagram": bool(question.get("has_diagram", False)),
                "diagram_description": str(question.get("diagram_description", "")).strip()
            }
            
            # Only include questions with actual content
            if cleaned_question["question_text"] and len(cleaned_question["question_text"]) > 10:
                cleaned_questions.append(cleaned_question)
        
        return cleaned_questions
    
    def _fallback_mcq_parse(self, text: str) -> List[Dict]:
        """
        Fallback parsing method using regex patterns for MCQ content.
        
        Args:
            text: Raw text to parse
            
        Returns:
            List of questions found using MCQ-specific patterns
        """
        print("🔄 Using fallback MCQ parsing...")
        questions = []
        lines = text.split('\n')
        current_question = None
        current_options = []
        question_id = 1
        
        # MCQ patterns
        question_patterns = [
            r'^\s*\d+\.\s*(.+)',  # 1. Question text
            r'^\s*QUESTION\s*\d+',  # QUESTION 1
            r'.*[Ww]hich.*\?',  # Which ... ?
            r'.*[Ss]tudy.*diagram.*',  # Study the diagram
            r'.*[Ll]ook.*figure.*',  # Look at the figure
        ]
        
        option_patterns = [
            r'^\s*\(([1-4A-Da-d])\)\s*(.+)',  # (1) option text
            r'^\s*([1-4A-Da-d])[\.\)]\s*(.+)',  # 1. option text
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a question
            is_question = False
            for pattern in question_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    # Save previous question if exists
                    if current_question and current_options:
                        questions.append(self._create_fallback_question(
                            question_id, current_question, current_options
                        ))
                        question_id += 1
                    
                    current_question = line
                    current_options = []
                    is_question = True
                    break
            
            if is_question:
                continue
            
            # Check if line is an option
            is_option = False
            for pattern in option_patterns:
                match = re.match(pattern, line)
                if match:
                    option_text = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    current_options.append(option_text.strip())
                    is_option = True
                    break
            
            # If not an option and we have a current question, it might be continuation
            if not is_option and current_question and not current_options:
                if line.endswith('?') or len(line) > 20:
                    current_question += " " + line
        
        # Don't forget the last question
        if current_question and current_options:
            questions.append(self._create_fallback_question(
                question_id, current_question, current_options
            ))
        
        print(f"📋 Fallback parsing found {len(questions)} questions")
        return questions
    
    def _create_fallback_question(self, question_id: int, question_text: str, options: List[str]) -> Dict:
        """Create a question dictionary from fallback parsing."""
        # Detect if question mentions diagrams/images
        has_diagram = any(word in question_text.lower() for word in [
            'diagram', 'figure', 'image', 'picture', 'chart', 'graph', 'drawing'
        ])
        
        # Basic subject detection
        subject_keywords = {
            'science': ['energy', 'force', 'motion', 'chemical', 'physical', 'biology', 'physics'],
            'math': ['calculate', 'equation', 'number', 'formula', 'solve'],
            'english': ['word', 'sentence', 'grammar', 'meaning', 'passage'],
            'history': ['year', 'period', 'historical', 'event', 'date'],
            'geography': ['map', 'location', 'country', 'region', 'climate']
        }
        
        subject_area = "unknown"
        for subject, keywords in subject_keywords.items():
            if any(keyword in question_text.lower() for keyword in keywords):
                subject_area = subject
                break
        
        return {
            "question_id": str(question_id),
            "question_text": question_text.strip(),
            "question_type": "multiple_choice",
            "options": options,
            "correct_answer": "",
            "difficulty_level": "unknown",
            "subject_area": subject_area,
            "page_number": "unknown",
            "has_diagram": has_diagram,
            "diagram_description": "Referenced in question text" if has_diagram else ""
        }
    
    def enhance_question_metadata(self, questions: List[Dict], original_text: str) -> List[Dict]:
        """
        Enhance questions with additional metadata using LLM.
        
        Args:
            questions: List of parsed questions
            original_text: Original text for context
            
        Returns:
            Enhanced questions with better metadata
        """
        if not questions:
            return questions
        
        try:
            enhancement_prompt = f"""
Analyze these MCQ questions and enhance their metadata. Focus on educational accuracy and proper categorization.

Questions: {json.dumps(questions, indent=2)}

For each question, improve:
1. Subject area classification (science, mathematics, english, history, geography, etc.)
2. Difficulty level (easy, medium, hard) based on cognitive complexity
3. Better diagram descriptions if diagrams are referenced
4. Question type accuracy (ensure it's truly multiple_choice)
5. Clean up any OCR artifacts in question text and options

Return the enhanced questions in the same JSON format with improved metadata.
Pay special attention to questions that reference diagrams or images.
"""
            
            response = self.model.generate_content(
                enhancement_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent metadata
                    max_output_tokens=self.max_tokens,
                )
            )
            
            enhanced_questions = self._extract_json_from_response(response.text.strip())
            
            if enhanced_questions and len(enhanced_questions) == len(questions):
                print("✨ Successfully enhanced question metadata")
                return self._validate_and_clean_questions(enhanced_questions)
            else:
                print("⚠️  Enhancement failed, returning original questions")
                return questions
                
        except Exception as e:
            print(f"❌ Error enhancing questions: {e}")
            return questions