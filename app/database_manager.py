import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from config.settings import settings

class DatabaseManager:
    """Handles database operations for storing parsed questions with advanced metadata and image support."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with database path."""
        self.db_path = db_path or settings.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables if they don't exist."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create paper_metadata table for storing paper-level information
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
            
            # Create enhanced questions table with new structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER,
                    question_number TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    options TEXT,  -- JSON object with option keys and values
                    marks TEXT,
                    question_type TEXT,
                    image_references_in_text TEXT,  -- JSON array of image references
                    image_links_used TEXT,  -- JSON array of actual image URLs/paths
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES paper_metadata (id)
                )
            ''')
            
            # Create images table to track stored images
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
            
            # Create unmatched_images table for tracking unused images
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
            
            # Create legacy table if it doesn't exist (for backward compatibility)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT,
                    options TEXT,
                    correct_answer TEXT,
                    difficulty_level TEXT,
                    subject_area TEXT,
                    page_number TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create processed files table
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
            
            conn.commit()
    
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
                    datetime.now()
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
                
                                 # Update processed files
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_files 
                    (filename, questions_count, images_count, processing_status, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (source_file, len(questions), len(image_mappings) if image_mappings is not None else 0, 'completed', datetime.now()))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving enhanced paper data: {e}")
            return False
    
    def save_image_info(self, image_info: Dict) -> bool:
        """
        Save image information to database.
        
        Args:
            image_info: Dictionary with image metadata
            
        Returns:
            True if successful, False otherwise
        """
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
            print(f"Error saving image info: {e}")
            return False
    
    def get_paper_by_file(self, source_file: str) -> Optional[Dict]:
        """
        Get complete paper data including metadata and questions.
        
        Args:
            source_file: Name of the source file
            
        Returns:
            Complete paper data or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get paper metadata
                cursor.execute('''
                    SELECT id, subject, school_name, booklet_type, total_marks,
                           time_limit, general_instructions, processed_at
                    FROM paper_metadata WHERE source_file = ?
                ''', (source_file,))
                
                paper_row = cursor.fetchone()
                if not paper_row:
                    return None
                
                paper_id = paper_row[0]
                paper_metadata = {
                    'id': paper_id,
                    'subject': paper_row[1],
                    'school_name': paper_row[2],
                    'booklet_type': paper_row[3],
                    'total_marks': paper_row[4],
                    'time_limit': paper_row[5],
                    'general_instructions': paper_row[6],
                    'processed_at': paper_row[7]
                }
                
                # Get questions
                cursor.execute('''
                    SELECT question_number, question_text, options, marks,
                           question_type, image_references_in_text, image_links_used
                    FROM questions_new WHERE paper_id = ?
                    ORDER BY question_number
                ''', (paper_id,))
                
                questions = []
                for row in cursor.fetchall():
                    try:
                        options = json.loads(row[2]) if row[2] else {}
                        image_refs = json.loads(row[5]) if row[5] else []
                        image_links = json.loads(row[6]) if row[6] else []
                    except json.JSONDecodeError:
                        options = {}
                        image_refs = []
                        image_links = []
                    
                    question = {
                        'question_number': row[0],
                        'question_text': row[1],
                        'options': options,
                        'marks': row[3],
                        'question_type': row[4],
                        'image_references_in_text': image_refs,
                        'image_links_used': image_links
                    }
                    questions.append(question)
                
                return {
                    'metadata': paper_metadata,
                    'questions': questions,
                    'source_file': source_file
                }
                
        except Exception as e:
            print(f"Error retrieving paper data: {e}")
            return None
    
    def get_all_papers(self) -> List[Dict]:
        """Get all processed papers with basic information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT pm.source_file, pm.subject, pm.school_name, pm.processed_at,
                           COUNT(q.id) as question_count
                    FROM paper_metadata pm
                    LEFT JOIN questions_new q ON pm.id = q.paper_id
                    GROUP BY pm.id, pm.source_file, pm.subject, pm.school_name, pm.processed_at
                    ORDER BY pm.processed_at DESC
                ''')
                
                papers = []
                for row in cursor.fetchall():
                    paper = {
                        'source_file': row[0],
                        'subject': row[1],
                        'school_name': row[2],
                        'processed_at': row[3],
                        'question_count': row[4]
                    }
                    papers.append(paper)
                
                return papers
                
        except Exception as e:
            print(f"Error retrieving papers: {e}")
            return []
    
    def get_image_by_path(self, relative_path: str) -> Optional[Dict]:
        """Get image information by relative path."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT original_filename, stored_filename, relative_path, full_path,
                           source_file, page_number, width, height, file_size, created_at
                    FROM images WHERE relative_path = ?
                ''', (relative_path,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'original_filename': row[0],
                        'stored_filename': row[1],
                        'relative_path': row[2],
                        'full_path': row[3],
                        'source_file': row[4],
                        'page_number': row[5],
                        'width': row[6],
                        'height': row[7],
                        'file_size': row[8],
                        'created_at': row[9]
                    }
                return None
                
        except Exception as e:
            print(f"Error retrieving image: {e}")
            return None
    
    def search_papers(self, search_term: str) -> List[Dict]:
        """Search papers by subject, school name, or question content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT pm.source_file, pm.subject, pm.school_name, pm.processed_at
                    FROM paper_metadata pm
                    LEFT JOIN questions_new q ON pm.id = q.paper_id
                    WHERE pm.subject LIKE ? OR pm.school_name LIKE ? OR q.question_text LIKE ?
                    ORDER BY pm.processed_at DESC
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
                
                papers = []
                for row in cursor.fetchall():
                    paper = {
                        'source_file': row[0],
                        'subject': row[1],
                        'school_name': row[2],
                        'processed_at': row[3]
                    }
                    papers.append(paper)
                
                return papers
                
        except Exception as e:
            print(f"Error searching papers: {e}")
            return []
    
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
                
                # Questions by type
                cursor.execute('''
                    SELECT question_type, COUNT(*) 
                    FROM questions_new 
                    GROUP BY question_type
                    ORDER BY COUNT(*) DESC
                ''')
                question_types = dict(cursor.fetchall())
                
                # Papers by subject
                cursor.execute('''
                    SELECT subject, COUNT(*) 
                    FROM paper_metadata 
                    WHERE subject IS NOT NULL
                    GROUP BY subject
                    ORDER BY COUNT(*) DESC
                ''')
                subjects = dict(cursor.fetchall())
                
                return {
                    'total_papers': total_papers,
                    'total_questions': total_questions,
                    'total_images': total_images,
                    'question_types': question_types,
                    'subjects': subjects
                }
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    # Legacy methods for backward compatibility
    def get_all_questions(self) -> List[Dict]:
        """Legacy method - get questions from old format."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question_id, question_text, question_type, options,
                           correct_answer, difficulty_level, subject_area, 
                           page_number, source_file, created_at
                    FROM questions ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                questions = []
                
                for row in rows:
                    try:
                        options = json.loads(row[4]) if row[4] else []
                    except json.JSONDecodeError:
                        options = []
                    
                    question = {
                        'id': row[0],
                        'question_id': row[1],
                        'question_text': row[2],
                        'question_type': row[3],
                        'options': options,
                        'correct_answer': row[5],
                        'difficulty_level': row[6],
                        'subject_area': row[7],
                        'page_number': row[8],
                        'source_file': row[9],
                        'created_at': row[10]
                    }
                    questions.append(question)
                
                return questions
                
        except Exception as e:
            print(f"Error retrieving legacy questions: {e}")
            return []