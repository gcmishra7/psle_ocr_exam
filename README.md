# PDF Question Parser

A Python-based OCR application that extracts questions from PDF files, parses them using Google's Gemini LLM, and stores them in a database with a user-friendly Streamlit interface.

## 🚀 Features

- **OCR Processing**: Extract text from PDF files using Tesseract OCR
- **AI-Powered Parsing**: Use Google's Gemini LLM to intelligently parse and categorize questions
- **Database Storage**: Store questions in SQLite database with metadata
- **Web Interface**: Modern Streamlit-based UI for easy interaction
- **Multiple Export Formats**: Download results as JSON, CSV, or Excel
- **Search & Filter**: Find questions by content, type, or source file
- **Statistics & Analytics**: View processing statistics and question distribution

## 📋 Requirements

### System Dependencies
- **Python 3.8+**
- **Tesseract OCR** (for text extraction from images)
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### API Requirements
- **Google Gemini API Key** (Get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## 🛠️ Installation

### Quick Setup
1. Clone or download this repository
2. Run the setup script:
   ```bash
   python setup.py
   ```

### Manual Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

4. Create data directory:
   ```bash
   mkdir -p data
   ```

## 🚀 Usage

### Starting the Application
```bash
# Using Streamlit directly
streamlit run main.py

# Or using Python
python main.py
```

The application will start on `http://localhost:8501`

### Using the Interface

#### 1. Upload & Process
- Navigate to "Upload & Process" page
- Upload a PDF file (max 10MB)
- Choose processing options:
  - **Enhance question metadata**: Use AI to improve categorization
  - **Save to database**: Store results for later access
- Click "Process PDF" to start

#### 2. View Questions
- Browse all stored questions
- Search by text or subject
- Filter by source file
- View detailed question information

#### 3. Statistics
- View processing statistics
- Analyze question distribution by type and difficulty
- Track processed files

#### 4. Settings
- View current configuration
- Check API connection status
- Monitor application settings

### Processing Flow
1. **PDF Upload**: User uploads a PDF file
2. **OCR Extraction**: Text is extracted using Tesseract OCR
3. **AI Parsing**: Gemini LLM parses and categorizes questions
4. **Metadata Enhancement**: AI improves question metadata (optional)
5. **Database Storage**: Questions are saved to SQLite database (optional)
6. **Results Display**: Questions are shown with export options

## 📁 Project Structure

```
pdf-question-parser/
├── app/                    # Main application modules
│   ├── __init__.py
│   ├── ocr_processor.py    # OCR and PDF processing
│   ├── llm_parser.py       # Gemini LLM integration
│   ├── database_manager.py # Database operations
│   └── streamlit_ui.py     # User interface
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Application settings
├── data/                   # Database and data files
│   └── questions.db        # SQLite database (auto-created)
├── .env.example            # Environment variables template
├── .env                    # Your environment variables (create this)
├── requirements.txt        # Python dependencies
├── setup.py               # Setup and installation script
├── main.py                # Application entry point
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required: Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Database Configuration
DATABASE_PATH=./data/questions.db

# Optional: OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_LANGUAGE=eng

# Optional: Application Configuration
APP_TITLE=PDF Question Parser
APP_PORT=8501
DEBUG_MODE=False

# Optional: File Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf

# Optional: Gemini Model Configuration
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=2048
```

### Question Data Structure

Each parsed question contains:
- **question_id**: Sequential identifier
- **question_text**: The actual question text
- **question_type**: multiple_choice, true_false, short_answer, essay, or other
- **options**: Array of multiple choice options (if applicable)
- **correct_answer**: Correct answer if available
- **difficulty_level**: easy, medium, hard, or unknown
- **subject_area**: Subject or topic area
- **page_number**: Source page number
- **source_file**: Original PDF filename
- **created_at**: Processing timestamp

## 🔧 Troubleshooting

### Common Issues

#### 1. Tesseract OCR Not Found
**Error**: `TesseractNotFoundError`
**Solution**: Install Tesseract OCR for your operating system

#### 2. Gemini API Key Issues
**Error**: `ValueError: Gemini API key is required`
**Solution**: Add your API key to the `.env` file

#### 3. PDF Processing Fails
**Error**: No text extracted from PDF
**Possible causes**:
- PDF contains only images (OCR will process these)
- PDF is password protected
- PDF is corrupted
- Insufficient permissions

#### 4. Import Errors
**Error**: `ModuleNotFoundError`
**Solution**: Install dependencies: `pip install -r requirements.txt`

#### 5. Port Already in Use
**Error**: `Address already in use`
**Solution**: Change port in `.env` file or stop other applications using port 8501

### Debug Mode

Enable debug mode by setting `DEBUG_MODE=True` in your `.env` file for more detailed error messages.

## 📊 Performance Considerations

- **PDF Size**: Larger PDFs take longer to process
- **Image Quality**: Higher DPI improves OCR accuracy but increases processing time
- **API Limits**: Gemini API has rate limits and token limits
- **Memory Usage**: Large PDFs may require significant memory for image processing

## 🔒 Security Notes

- **API Keys**: Never commit your `.env` file to version control
- **File Uploads**: Files are processed locally and temporarily stored
- **Database**: SQLite database is stored locally
- **Network**: Application runs locally by default

## 🧪 Development

### Adding New Question Types
1. Modify the prompt in `llm_parser.py`
2. Update the database schema if needed
3. Adjust the UI components accordingly

### Custom OCR Settings
Modify OCR parameters in `ocr_processor.py`:
- DPI settings for image conversion
- Tesseract configuration parameters
- Image preprocessing options

### Database Extensions
The SQLite database can be extended with additional tables or fields by modifying `database_manager.py`.

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration settings
3. Ensure all dependencies are properly installed
4. Check that your Gemini API key is valid and has sufficient quota

## 🎯 Future Enhancements

- Support for additional file formats (DOCX, TXT, etc.)
- Batch processing of multiple files
- Advanced question analytics
- Export to quiz platforms
- Multi-language OCR support
- Cloud deployment options
- Real-time collaboration features

---

**Happy Question Parsing! 📝✨**
