#!/usr/bin/env python3
"""
Test script to verify dependency-free OCR processing
"""

import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def test_simple_database_manager():
    """Test the simple database manager directly."""
    print("🔧 Testing SimpleDatabaseManager...")
    
    try:
        from app.simple_database_manager import SimpleDatabaseManager
        
        # Initialize
        db = SimpleDatabaseManager("./data/test_questions.db")
        print("✅ SimpleDatabaseManager initialized")
        
        # Test data
        test_data = {
            'metadata': {
                'subject': 'Test Subject',
                'school_name': 'Test School',
                'total_marks': '100'
            },
            'questions': [
                {
                    'question_number': '1',
                    'question_text': 'What is 2+2?',
                    'options': {'A': '3', 'B': '4', 'C': '5'},
                    'marks': '2',
                    'question_type': 'MCQ',
                    'image_references_in_text': [],
                    'image_links_used': []
                }
            ],
            'unmatched_image_links': []
        }
        
        # Test save
        success = db.save_enhanced_paper_data(test_data, "test.pdf", {})
        
        if success:
            print("✅ Data saved successfully")
            
            # Test statistics
            stats = db.get_statistics()
            print(f"📊 Statistics: {stats}")
            
            # Clean up
            import os
            if os.path.exists("./data/test_questions.db"):
                os.remove("./data/test_questions.db")
                print("🧹 Test database cleaned up")
            
            return True
        else:
            print("❌ Data save failed")
            return False
            
    except Exception as e:
        print(f"❌ SimpleDatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_ocr_processor():
    """Test OCR processor with fallback components."""
    print("\n🔧 Testing OCR processor with dependency fallbacks...")
    
    try:
        # This should trigger the fallback mechanism if dependencies are missing
        from app.ocr_processor import OCRProcessor
        
        processor = OCRProcessor()
        print("✅ OCRProcessor initialized (possibly with fallbacks)")
        
        # Check which components are available
        if processor.db_manager is not None:
            print("✅ Database manager available")
        else:
            print("❌ Database manager not available")
            
        if processor.llm_parser is not None:
            print("✅ LLM parser available")
        else:
            print("⚠️  LLM parser not available (fallback mode)")
            
        if processor.image_processor is not None:
            print("✅ Image processor available")
        else:
            print("⚠️  Image processor not available (fallback mode)")
        
        # Test basic parsing structure
        test_text = "This is a test question. What is the answer?"
        basic_data = processor.create_basic_parsed_data(test_text, "test.pdf")
        
        if basic_data and 'questions' in basic_data:
            print("✅ Basic parsed data creation works")
            print(f"📊 Created {len(basic_data['questions'])} questions")
            return True
        else:
            print("❌ Basic parsed data creation failed")
            return False
            
    except Exception as e:
        print(f"❌ OCR processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_save_operation():
    """Test the exact database save operation that was failing."""
    print("\n🔧 Testing exact database save operation...")
    
    try:
        from app.simple_database_manager import SimpleDatabaseManager
        
        db = SimpleDatabaseManager()
        
        # Simulate the exact data structure from the error
        test_paper_data = {
            'metadata': {'subject': 'Science'},
            'questions': [{'question_number': '1', 'question_text': 'Test', 'options': {}, 'marks': '1', 'question_type': 'MCQ', 'image_references_in_text': [], 'image_links_used': []}],
            'unmatched_image_links': []
        }
        
        image_mappings = {
            '/data/images/P6_Science_2024_WA1_acsjunior/P6_Science_2024_WA1_acsjunior_page_3_20250708_160204.png': '/data/images/P6_Science_2024_WA1_acsjunior/P6_Science_2024_WA1_acsjunior_page_3_20250708_160204.png'
        }
        
        print("💾 Testing save_enhanced_paper_data...")
        success = db.save_enhanced_paper_data(
            test_paper_data, 
            "P6_Science_2024_WA1_acsjunior.pdf", 
            image_mappings
        )
        
        if success:
            print("✅ Enhanced paper data save successful!")
            return True
        else:
            print("❌ Enhanced paper data save failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database save test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Dependency Fix Test Suite")
    print("=" * 60)
    
    tests = [
        ("Simple Database Manager", test_simple_database_manager),
        ("Fallback OCR Processor", test_fallback_ocr_processor),
        ("Database Save Operation", test_database_save_operation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The dependency fix should work.")
        print("🚀 Try uploading your PDF again - it should work now!")
    else:
        print("\n🔧 Some tests failed. Check the errors above.")
    
    print("=" * 60)