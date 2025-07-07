import streamlit as st
import pandas as pd
from typing import List, Dict
import json
from datetime import datetime
import io

from app.ocr_processor import OCRProcessor
from app.llm_parser import LLMParser
from app.database_manager import DatabaseManager
from config.settings import settings

class StreamlitUI:
    """Streamlit-based user interface for the OCR application."""
    
    def __init__(self):
        """Initialize UI components."""
        self.ocr_processor = None
        self.llm_parser = None
        self.db_manager = DatabaseManager()
        
        # Initialize session state
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = ""
        if 'parsed_questions' not in st.session_state:
            st.session_state.parsed_questions = []
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=settings.APP_TITLE,
            page_icon="📝",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_components(self):
        """Initialize OCR and LLM components with error handling."""
        try:
            if self.ocr_processor is None:
                self.ocr_processor = OCRProcessor()
            
            if self.llm_parser is None:
                if not settings.GEMINI_API_KEY:
                    st.error("❌ Gemini API key is not configured. Please add it to your .env file.")
                    st.stop()
                self.llm_parser = LLMParser()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error initializing components: {str(e)}")
            return False
    
    def render_sidebar(self):
        """Render sidebar with navigation and settings."""
        with st.sidebar:
            st.title("📝 PDF Question Parser")
            
            # Navigation
            st.subheader("Navigation")
            page = st.selectbox(
                "Select Page",
                ["Upload & Process", "View Questions", "Statistics", "Settings"]
            )
            
            # Quick stats
            stats = self.db_manager.get_statistics()
            st.subheader("Quick Stats")
            st.metric("Total Questions", stats.get('total_questions', 0))
            st.metric("Files Processed", stats.get('total_files', 0))
            
            return page
    
    def render_upload_page(self):
        """Render file upload and processing page."""
        st.header("📄 Upload PDF and Extract Questions")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help=f"Maximum file size: {settings.MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.info(f"File size: {uploaded_file.size / 1024 / 1024:.2f} MB")
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                enhance_metadata = st.checkbox(
                    "Enhance question metadata", 
                    value=True,
                    help="Use LLM to improve question categorization and metadata"
                )
            
            with col2:
                save_to_db = st.checkbox(
                    "Save to database", 
                    value=True,
                    help="Store extracted questions in the database"
                )
            
            # Process button
            if st.button("🚀 Process PDF", type="primary", use_container_width=True):
                self.process_pdf(uploaded_file, enhance_metadata, save_to_db)
    
    def process_pdf(self, uploaded_file, enhance_metadata: bool, save_to_db: bool):
        """Process the uploaded PDF file."""
        if not self.initialize_components():
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: OCR Processing
            status_text.text("🔍 Extracting text from PDF...")
            progress_bar.progress(20)
            
            if self.ocr_processor:
                extracted_text = self.ocr_processor.extract_from_uploaded_file(uploaded_file)
            else:
                st.error("❌ OCR processor not initialized")
                return
            
            if not extracted_text.strip():
                st.error("❌ No text could be extracted from the PDF. Please check if the file contains readable text.")
                return
            
            st.session_state.extracted_text = extracted_text
            
            # Step 2: LLM Parsing
            status_text.text("🤖 Parsing questions with Gemini LLM...")
            progress_bar.progress(50)
            
            if self.llm_parser:
                parsed_questions = self.llm_parser.parse_questions(extracted_text)
            else:
                st.error("❌ LLM parser not initialized")
                return
            
            if not parsed_questions:
                st.warning("⚠️ No questions were found in the extracted text.")
                return
            
            # Step 3: Enhance metadata (optional)
            if enhance_metadata and self.llm_parser:
                status_text.text("✨ Enhancing question metadata...")
                progress_bar.progress(70)
                parsed_questions = self.llm_parser.enhance_question_metadata(
                    parsed_questions, extracted_text
                )
            
            st.session_state.parsed_questions = parsed_questions
            
            # Step 4: Save to database (optional)
            if save_to_db:
                status_text.text("💾 Saving to database...")
                progress_bar.progress(90)
                success = self.db_manager.save_questions(parsed_questions, uploaded_file.name)
                if not success:
                    st.error("❌ Failed to save questions to database.")
                    return
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            st.session_state.processing_complete = True
            
            # Display results
            self.display_processing_results(parsed_questions, extracted_text)
            
        except Exception as e:
            st.error(f"❌ Error processing PDF: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    def display_processing_results(self, questions: List[Dict], extracted_text: str):
        """Display the results of PDF processing."""
        st.success(f"🎉 Successfully extracted {len(questions)} questions!")
        
        # Display extracted text (collapsible)
        with st.expander("📝 View Extracted Text"):
            st.text_area("Raw OCR Text", extracted_text, height=200)
        
        # Display parsed questions
        st.subheader("📋 Parsed Questions")
        
        for i, question in enumerate(questions, 1):
            with st.expander(f"Question {i}: {question.get('question_text', '')[:100]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Text:** {question.get('question_text', '')}")
                    st.write(f"**Type:** {question.get('question_type', 'Unknown')}")
                    st.write(f"**Subject:** {question.get('subject_area', 'Unknown')}")
                
                with col2:
                    st.write(f"**Difficulty:** {question.get('difficulty_level', 'Unknown')}")
                    st.write(f"**Page:** {question.get('page_number', 'Unknown')}")
                    if question.get('options'):
                        st.write("**Options:**")
                        for option in question['options']:
                            st.write(f"  • {option}")
        
        # Download options
        self.render_download_options(questions)
    
    def render_download_options(self, questions: List[Dict]):
        """Render download options for processed questions."""
        st.subheader("📥 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download as JSON
            json_data = json.dumps(questions, indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Download as CSV
            if questions:
                df = pd.json_normalize(questions)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv_data,
                    file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            # Download as Excel
            if questions:
                df = pd.json_normalize(questions)
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                excel_data = buffer.getvalue()
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    def render_questions_page(self):
        """Render page to view and manage stored questions."""
        st.header("📚 View Questions Database")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search questions", "")
        
        with col2:
            files = [f['filename'] for f in self.db_manager.get_processed_files()]
            selected_file = st.selectbox("📁 Filter by file", ["All files"] + files)
        
        with col3:
            refresh_btn = st.button("🔄 Refresh", use_container_width=True)
        
        # Get questions based on filters
        if search_term:
            questions = self.db_manager.search_questions(search_term)
        elif selected_file != "All files":
            questions = self.db_manager.get_questions_by_file(selected_file)
        else:
            questions = self.db_manager.get_all_questions()
        
        if not questions:
            st.info("📭 No questions found. Upload and process some PDF files first!")
            return
        
        # Display questions in a table
        st.subheader(f"Found {len(questions)} questions")
        
        # Convert to DataFrame for better display
        df_data = []
        for q in questions:
            df_data.append({
                'ID': q['id'],
                'Question': q['question_text'][:100] + '...' if len(q['question_text']) > 100 else q['question_text'],
                'Type': q['question_type'],
                'Subject': q['subject_area'],
                'Difficulty': q['difficulty_level'],
                'Source': q['source_file'],
                'Created': q['created_at']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def render_statistics_page(self):
        """Render statistics and analytics page."""
        st.header("📊 Statistics & Analytics")
        
        stats = self.db_manager.get_statistics()
        
        if stats.get('total_questions', 0) == 0:
            st.info("📊 No data available. Process some PDF files to see statistics.")
            return
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Questions", stats.get('total_questions', 0))
        
        with col2:
            st.metric("Files Processed", stats.get('total_files', 0))
        
        with col3:
            avg_per_file = stats.get('total_questions', 0) / max(stats.get('total_files', 1), 1)
            st.metric("Avg Questions/File", f"{avg_per_file:.1f}")
        
        with col4:
            most_common_type = max(stats.get('questions_by_type', {}).items(), 
                                 key=lambda x: x[1], default=('N/A', 0))[0]
            st.metric("Most Common Type", most_common_type)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Questions by Type")
            if stats.get('questions_by_type'):
                type_df = pd.DataFrame(
                    list(stats['questions_by_type'].items()),
                    columns=['Type', 'Count']
                )
                st.bar_chart(type_df.set_index('Type'))
        
        with col2:
            st.subheader("Questions by Difficulty")
            if stats.get('questions_by_difficulty'):
                diff_df = pd.DataFrame(
                    list(stats['questions_by_difficulty'].items()),
                    columns=['Difficulty', 'Count']
                )
                st.bar_chart(diff_df.set_index('Difficulty'))
        
        # Processed files table
        st.subheader("📁 Processed Files")
        files = self.db_manager.get_processed_files()
        if files:
            files_df = pd.DataFrame(files)
            st.dataframe(files_df, use_container_width=True)
    
    def render_settings_page(self):
        """Render settings and configuration page."""
        st.header("⚙️ Settings & Configuration")
        
        # API Configuration
        st.subheader("🔑 API Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_key_status = "✅ Configured" if settings.GEMINI_API_KEY else "❌ Not configured"
            st.info(f"Gemini API Key: {api_key_status}")
            st.text_input("Gemini Model", value=settings.GEMINI_MODEL, disabled=True)
        
        with col2:
            st.number_input("Temperature", value=settings.GEMINI_TEMPERATURE, disabled=True)
            st.number_input("Max Tokens", value=settings.GEMINI_MAX_TOKENS, disabled=True)
        
        # Database Configuration
        st.subheader("🗄️ Database Configuration")
        st.text_input("Database Path", value=settings.DATABASE_PATH, disabled=True)
        
        # OCR Configuration
        st.subheader("👁️ OCR Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Tesseract Path", value=settings.TESSERACT_PATH, disabled=True)
        
        with col2:
            st.text_input("OCR Language", value=settings.OCR_LANGUAGE, disabled=True)
        
        # Application Information
        st.subheader("ℹ️ Application Information")
        st.info(f"""
        **Application Title:** {settings.APP_TITLE}
        **Port:** {settings.APP_PORT}
        **Debug Mode:** {settings.DEBUG_MODE}
        **Max File Size:** {settings.MAX_FILE_SIZE_MB} MB
        """)
    
    def run(self):
        """Main function to run the Streamlit application."""
        self.setup_page_config()
        
        # Render sidebar and get selected page
        page = self.render_sidebar()
        
        # Render selected page
        if page == "Upload & Process":
            self.render_upload_page()
        elif page == "View Questions":
            self.render_questions_page()
        elif page == "Statistics":
            self.render_statistics_page()
        elif page == "Settings":
            self.render_settings_page()

# Main entry point for Streamlit
def main():
    """Main function to initialize and run the Streamlit UI."""
    ui = StreamlitUI()
    ui.run()

if __name__ == "__main__":
    main()