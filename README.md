# 🎓 Enhanced OCR Question Paper Parser

A comprehensive Python application that transforms PDF question papers into structured data with advanced image support, metadata extraction, and intelligent question parsing using Google's Gemini LLM.

## ✨ Key Features

### 🚀 **Enhanced Processing Pipeline**
- **Image Extraction**: Automatically extracts and stores images from PDF pages
- **Advanced OCR**: Optimized text extraction with confidence scoring
- **Smart LLM Parsing**: Uses Google Gemini with sophisticated prompts for accurate question parsing
- **Metadata Detection**: Extracts paper metadata (subject, school, marks, time limit, instructions)
- **Image Reference Matching**: Intelligently links question text to extracted images

### 📊 **Advanced Database Schema**
- **Paper Metadata**: Complete paper information storage
- **Enhanced Questions**: Comprehensive question structure with image support
- **Image Management**: Full image metadata and storage tracking
- **Legacy Compatibility**: Backward compatibility with existing data

### 🖼️ **Image Support**
- **Automatic Extraction**: PDF pages converted to high-quality images
- **Smart Storage**: Organized folder structure by source file
- **Reference Matching**: Links image references in text to actual stored files
- **Web Display**: Images rendered in UI with proper paths

### 🎯 **Question Types Supported**
- Multiple Choice Questions (MCQ)
- Short Answer Questions
- Long Answer/Descriptive Questions
- Fill-in-the-Blanks
- True/False Questions
- Diagram-based Questions
- Passage-based Questions
- Assertion-Reason Questions
- Numerical Problems
- Definition Questions

### 🌐 **Modern Web Interface**
- **Multi-page Application**: Process, Browse, Statistics, Gallery, Settings
- **Real-time Processing**: Progress bars and status updates
- **Image Gallery**: View all extracted images with question context
- **Advanced Statistics**: Comprehensive analytics with charts
- **Responsive Design**: Modern UI with custom styling

## 🏗️ **System Architecture**

```
📁 Enhanced OCR Application
├── 🧠 app/
│   ├── ocr_processor.py      # Enhanced OCR with image extraction
│   ├── llm_parser.py         # Advanced Gemini LLM parsing
│   ├── database_manager.py   # Enhanced database operations
│   └── image_processor.py    # Image extraction and management
├── ⚙️ config/
│   └── settings.py           # Configuration management
├── 💾 data/
│   ├── questions.db          # Enhanced SQLite database
│   └── images/               # Organized image storage
│       └── [pdf_name]/       # Images per PDF file
├── 🌐 main.py               # Enhanced Streamlit application
└── 📚 requirements.txt       # Complete dependencies
```

## 🗄️ **Enhanced Database Schema**

### Paper Metadata Table
```sql
paper_metadata (
    id, source_file, subject, school_name, booklet_type,
    total_marks, time_limit, general_instructions,
    processed_at, updated_at
)
```

### Enhanced Questions Table
```sql
questions_new (
    id, paper_id, question_number, question_text,
    options (JSON), marks, question_type,
    image_references_in_text (JSON), image_links_used (JSON),
    source_file, created_at, updated_at
)
```

### Images Table
```sql
images (
    id, original_filename, stored_filename, relative_path,
    full_path, source_file, page_number, width, height,
    file_size, created_at
)
```

## 🚀 **Quick Start**

### 1. **Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd psle_ocr_exam

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. **System Dependencies**
```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils

# Check installation
tesseract --version
```

### 4. **Run Application**
```bash
# Start the enhanced application
python3 -m streamlit run main.py

# Or use the run script
chmod +x run.sh
./run.sh
```

## 🎯 **Advanced Usage**

### **Processing Pipeline**
1. **Upload PDF**: Select a clear, high-quality PDF question paper
2. **Automatic Processing**: 
   - Images extracted from all pages
   - OCR performed with optimization
   - Advanced LLM parsing with metadata extraction
   - Smart image reference matching
   - Comprehensive database storage
3. **Review Results**: View parsed questions, metadata, and images
4. **Browse & Analyze**: Use the multi-page interface for exploration

### **Advanced Features**

#### **Image Reference Matching**
The system automatically matches text references like "Figure 1.1" or "Diagram A" to actual extracted images using:
- Pattern recognition
- Page number correlation
- Fuzzy matching algorithms
- Filename analysis

#### **Metadata Extraction**
Automatically detects and extracts:
- **Subject**: Subject area (Physics, Math, English, etc.)
- **School Name**: Institution name
- **Booklet Type**: Set identifiers (Set A, Code 101, etc.)
- **Total Marks**: Maximum marks for the paper
- **Time Limit**: Duration allowed
- **Instructions**: General instructions for the paper

