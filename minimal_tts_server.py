"""
Minimal TTS Server
Provides direct access to Google TTS with Chirp 3 HD voices
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import os
import logging
from google.cloud import texttospeech

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["X-Voice-Used", "X-Voice-Type"])

# Initialize TTS client
tts_client = None
try:
    tts_client = texttospeech.TextToSpeechClient()
    logger.info("TTS client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TTS client: {e}")

@app.route('/')
def index():
    return jsonify({"status": "Minimal TTS Server is running"})

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech using Google Cloud TTS.
    
    Request body:
    {
        "text": "Text to convert to speech",
        "speed": 1.0,
        "pitch": 0.2
    }
    """
    if not tts_client:
        return jsonify({"error": "TTS client not initialized"}), 500
    
    try:
        # Get request data
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text parameter"}), 400
        
        text = data['text']
        speed = data.get('speed', 1.0)
        pitch = data.get('pitch', 0.0)  # Default to neutral pitch
        
        logger.info(f"TTS request: {len(text)} chars, speed={speed}, pitch={pitch}")
        
        # Find best available voice
        voice_name = get_best_available_voice()
        logger.info(f"Selected voice: {voice_name}")
        
        # Determine voice type
        voice_type = "Standard"
        is_chirp3_hd = False
        if "Chirp3-HD" in voice_name:
            voice_type = "Chirp 3 HD"
            is_chirp3_hd = True
        elif "Chirp-HD" in voice_name:
            voice_type = "Chirp HD"
        elif "Studio" in voice_name:
            voice_type = "Studio"
        elif "Neural2" in voice_name:
            voice_type = "Neural2"
        elif "Wavenet" in voice_name:
            voice_type = "Wavenet"
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            name=voice_name,
            language_code="en-US"
        )
        
        # Configure audio - handle Chirp3-HD pitch limitations
        audio_config_params = {
            "audio_encoding": texttospeech.AudioEncoding.MP3,
            "speaking_rate": float(speed),
            "volume_gain_db": 1.0
        }
        
        # Only add pitch if not using Chirp3-HD voices
        if not is_chirp3_hd:
            audio_config_params["pitch"] = float(pitch)
            
        audio_config = texttospeech.AudioConfig(**audio_config_params)
        
        # Generate speech with plain text
        logger.info(f"Generating speech with plain text...")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        logger.info("Plain text synthesis successful")
        
        # Create a file-like object from the audio content
        audio_io = io.BytesIO(response.audio_content)
        audio_io.seek(0)
        
        # Create response
        logger.info(f"Sending audio response, size: {len(response.audio_content)} bytes")
        
        # Use send_file to return the audio with proper headers
        return send_file(
            audio_io,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="tts.mp3",
            headers={
                "X-Voice-Used": voice_name,
                "X-Voice-Type": voice_type,
                "Access-Control-Expose-Headers": "X-Voice-Used, X-Voice-Type",
                "Cache-Control": "no-cache"
            }
        )
    
    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}")
        return jsonify({"error": str(e)}), 500

def get_best_available_voice():
    """Find the best available voice from Google Cloud TTS."""
    try:
        # List available voices
        voices_response = tts_client.list_voices(language_code="en-US")
        voice_names = [v.name for v in voices_response.voices]
        
        # Check for Chirp 3 HD voices first
        chirp3_hd_voices = [v for v in voice_names if "Chirp3-HD" in v]
        
        # Try to find the best Chirp 3 HD voice
        if chirp3_hd_voices:
            # Prioritize specific voices
            priority_voices = [
                "en-US-Chirp3-HD-Kore", 
                "en-US-Chirp3-HD-Leda",
                "en-US-Chirp3-HD-Aoede",
                "en-US-Chirp3-HD-Charon",
                "en-US-Chirp3-HD-Puck",
                "en-US-Chirp3-HD-Zephyr"
            ]
            
            # Try to find one of the priority voices
            for voice in priority_voices:
                if voice in chirp3_hd_voices:
                    logger.info(f"Using priority Chirp 3 HD voice: {voice}")
                    return voice
            
            # Otherwise use the first available
            logger.info(f"Using Chirp 3 HD voice: {chirp3_hd_voices[0]}")
            return chirp3_hd_voices[0]
        
        # Check for regular Chirp HD voices
        chirp_hd_voices = [v for v in voice_names if "Chirp-HD" in v]
        if chirp_hd_voices:
            logger.info(f"Using Chirp HD voice: {chirp_hd_voices[0]}")
            return chirp_hd_voices[0]
        
        # Check for Studio voices
        studio_voices = [v for v in voice_names if "Studio" in v]
        if studio_voices:
            logger.info(f"Using Studio voice: {studio_voices[0]}")
            return studio_voices[0]
        
        # Check for Neural2 voices
        neural_voices = [v for v in voice_names if "Neural2" in v]
        if neural_voices:
            logger.info(f"Using Neural2 voice: {neural_voices[0]}")
            return neural_voices[0]
        
        # Check for Wavenet voices
        wavenet_voices = [v for v in voice_names if "Wavenet" in v]
        if wavenet_voices:
            logger.info(f"Using Wavenet voice: {wavenet_voices[0]}")
            return wavenet_voices[0]
        
        # Fallback to first available
        if voice_names:
            logger.info(f"Using standard voice: {voice_names[0]}")
            return voice_names[0]
        
        # Last resort
        logger.warning("No voices found, using default")
        return "en-US-Standard-C"
    
    except Exception as e:
        logger.error(f"Error selecting voice: {e}")
        return "en-US-Standard-C"

if __name__ == "__main__":
    # Print Google credentials path
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        logger.info(f"Using Google credentials from: {creds_path}")
        logger.info(f"Credentials file exists: {os.path.exists(creds_path)}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set!")
    
    # Run the Flask app
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting TTS server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True) 