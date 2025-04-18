"""
Simple direct TTS script without Flask
Just generates an MP3 file directly using Google Cloud TTS
"""

import os
import logging
import sys
import json
from google.cloud import texttospeech

# Configure logging - increase level to debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_tts_file():
    """Generate an MP3 file using Google Cloud TTS without a server"""
    try:
        # Print Python version and location
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Python executable: {sys.executable}")
        
        # Print environment variables
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if "GOOGLE" in key:
                logger.info(f"  {key}: {value}")
        
        # Create the client
        logger.info("Creating TTS client...")
        client = texttospeech.TextToSpeechClient()
        logger.info("TTS client initialized")
        
        # Find available voices
        logger.info("Listing available voices...")
        voices_response = client.list_voices(language_code="en-US")
        voices = voices_response.voices
        logger.info(f"Found {len(voices)} voices")
        
        # Print first few voices for debugging
        for i, voice in enumerate(voices[:5]):
            logger.info(f"Voice {i+1}: {voice.name} - {voice.language_codes}")
        
        # Look for any voice (from best to worst)
        voice_categories = [
            [v.name for v in voices if "Chirp3-HD" in v.name],
            [v.name for v in voices if "Chirp-HD" in v.name],
            [v.name for v in voices if "Studio" in v.name],
            [v.name for v in voices if "Neural2" in v.name],
            [v.name for v in voices if "Wavenet" in v.name],
            [v.name for v in voices]
        ]
        
        # Log what we found
        logger.info(f"Found {len(voice_categories[0])} Chirp3-HD voices")
        logger.info(f"Found {len(voice_categories[1])} Chirp-HD voices")
        logger.info(f"Found {len(voice_categories[2])} Studio voices")
        logger.info(f"Found {len(voice_categories[3])} Neural2 voices")
        logger.info(f"Found {len(voice_categories[4])} Wavenet voices")
        logger.info(f"Total voices: {len(voice_categories[5])}")
        
        voice_name = None
        voice_type = "Standard"
        
        # Choose first available voice from any category
        for i, category in enumerate(voice_categories):
            if category:
                voice_name = category[0]
                if "Chirp3-HD" in voice_name:
                    voice_type = "Chirp 3 HD"
                elif "Chirp-HD" in voice_name:
                    voice_type = "Chirp HD"
                elif "Studio" in voice_name:
                    voice_type = "Studio"
                elif "Neural2" in voice_name:
                    voice_type = "Neural2"
                elif "Wavenet" in voice_name:
                    voice_type = "Wavenet"
                logger.info(f"Selected voice from category {i+1}")
                break
        
        if not voice_name:
            logger.error("No voices found!")
            return False
        
        logger.info(f"Using voice: {voice_name} ({voice_type})")
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            name=voice_name,
            language_code="en-US"
        )
        
        # Configure audio - do NOT use pitch for Chirp3-HD
        audio_config_params = {
            "audio_encoding": texttospeech.AudioEncoding.MP3,
            "speaking_rate": 1.0,
            "volume_gain_db": 1.0
        }
        
        # Only add pitch for non-Chirp3-HD voices
        if "Chirp3-HD" not in voice_name:
            audio_config_params["pitch"] = 0.2
            
        audio_config = texttospeech.AudioConfig(**audio_config_params)
        logger.info(f"Audio config: {json.dumps(audio_config_params)}")
        
        # Text to synthesize
        text = """Hello, this is a test of the Google TTS voice.
        This is a simple test to see if speech synthesis is working properly.
        If you can hear this clearly, then the TTS system is working correctly."""
        
        # Generate speech
        logger.info("Generating speech...")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        logger.info("Calling synthesize_speech...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        logger.info(f"Received response with {len(response.audio_content)} bytes")
        
        # Save the audio to a file
        output_file = "test_tts.mp3"
        logger.info(f"Writing to file {output_file}...")
        
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"Audio saved to {output_file}")
        
        # Print file path and size
        file_size = os.path.getsize(output_file)
        logger.info(f"File size: {file_size/1024:.2f} KB")
        
        # Get full path
        abs_path = os.path.abspath(output_file)
        logger.info(f"Full path: {abs_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating TTS: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Print Google credentials info
    logger.info("Starting TTS generation")
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        logger.info(f"Using Google credentials from: {creds_path}")
        logger.info(f"File exists: {os.path.exists(creds_path)}")
        
        if os.path.exists(creds_path):
            # Print first few lines of credentials file for debugging
            try:
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    logger.info(f"Credentials type: {creds_data.get('type')}")
                    logger.info(f"Project ID: {creds_data.get('project_id')}")
            except Exception as e:
                logger.error(f"Error reading credentials file: {e}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set!")
    
    # Generate the file
    success = generate_tts_file()
    
    if success:
        logger.info("✓ TTS file generated successfully")
        logger.info("To play: Double-click the test_tts.mp3 file in your file explorer")
    else:
        logger.error("✗ Failed to generate TTS file") 