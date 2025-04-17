import os
import logging
import traceback
import google.generativeai as genai
from google.cloud import texttospeech, speech, aiplatform

logger = logging.getLogger(__name__)

class GoogleCloudManager:
    """
    Manages Google Cloud service initialization and authentication
    """
    
    def __init__(self):
        self.initialized = False
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "keys/service-account.json")
        self.api_key = os.getenv("API_KEY", "")
        self.project_id = os.getenv("PROJECT_ID", "")
        self.location = os.getenv("LOCATION", "us-central1")
        
        # Service clients
        self.genai_client = None
        self.tts_client = None
        self.stt_client = None
        self.vertex_ai_client = None
        
    def initialize(self):
        """Initialize all Google Cloud services"""
        try:
            # Set up Gemini AI (PaLM)
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.genai_client = True
                logger.info("Initialized Gemini API client")
            
            # Set credentials for other services if credentials file exists
            if os.path.exists(self.credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                
                # Initialize Text-to-Speech
                try:
                    self.tts_client = texttospeech.TextToSpeechClient()
                    logger.info("Initialized Text-to-Speech client")
                except Exception as e:
                    logger.error(f"Failed to initialize Text-to-Speech: {e}")
                
                # Initialize Speech-to-Text
                try:
                    self.stt_client = speech.SpeechClient()
                    logger.info("Initialized Speech-to-Text client")
                except Exception as e:
                    logger.error(f"Failed to initialize Speech-to-Text: {e}")
                
                # Initialize Vertex AI
                try:
                    aiplatform.init(project=self.project_id, location=self.location)
                    self.vertex_ai_client = True
                    logger.info("Initialized Vertex AI client")
                except Exception as e:
                    logger.error(f"Failed to initialize Vertex AI: {e}")
            else:
                logger.warning(f"Credentials file not found at {self.credentials_path}")
                logger.warning("Only API key-based services will be available")
            
            self.initialized = (self.genai_client is not None)
            return self.initialized
            
        except Exception as e:
            logger.error(f"Error initializing Google Cloud services: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def is_initialized(self):
        """Check if Google Cloud services are initialized"""
        return self.initialized
    
    def get_genai_model(self, model_name="gemini-1.5-pro-latest"):
        """Get a Gemini model for text generation"""
        if not self.genai_client:
            logger.error("Gemini API client not initialized")
            return None
        
        try:
            return genai.GenerativeModel(model_name)
        except Exception as e:
            logger.error(f"Error getting Gemini model: {e}")
            return None
    
    def get_tts_client(self):
        """Get the Text-to-Speech client"""
        return self.tts_client
    
    def get_stt_client(self):
        """Get the Speech-to-Text client"""
        return self.stt_client
    
    def get_status(self):
        """Get status of all Google Cloud services"""
        return {
            "initialized": self.initialized,
            "genai": self.genai_client is not None,
            "tts": self.tts_client is not None,
            "stt": self.stt_client is not None,
            "vertex_ai": self.vertex_ai_client is not None,
        }

# Create a singleton instance
cloud_manager = GoogleCloudManager() 