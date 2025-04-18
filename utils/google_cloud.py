import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import texttospeech, speech, aiplatform

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GoogleCloudManager:
    def __init__(self):
        self.api_key = os.getenv("API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.project_id = os.getenv("PROJECT_ID", "vc-interview-agent")
        self.location = os.getenv("LOCATION", "us-central1")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Clients
        self.genai_client = None
        self.tts_client = None
        self.speech_client = None
        self.vertex_client = None
        
        # Status
        self.initialized = False
        self.error_message = None
    
    def initialize(self):
        """Initialize all Google Cloud services"""
        try:
            if self.credentials_path:
                # Set environment variable for Google Cloud clients
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                logger.info(f"Using credentials from {self.credentials_path}")
            
            # Initialize Gemini
            if self.api_key:
                try:
                    genai.configure(api_key=self.api_key)
                    # Test by listing models
                    models = genai.list_models()
                    self.genai_client = genai
                    logger.info(f"Gemini API initialized, available models: {[m.name for m in models]}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini API: {e}")
                    self.error_message = f"Gemini initialization failed: {str(e)}"
            else:
                logger.warning("No API key provided for Gemini")
            
            # Initialize Text-to-Speech
            try:
                self.tts_client = texttospeech.TextToSpeechClient()
                logger.info("Text-to-Speech client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Text-to-Speech client: {e}")
                self.error_message = f"TTS initialization failed: {str(e)}"
            
            # Initialize Speech-to-Text
            try:
                self.speech_client = speech.SpeechClient()
                logger.info("Speech-to-Text client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Speech-to-Text client: {e}")
                self.error_message = f"STT initialization failed: {str(e)}"
            
            # Initialize Vertex AI
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                self.vertex_client = aiplatform
                logger.info("Vertex AI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}")
                self.error_message = f"Vertex AI initialization failed: {str(e)}"
            
            # Set initialization status
            self.initialized = (
                self.genai_client is not None or 
                self.tts_client is not None or 
                self.speech_client is not None or 
                self.vertex_client is not None
            )
            
            return self.initialized
        except Exception as e:
            logger.error(f"Error during Google Cloud services initialization: {e}")
            self.error_message = str(e)
            self.initialized = False
            return False
    
    def get_status(self):
        """Get the status of all services"""
        return {
            "initialized": self.initialized,
            "error": self.error_message,
            "services": {
                "genai": self.genai_client is not None,
                "tts": self.tts_client is not None,
                "stt": self.speech_client is not None,
                "vertex_ai": self.vertex_client is not None
            }
        }
    
    def is_initialized(self):
        """Check if manager is initialized"""
        return self.initialized

    def init_tts(self):
        try:
            self.tts = texttospeech.TextToSpeechClient()
            self._services_status['tts'] = True
            
            # Get available voices
            voices_response = self.tts.list_voices(language_code="en-US")
            voices = voices_response.voices
            
            # Look for advanced voices in order of preference
            voice_categories = [
                [v.name for v in voices if "Chirp3-HD" in v.name],
                [v.name for v in voices if "Chirp-HD" in v.name],
                [v.name for v in voices if "Studio" in v.name],
                [v.name for v in voices if "Neural2" in v.name],
                [v.name for v in voices if "Wavenet" in v.name]
            ]
            
            # Store information about available voices
            self._service_info['tts_voices'] = {
                'chirp3_hd': voice_categories[0],
                'chirp_hd': voice_categories[1],
                'studio': voice_categories[2], 
                'neural2': voice_categories[3],
                'wavenet': voice_categories[4]
            }
            
            # Determine best available voice
            for category in voice_categories:
                if category:
                    self._service_info['tts_best_voice'] = category[0]
                    self._service_info['tts_voice_type'] = category[0].split('-')[2] if len(category[0].split('-')) > 2 else 'Standard'
                    break
            
            logging.info(f"TTS initialized with best voice: {self._service_info.get('tts_best_voice', 'Default')}")
            return True
        except Exception as e:
            logging.error(f"Error initializing TTS: {e}")
            self._services_status['tts'] = False
            return False

# Create an instance for global use
cloud_manager = GoogleCloudManager()

# Initialize on module import
initialized = cloud_manager.initialize()

if not initialized:
    logger.error("Failed to initialize Google Cloud services")
else:
    logger.info("Google Cloud services initialized successfully")
