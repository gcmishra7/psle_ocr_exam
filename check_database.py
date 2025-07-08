#!/usr/bin/env python3
"""
Database Schema Checker
Check the current database schema to debug the images_count column issue.
"""

import sqlite3
import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def check_database_schema():
    """Check the current database schema."""
    try:
        from config.settings import settings
        db_path = settings.DATABASE_PATH
    except:
        db_path = "./data/questions.db"
    
    print(f"🔍 Checking database: {db_path}")
    print("=" * 60)
    
    if not Path(db_path).exists():
        print("❌ Database file doesn't exist!")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📋 Tables found: {tables}")
            print()
            
            # Check each table's schema
            for table in tables:
                print(f"📊 Table '{table}':")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                print("   Columns:")
                for col in columns:
                    print(f"     • {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
                
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   Rows: {count}")
                print()
            
            # Specifically check processed_files table
            if 'processed_files' in tables:
                print("🔍 DETAILED CHECK: processed_files table")
                cursor.execute("PRAGMA table_info(processed_files)")
                columns = cursor.fetchall()
                
                column_names = [col[1] for col in columns]
                print(f"   Column names: {column_names}")
                
                required_columns = ['images_count', 'processing_status', 'error_message']
                missing = [col for col in required_columns if col not in column_names]
                
                if missing:
                    print(f"   ❌ Missing columns: {missing}")
                    return False
                else:
                    print(f"   ✅ All required columns present")
                    return True
            else:
                print("❌ processed_files table not found!")
                return False
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_manager():
    """Test if the DatabaseManager can connect properly."""
    try:
        print("\n🔧 Testing DatabaseManager connection...")
        from app.database_manager import DatabaseManager
        
        db = DatabaseManager()
        print("✅ DatabaseManager initialized successfully")
        
        # Try to get statistics
        stats = db.get_statistics()
        print(f"📊 Statistics retrieved: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Database Schema Checker")
    print("=" * 60)
    
    schema_ok = check_database_schema()
    db_manager_ok = test_database_manager()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    if schema_ok:
        print("✅ Database schema looks correct")
    else:
        print("❌ Database schema has issues")
    
    if db_manager_ok:
        print("✅ DatabaseManager works correctly")
    else:
        print("❌ DatabaseManager has issues")
    
    if schema_ok and db_manager_ok:
        print("\n🎉 Database should be working correctly!")
        print("The error might be elsewhere in the code.")
    else:
        print("\n🔧 Database needs to be fixed.")
        print("Run: python3 migrate_database.py")