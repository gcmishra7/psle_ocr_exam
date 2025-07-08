import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration management."""
    
    # Primary AI Configuration - Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '8192'))
    
    # Llama Parse Configuration
    LLAMA_CLOUD_API_KEY = os.getenv('LLAMA_CLOUD_API_KEY', '')
    LLAMA_PARSE_RESULT_TYPE = os.getenv('LLAMA_PARSE_RESULT_TYPE', 'markdown')
    LLAMA_PARSE_LANGUAGE = os.getenv('LLAMA_PARSE_LANGUAGE', 'english')
    
    # OpenAI Configuration (for vision models)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_VISION_MODEL = os.getenv('OPENAI_VISION_MODEL', 'gpt-4-vision-preview')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
    
    # Anthropic Configuration (optional)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', './data/questions.db')
    
    # OCR Configuration
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
    OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'eng')
    
    # Application Configuration
    APP_TITLE = os.getenv('APP_TITLE', 'Enhanced OCR Parser with Multimodal AI')
    APP_PORT = int(os.getenv('APP_PORT', '8501'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf').split(',')
    
    # Multimodal Processing Configuration
    ENABLE_MULTIMODAL = os.getenv('ENABLE_MULTIMODAL', 'True').lower() == 'true'
    AUTO_CLEANUP_REPROCESS = os.getenv('AUTO_CLEANUP_REPROCESS', 'True').lower() == 'true'
    VISION_ANALYSIS_TIMEOUT = int(os.getenv('VISION_ANALYSIS_TIMEOUT', '30'))
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', '600'))
    
    @classmethod
    def validate_settings(cls):
        """Validate required settings are present."""
        warnings = []
        
        # Check for at least one AI API key
        has_ai_key = any([
            cls.GEMINI_API_KEY,
            cls.LLAMA_CLOUD_API_KEY,
            cls.OPENAI_API_KEY,
            cls.ANTHROPIC_API_KEY
        ])
        
        if not has_ai_key:
            raise ValueError(
                "At least one AI API key is required. Please set one of:\n"
                "- GEMINI_API_KEY (recommended)\n"
                "- LLAMA_CLOUD_API_KEY (for advanced parsing)\n"
                "- OPENAI_API_KEY (for vision analysis)\n"
                "- ANTHROPIC_API_KEY (optional)\n"
                "in your .env file."
            )
        
        # Warn about missing optional keys
        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not set - LLM parsing will be limited")
        
        if not cls.LLAMA_CLOUD_API_KEY:
            warnings.append("LLAMA_CLOUD_API_KEY not set - advanced document parsing disabled")
        
        if not cls.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY not set - OpenAI vision analysis disabled")
        
        # Print warnings
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"   • {warning}")
            print("   For full functionality, consider adding missing API keys to .env\n")
        
        # Create data directory if it doesn't exist
        db_dir = Path(cls.DATABASE_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        return True
    
    @classmethod
    def get_available_models(cls):
        """Get list of available AI models based on configured API keys."""
        models = []
        
        if cls.GEMINI_API_KEY:
            models.append("Gemini Vision (gemini-1.5-pro)")
        
        if cls.LLAMA_CLOUD_API_KEY:
            models.append("Llama Parse (Document Parsing)")
        
        if cls.OPENAI_API_KEY:
            models.append("OpenAI Vision (gpt-4-vision-preview)")
        
        if cls.ANTHROPIC_API_KEY:
            models.append("Claude (claude-3-sonnet)")
        
        return models if models else ["No AI models configured"]

# Create settings instance
settings = Settings()