# 🤖 Enhanced OCR Parser with Multimodal AI

Transform PDF question papers into structured data using advanced multimodal AI capabilities including Llama Parse, Vision Models, and automatic cleanup features.

## 🌟 Key Features

### 🚀 **Multimodal AI Processing**
- **Llama Parse Integration** - Advanced document structure understanding
- **Vision Model Analysis** - Intelligent image analysis using Gemini Vision & OpenAI Vision
- **Smart Image Extraction** - Automatically extracts question-specific diagrams and figures
- **Enhanced Metadata Extraction** - Comprehensive document information extraction

### 🔄 **Automatic Cleanup**
- **Reprocessing Support** - Automatically truncates images folder and database entries when reprocessing the same file
- **No Duplicate Data** - Ensures clean data storage without conflicts
- **Version Control** - Maintains data integrity across multiple processing attempts

### 📊 **Advanced Question Processing**
- **Multiple Question Types** - MCQ, Short Answer, Long Answer, etc.
- **Image-Question Matching** - Links images to relevant questions using AI
- **Comprehensive Metadata** - Subject, school, marks, time limits, instructions
- **Structured Output** - Clean JSON format for easy integration

### 🖼️ **Enhanced Image Processing**
- **Full Page Extraction** - Complete page images for reference
- **Diagram Detection** - Automatically identifies and extracts diagrams/figures
- **Smart Reference Matching** - Maps "Figure 1.1" references to actual images
- **Web-Accessible Storage** - Organized image storage with web links

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd enhanced-ocr-parser
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` file with your API keys:

```env
# Required: At least one AI API key
GEMINI_API_KEY=your_gemini_api_key_here
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 4. Run Application
```bash
streamlit run main.py
```

## 🔑 API Key Setup

### 🎯 **Recommended Setup (Gemini + Llama Parse)**

#### Google Gemini API (Recommended)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create API key
4. Add to `.env`: `GEMINI_API_KEY=your_key_here`

**Best for:** Question parsing, text analysis, image understanding

