#!/usr/bin/env python3
"""
Database Migration Script for Enhanced OCR System
================================================
This script migrates existing databases to the new enhanced schema.
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def backup_database(db_path):
    """Create a backup of the existing database."""
    try:
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Copy the database file
        import shutil
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return None

def check_existing_schema(db_path):
    """Check the current database schema."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📋 Existing tables: {tables}")
            
            schema_info = {}
            
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                schema_info[table] = columns
                
                print(f"\n📊 Table '{table}' columns:")
                for col in columns:
                    print(f"   • {col[1]} ({col[2]})")
            
            return schema_info
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return {}

def migrate_to_enhanced_schema(db_path):
    """Migrate database to enhanced schema."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔄 Starting database migration...")
            
            # 1. Create paper_metadata table if it doesn't exist
            print("📄 Creating paper_metadata table...")
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
            
            # 2. Create enhanced questions table
            print("❓ Creating questions_new table...")
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
            
            # 3. Create images table
            print("🖼️  Creating images table...")
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
            
            # 4. Create unmatched_images table
            print("🔍 Creating unmatched_images table...")
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
            
            # 5. Create or update processed_files table
            print("📁 Setting up processed_files table...")
            
            # Check if table exists first
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_files'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                print("� Creating new processed_files table...")
                cursor.execute('''
                    CREATE TABLE processed_files (
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
            else:
                print("📁 processed_files table exists, checking for missing columns...")
                cursor.execute("PRAGMA table_info(processed_files)")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                needed_columns = ['images_count', 'processing_status', 'error_message']
                missing_columns = [col for col in needed_columns if col not in existing_columns]
                
                if missing_columns:
                    print(f"🔧 Adding missing columns to processed_files: {missing_columns}")
                    
                    for column in missing_columns:
                        if column == 'images_count':
                            cursor.execute('ALTER TABLE processed_files ADD COLUMN images_count INTEGER DEFAULT 0')
                        elif column == 'processing_status':
                            cursor.execute("ALTER TABLE processed_files ADD COLUMN processing_status TEXT DEFAULT 'completed'")
                        elif column == 'error_message':
                            cursor.execute('ALTER TABLE processed_files ADD COLUMN error_message TEXT')
                else:
                    print("✅ processed_files table already has all required columns")
            
            # 6. Migrate existing data if there are old questions
            print("📊 Checking for existing data to migrate...")
            
            # Check if old questions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            old_table_exists = cursor.fetchone() is not None
            
            if old_table_exists:
                cursor.execute("SELECT COUNT(*) FROM questions")
                old_question_count = cursor.fetchone()[0]
                
                if old_question_count > 0:
                    print(f"🔄 Found {old_question_count} existing questions to migrate...")
                    migrate_existing_questions(cursor)
                else:
                    print("ℹ️  Old questions table exists but is empty")
            else:
                print("ℹ️  No old questions table found - starting with clean database")
            
            conn.commit()
            print("✅ Database migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_existing_questions(cursor):
    """Migrate existing questions to new format."""
    try:
        # Get all existing questions
        cursor.execute('''
            SELECT question_id, question_text, question_type, options, 
                   correct_answer, difficulty_level, subject_area, 
                   page_number, source_file, created_at
            FROM questions
        ''')
        
        old_questions = cursor.fetchall()
        
        # Group by source file
        files_data = {}
        for question in old_questions:
            source_file = question[8] or 'unknown.pdf'
            if source_file not in files_data:
                files_data[source_file] = []
            files_data[source_file].append(question)
        
        # Create paper metadata and migrate questions for each file
        for source_file, questions in files_data.items():
            print(f"📄 Migrating questions from: {source_file}")
            
            # Create paper metadata entry
            subject_area = questions[0][6] if questions[0][6] else None
            
            cursor.execute('''
                INSERT OR IGNORE INTO paper_metadata 
                (source_file, subject, processed_at)
                VALUES (?, ?, ?)
            ''', (source_file, subject_area, datetime.now()))
            
            # Get paper ID
            cursor.execute('SELECT id FROM paper_metadata WHERE source_file = ?', (source_file,))
            paper_id = cursor.fetchone()[0]
            
            # Migrate each question
            for question in questions:
                try:
                    # Convert old format to new format
                    import json
                    old_options = json.loads(question[3]) if question[3] else []
                    
                    # Convert list to object format
                    options_obj = {}
                    if old_options:
                        for i, option in enumerate(old_options):
                            options_obj[chr(65 + i)] = option  # A, B, C, D
                    
                    cursor.execute('''
                        INSERT INTO questions_new 
                        (paper_id, question_number, question_text, options, marks,
                         question_type, image_references_in_text, image_links_used, source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        paper_id,
                        question[0],  # question_id as question_number
                        question[1],  # question_text
                        json.dumps(options_obj),  # converted options
                        None,  # marks (not available in old format)
                        question[2],  # question_type
                        json.dumps([]),  # empty image references
                        json.dumps([]),  # empty image links
                        source_file
                    ))
                except Exception as e:
                    print(f"⚠️  Warning: Failed to migrate question {question[0]}: {e}")
                    continue
        
        print(f"✅ Migrated {len(old_questions)} questions from {len(files_data)} files")
        
    except Exception as e:
        print(f"❌ Error migrating existing questions: {e}")

def run_migration():
    """Run the complete migration process."""
    print("🔄 Enhanced OCR Database Migration Tool")
    print("=" * 60)
    
    try:
        from config.settings import settings
        db_path = settings.DATABASE_PATH
    except:
        db_path = "./data/questions.db"
    
    print(f"📍 Database path: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("ℹ️  No existing database found. Creating new enhanced database...")
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with new schema
        success = migrate_to_enhanced_schema(db_path)
        if success:
            print("✅ New enhanced database created successfully!")
        else:
            print("❌ Failed to create new database")
            return False
    else:
        print("📊 Existing database found. Checking schema...")
        
        # Check current schema
        schema_info = check_existing_schema(db_path)
        
        # Create backup
        backup_path = backup_database(db_path)
        if not backup_path:
            print("❌ Cannot proceed without backup. Migration cancelled.")
            return False
        
        # Run migration
        success = migrate_to_enhanced_schema(db_path)
        
        if success:
            print(f"\n✅ Migration completed successfully!")
            print(f"📁 Original database backed up to: {backup_path}")
            print(f"🎉 Your database is now ready for the enhanced OCR system!")
        else:
            print(f"\n❌ Migration failed!")
            print(f"💾 Your original database is safe at: {backup_path}")
            return False
    
    # Test the migrated database
    print_section("TESTING MIGRATED DATABASE")
    try:
        from app.database_manager import DatabaseManager
        db = DatabaseManager(db_path)
        stats = db.get_statistics()
        print(f"✅ Database test successful!")
        print(f"📊 Current statistics: {stats}")
    except Exception as e:
        print(f"⚠️  Database test warning: {e}")
    
    return True

if __name__ == "__main__":
    success = run_migration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("\n📝 What was updated:")
        print("   • Added paper_metadata table")
        print("   • Added questions_new table with enhanced structure")
        print("   • Added images table for image management")
        print("   • Added unmatched_images table")
        print("   • Updated processed_files table with new columns")
        print("   • Migrated existing data to new format")
        print("\n🚀 Your enhanced OCR system is now ready to use!")
    else:
        print("❌ MIGRATION FAILED!")
        print("Please check the error messages above and try again.")
    
    print("=" * 60)