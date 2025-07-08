#!/usr/bin/env python3
"""
Manual Database Migration Script
Fix existing database schema issues by adding missing columns
"""

import sqlite3
import os
from pathlib import Path

def migrate_database(db_path="./data/questions.db"):
    """
    Manually migrate database to fix schema issues.
    
    Args:
        db_path: Path to the database file
    """
    print("🔄 Starting manual database migration...")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("📋 Checking current database schema...")
            
            # Check processed_files table structure
            try:
                cursor.execute("PRAGMA table_info(processed_files)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"📊 Current processed_files columns: {columns}")
                
                # Required columns for the enhanced system
                required_columns = {
                    'images_count': 'INTEGER DEFAULT 0',
                    'processing_status': 'TEXT DEFAULT "completed"',
                    'error_message': 'TEXT'
                }
                
                # Find missing columns
                missing_columns = [col for col in required_columns.keys() if col not in columns]
                
                if missing_columns:
                    print(f"🔧 Missing columns found: {missing_columns}")
                    
                    # Add missing columns
                    for column in missing_columns:
                        column_def = required_columns[column]
                        sql = f"ALTER TABLE processed_files ADD COLUMN {column} {column_def}"
                        
                        try:
                            cursor.execute(sql)
                            print(f"✅ Added column: {column}")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" in str(e).lower():
                                print(f"ℹ️  Column {column} already exists")
                            else:
                                print(f"❌ Error adding {column}: {e}")
                                return False
                else:
                    print("✅ All required columns already exist!")
                
                # Verify the final schema
                cursor.execute("PRAGMA table_info(processed_files)")
                final_columns = [row[1] for row in cursor.fetchall()]
                print(f"📊 Final processed_files columns: {final_columns}")
                
                conn.commit()
                print("✅ Database migration completed successfully!")
                
                # Test insert to verify schema works
                test_insert_query = '''
                    INSERT OR REPLACE INTO processed_files 
                    (filename, questions_count, images_count, processing_status, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                '''
                
                cursor.execute(test_insert_query, (
                    'test_migration.pdf', 
                    5, 
                    3, 
                    'completed', 
                    '2024-01-01 12:00:00'
                ))
                
                # Remove test entry
                cursor.execute("DELETE FROM processed_files WHERE filename = 'test_migration.pdf'")
                conn.commit()
                
                print("✅ Database schema test passed!")
                return True
                
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    print("⚠️  processed_files table doesn't exist. This might be a fresh database.")
                    print("🔄 Creating processed_files table with correct schema...")
                    
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
                    
                    conn.commit()
                    print("✅ Created processed_files table with correct schema!")
                    return True
                else:
                    print(f"❌ Database error: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def backup_database(db_path="./data/questions.db"):
    """Create a backup of the database before migration."""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"💾 Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
            return None
    return None

def main():
    """Main migration script."""
    print("🔧 Manual Database Migration for Enhanced OCR System")
    print("=" * 60)
    
    db_path = "./data/questions.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("ℹ️  The database will be created automatically when you process your first PDF.")
        return
    
    # Create backup
    backup_path = backup_database(db_path)
    if backup_path:
        print(f"✅ Backup created at: {backup_path}")
    
    # Run migration
    success = migrate_database(db_path)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("✅ Your database is now ready for the enhanced OCR system")
        print("🚀 You can now process PDFs without database errors")
        if backup_path:
            print(f"💾 Backup available at: {backup_path}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED!")
        print("🔧 Please check the error messages above")
        if backup_path:
            print(f"🔄 You can restore from backup: {backup_path}")
        print("=" * 60)

if __name__ == "__main__":
    main()