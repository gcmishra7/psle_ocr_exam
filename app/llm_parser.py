import google.generativeai as genai
from typing import List, Dict, Optional
import json
import re
from config.settings import settings

class LLMParser:
    """Handles parsing of extracted text using Gemini LLM."""
    
    def __init__(self):
        """Initialize LLM parser with Gemini configuration."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
    
    def create_parsing_prompt(self, text: str) -> str:
        """
        Create a prompt for parsing questions from text.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""
You are an expert at parsing and extracting questions from educational content. 
Analyze the following text and extract all questions with their relevant information.

For each question found, provide a JSON object with the following structure:
{{
    "question_id": "sequential number starting from 1",
    "question_text": "the actual question text",
    "question_type": "multiple_choice, true_false, short_answer, essay, or other",
    "options": ["option1", "option2", "option3", "option4"] (if applicable),
    "correct_answer": "correct answer if available",
    "difficulty_level": "easy, medium, hard, or unknown",
    "subject_area": "the subject or topic area",
    "page_number": "page number where found (if mentioned)"
}}

Text to analyze:
{text}

Please extract all questions and return them as a JSON array. If no questions are found, return an empty array.
Focus on identifying clear question patterns like:
- Sentences ending with question marks
- Multiple choice questions with options A, B, C, D
- Fill-in-the-blank questions
- True/False questions
- Essay or short answer prompts

Return only the JSON array, no additional text.
"""
        return prompt
    
    def parse_questions(self, text: str) -> List[Dict]:
        """
        Parse questions from extracted text using Gemini LLM.
        
        Args:
            text: Raw text from OCR
            
        Returns:
            List of parsed questions as dictionaries
        """
        try:
            prompt = self.create_parsing_prompt(text)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Extract and parse JSON response
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                questions = json.loads(json_text)
                return questions
            else:
                # If no JSON array found, try to parse the entire response
                questions = json.loads(response_text)
                return questions
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return self._fallback_parse(text)
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> List[Dict]:
        """
        Fallback parsing method using regex patterns.
        
        Args:
            text: Raw text to parse
            
        Returns:
            List of questions found using basic patterns
        """
        questions = []
        lines = text.split('\n')
        question_id = 1
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for lines ending with question marks
            if line.endswith('?') and len(line) > 10:
                question = {
                    "question_id": str(question_id),
                    "question_text": line,
                    "question_type": "unknown",
                    "options": [],
                    "correct_answer": "",
                    "difficulty_level": "unknown",
                    "subject_area": "unknown",
                    "page_number": "unknown"
                }
                
                # Look for multiple choice options in following lines
                options = []
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if re.match(r'^[A-D][\.\)]\s*', next_line):
                        options.append(next_line)
                    elif next_line and not re.match(r'^[A-D][\.\)]\s*', next_line):
                        break
                
                if options:
                    question["question_type"] = "multiple_choice"
                    question["options"] = options
                
                questions.append(question)
                question_id += 1
        
        return questions
    
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
Given these parsed questions and the original text, enhance each question with better metadata:

Questions: {json.dumps(questions, indent=2)}

Original text context: {original_text[:1000]}...

For each question, improve the metadata by analyzing:
1. Subject area (math, science, history, etc.)
2. Difficulty level based on complexity
3. Question type accuracy
4. Any missing information

Return the enhanced questions in the same JSON format.
"""
            
            response = self.model.generate_content(enhancement_prompt)
            enhanced_questions = json.loads(response.text.strip())
            return enhanced_questions
            
        except Exception as e:
            print(f"Error enhancing questions: {e}")
            return questions