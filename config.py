import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("config")

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # Environment settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # production, development, testing
    
    # Google Cloud credentials
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "keys/service-account.json")
    
    # Project configuration
    PROJECT_ID: str = os.getenv("PROJECT_ID", "ventureai-project")
    LOCATION: str = os.getenv("LOCATION", "us-central1")
    
    # Google API key for Gemini
    API_KEY: str = os.getenv("API_KEY", "AIzaSyCNjAzI3AYUDHlcPuXbZ42fQFhzxmZ4qrw")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "AIzaSyCNjAzI3AYUDHlcPuXbZ42fQFhzxmZ4qrw")
    
    # Audio configuration
    AUDIO_FORMAT: int = 8  # pyaudio.paInt16
    CHANNELS: int = 1
    RATE: int = int(os.getenv("RATE", "16000"))
    CHUNK: int = int(os.getenv("CHUNK", "1024"))
    RECORD_SECONDS: int = 120
    
    # File paths
    QUESTIONS_CSV: str = os.getenv("QUESTIONS_CSV", "data/questions.csv")
    questions_csv_path: str = os.getenv("QUESTIONS_CSV_PATH", "vc_interview_questions_full.csv")
    
    # Session storage
    SESSION_DIR: str = os.getenv("SESSION_DIR", "sessions")
    sessions_dir: str = os.getenv("SESSIONS_DIR", "sessions")
    
    # Model configuration
    generative_model_name: str = os.getenv("GENERATIVE_MODEL_NAME", "gemini-1.5-pro-latest")
    
    # API settings
    ENABLE_CORS: bool = os.getenv("ENABLE_CORS", "true").lower() in ["true", "1", "yes"]
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    
    # Performance settings
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "true").lower() in ["true", "1", "yes"]
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    
    # Speech service config
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-Studio-O")
    STT_MODEL: str = os.getenv("STT_MODEL", "latest_long")
    
    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    model_config = {
        "env_file": ".env",
        "extra": "allow",
        "case_sensitive": False
    }
    
    # Validate the config
    def validate_settings(self) -> bool:
        """Validate that the settings are properly configured"""
        warnings = []
        
        if not os.path.exists(self.GOOGLE_APPLICATION_CREDENTIALS):
            warnings.append(f"Google credentials file not found: {self.GOOGLE_APPLICATION_CREDENTIALS}")
            logger.warning(f"Google credentials file not found: {self.GOOGLE_APPLICATION_CREDENTIALS}")
        
        if not os.path.exists(self.QUESTIONS_CSV):
            # Create the questions CSV file if it doesn't exist
            os.makedirs(os.path.dirname(self.QUESTIONS_CSV), exist_ok=True)
            with open(self.QUESTIONS_CSV, 'w') as f:
                f.write("category,question\n")
            logger.warning(f"Created empty questions CSV file: {self.QUESTIONS_CSV}")
        
        if not self.API_KEY or self.API_KEY == "YOUR_API_KEY":
            warnings.append("API_KEY not properly configured")
            logger.warning("API_KEY not properly configured, some features may be limited")
        
        if warnings:
            logger.warning("Configuration validation warnings:")
            for warning in warnings:
                logger.warning(f"- {warning}")
            # Return True anyway, allowing the application to start with warnings
            return True
        
        return True

settings = Settings()

# Log settings validation results but don't prevent app from starting
settings.validate_settings()