#### **Question Type Detection**
Advanced classification of questions into specific types:
- **MCQ**: Multiple choice with option detection
- **Diagram-based**: Questions referencing images
- **Passage-based**: Questions with reading passages
- **Numerical**: Mathematical problem solving
- **And more...**

## 📊 **Database Access**

### **Command Line Interface**
```bash
# View database information
python read_database.py info

# Show database schema
python read_database.py schema

# Export data
python read_database.py export-json output.json
python read_database.py export-csv output.csv

# Search functionality
python read_database.py search "physics"
```

### **Programmatic Access**
```python
from app.database_manager import DatabaseManager

# Initialize database manager
db = DatabaseManager()

# Get complete paper data
paper_data = db.get_paper_by_file("sample.pdf")

# Get all papers
papers = db.get_all_papers()

# Get statistics
stats = db.get_statistics()
```

## 🔧 **Configuration Options**

### **Environment Variables** (`.env`)
```env
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional customization
DATABASE_PATH=./data/questions.db
OCR_LANGUAGE=eng
TESSERACT_PATH=/usr/local/bin/tesseract
DEBUG=false
```

### **Advanced Settings** (`config/settings.py`)
- OCR optimization parameters
- Image processing settings
- LLM parsing configuration
- Database connection options

## 🖼️ **Image Management**

### **Storage Structure**
```
data/images/
├── sample_paper/
│   ├── sample_paper_page_1_20231201_143022.png
│   ├── sample_paper_page_2_20231201_143023.png
│   └── ...
└── another_paper/
    └── ...
```

### **Image Processing Features**
- **High-Quality Extraction**: 300 DPI PNG format
- **Automatic Optimization**: Web-optimized sizing
- **Metadata Storage**: Dimensions, file size, source tracking
- **Web Accessibility**: Proper paths for UI rendering

## 📈 **Analytics & Statistics**

The enhanced system provides comprehensive analytics:

- **Processing Statistics**: Pages, images, questions counts
- **Question Type Distribution**: Visual charts and breakdowns
- **Subject Analysis**: Papers by subject area
- **Image Usage**: Images per paper, reference matching rates
- **Performance Metrics**: Processing times, confidence scores

## � **Troubleshooting**

### **Common Issues**

#### **OCR Quality Issues**
```bash
# Check Tesseract installation
tesseract --version

# Verify Poppler installation
pdftoppm -h

# Test with high-quality PDF
```

#### **Image Processing Issues**
```bash
# Check available disk space
df -h

# Verify image directory permissions
ls -la data/images/
```

#### **LLM Parsing Issues**
```bash
# Verify API key
python -c "from config.settings import settings; print(bool(settings.GEMINI_API_KEY))"

# Check internet connectivity
curl -I https://generativelanguage.googleapis.com
```

#### **Database Issues**
```bash
# Reset database (WARNING: Deletes all data)
rm data/questions.db
python -c "from app.database_manager import DatabaseManager; DatabaseManager()"
```

## 🤝 **Contributing**

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black .
flake8 .
```

### **Code Structure**
- **OCR Processing**: `app/ocr_processor.py`
- **LLM Integration**: `app/llm_parser.py`
- **Database Operations**: `app/database_manager.py`
- **Image Management**: `app/image_processor.py`
- **Web Interface**: `main.py`

## 📋 **Changelog**

### **v2.0.0 - Enhanced Edition**
- ✨ Image extraction and storage system
- 🧠 Advanced LLM parsing with sophisticated prompts
- 📊 Enhanced database schema with metadata support
- 🖼️ Smart image reference matching
- 🌐 Multi-page web interface with image gallery
- 📈 Comprehensive analytics and statistics
- 🔧 Improved error handling and diagnostics

### **v1.0.0 - Initial Release**
- Basic OCR processing
- Simple question extraction
- Basic database storage
- Simple web interface

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **Google Generative AI**: For powerful LLM capabilities
- **Tesseract OCR**: For robust text recognition
- **Streamlit**: For the intuitive web framework
- **pdf2image & Poppler**: For PDF processing
- **OpenCV & Pillow**: For image processing

## 📞 **Support**

For issues, feature requests, or questions:

1. **Check Documentation**: Review this README and code comments
2. **Search Issues**: Look for existing GitHub issues
3. **Create Issue**: Submit detailed bug reports or feature requests
4. **Community**: Join discussions in the repository

---

**🎯 Transform your question papers into structured, searchable data with advanced AI-powered parsing and comprehensive image support!**
