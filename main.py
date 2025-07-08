#!/usr/bin/env python3
"""
PDF Question Parser - Main Application Entry Point

This is the main entry point for the PDF OCR Question Parser application.
Run this file to start the Streamlit web interface.

Usage:
    streamlit run main.py
    
or

    python main.py
"""

import sys
import os
from pathlib import Path
import streamlit as st
import tempfile
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import base64

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from config.settings import settings
    from app.streamlit_ui import main
    from app.ocr_processor import OCRProcessor
    from app.database_manager import DatabaseManager
    from app.image_processor import ImageProcessor
    
    # Page configuration
    st.set_page_config(
        page_title="Enhanced OCR Question Paper Parser",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better UI
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .step-header {
            font-size: 1.5rem;
            font-weight: bold;
            color: #ff7f0e;
            margin: 1rem 0;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #c3e6cb;
            margin: 1rem 0;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #f5c6cb;
            margin: 1rem 0;
        }
        .info-box {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #b8daff;
            margin: 1rem 0;
        }
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
        }
    </style>
    """, unsafe_allow_html=True)

    def initialize_components():
        """Initialize all components."""
        try:
            ocr_processor = OCRProcessor()
            db_manager = DatabaseManager()
            image_processor = ImageProcessor()
            return ocr_processor, db_manager, image_processor, True
        except Exception as e:
            st.error(f"❌ Failed to initialize components: {e}")
            return None, None, None, False

    def display_header():
        """Display the main header."""
        st.markdown('<div class="main-header">🎓 Enhanced OCR Question Paper Parser</div>', unsafe_allow_html=True)
        st.markdown("### Transform PDF question papers into structured data with image support!")

    def display_sidebar():
        """Display the sidebar with navigation and stats."""
        with st.sidebar:
            st.title("📊 Navigation")
            
            page = st.selectbox(
                "Choose a function:",
                ["📄 Process New PDF", "📚 Browse Questions", "📈 Statistics", "🖼️ Image Gallery", "⚙️ Settings"]
            )
            
            st.markdown("---")
            
            # Display quick stats
            st.subheader("📊 Quick Stats")
            try:
                db_manager = DatabaseManager()
                stats = db_manager.get_statistics()
                
                st.metric("Papers Processed", stats.get('total_papers', 0))
                st.metric("Questions Found", stats.get('total_questions', 0))
                st.metric("Images Stored", stats.get('total_images', 0))
                
            except Exception as e:
                st.error(f"Error loading stats: {e}")
            
            st.markdown("---")
            
            # System info
            st.subheader("🔧 System Info")
            st.info(f"Database: {settings.DATABASE_PATH}")
            st.info(f"Images: ./data/images/")
            
            return page

    def process_pdf_page():
        """PDF processing page with enhanced features."""
        st.markdown('<div class="step-header">📄 Process New PDF</div>', unsafe_allow_html=True)
        
        # Initialize components
        ocr_processor, db_manager, image_processor, components_ok = initialize_components()
        
        if not components_ok:
            st.error("❌ System initialization failed. Please check your configuration.")
            return
        
        st.markdown("""
        <div class="info-box">
        🚀 <strong>Enhanced Processing Features:</strong><br>
        • Extract images from PDF pages<br>
        • Advanced metadata detection (subject, school, marks, etc.)<br>
        • Smart image reference matching<br>
        • Multiple question types support<br>
        • Comprehensive database storage
        </div>
        """, unsafe_allow_html=True)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload a PDF question paper:",
            type=['pdf'],
            help="Upload a clear, high-quality PDF for best results"
        )
        
        if uploaded_file is not None:
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Name", uploaded_file.name)
            with col2:
                st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
            with col3:
                if st.button("🚀 Process PDF", type="primary"):
                    process_uploaded_file(uploaded_file, ocr_processor, db_manager)

    def process_uploaded_file(uploaded_file, ocr_processor, db_manager):
        """Process the uploaded PDF file."""
        try:
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            progress_bar.progress(10)
            status_text.text("📁 File saved temporarily...")
            
            # Process the PDF
            with st.spinner("🔄 Processing PDF with enhanced features..."):
                progress_bar.progress(30)
                status_text.text("📸 Extracting images and performing OCR...")
                
                success = ocr_processor.process_pdf_comprehensive(tmp_path, uploaded_file.name)
                
                progress_bar.progress(90)
                status_text.text("💾 Saving to database...")
            
            # Clean up temporary file
            os.unlink(tmp_path)
            progress_bar.progress(100)
            
            if success:
                status_text.empty()
                progress_bar.empty()
                
                # Display success message with stats
                stats = ocr_processor.get_processing_stats()
                
                st.markdown(f"""
                <div class="success-message">
                ✅ <strong>Processing completed successfully!</strong><br><br>
                📊 <strong>Processing Statistics:</strong><br>
                • Pages processed: {stats.get('pages_processed', 0)}<br>
                • Images extracted: {stats.get('images_extracted', 0)}<br>
                • Questions found: {stats.get('questions_found', 0)}<br>
                • Processing time: {stats.get('processing_time', 0)} seconds
                </div>
                """, unsafe_allow_html=True)
                
                # Show processed data
                display_processed_data(uploaded_file.name, db_manager)
                
            else:
                st.markdown("""
                <div class="error-message">
                ❌ <strong>Processing failed!</strong><br>
                Please check the PDF quality and try again.
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

    def display_processed_data(filename, db_manager):
        """Display the processed data for a file."""
        try:
            paper_data = db_manager.get_paper_by_file(filename)
            
            if not paper_data:
                st.warning("No data found for this file.")
                return
            
            st.markdown('<div class="step-header">📋 Processed Data</div>', unsafe_allow_html=True)
            
            # Display metadata
            metadata = paper_data.get('metadata', {})
            if any(metadata.values()):
                st.subheader("📄 Paper Metadata")
                
                col1, col2 = st.columns(2)
                with col1:
                    if metadata.get('subject'):
                        st.info(f"**Subject:** {metadata['subject']}")
                    if metadata.get('school_name'):
                        st.info(f"**School:** {metadata['school_name']}")
                    if metadata.get('booklet_type'):
                        st.info(f"**Booklet Type:** {metadata['booklet_type']}")
                
                with col2:
                    if metadata.get('total_marks'):
                        st.info(f"**Total Marks:** {metadata['total_marks']}")
                    if metadata.get('time_limit'):
                        st.info(f"**Time Limit:** {metadata['time_limit']}")
                
                if metadata.get('general_instructions'):
                    st.subheader("📋 General Instructions")
                    st.text_area("Instructions", metadata['general_instructions'], height=100, disabled=True)
            
            # Display questions
            questions = paper_data.get('questions', [])
            if questions:
                st.subheader(f"❓ Questions ({len(questions)} found)")
                
                for i, question in enumerate(questions, 1):
                    with st.expander(f"Question {question.get('question_number', i)} - {question.get('question_type', 'Unknown')}"):
                        
                        # Question text
                        st.write("**Question Text:**")
                        st.write(question.get('question_text', 'No text'))
                        
                        # Options (if any)
                        options = question.get('options', {})
                        if options and isinstance(options, dict) and options:
                            st.write("**Options:**")
                            for key, value in options.items():
                                st.write(f"• **{key}:** {value}")
                        
                        # Additional info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if question.get('marks'):
                                st.info(f"**Marks:** {question['marks']}")
                        with col2:
                            st.info(f"**Type:** {question.get('question_type', 'Unknown')}")
                        with col3:
                            image_refs = question.get('image_references_in_text', [])
                            if image_refs:
                                st.info(f"**Images:** {len(image_refs)} referenced")
                        
                        # Display images if any
                        image_links = question.get('image_links_used', [])
                        if image_links:
                            st.write("**Associated Images:**")
                            display_question_images(image_links)
        
        except Exception as e:
            st.error(f"Error displaying processed data: {e}")

    def display_question_images(image_links):
        """Display images associated with a question."""
        try:
            cols = st.columns(min(len(image_links), 3))
            
            for i, image_link in enumerate(image_links):
                col_idx = i % 3
                
                with cols[col_idx]:
                    # Try to find and display the image
                    image_path = image_link.replace('/data/', 'data/')
                    
                    if os.path.exists(image_path):
                        try:
                            image = Image.open(image_path)
                            st.image(image, caption=f"Image {i+1}", use_column_width=True)
                        except Exception as e:
                            st.error(f"Error loading image: {e}")
                    else:
                        st.warning(f"Image not found: {image_path}")
        
        except Exception as e:
            st.error(f"Error displaying images: {e}")

    def browse_questions_page():
        """Browse all processed questions."""
        st.markdown('<div class="step-header">📚 Browse Questions</div>', unsafe_allow_html=True)
        
        try:
            db_manager = DatabaseManager()
            papers = db_manager.get_all_papers()
            
            if not papers:
                st.info("No papers processed yet. Upload a PDF to get started!")
                return
            
            # Select paper
            paper_options = {f"{paper['source_file']} ({paper.get('subject', 'Unknown Subject')})": paper['source_file'] 
                            for paper in papers}
            
            selected_display = st.selectbox("Select a paper to view:", list(paper_options.keys()))
            selected_file = paper_options[selected_display]
            
            # Display paper data
            if selected_file:
                display_processed_data(selected_file, db_manager)
        
        except Exception as e:
            st.error(f"Error browsing questions: {e}")

    def statistics_page():
        """Display comprehensive statistics."""
        st.markdown('<div class="step-header">📈 Statistics</div>', unsafe_allow_html=True)
        
        try:
            db_manager = DatabaseManager()
            image_processor = ImageProcessor()
            
            # Get database stats
            db_stats = db_manager.get_statistics()
            image_stats = image_processor.get_image_stats()
            
            # Main metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Papers", db_stats.get('total_papers', 0))
            with col2:
                st.metric("Total Questions", db_stats.get('total_questions', 0))
            with col3:
                st.metric("Total Images", db_stats.get('total_images', 0))
            with col4:
                st.metric("Storage Used", f"{image_stats.get('total_size_mb', 0)} MB")
            
            # Question types chart
            question_types = db_stats.get('question_types', {})
            if question_types:
                st.subheader("📊 Question Types Distribution")
                df_types = pd.DataFrame(list(question_types.items()), columns=['Type', 'Count'])
                st.bar_chart(df_types.set_index('Type'))
            
            # Subjects chart
            subjects = db_stats.get('subjects', {})
            if subjects:
                st.subheader("📚 Subjects Distribution")
                df_subjects = pd.DataFrame(list(subjects.items()), columns=['Subject', 'Count'])
                st.bar_chart(df_subjects.set_index('Subject'))
            
            # Recent papers
            papers = db_manager.get_all_papers()
            if papers:
                st.subheader("📄 Recent Papers")
                df_papers = pd.DataFrame(papers)
                st.dataframe(df_papers, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error displaying statistics: {e}")

    def image_gallery_page():
        """Display image gallery."""
        st.markdown('<div class="step-header">🖼️ Image Gallery</div>', unsafe_allow_html=True)
        
        try:
            db_manager = DatabaseManager()
            papers = db_manager.get_all_papers()
            
            if not papers:
                st.info("No papers with images found.")
                return
            
            # Select paper for image viewing
            paper_options = {paper['source_file']: paper['source_file'] for paper in papers}
            selected_file = st.selectbox("Select a paper to view images:", list(paper_options.keys()))
            
            if selected_file:
                paper_data = db_manager.get_paper_by_file(selected_file)
                
                if paper_data:
                    questions = paper_data.get('questions', [])
                    all_images = []
                    
                    # Collect all image links
                    for question in questions:
                        image_links = question.get('image_links_used', [])
                        for link in image_links:
                            all_images.append({
                                'link': link,
                                'question': question.get('question_number', 'Unknown'),
                                'question_text': question.get('question_text', '')[:100] + '...'
                            })
                    
                    if all_images:
                        st.subheader(f"🖼️ Images from {selected_file} ({len(all_images)} found)")
                        
                        # Display images in grid
                        cols = st.columns(3)
                        
                        for i, img_data in enumerate(all_images):
                            col_idx = i % 3
                            
                            with cols[col_idx]:
                                image_path = img_data['link'].replace('/data/', 'data/')
                                
                                if os.path.exists(image_path):
                                    try:
                                        image = Image.open(image_path)
                                        st.image(image, 
                                               caption=f"Q{img_data['question']}: {img_data['question_text'][:50]}...",
                                               use_column_width=True)
                                    except Exception as e:
                                        st.error(f"Error loading image: {e}")
                                else:
                                    st.warning(f"Image not found: {image_path}")
                    else:
                        st.info("No images found in this paper.")
        
        except Exception as e:
            st.error(f"Error displaying image gallery: {e}")

    def settings_page():
        """Display settings and configuration."""
        st.markdown('<div class="step-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
        st.subheader("🔧 System Configuration")
        
        # Display current settings
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Database Path:** {settings.DATABASE_PATH}")
            st.info(f"**Gemini Model:** {getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')}")
            st.info(f"**OCR Language:** {getattr(settings, 'OCR_LANGUAGE', 'eng')}")
        
        with col2:
            st.info(f"**Images Directory:** ./data/images/")
            st.info(f"**Processing DPI:** 300")
            st.info(f"**Max Tokens:** 8192")
        
        # Environment check
        st.subheader("🔍 Environment Check")
        
        env_checks = {
            "Gemini API Key": bool(settings.GEMINI_API_KEY),
            "Database Directory": os.path.exists(os.path.dirname(settings.DATABASE_PATH)),
            "Images Directory": os.path.exists("data/images"),
        }
        
        for check, status in env_checks.items():
            if status:
                st.success(f"✅ {check}: OK")
            else:
                st.error(f"❌ {check}: Not configured")
        
        # Actions
        st.subheader("🔧 Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Cache"):
                st.cache_data.clear()
                st.success("Cache cleared!")
        
        with col2:
            if st.button("📊 Refresh Stats"):
                st.rerun()
        
        with col3:
            if st.button("🔄 Reset Database"):
                if st.checkbox("Confirm reset (this will delete all data)"):
                    try:
                        db_manager = DatabaseManager()
                        # This would need implementation
                        st.warning("Reset functionality would go here")
                    except Exception as e:
                        st.error(f"Error resetting database: {e}")

    def main():
        """Main application function."""
        # Display header
        display_header()
        
        # Display sidebar and get selected page
        page = display_sidebar()
        
        # Route to appropriate page
        if page == "📄 Process New PDF":
            process_pdf_page()
        elif page == "📚 Browse Questions":
            browse_questions_page()
        elif page == "📈 Statistics":
            statistics_page()
        elif page == "🖼️ Image Gallery":
            image_gallery_page()
        elif page == "⚙️ Settings":
            settings_page()

    if __name__ == "__main__":
        # Validate settings before starting
        try:
            settings.validate_settings()
            print(f"✅ Starting {settings.APP_TITLE}...")
            print(f"🌐 Access the application at: http://localhost:{settings.APP_PORT}")
            
            # Run the Streamlit app
            main()
            
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("Please check your .env file and ensure all required settings are configured.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Application Error: {e}")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)