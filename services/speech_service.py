import os
import io
from google.cloud import texttospeech as tts
from google.cloud import speech
from config import settings
import logging
import tempfile
import time
import base64
import traceback

logger = logging.getLogger(__name__)

# Initialize clients
tts_client = tts.TextToSpeechClient()
speech_client = speech.SpeechClient()

# Enhanced Audio configuration for Text-to-Speech
voice = tts.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Studio-O",  # Using Studio voice for more natural sound
)

audio_config = tts.AudioConfig(
    audio_encoding=tts.AudioEncoding.LINEAR16,
    speaking_rate=0.97,  # Slightly slower for clarity
    pitch=0.0,
    volume_gain_db=1.0,
    effects_profile_id=["large-home-entertainment-class-device"],  # Better audio quality
    sample_rate_hertz=24000,  # Higher sample rate for better quality
)

def format_text_as_ssml(text):
    """Format text with SSML tags for better speech synthesis"""
    # Filter unwanted words
    unwanted_words = ['asterisk', '*']
    for word in unwanted_words:
        text = text.replace(word, '')
    
    # Handle basic formatting
    text = text.replace('\n\n', '<break time="750ms"/>')
    text = text.replace('\n', '<break time="500ms"/>')
    
    # Emphasize questions
    if text.endswith('?'):
        text = text.replace('?', '<break time="200ms"/>?')
    
    # Format important business terms for emphasis
    business_terms = ['ROI', 'CAC', 'LTV', 'market fit', 'valuation', 'runway', 'burn rate']
    for term in business_terms:
        if term.lower() in text.lower():
            # Use case-insensitive replacement while preserving case
            index = text.lower().find(term.lower())
            actual_term = text[index:index+len(term)]
            text = text.replace(actual_term, f'<emphasis level="moderate">{actual_term}</emphasis>')
    
    # Wrap in speak tags
    ssml = f'<speak>{text}</speak>'
    return ssml

def text_to_speech(text, voice_name="en-US-Studio-O"):
    """
    Convert text to speech using Google Cloud Text-to-Speech API
    Returns raw audio bytes in WAV format
    """
    try:
        # Try to get the client from our cloud manager
        try:
            from utils.google_cloud import cloud_manager
            client = cloud_manager.get_tts_client()
            
            if client is None:
                logger.warning("TTS client not available, using fallback mechanism")
                return generate_fallback_tts(text)
        except Exception as e:
            logger.error(f"Error getting TTS client: {e}")
            return generate_fallback_tts(text)
        
        # Construct the synthesis input
        synthesis_input = tts.SynthesisInput(text=text)
        
        # Configure voice parameters
        voice = tts.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name,
        )
        
        # Select the audio encoding
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,  # WAV format
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0,
            sample_rate_hertz=24000,
        )
        
        # Perform the API call
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content
        
    except Exception as e:
        logger.error(f"Error in text_to_speech: {e}")
        logger.error(traceback.format_exc())
        return generate_fallback_tts(text)

def speech_to_text(audio_data, language_code="en-US", model="latest_long"):
    """
    Convert speech to text using Google Cloud Speech-to-Text API
    """
    try:
        # Try to get the client from our cloud manager
        try:
            from utils.google_cloud import cloud_manager
            client = cloud_manager.get_stt_client()
            
            if client is None:
                logger.warning("STT client not available, using fallback mechanism")
                return generate_fallback_stt(audio_data)
        except Exception as e:
            logger.error(f"Error getting STT client: {e}")
            return generate_fallback_stt(audio_data)
        
        # Configure audio and recognition parameters
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            model=model,
            enable_automatic_punctuation=True
        )
        
        # Perform the API call
        response = client.recognize(config=config, audio=audio)
        
        # Extract and return the transcription
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        if not transcript:
            logger.warning("No transcript returned from Speech-to-Text")
            transcript = generate_fallback_stt(audio_data)
            
        return transcript
        
    except Exception as e:
        logger.error(f"Error in speech_to_text: {e}")
        logger.error(traceback.format_exc())
        return generate_fallback_stt(audio_data)

def generate_fallback_tts(text):
    """
    Generate a fallback TTS response when the service is unavailable
    """
    logger.info("Using fallback TTS mechanism")
    
    # In a real system, you might use a local TTS library here
    # For now, we'll just create a simple WAV file with silence
    
    # Create an empty WAV file with the right header (8 kHz, 16-bit, mono)
    sample_rate = 8000
    duration = 1.0  # 1 second of silence
    num_samples = int(sample_rate * duration)
    
    buffer = io.BytesIO()
    
    # WAV header
    buffer.write(b'RIFF')
    buffer.write((36 + num_samples * 2).to_bytes(4, 'little'))  # File size
    buffer.write(b'WAVE')
    buffer.write(b'fmt ')
    buffer.write((16).to_bytes(4, 'little'))  # Format chunk size
    buffer.write((1).to_bytes(2, 'little'))  # Format type (PCM)
    buffer.write((1).to_bytes(2, 'little'))  # Number of channels
    buffer.write((sample_rate).to_bytes(4, 'little'))  # Sample rate
    buffer.write((sample_rate * 2).to_bytes(4, 'little'))  # Byte rate
    buffer.write((2).to_bytes(2, 'little'))  # Block align
    buffer.write((16).to_bytes(2, 'little'))  # Bits per sample
    buffer.write(b'data')
    buffer.write((num_samples * 2).to_bytes(4, 'little'))  # Data chunk size
    
    # Write silence (all zeros)
    for _ in range(num_samples):
        buffer.write((0).to_bytes(2, 'little'))
    
    # Return the WAV file as bytes
    buffer.seek(0)
    return buffer.read()

def generate_fallback_stt(audio_data):
    """
    Generate a fallback STT response when the service is unavailable
    """
    logger.info("Using fallback STT mechanism")
    
    # In a real system, you might use a local STT library here
    # For now, just return a placeholder message
    return "[Speech recognition unavailable. Please try again later.]"
