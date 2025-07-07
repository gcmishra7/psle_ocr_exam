import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration management."""
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.2'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', './data/questions.db')
    
    # OCR Configuration
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
    OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'eng')
    
    # Application Configuration
    APP_TITLE = os.getenv('APP_TITLE', 'PDF Question Parser')
    APP_PORT = int(os.getenv('APP_PORT', '8501'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf').split(',')
    
    @classmethod
    def validate_settings(cls):
        """Validate required settings are present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file.")
        
        # Create data directory if it doesn't exist
        db_dir = Path(cls.DATABASE_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        return True

# Create settings instance
settings = Settings()