#### Llama Parse API (Advanced Document Parsing)
1. Go to [LlamaIndex Cloud](https://cloud.llamaindex.ai)
2. Sign up for account
3. Get API key from dashboard
4. Add to `.env`: `LLAMA_CLOUD_API_KEY=your_key_here`

**Best for:** Complex document structure parsing, educational content

### 🔧 **Optional Enhancements**

#### OpenAI API (Vision Analysis)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create account and add payment method
3. Generate API key
4. Add to `.env`: `OPENAI_API_KEY=your_key_here`

**Best for:** Advanced image analysis, diagram understanding

#### Anthropic API (Alternative LLM)
1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create account
3. Generate API key
4. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

**Best for:** Alternative text analysis, backup processing

## 🚀 Usage

### Web Interface
1. Run `streamlit run main.py`
2. Upload PDF file
3. Click "🚀 Process PDF"
4. View results with images and metadata

### Command Line Processing
```python
from app.llama_multimodal_parser import LlamaMultimodalParser

# Initialize parser
parser = LlamaMultimodalParser()

# Process PDF
parsed_data, image_info = parser.process_pdf_multimodal("path/to/file.pdf", "filename.pdf")

# Access results
print(f"Questions found: {len(parsed_data['questions'])}")
print(f"Images extracted: {len(image_info)}")
```

## 📁 System Architecture

### **Processing Pipeline**
```
📄 PDF Input
    ↓
🧹 Auto Cleanup (if reprocessing)
    ↓
📸 Image Extraction (Full pages + Diagrams)
    ↓
📄 Llama Parse (Document structure)
    ↓
👁️ Vision Analysis (Image understanding)
    ↓
🧠 Enhanced LLM Parsing (Question extraction)
    ↓
🔗 Smart Image Matching (Link images to questions)
    ↓
💾 Database Storage (Structured data)
```

### **File Organization**
```
project/
├── app/
│   ├── llama_multimodal_parser.py  # Main multimodal parser
│   ├── ocr_processor.py            # Processing coordination
│   ├── image_processor.py          # Image extraction & analysis
│   ├── simple_database_manager.py  # Database operations
│   └── ...
├── data/
│   ├── images/                     # Extracted images
│   │   └── [pdf_name]/
│   │       ├── page_1.png         # Full page images
│   │       └── diagram_1.png      # Extracted diagrams
│   └── questions.db               # SQLite database
├── config/
│   └── settings.py                # Configuration management
└── main.py                        # Streamlit web app
```

## 📊 Database Schema

### **Enhanced Tables**
- `paper_metadata` - Document metadata (subject, school, marks, etc.)
- `questions_new` - Questions with image references
- `images` - Image storage information
- `unmatched_images` - Images that couldn't be matched to questions
- `processed_files` - Processing history and statistics

### **Auto-Cleanup Features**
When reprocessing the same file:
- ✅ Automatically removes previous image folder
- ✅ Deletes previous database entries
- ✅ Ensures clean, conflict-free data storage

## 🎯 Output Format

### **Structured JSON Response**
```json
{
  "metadata": {
    "subject": "Mathematics",
    "school_name": "ABC School",
    "booklet_type": "Question Paper",
    "total_marks": "100",
    "time_limit": "3 hours",
    "general_instructions": "..."
  },
  "questions": [
    {
      "question_number": "1",
      "question_text": "Solve the following equation...",
      "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      },
      "marks": "5",
      "question_type": "MCQ",
      "image_references_in_text": ["Figure 1.1"],
      "image_links_used": ["/data/images/sample/diagram_1.png"]
    }
  ],
  "unmatched_image_links": []
}
```

## 🔧 Configuration Options

### **Environment Variables**
```env
# Multimodal Processing
ENABLE_MULTIMODAL=True
AUTO_CLEANUP_REPROCESS=True
VISION_ANALYSIS_TIMEOUT=30
PROCESSING_TIMEOUT=600

# Model Settings
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.1
OPENAI_VISION_MODEL=gpt-4-vision-preview

# File Processing
MAX_FILE_SIZE_MB=100
ALLOWED_EXTENSIONS=pdf
```

## 🛡️ Troubleshooting

### **Common Issues**

#### No AI Models Configured
```
Error: At least one AI API key is required
```
**Solution:** Add at least one API key to `.env` file

#### Database Column Errors
```
Error: table processed_files has no column named images_count
```
**Solution:** System automatically uses SimpleDatabaseManager with correct schema

#### Import Errors
```
Error: No module named 'llama_parse'
```
**Solution:** Install dependencies: `pip install -r requirements.txt`

### **Fallback Behavior**
The system includes robust fallback mechanisms:
- If Llama Parse fails → Falls back to traditional OCR
- If vision models fail → Uses basic image processing
- If multimodal fails → Uses legacy processing pipeline
- Missing dependencies → Graceful degradation with warnings

## 📈 Performance Features

### **Smart Processing**
- **Parallel image analysis** for faster processing
- **Intelligent caching** to avoid reprocessing
- **Incremental updates** for efficiency
- **Resource optimization** based on available models

### **Scalability**
- **Batch processing** support
- **Concurrent file handling**
- **Memory-efficient** image processing
- **Database optimization** for large datasets

## 🔄 Migration from Previous Versions

### **Automatic Migration**
The system automatically handles migration from previous versions:
- Database schema updates applied automatically
- Backward compatibility maintained
- Existing data preserved during upgrades

### **Manual Migration** (if needed)
```python
from app.migrate_database import migrate_database
migrate_database()
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LlamaIndex** for advanced document parsing capabilities
- **Google Gemini** for powerful multimodal AI
- **OpenAI** for vision analysis capabilities
- **Streamlit** for the beautiful web interface

---

## 🚀 Quick Start Example

```bash
# 1. Setup
git clone <repo>
cd enhanced-ocr-parser
pip install -r requirements.txt

# 2. Configure (minimum)
echo "GEMINI_API_KEY=your_key_here" > .env

# 3. Run
streamlit run main.py

# 4. Upload PDF and process!
```

**Ready to transform your educational PDFs with AI! 🎓✨**
