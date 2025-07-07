import sqlite3
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from config.settings import settings

class DatabaseManager:
    """Handles database operations for storing parsed questions."""
    
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
            
            # Create questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT,
                    options TEXT,  -- JSON array of options
                    correct_answer TEXT,
                    difficulty_level TEXT,
                    subject_area TEXT,
                    page_number TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create files table to track processed files
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    file_hash TEXT,
                    questions_count INTEGER DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed'
                )
            ''')
            
            conn.commit()
    
    def save_questions(self, questions: List[Dict], source_file: str) -> bool:
        """
        Save parsed questions to database.
        
        Args:
            questions: List of question dictionaries
            source_file: Name of the source PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for question in questions:
                    # Convert options list to JSON string
                    options_json = json.dumps(question.get('options', []))
                    
                    cursor.execute('''
                        INSERT INTO questions (
                            question_id, question_text, question_type, options,
                            correct_answer, difficulty_level, subject_area, 
                            page_number, source_file
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        question.get('question_id', ''),
                        question.get('question_text', ''),
                        question.get('question_type', ''),
                        options_json,
                        question.get('correct_answer', ''),
                        question.get('difficulty_level', ''),
                        question.get('subject_area', ''),
                        question.get('page_number', ''),
                        source_file
                    ))
                
                # Update processed files table
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_files 
                    (filename, questions_count, processed_at, status)
                    VALUES (?, ?, ?, ?)
                ''', (source_file, len(questions), datetime.now(), 'completed'))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving questions to database: {e}")
            return False
    
    def get_all_questions(self) -> List[Dict]:
        """
        Retrieve all questions from database.
        
        Returns:
            List of question dictionaries
        """
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
                    options = json.loads(row[4]) if row[4] else []
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
            print(f"Error retrieving questions: {e}")
            return []
    
    def get_questions_by_file(self, source_file: str) -> List[Dict]:
        """
        Retrieve questions from a specific source file.
        
        Args:
            source_file: Name of the source file
            
        Returns:
            List of question dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question_id, question_text, question_type, options,
                           correct_answer, difficulty_level, subject_area, 
                           page_number, source_file, created_at
                    FROM questions WHERE source_file = ? ORDER BY question_id
                ''', (source_file,))
                
                rows = cursor.fetchall()
                questions = []
                
                for row in rows:
                    options = json.loads(row[4]) if row[4] else []
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
            print(f"Error retrieving questions by file: {e}")
            return []
    
    def get_processed_files(self) -> List[Dict]:
        """
        Get list of processed files.
        
        Returns:
            List of processed file information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT filename, questions_count, processed_at, status
                    FROM processed_files ORDER BY processed_at DESC
                ''')
                
                rows = cursor.fetchall()
                files = []
                
                for row in rows:
                    file_info = {
                        'filename': row[0],
                        'questions_count': row[1],
                        'processed_at': row[2],
                        'status': row[3]
                    }
                    files.append(file_info)
                
                return files
                
        except Exception as e:
            print(f"Error retrieving processed files: {e}")
            return []
    
    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question by its database ID.
        
        Args:
            question_id: Database ID of the question
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False
    
    def search_questions(self, search_term: str) -> List[Dict]:
        """
        Search questions by text content.
        
        Args:
            search_term: Term to search for in question text
            
        Returns:
            List of matching questions
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question_id, question_text, question_type, options,
                           correct_answer, difficulty_level, subject_area, 
                           page_number, source_file, created_at
                    FROM questions 
                    WHERE question_text LIKE ? OR subject_area LIKE ?
                    ORDER BY created_at DESC
                ''', (f'%{search_term}%', f'%{search_term}%'))
                
                rows = cursor.fetchall()
                questions = []
                
                for row in rows:
                    options = json.loads(row[4]) if row[4] else []
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
            print(f"Error searching questions: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total questions
                cursor.execute('SELECT COUNT(*) FROM questions')
                total_questions = cursor.fetchone()[0]
                
                # Questions by type
                cursor.execute('''
                    SELECT question_type, COUNT(*) 
                    FROM questions 
                    GROUP BY question_type
                ''')
                types_count = dict(cursor.fetchall())
                
                # Questions by difficulty
                cursor.execute('''
                    SELECT difficulty_level, COUNT(*) 
                    FROM questions 
                    GROUP BY difficulty_level
                ''')
                difficulty_count = dict(cursor.fetchall())
                
                # Total files processed
                cursor.execute('SELECT COUNT(*) FROM processed_files')
                total_files = cursor.fetchone()[0]
                
                return {
                    'total_questions': total_questions,
                    'total_files': total_files,
                    'questions_by_type': types_count,
                    'questions_by_difficulty': difficulty_count
                }
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}