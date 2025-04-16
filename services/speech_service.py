import os
import io
from google.cloud import texttospeech as tts
from google.cloud import speech
from config import settings

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

def text_to_speech(text):
    """Convert text to speech with enhanced voices and SSML"""
    try:
        # Format text as SSML for better speech quality
        ssml = format_text_as_ssml(text)
        synthesis_input = tts.SynthesisInput(ssml=ssml)
        
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        # Fallback to basic TTS without SSML
        synthesis_input = tts.SynthesisInput(text=text)
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content

def speech_to_text(audio_data):
    """Transcribe audio using Google Speech-to-Text with enhanced configuration"""
    audio = speech.RecognitionAudio(content=audio_data)
    
    # Check if this is a WEBM file (from browser recording)
    is_webm = False
    try:
        # Check for WEBM header signature
        if audio_data[:4] == b'\x1a\x45\xdf\xa3' or b'webm' in audio_data[:50]:
            is_webm = True
    except:
        pass
    
    # Add industry-specific phrases to improve recognition accuracy
    speech_contexts = speech.SpeechContext(
        phrases=[
            "venture capital", "startup", "funding", "investment",
            "MVP", "product market fit", "acquisition", "ROI", "CAC", 
            "LTV", "churn", "valuation", "runway", "burn rate",
            "user acquisition", "monetization", "scaling", "series A",
            "angel investor", "pitch deck", "business model"
        ]
    )
    
    if is_webm:
        # For browser-recorded audio (typically WEBM format at 48000 Hz)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
            use_enhanced=True,
            speech_contexts=[speech_contexts],
            enable_speaker_diarization=False,
            diarization_speaker_count=1,
            profanity_filter=False
        )
    else:
        # For regular audio (e.g., wav files)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=settings.RATE,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
            use_enhanced=True,
            speech_contexts=[speech_contexts],
            enable_speaker_diarization=False,
            diarization_speaker_count=1,
            profanity_filter=False
        )
    
    try:
        response = speech_client.recognize(config=config, audio=audio)
        
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        return transcript
    except Exception as e:
        print(f"Speech recognition error: {str(e)}")
        return "Error transcribing audio. Please try again."
