"""
Super simple TTS generator - minimal version that should always work
"""

import os
from google.cloud import texttospeech

def main():
    print("Creating the TTS client...")
    client = texttospeech.TextToSpeechClient()
    
    print("Setting up a basic voice...")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C"  # Using a standard voice that should always work
    )
    
    print("Configuring audio settings...")
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0  # Neutral pitch
    )
    
    print("Setting up text...")
    text = "This is a super simple test of text to speech. If you can hear this, it means the basic TTS functionality is working properly."
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    print("Generating speech...")
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    print(f"Received {len(response.audio_content)} bytes of audio data")
    
    # Save the audio
    output_file = "super_simple.mp3"
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        
    print(f"Saved audio to {output_file}")
    print(f"File size: {os.path.getsize(output_file)/1024:.2f} KB")
    print("To play the file, open it in your browser or media player.")

if __name__ == "__main__":
    print("Starting super simple TTS test...")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"Using credentials from: {creds_path}")
        print(f"Credentials file exists: {os.path.exists(creds_path)}")
    else:
        print("WARNING: GOOGLE_APPLICATION_CREDENTIALS not set!")
    
    try:
        main()
        print("SUCCESS! TTS generation completed.")
    except Exception as e:
        print(f"ERROR: {e}")
        print("Please check your Google Cloud credentials and try again.") 