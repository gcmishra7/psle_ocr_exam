#!/usr/bin/env python3
"""
Direct Database Connection Fix
==============================
This script directly tests database operations to fix the connection issue.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def test_direct_database_operations():
    """Test database operations directly without dependencies."""
    
    db_path = "./data/questions.db"
    print(f"🔍 Testing database operations directly: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Test 1: Verify schema
            print("\n📊 Schema verification:")
            cursor.execute("PRAGMA table_info(processed_files)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"   Columns: {column_names}")
            
            required = ['images_count', 'processing_status', 'error_message']
            missing = [col for col in required if col not in column_names]
            
            if missing:
                print(f"   ❌ Missing: {missing}")
                return False
            else:
                print(f"   ✅ All required columns present")
            
            # Test 2: Try inserting test data (exactly like the app does)
            print("\n💾 Testing data insertion:")
            
            test_data = {
                'metadata': {'subject': 'Test Subject'},
                'questions': [
                    {
                        'question_number': '1',
                        'question_text': 'Test question',
                        'options': {'A': 'Option A', 'B': 'Option B'},
                        'marks': '2',
                        'question_type': 'MCQ',
                        'image_references_in_text': [],
                        'image_links_used': []
                    }
                ],
                'unmatched_image_links': []
            }
            
            source_file = "test_file.pdf"
            image_mappings = {}
            
            # Simulate the exact operations from save_enhanced_paper_data
            
            # Step 1: Insert paper metadata
            cursor.execute('''
                INSERT OR REPLACE INTO paper_metadata 
                (source_file, subject, school_name, booklet_type, total_marks, 
                 time_limit, general_instructions, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_file,
                test_data['metadata'].get('subject'),
                test_data['metadata'].get('school_name'),
                test_data['metadata'].get('booklet_type'),
                test_data['metadata'].get('total_marks'),
                test_data['metadata'].get('time_limit'),
                test_data['metadata'].get('general_instructions'),
                datetime.now()
            ))
            
            paper_id = cursor.lastrowid
            print(f"   ✅ Paper metadata inserted, ID: {paper_id}")
            
            # Step 2: Insert questions
            for question in test_data['questions']:
                options_json = json.dumps(question.get('options', {}))
                image_refs_json = json.dumps(question.get('image_references_in_text', []))
                image_links_json = json.dumps(question.get('image_links_used', []))
                
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
            
            print(f"   ✅ Questions inserted: {len(test_data['questions'])}")
            
            # Step 3: THE CRITICAL TEST - Insert into processed_files
            print("\n🔥 CRITICAL TEST - processed_files insertion:")
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO processed_files 
                    (filename, questions_count, images_count, processing_status, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    source_file, 
                    len(test_data['questions']), 
                    len(image_mappings), 
                    'completed', 
                    datetime.now()
                ))
                
                print("   ✅ processed_files insertion SUCCESSFUL!")
                
                # Verify the insert
                cursor.execute('SELECT * FROM processed_files WHERE filename = ?', (source_file,))
                row = cursor.fetchone()
                if row:
                    print(f"   📊 Inserted data: {row}")
                else:
                    print("   ⚠️  No data found after insert")
                
            except Exception as e:
                print(f"   ❌ processed_files insertion FAILED: {e}")
                return False
            
            # Clean up test data
            cursor.execute('DELETE FROM processed_files WHERE filename = ?', (source_file,))
            cursor.execute('DELETE FROM questions_new WHERE source_file = ?', (source_file,))
            cursor.execute('DELETE FROM paper_metadata WHERE source_file = ?', (source_file,))
            
            conn.commit()
            print("\n🧹 Test data cleaned up")
            
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_file_paths():
    """Check if there are multiple database files."""
    
    print("\n🔍 Checking for multiple database files:")
    
    possible_paths = [
        "./data/questions.db",
        "./questions.db", 
        "/tmp/questions.db",
        "data/questions.db"
    ]
    
    existing_files = []
    
    for path in possible_paths:
        if Path(path).exists():
            existing_files.append(path)
            size = Path(path).stat().st_size
            print(f"   📁 Found: {path} ({size} bytes)")
    
    if len(existing_files) > 1:
        print(f"   ⚠️  Multiple database files found! This could cause confusion.")
    elif len(existing_files) == 1:
        print(f"   ✅ Single database file: {existing_files[0]}")
    else:
        print(f"   ❌ No database files found!")
    
    return existing_files

def create_simple_database_test():
    """Create a simplified database manager for testing."""
    
    print("\n🔧 Creating simple database manager test:")
    
    class SimpleDatabaseManager:
        def __init__(self, db_path="./data/questions.db"):
            self.db_path = db_path
        
        def save_enhanced_paper_data(self, paper_data, source_file, image_mappings=None):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Test the exact same operation that's failing
                    cursor.execute('''
                        INSERT OR REPLACE INTO processed_files 
                        (filename, questions_count, images_count, processing_status, processed_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        source_file, 
                        len(paper_data.get('questions', [])), 
                        len(image_mappings) if image_mappings else 0, 
                        'completed', 
                        datetime.now()
                    ))
                    
                    conn.commit()
                    return True
                    
            except Exception as e:
                print(f"   ❌ SimpleDatabaseManager failed: {e}")
                return False
    
    # Test the simple manager
    test_db = SimpleDatabaseManager()
    test_data = {'questions': [{'test': 'data'}]}
    
    success = test_db.save_enhanced_paper_data(test_data, "simple_test.pdf", {})
    
    if success:
        print("   ✅ SimpleDatabaseManager works!")
        
        # Clean up
        with sqlite3.connect("./data/questions.db") as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM processed_files WHERE filename = ?', ("simple_test.pdf",))
            conn.commit()
        
        return True
    else:
        print("   ❌ SimpleDatabaseManager failed!")
        return False

if __name__ == "__main__":
    print("🔧 Direct Database Connection Fix")
    print("=" * 60)
    
    # Check for multiple database files
    db_files = check_database_file_paths()
    
    # Test direct database operations
    direct_test_ok = test_direct_database_operations()
    
    # Test simple database manager
    simple_test_ok = create_simple_database_test()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    
    if direct_test_ok and simple_test_ok:
        print("✅ Database operations work correctly!")
        print("✅ The issue is likely in the application's import/dependency chain.")
        print("\n🔧 SOLUTION: The database is fine, but the app needs dependency fixes.")
        print("   The error suggests missing 'dotenv' package or similar import issues.")
    else:
        print("❌ Database operations are failing.")
        print("🔧 Need to investigate further.")
    
    print("=" * 60)