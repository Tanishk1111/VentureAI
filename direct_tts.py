"""
Direct TTS script for testing Google Cloud Text-to-Speech with Chirp 3 HD voices
No frameworks, just direct API calls to Google
"""

import os
from google.cloud import texttospeech
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def direct_tts_test():
    """Direct test of Google Cloud TTS with Chirp 3 HD voices"""
    logger.info("Starting direct TTS test...")
    
    try:
        # Create the client
        client = texttospeech.TextToSpeechClient()
        
        # List available voices
        logger.info("Listing voices...")
        response = client.list_voices(language_code="en-US")
        voices = response.voices
        
        # Look for Chirp3-HD voices
        chirp3_voices = [v.name for v in voices if "Chirp3-HD" in v.name]
        
        if not chirp3_voices:
            logger.warning("No Chirp3-HD voices found! Using standard voice instead.")
            test_voice = "en-US-Standard-C"
        else:
            logger.info(f"Found {len(chirp3_voices)} Chirp3-HD voices")
            logger.info(f"Available Chirp3-HD voices: {', '.join(chirp3_voices)}")
            
            # Choose the best voice - try these in order of preference
            preferred_voices = [
                "en-US-Chirp3-HD-Kore",
                "en-US-Chirp3-HD-Leda", 
                "en-US-Chirp3-HD-Aoede", 
                "en-US-Chirp3-HD-Charon", 
                "en-US-Chirp3-HD-Puck"
            ]
            
            test_voice = None
            for voice in preferred_voices:
                if voice in chirp3_voices:
                    test_voice = voice
                    break
            
            # If none of the preferred voices are available, use the first Chirp3-HD voice
            if not test_voice:
                test_voice = chirp3_voices[0]
        
        logger.info(f"Selected voice: {test_voice}")
        
        # Set up voice parameters
        voice = texttospeech.VoiceSelectionParams(
            name=test_voice,
            language_code="en-US"
        )
        
        # Configure audio settings
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.2
        )
        
        # Text to synthesize
        text = """
        Hello, this is a test of the Google Chirp 3 HD voice. 
        This voice should sound natural and expressive, almost like a real human.
        We're testing if it works properly in our application.
        """
        
        # Try SSML first for Chirp3-HD voices
        try:
            logger.info("Trying SSML synthesis...")
            ssml = f"""
            <speak>
              <prosody rate="1.0" pitch="20%" volume="loud">
                {text}
              </prosody>
            </speak>
            """
            
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info("SSML synthesis successful")
        except Exception as e:
            logger.warning(f"SSML synthesis failed: {e}")
            logger.info("Falling back to plain text synthesis...")
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info("Plain text synthesis successful")
        
        # Save the audio to a file
        output_file = "chirp3_test.mp3"
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"Audio saved to {output_file}")
        
        # Print instructions to play the file
        logger.info(f"To play the audio, use a media player to open {output_file}")
        logger.info(f"Voice used: {test_voice}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in direct TTS test: {e}")
        return False

if __name__ == "__main__":
    # Print Google credentials path
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        logger.info(f"Using Google credentials from: {creds_path}")
        logger.info(f"File exists: {os.path.exists(creds_path)}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set!")
    
    # Run the test
    result = direct_tts_test()
    
    if result:
        logger.info("✓ Direct TTS test completed successfully")
    else:
        logger.error("✗ Direct TTS test failed") 