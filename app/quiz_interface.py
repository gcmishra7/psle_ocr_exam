import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json
from PIL import Image
import base64
import io

class QuizInterface:
    """
    Modern quiz app interface for displaying questions with proper MCQ rendering
    and inline image support.
    """
    
    def __init__(self):
        """Initialize the quiz interface."""
        self.current_question = 0
        self.user_answers = {}
        
    def render_quiz_app(self, paper_data: Dict):
        """
        Render the complete quiz application interface.
        
        Args:
            paper_data: Parsed paper data with questions and metadata
        """
        st.markdown(self._get_quiz_css(), unsafe_allow_html=True)
        
        # Extract data
        metadata = paper_data.get('metadata', {})
        questions = paper_data.get('questions', [])
        
        if not questions:
            st.warning("No questions found in this paper.")
            return
        
        # Header section
        self._render_quiz_header(metadata)
        
        # Quiz navigation and content
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Main quiz area
            self._render_question_area(questions)
        
        with col2:
            # Sidebar with navigation
            self._render_quiz_sidebar(questions)
    
    def _get_quiz_css(self) -> str:
        """Return CSS styles for the quiz interface."""
        return """
        <style>
        .quiz-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .quiz-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: bold;
        }
        
        .quiz-header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .question-card {
            background: white;
            border: 2px solid #e1e8ed;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .question-card:hover {
            border-color: #667eea;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .question-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .question-number {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }
        
        .question-type {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .question-marks {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .question-text {
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 20px;
            color: #333;
        }
        
        .mcq-options {
            margin: 20px 0;
        }
        
        .mcq-option {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
        }
        
        .mcq-option:hover {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        
        .mcq-option.selected {
            background: #e8f5e8;
            border-color: #4caf50;
        }
        
        .option-letter {
            background: #6c757d;
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            font-size: 0.9rem;
        }
        
        .selected .option-letter {
            background: #4caf50;
        }
        
        .option-text {
            flex: 1;
            font-size: 1rem;
        }
        
        .question-image {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin: 15px 0;
            max-width: 100%;
            height: auto;
        }
        
        .image-caption {
            text-align: center;
            font-style: italic;
            color: #666;
            margin-top: 5px;
            font-size: 0.9rem;
        }
        
        .navigation-panel {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            position: sticky;
            top: 20px;
        }
        
        .nav-title {
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        
        .question-nav-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 20px;
        }
        
        .question-nav-item {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 8px;
            text-align: center;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .question-nav-item:hover {
            border-color: #007bff;
        }
        
        .question-nav-item.current {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        
        .question-nav-item.answered {
            background: #28a745;
            color: white;
            border-color: #28a745;
        }
        
        .progress-info {
            background: white;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            margin: 10px 0;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #28a745, #20c997);
            border-radius: 10px;
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .image-gallery {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }
        
        .inline-image {
            max-width: 300px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        </style>
        """
    
    def _render_quiz_header(self, metadata: Dict):
        """Render the quiz header with paper information."""
        subject = metadata.get('subject', 'Unknown Subject')
        school = metadata.get('school_name', '')
        total_marks = metadata.get('total_marks', '')
        time_limit = metadata.get('time_limit', '')
        
        header_html = f"""
        <div class="quiz-header">
            <h1>📚 {subject}</h1>
            <div class="subtitle">
                {school} {f"• {total_marks} marks" if total_marks else ""} {f"• {time_limit}" if time_limit else ""}
            </div>
        </div>
        """
        
        st.markdown(header_html, unsafe_allow_html=True)
    
    def _render_question_area(self, questions: List[Dict]):
        """Render the main question display area."""
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = {}
        
        current_q = st.session_state.current_question
        
        if 0 <= current_q < len(questions):
            question = questions[current_q]
            self._render_single_question(question, current_q + 1)
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if current_q > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.current_question = current_q - 1
                    st.rerun()
        
        with col3:
            if current_q < len(questions) - 1:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.current_question = current_q + 1
                    st.rerun()
            else:
                if st.button("🏁 Finish", use_container_width=True, type="primary"):
                    st.success("Quiz completed! Review your answers in the sidebar.")
    
    def _render_single_question(self, question: Dict, question_num: int):
        """Render a single question with proper formatting."""
        question_text = question.get('question_text', '')
        options = question.get('options', {})
        question_type = question.get('question_type', 'Unknown')
        marks = question.get('marks', '')
        image_links = question.get('image_links_used', [])
        
        # Question card container
        card_html = f"""
        <div class="question-card">
            <div class="question-header">
                <div class="question-number">{question_num}</div>
                <div class="question-type">{question_type}</div>
                {f'<div class="question-marks">{marks} marks</div>' if marks else ''}
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Question text
        st.markdown(f'<div class="question-text">{question_text}</div>', unsafe_allow_html=True)
        
        # Display images if any
        if image_links:
            self._render_question_images(image_links)
        
        # Render options based on question type
        if question_type == 'MCQ' and options:
            self._render_mcq_options(question, question_num)
        elif options:
            self._render_other_options(options)
        
        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)
    
    def _render_mcq_options(self, question: Dict, question_num: int):
        """Render MCQ options with interactive selection."""
        options = question.get('options', {})
        
        if not options:
            return
        
        # Get current answer
        current_answer = st.session_state.user_answers.get(f"q_{question_num}", None)
        
        st.markdown('<div class="mcq-options">', unsafe_allow_html=True)
        
        # Create radio button for selection
        option_keys = list(options.keys())
        option_labels = [f"{key}. {options[key]}" for key in option_keys]
        
        selected = st.radio(
            f"Select your answer for Question {question_num}:",
            options=option_keys,
            format_func=lambda x: f"{x}. {options[x]}",
            index=option_keys.index(current_answer) if current_answer in option_keys else None,
            key=f"mcq_{question_num}",
            label_visibility="collapsed"
        )
        
        if selected:
            st.session_state.user_answers[f"q_{question_num}"] = selected
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_other_options(self, options: Dict):
        """Render non-MCQ options."""
        if not options:
            return
            
        st.markdown("**Options:**")
        for key, value in options.items():
            st.markdown(f"**{key}.** {value}")
    
    def _render_question_images(self, image_links: List[str]):
        """Render images associated with a question."""
        if not image_links:
            return
        
        st.markdown("**Reference Images:**")
        
        # Display images in a responsive layout
        cols = st.columns(min(len(image_links), 2))
        
        for i, image_link in enumerate(image_links):
            with cols[i % 2]:
                self._display_image_safely(image_link, f"Image {i+1}")
    
    def _display_image_safely(self, image_path: str, caption: str = ""):
        """Safely display an image with error handling."""
        try:
            # Clean the image path
            clean_path = image_path.replace('/data/', 'data/').replace('/images/', 'images/')
            
            if os.path.exists(clean_path):
                image = Image.open(clean_path)
                st.image(image, caption=caption, use_column_width=True)
            else:
                # Try alternative paths
                alternative_paths = [
                    image_path.lstrip('/'),
                    f"data/{image_path.lstrip('/')}",
                    f"data/images/{Path(image_path).name}"
                ]
                
                image_found = False
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        image = Image.open(alt_path)
                        st.image(image, caption=caption, use_column_width=True)
                        image_found = True
                        break
                
                if not image_found:
                    st.warning(f"⚠️ Image not found: {image_path}")
                    
        except Exception as e:
            st.error(f"❌ Error loading image: {e}")
    
    def _render_quiz_sidebar(self, questions: List[Dict]):
        """Render the quiz navigation sidebar."""
        st.markdown('<div class="navigation-panel">', unsafe_allow_html=True)
        
        # Progress info
        total_questions = len(questions)
        answered_count = len(st.session_state.user_answers)
        progress = (answered_count / total_questions) * 100 if total_questions > 0 else 0
        
        st.markdown(f'<div class="nav-title">📊 Progress</div>', unsafe_allow_html=True)
        
        progress_html = f"""
        <div class="progress-info">
            <div><strong>{answered_count}/{total_questions}</strong> answered</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress}%"></div>
            </div>
            <div>{progress:.1f}% complete</div>
        </div>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
        
        # Question navigation grid
        st.markdown('<div class="nav-title">🎯 Questions</div>', unsafe_allow_html=True)
        
        # Create clickable question numbers
        cols = st.columns(4)
        
        for i, question in enumerate(questions):
            with cols[i % 4]:
                is_current = st.session_state.current_question == i
                is_answered = f"q_{i+1}" in st.session_state.user_answers
                
                button_type = "primary" if is_current else "secondary"
                button_label = f"{'✓' if is_answered else ''} {i+1}"
                
                if st.button(button_label, key=f"nav_q_{i}", use_container_width=True, type=button_type):
                    st.session_state.current_question = i
                    st.rerun()
        
        # Question type summary
        st.markdown('<div class="nav-title">📋 Summary</div>', unsafe_allow_html=True)
        
        question_types = {}
        for q in questions:
            q_type = q.get('question_type', 'Unknown')
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        for q_type, count in question_types.items():
            st.markdown(f"**{q_type}:** {count}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_quiz_results(self, questions: List[Dict]):
        """Render quiz results and answers summary."""
        st.markdown("## 📊 Quiz Results")
        
        if not st.session_state.user_answers:
            st.warning("No answers recorded yet.")
            return
        
        # Results summary
        total_questions = len(questions)
        answered_count = len(st.session_state.user_answers)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Answered", answered_count)
        with col3:
            st.metric("Completion", f"{(answered_count/total_questions)*100:.1f}%")
        
        # Detailed answers
        st.markdown("### 📝 Your Answers")
        
        for i, question in enumerate(questions, 1):
            user_answer = st.session_state.user_answers.get(f"q_{i}", "Not answered")
            
            with st.expander(f"Question {i}: {question.get('question_text', '')[:50]}..."):
                st.write(f"**Your Answer:** {user_answer}")
                
                options = question.get('options', {})
                if options:
                    st.write("**Available Options:**")
                    for key, value in options.items():
                        emoji = "✅" if key == user_answer else "◯"
                        st.write(f"{emoji} **{key}.** {value}")

# Import os for file path checking
import os