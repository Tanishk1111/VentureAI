# VentureAI

A venture capital interview assistant built with FastAPI, Google Cloud, and HTML/JS.

## Features

- API for venture capital interview questions
- Text-to-Speech with Google Cloud Chirp 3 HD voices
- Speech-to-Text capabilities
- Simple web UI for testing

## Setup

1. Ensure you have Python 3.8+ installed
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Google Cloud credentials:
   - Create a service account with access to Text-to-Speech, Speech-to-Text, and Generative AI
   - Download credentials JSON file
   - Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json`

## Running the API

Start the API server:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## TTS Testing

For TTS testing, we have several options:

1. **Super Simple TTS** - Generate a local MP3 file:

   ```bash
   python super_simple_tts.py
   ```

   Then open `super_simple.html` in your browser

2. **Flask TTS Server** - Start a standalone TTS server:
   ```bash
   python minimal_tts_server.py
   ```
   In another terminal, start an HTTP server:
   ```bash
   python -m http.server 8000
   ```
   Then open `http://localhost:8000/flask_tts_test.html` in your browser

## Notes on Google Cloud TTS

- The API supports Google's newest Chirp 3 HD voices
- For Chirp3-HD voices, pitch parameter and SSML must be disabled
- Other voices (Studio, Neural2, etc.) work with pitch and SSML
- Credentials must have access to the Cloud Text-to-Speech API

## Troubleshooting

If TTS is not working:

1. Check that `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
2. Verify that the credentials JSON file exists and is readable
3. Ensure the service account has TTS API access
4. For Chirp3-HD voices, try without pitch parameters
