import gradio as gr
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
import base64
from io import BytesIO

class GradioQuizApp:
    """
    Gradio-based quiz application with proper image rendering and navigation.
    """
    
    def __init__(self):
        """Initialize the quiz app."""
        self.current_question_idx = 0
        self.questions = []
        self.paper_metadata = {}
        self.user_answers = {}
        self.selected_paper = None
        
    def load_papers(self) -> List[str]:
        """Load available papers from database."""
        try:
            # Import here to avoid circular imports
            from app.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            papers = db_manager.get_all_papers()
            
            if not papers:
                return ["No papers found - Please process a PDF first"]
            
            paper_options = []
            for paper in papers:
                subject = paper.get('subject', 'Unknown Subject')
                school = paper.get('school_name', '')
                display_name = f"{subject}"
                if school:
                    display_name += f" - {school}"
                display_name += f" ({paper['source_file']})"
                paper_options.append(display_name)
            
            return paper_options
            
        except Exception as e:
            print(f"Error loading papers: {e}")
            return [f"Error loading papers: {e}"]
    
    def load_paper_data(self, paper_selection: str) -> Tuple[str, str, str, str, str, str]:
        """Load paper data and return initial question display."""
        try:
            if not paper_selection or paper_selection.startswith("No papers") or paper_selection.startswith("Error"):
                return ("Select a paper to start the quiz", "", "", "", "", "No paper selected")
            
            # Extract filename from selection
            if "(" in paper_selection and ")" in paper_selection:
                filename = paper_selection.split("(")[-1].rstrip(")")
            else:
                filename = paper_selection
            
            # Import here to avoid circular imports
            from app.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            paper_data = db_manager.get_paper_by_file(filename)
            
            if not paper_data:
                return ("Paper not found", "", "", "", "", "Paper not found")
            
            self.paper_metadata = paper_data.get('metadata', {})
            self.questions = paper_data.get('questions', [])
            self.current_question_idx = 0
            self.user_answers = {}
            self.selected_paper = filename
            
            if not self.questions:
                return ("No questions found in this paper", "", "", "", "", "No questions found")
            
            # Return initial question display
            return self.display_current_question()
            
        except Exception as e:
            error_msg = f"Error loading paper: {e}"
            print(error_msg)
            return (error_msg, "", "", "", "", error_msg)
    
    def display_current_question(self) -> Tuple[str, str, str, str, str, str]:
        """Display the current question with all details."""
        try:
            if not self.questions or self.current_question_idx >= len(self.questions):
                return ("No question to display", "", "", "", "", "No question available")
            
            question = self.questions[self.current_question_idx]
            question_num = self.current_question_idx + 1
            total_questions = len(self.questions)
            
            # Question header with progress
            progress = f"Question {question_num} of {total_questions}"
            subject = self.paper_metadata.get('subject', 'Quiz')
            header = f"📚 {subject} - {progress}"
            
            # Question text with styling
            question_text = question.get('question_text', 'No question text')
            question_type = question.get('question_type', 'Unknown')
            marks = question.get('marks', '')
            
            formatted_question = f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                <h3 style="margin: 0;">Question {question_num}</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{question_type} {f"• {marks} marks" if marks else ""}</p>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 10px; border: 2px solid #e1e8ed; margin-bottom: 15px;">
                <p style="font-size: 16px; line-height: 1.6; margin: 0;">{question_text}</p>
            </div>
            """
            
            # Options for MCQ
            options_html = ""
            options = question.get('options', {})
            if options and isinstance(options, dict):
                options_html = "<div style='margin-top: 15px;'><h4>Options:</h4>"
                for key, value in options.items():
                    selected = "✅" if self.user_answers.get(f"q_{question_num}") == key else "◯"
                    options_html += f"<p><strong>{selected} {key}:</strong> {value}</p>"
                options_html += "</div>"
            
            # Combine question and options
            full_question = formatted_question + options_html
            
            # Image display
            image_display = self.get_question_image(question)
            
            # Navigation info
            nav_info = f"Progress: {question_num}/{total_questions} | Answered: {len(self.user_answers)}"
            
            # Button states
            prev_enabled = self.current_question_idx > 0
            next_enabled = self.current_question_idx < len(self.questions) - 1
            
            prev_button = "⬅️ Previous" if prev_enabled else "⬅️ Previous (disabled)"
            next_button = "Next ➡️" if next_enabled else "Next ➡️ (disabled)"
            
            return (header, full_question, image_display, nav_info, prev_button, next_button)
            
        except Exception as e:
            error_msg = f"Error displaying question: {e}"
            print(error_msg)
            return (error_msg, "", "", "", "", "")
    
    def get_question_image(self, question: Dict) -> str:
        """Get and properly format question image for display."""
        try:
            image_links = question.get('image_links_used', [])
            
            if not image_links:
                return "No images for this question"
            
            # Try to find and display the first valid image
            for image_link in image_links:
                # Clean and normalize the image path
                image_path = self.normalize_image_path(image_link)
                
                if os.path.exists(image_path):
                    try:
                        # Load and resize image for web display
                        image = Image.open(image_path)
                        
                        # Resize if too large
                        max_width = 800
                        if image.width > max_width:
                            ratio = max_width / image.width
                            new_height = int(image.height * ratio)
                            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Return the path for Gradio to display
                        return image_path
                        
                    except Exception as e:
                        print(f"Error loading image {image_path}: {e}")
                        continue
                else:
                    print(f"Image not found: {image_path}")
                    continue
            
            return "Images not found or could not be loaded"
            
        except Exception as e:
            print(f"Error getting question image: {e}")
            return f"Error loading image: {e}"
    
    def normalize_image_path(self, image_link: str) -> str:
        """Normalize image path to ensure it exists."""
        try:
            # Remove leading slashes and normalize
            clean_path = image_link.lstrip('/')
            
            # Try different path combinations
            possible_paths = [
                clean_path,
                image_link.replace('/data/', 'data/'),
                f"data/{clean_path}",
                f"data/images/{Path(image_link).name}",
                os.path.join("data", "images", Path(image_link).name)
            ]
            
            # Also try with the selected paper name
            if self.selected_paper:
                paper_name = Path(self.selected_paper).stem
                possible_paths.extend([
                    f"data/images/{paper_name}/{Path(image_link).name}",
                    os.path.join("data", "images", paper_name, Path(image_link).name)
                ])
            
            # Return the first existing path
            for path in possible_paths:
                if os.path.exists(path):
                    return os.path.abspath(path)
            
            # If none found, return the original
            return image_link
            
        except Exception as e:
            print(f"Error normalizing image path: {e}")
            return image_link
    
    def previous_question(self) -> Tuple[str, str, str, str, str, str]:
        """Navigate to previous question."""
        if self.current_question_idx > 0:
            self.current_question_idx -= 1
        return self.display_current_question()
    
    def next_question(self) -> Tuple[str, str, str, str, str, str]:
        """Navigate to next question."""
        if self.current_question_idx < len(self.questions) - 1:
            self.current_question_idx += 1
        return self.display_current_question()
    
    def answer_question(self, answer: str) -> Tuple[str, str, str, str, str, str]:
        """Record answer for current question."""
        try:
            if self.questions and 0 <= self.current_question_idx < len(self.questions):
                question_num = self.current_question_idx + 1
                self.user_answers[f"q_{question_num}"] = answer
                print(f"Recorded answer for Q{question_num}: {answer}")
            
            # Refresh display to show updated answer
            return self.display_current_question()
            
        except Exception as e:
            print(f"Error recording answer: {e}")
            return self.display_current_question()
    
    def jump_to_question(self, question_num: int) -> Tuple[str, str, str, str, str, str]:
        """Jump directly to a specific question number."""
        try:
            # Convert to 0-based index
            target_idx = question_num - 1
            
            if 0 <= target_idx < len(self.questions):
                self.current_question_idx = target_idx
            
            return self.display_current_question()
            
        except Exception as e:
            print(f"Error jumping to question: {e}")
            return self.display_current_question()
    
    def get_quiz_summary(self) -> str:
        """Get a summary of quiz progress."""
        try:
            if not self.questions:
                return "No quiz loaded"
            
            total_questions = len(self.questions)
            answered_questions = len(self.user_answers)
            completion_percent = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
            
            summary = f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                <h3 style="color: #28a745; margin-top: 0;">📊 Quiz Progress</h3>
                <p><strong>Paper:</strong> {self.paper_metadata.get('subject', 'Unknown')}</p>
                <p><strong>Questions:</strong> {answered_questions}/{total_questions} answered</p>
                <p><strong>Completion:</strong> {completion_percent:.1f}%</p>
                <p><strong>Current Question:</strong> {self.current_question_idx + 1}</p>
            </div>
            
            <div style="margin-top: 15px;">
                <h4>Your Answers:</h4>
            """
            
            for i, question in enumerate(self.questions, 1):
                user_answer = self.user_answers.get(f"q_{i}", "Not answered")
                status = "✅" if f"q_{i}" in self.user_answers else "❌"
                summary += f"<p>{status} Q{i}: {user_answer}</p>"
            
            summary += "</div>"
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        
        with gr.Blocks(
            title="🎓 Enhanced Quiz App",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .quiz-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 20px;
            }
            .question-card {
                background: white;
                border: 2px solid #e1e8ed;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
            .progress-info {
                background: #e8f5e8;
                border: 1px solid #28a745;
                border-radius: 5px;
                padding: 10px;
                margin: 10px 0;
            }
            """
        ) as interface:
            
            # Header
            gr.HTML("""
            <div class="quiz-header">
                <h1>🎓 Interactive Quiz Application</h1>
                <p>Smart Content Extraction + Modern Quiz Experience</p>
            </div>
            """)
            
            with gr.Row():
                # Left column - Quiz interface
                with gr.Column(scale=2):
                    # Paper selection
                    paper_dropdown = gr.Dropdown(
                        choices=self.load_papers(),
                        label="📚 Select a Paper",
                        value=None,
                        interactive=True
                    )
                    
                    # Question display area
                    question_header = gr.HTML("Select a paper to start the quiz")
                    question_display = gr.HTML("")
                    
                    # Image display
                    question_image = gr.Image(
                        label="📸 Question Image/Diagram",
                        show_label=True,
                        height=400,
                        show_download_button=False
                    )
                    
                    # Answer input for MCQ
                    with gr.Row():
                        answer_input = gr.Textbox(
                            label="Your Answer (A, B, C, D, etc.)",
                            placeholder="Enter your answer choice...",
                            max_lines=1
                        )
                        submit_answer = gr.Button("✅ Submit Answer", variant="primary")
                    
                    # Navigation
                    with gr.Row():
                        prev_btn = gr.Button("⬅️ Previous", variant="secondary")
                        next_btn = gr.Button("Next ➡️", variant="secondary")
                    
                    # Progress info
                    progress_info = gr.HTML("")
                
                # Right column - Summary and navigation
                with gr.Column(scale=1):
                    gr.HTML("<h3>🎯 Quiz Navigation</h3>")
                    
                    # Quick jump to question
                    with gr.Row():
                        question_jump = gr.Number(
                            label="Jump to Question #",
                            minimum=1,
                            maximum=100,
                            value=1,
                            precision=0
                        )
                        jump_btn = gr.Button("🎯 Jump", size="sm")
                    
                    # Quiz summary
                    summary_display = gr.HTML("Load a paper to see progress")
                    
                    # Refresh summary button
                    refresh_summary = gr.Button("🔄 Refresh Progress", variant="secondary")
            
            # Event handlers
            paper_dropdown.change(
                fn=self.load_paper_data,
                inputs=[paper_dropdown],
                outputs=[question_header, question_display, question_image, progress_info, prev_btn, next_btn]
            )
            
            prev_btn.click(
                fn=self.previous_question,
                outputs=[question_header, question_display, question_image, progress_info, prev_btn, next_btn]
            )
            
            next_btn.click(
                fn=self.next_question,
                outputs=[question_header, question_display, question_image, progress_info, prev_btn, next_btn]
            )
            
            submit_answer.click(
                fn=self.answer_question,
                inputs=[answer_input],
                outputs=[question_header, question_display, question_image, progress_info, prev_btn, next_btn]
            )
            
            jump_btn.click(
                fn=self.jump_to_question,
                inputs=[question_jump],
                outputs=[question_header, question_display, question_image, progress_info, prev_btn, next_btn]
            )
            
            refresh_summary.click(
                fn=self.get_quiz_summary,
                outputs=[summary_display]
            )
            
            # Auto-refresh summary when answer is submitted
            submit_answer.click(
                fn=self.get_quiz_summary,
                outputs=[summary_display]
            )
        
        return interface

def launch_quiz_app():
    """Launch the Gradio quiz application."""
    app = GradioQuizApp()
    interface = app.create_interface()
    
    print("🚀 Starting Enhanced Quiz Application...")
    print("🎓 Features:")
    print("  • Smart image extraction and display")
    print("  • Interactive quiz navigation")
    print("  • Progress tracking")
    print("  • Answer recording")
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    launch_quiz_app()