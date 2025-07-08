#!/usr/bin/env python3
"""
Database Reader Script for PDF Question Parser

This script helps you read and explore the SQLite database containing parsed questions.
Usage:
    python3 read_database.py [options]
"""

import sqlite3
import json
import sys
import csv
from pathlib import Path
from datetime import datetime

# Default database path
DEFAULT_DB_PATH = "./data/questions.db"

class DatabaseReader:
    """Read and explore the questions database."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """Initialize database reader."""
        self.db_path = db_path
        if not Path(db_path).exists():
            print(f"❌ Database file not found: {db_path}")
            print("Make sure you've processed some PDFs first!")
            sys.exit(1)
    
    def show_database_info(self):
        """Show basic database information."""
        print("📊 DATABASE INFORMATION")
        print("=" * 50)
        print(f"Database file: {self.db_path}")
        print(f"File size: {Path(self.db_path).stat().st_size / 1024:.1f} KB")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Show tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables: {', '.join([table[0] for table in tables])}")
            
            # Show record counts
            cursor.execute("SELECT COUNT(*) FROM questions")
            questions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processed_files")
            files_count = cursor.fetchone()[0]
            
            print(f"Total questions: {questions_count}")
            print(f"Processed files: {files_count}")
    
    def show_table_schema(self):
        """Show database table schemas."""
        print("\n🏗️  DATABASE SCHEMA")
        print("=" * 50)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Questions table schema
            print("\n📋 QUESTIONS TABLE:")
            cursor.execute("PRAGMA table_info(questions)")
            columns = cursor.fetchall()
            for col in columns:
                col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                pk_indicator = " (PRIMARY KEY)" if pk else ""
                null_indicator = " NOT NULL" if not_null else ""
                default_indicator = f" DEFAULT {default}" if default else ""
                print(f"  • {col_name}: {col_type}{pk_indicator}{null_indicator}{default_indicator}")
            
            # Processed files table schema
            print("\n📁 PROCESSED_FILES TABLE:")
            cursor.execute("PRAGMA table_info(processed_files)")
            columns = cursor.fetchall()
            for col in columns:
                col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                pk_indicator = " (PRIMARY KEY)" if pk else ""
                null_indicator = " NOT NULL" if not_null else ""
                default_indicator = f" DEFAULT {default}" if default else ""
                print(f"  • {col_name}: {col_type}{pk_indicator}{null_indicator}{default_indicator}")
    
    def show_sample_data(self, limit: int = 3):
        """Show sample data from the database."""
        print(f"\n📝 SAMPLE DATA (showing {limit} records)")
        print("=" * 50)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT id, question_id, question_text, question_type, options, 
                       correct_answer, difficulty_level, subject_area, 
                       source_file, created_at
                FROM questions 
                ORDER BY created_at DESC 
                LIMIT {limit}
            """)
            
            questions = cursor.fetchall()
            
            for i, q in enumerate(questions, 1):
                print(f"\n--- Question {i} ---")
                print(f"ID: {q[0]}")
                print(f"Question ID: {q[1]}")
                print(f"Text: {q[2][:100]}..." if len(q[2]) > 100 else f"Text: {q[2]}")
                print(f"Type: {q[3]}")
                
                # Parse options from JSON
                try:
                    options = json.loads(q[4]) if q[4] else []
                    if options:
                        print("Options:")
                        for idx, option in enumerate(options, 1):
                            print(f"  {idx}. {option}")
                except json.JSONDecodeError:
                    print(f"Options: {q[4]}")
                
                print(f"Correct Answer: {q[5]}")
                print(f"Difficulty: {q[6]}")
                print(f"Subject: {q[7]}")
                print(f"Source File: {q[8]}")
                print(f"Created: {q[9]}")
    
    def export_to_json(self, output_file: str = "questions_export.json"):
        """Export all questions to JSON file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, question_id, question_text, question_type, options,
                       correct_answer, difficulty_level, subject_area, 
                       page_number, source_file, created_at
                FROM questions ORDER BY created_at DESC
            """)
            
            questions = []
            for row in cursor.fetchall():
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
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(questions)} questions to {output_file}")
    
    def export_to_csv(self, output_file: str = "questions_export.csv"):
        """Export all questions to CSV file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, question_id, question_text, question_type, options,
                       correct_answer, difficulty_level, subject_area, 
                       page_number, source_file, created_at
                FROM questions ORDER BY created_at DESC
            """)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'ID', 'Question_ID', 'Question_Text', 'Question_Type', 
                    'Options', 'Correct_Answer', 'Difficulty_Level', 
                    'Subject_Area', 'Page_Number', 'Source_File', 'Created_At'
                ])
                
                # Write data
                for row in cursor.fetchall():
                    writer.writerow(row)
            
            print(f"✅ Exported questions to {output_file}")
    
    def search_questions(self, search_term: str):
        """Search questions by text."""
        print(f"\n🔍 SEARCH RESULTS for '{search_term}'")
        print("=" * 50)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, question_text, subject_area, source_file
                FROM questions 
                WHERE question_text LIKE ? OR subject_area LIKE ?
                ORDER BY created_at DESC
            """, (f'%{search_term}%', f'%{search_term}%'))
            
            results = cursor.fetchall()
            
            if results:
                for i, (qid, text, subject, source) in enumerate(results, 1):
                    print(f"\n{i}. ID: {qid}")
                    print(f"   Subject: {subject}")
                    print(f"   Source: {source}")
                    print(f"   Text: {text[:150]}..." if len(text) > 150 else f"   Text: {text}")
            else:
                print("No questions found matching your search.")
    
    def show_statistics(self):
        """Show database statistics."""
        print("\n📈 STATISTICS")
        print("=" * 50)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Questions by type
            cursor.execute("""
                SELECT question_type, COUNT(*) 
                FROM questions 
                GROUP BY question_type 
                ORDER BY COUNT(*) DESC
            """)
            types_stats = cursor.fetchall()
            
            print("\nQuestions by Type:")
            for qtype, count in types_stats:
                print(f"  • {qtype}: {count}")
            
            # Questions by subject
            cursor.execute("""
                SELECT subject_area, COUNT(*) 
                FROM questions 
                GROUP BY subject_area 
                ORDER BY COUNT(*) DESC
            """)
            subject_stats = cursor.fetchall()
            
            print("\nQuestions by Subject:")
            for subject, count in subject_stats:
                print(f"  • {subject}: {count}")
            
            # Questions by difficulty
            cursor.execute("""
                SELECT difficulty_level, COUNT(*) 
                FROM questions 
                GROUP BY difficulty_level 
                ORDER BY COUNT(*) DESC
            """)
            difficulty_stats = cursor.fetchall()
            
            print("\nQuestions by Difficulty:")
            for difficulty, count in difficulty_stats:
                print(f"  • {difficulty}: {count}")
            
            # Processed files
            cursor.execute("""
                SELECT filename, questions_count, processed_at
                FROM processed_files 
                ORDER BY processed_at DESC
            """)
            files = cursor.fetchall()
            
            print("\nProcessed Files:")
            for filename, count, processed_at in files:
                print(f"  • {filename}: {count} questions ({processed_at})")

def main():
    """Main function with command line interface."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            print("\nOptions:")
            print("  -h, --help     Show this help message")
            print("  info           Show database information")
            print("  schema         Show table schemas")
            print("  sample         Show sample data")
            print("  stats          Show statistics")
            print("  export-json    Export all questions to JSON")
            print("  export-csv     Export all questions to CSV")
            print("  search <term>  Search questions")
            print("\nExamples:")
            print("  python3 read_database.py info")
            print("  python3 read_database.py export-json")
            print("  python3 read_database.py search 'diagram'")
            return
    
    # Initialize reader
    reader = DatabaseReader()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'info':
            reader.show_database_info()
        elif command == 'schema':
            reader.show_table_schema()
        elif command == 'sample':
            reader.show_sample_data()
        elif command == 'stats':
            reader.show_statistics()
        elif command == 'export-json':
            output_file = sys.argv[2] if len(sys.argv) > 2 else "questions_export.json"
            reader.export_to_json(output_file)
        elif command == 'export-csv':
            output_file = sys.argv[2] if len(sys.argv) > 2 else "questions_export.csv"
            reader.export_to_csv(output_file)
        elif command == 'search':
            if len(sys.argv) > 2:
                search_term = ' '.join(sys.argv[2:])
                reader.search_questions(search_term)
            else:
                print("Please provide a search term")
        else:
            print(f"Unknown command: {command}")
            print("Use -h or --help for usage information")
    else:
        # Default: show all information
        reader.show_database_info()
        reader.show_table_schema()
        reader.show_sample_data()
        reader.show_statistics()

if __name__ == "__main__":
    main()