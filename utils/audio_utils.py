import io
import wave
import pyaudio
import threading
from config import settings

def create_audio_stream():
    """Create and return a PyAudio stream for recording"""
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=settings.AUDIO_FORMAT,
        channels=settings.CHANNELS,
        rate=settings.RATE,
        input=True,
        frames_per_buffer=settings.CHUNK
    )
    return audio, stream

def record_audio_chunk(audio, stream, duration=5):
    """Record audio for a specified duration and return as bytes"""
    frames = []
    for _ in range(0, int(settings.RATE / settings.CHUNK * duration)):
        data = stream.read(settings.CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    # Convert frames to bytes
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(settings.CHANNELS)
        wf.setsampwidth(audio.get_sample_size(settings.AUDIO_FORMAT))
        wf.setframerate(settings.RATE)
        wf.writeframes(b''.join(frames))
    
    return buffer.getvalue()

def save_audio_file(audio_data, filename):
    """Save audio data to a WAV file"""
    with open(filename, 'wb') as f:
        f.write(audio_data)
    return filename

def wav_to_bytes(wav_file):
    """Read a WAV file and return its contents as bytes"""
    with open(wav_file, 'rb') as f:
        return f.read()
