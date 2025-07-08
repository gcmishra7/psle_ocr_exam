import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

class SimpleDatabaseManager:
    """Dependency-free database manager for the enhanced OCR system."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with database path."""
        self.db_path = db_path or "./data/questions.db"
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create paper_metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL UNIQUE,
                    subject TEXT,
                    school_name TEXT,
                    booklet_type TEXT,
                    total_marks TEXT,
                    time_limit TEXT,
                    general_instructions TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create enhanced questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER,
                    question_number TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    options TEXT,
                    marks TEXT,
                    question_type TEXT,
                    image_references_in_text TEXT,
                    image_links_used TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES paper_metadata (id)
                )
            ''')
            
            # Create images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_filename TEXT,
                    stored_filename TEXT UNIQUE,
                    relative_path TEXT,
                    full_path TEXT,
                    source_file TEXT,
                    page_number INTEGER,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create unmatched_images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unmatched_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER,
                    image_path TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES paper_metadata (id)
                )
            ''')
            
            # Create processed_files table with all required columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    file_hash TEXT,
                    questions_count INTEGER DEFAULT 0,
                    images_count INTEGER DEFAULT 0,
                    processing_status TEXT DEFAULT 'completed',
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            ''')
            
            # Migrate existing tables to add missing columns
            self._migrate_database_schema(cursor)
            
            conn.commit()
    
    def _migrate_database_schema(self, cursor):
        """Migrate existing database schema to add missing columns."""
        try:
            print("🔄 Checking database schema and applying migrations...")
            
            # Check if processed_files table exists and has the correct columns
            cursor.execute("PRAGMA table_info(processed_files)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = ['images_count', 'processing_status', 'error_message']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"🔧 Adding missing columns to processed_files: {missing_columns}")
                
                # Add missing columns one by one
                for column in missing_columns:
                    if column == 'images_count':
                        cursor.execute("ALTER TABLE processed_files ADD COLUMN images_count INTEGER DEFAULT 0")
                        print("✅ Added images_count column")
                    elif column == 'processing_status':
                        cursor.execute("ALTER TABLE processed_files ADD COLUMN processing_status TEXT DEFAULT 'completed'")
                        print("✅ Added processing_status column")
                    elif column == 'error_message':
                        cursor.execute("ALTER TABLE processed_files ADD COLUMN error_message TEXT")
                        print("✅ Added error_message column")
            else:
                print("✅ Database schema is up to date")
                
        except Exception as e:
            print(f"⚠️  Database migration error (non-critical): {e}")
            # Continue anyway - the system can still work with basic functionality
    
    def save_enhanced_paper_data(self, paper_data: Dict, source_file: str, image_mappings: Optional[Dict] = None) -> bool:
        """
        Save parsed paper data with enhanced structure.
        
        Args:
            paper_data: Parsed paper data with metadata and questions
            source_file: Name of the source PDF file
            image_mappings: Dictionary mapping image references to stored file paths
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract metadata
                metadata = paper_data.get('metadata', {})
                questions = paper_data.get('questions', [])
                unmatched_images = paper_data.get('unmatched_image_links', [])
                
                # Insert paper metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO paper_metadata 
                    (source_file, subject, school_name, booklet_type, total_marks, 
                     time_limit, general_instructions, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    source_file,
                    metadata.get('subject'),
                    metadata.get('school_name'),
                    metadata.get('booklet_type'),
                    metadata.get('total_marks'),
                    metadata.get('time_limit'),
                    metadata.get('general_instructions'),
                    datetime.now().isoformat()  # Use ISO format to avoid deprecation warning
                ))
                
                # Get the paper ID
                paper_id = cursor.lastrowid
                
                # Insert questions
                for question in questions:
                    # Convert options object to JSON string
                    options_json = json.dumps(question.get('options', {}))
                    
                    # Convert image arrays to JSON strings
                    image_refs_json = json.dumps(question.get('image_references_in_text', []))
                    
                    # Map image references to actual stored paths
                    image_links = question.get('image_links_used', [])
                    if image_mappings is not None:
                        # Replace original URLs with stored file paths
                        mapped_links = []
                        for link in image_links:
                            if link in image_mappings:
                                mapped_links.append(image_mappings[link])
                            else:
                                mapped_links.append(link)
                        image_links = mapped_links
                    
                    image_links_json = json.dumps(image_links)
                    
                    cursor.execute('''
                        INSERT INTO questions_new 
                        (paper_id, question_number, question_text, options, marks,
                         question_type, image_references_in_text, image_links_used, source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        paper_id,
                        question.get('question_number', ''),
                        question.get('question_text', ''),
                        options_json,
                        question.get('marks'),
                        question.get('question_type', ''),
                        image_refs_json,
                        image_links_json,
                        source_file
                    ))
                
                # Insert unmatched images
                for image_path in unmatched_images:
                    cursor.execute('''
                        INSERT INTO unmatched_images (paper_id, image_path, reason)
                        VALUES (?, ?, ?)
                    ''', (paper_id, image_path, 'No matching question reference found'))
                
                # **THE CRITICAL PART** - Update processed files with all required columns
                print(f"💾 Saving to processed_files: {source_file}")
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_files 
                    (filename, questions_count, images_count, processing_status, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    source_file, 
                    len(questions), 
                    len(image_mappings) if image_mappings is not None else 0, 
                    'completed', 
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                print(f"✅ Successfully saved paper data for: {source_file}")
                return True
                
        except Exception as e:
            print(f"❌ Error saving enhanced paper data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_image_info(self, image_info: Dict) -> bool:
        """Save image information to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO images 
                    (original_filename, stored_filename, relative_path, full_path,
                     source_file, page_number, width, height, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_info.get('original_filename'),
                    image_info.get('stored_filename'),
                    image_info.get('relative_path'),
                    image_info.get('full_path'),
                    image_info.get('source_file'),
                    image_info.get('page_number'),
                    image_info.get('width'),
                    image_info.get('height'),
                    image_info.get('file_size')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Error saving image info: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get enhanced database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total papers
                cursor.execute('SELECT COUNT(*) FROM paper_metadata')
                total_papers = cursor.fetchone()[0]
                
                # Total questions
                cursor.execute('SELECT COUNT(*) FROM questions_new')
                total_questions = cursor.fetchone()[0]
                
                # Total images
                cursor.execute('SELECT COUNT(*) FROM images')
                total_images = cursor.fetchone()[0]
                
                return {
                    'total_papers': total_papers,
                    'total_questions': total_questions,
                    'total_images': total_images
                }
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {
                'total_papers': 0,
                'total_questions': 0,
                'total_images': 0
            }