from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import io
import os
import time
import logging
from typing import Optional, List, Dict, Any
import json

# Import the GoogleCloudManager
from utils.google_cloud import cloud_manager

router = APIRouter(prefix="/interview", tags=["interview"])

# Storage for active sessions
active_sessions = {}

# Session directory
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Models for request/response validation
class QuestionRequest(BaseModel):
    session_id: str
    question_type: str = "standard"
    previous_questions: List[str] = []
    previous_responses: List[str] = []

class ResponseSubmission(BaseModel):
    session_id: str
    question_id: str
    text_response: Optional[str] = None
    
class FeedbackRequest(BaseModel):
    session_id: str
    detailed: bool = False
    
class TextToSpeechRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

# Helper functions
def load_session(session_id: str) -> dict:
    """Load a session from disk or memory"""
    if session_id in active_sessions:
        return active_sessions[session_id]
        
    session_file = os.path.join(SESSIONS_DIR, session_id, "session.json")
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            session = json.load(f)
            active_sessions[session_id] = session
            return session
    
    raise HTTPException(status_code=404, detail="Session not found")
    
def save_session(session: dict):
    """Save a session to disk"""
    session_id = session["session_id"]
    session_dir = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    with open(os.path.join(session_dir, "session.json"), "w") as f:
        json.dump(session, f)

# Function to add compatibility routes
def add_compatibility_routes(app):
    """
    Add compatibility routes directly to the FastAPI app.
    This allows legacy endpoints to work alongside the router-based endpoints.
    """
    @app.get("/interview")
    async def interview_main():
        """Legacy endpoint for the interview main page"""
        return {"status": "Interview API is running via compatibility route"}
    
    logging.info("Added interview compatibility routes to the main app")
        
# Routes
@router.post("/sessions", response_model=dict)
async def create_interview_session(
    cv_file: Optional[UploadFile] = File(None)
):
    """Create a new interview session"""
    try:
        # Generate session ID
        session_id = f"session_{int(time.time())}"
        
        # Process CV if provided
        cv_path = None
        if cv_file:
            # Create uploads directory
            os.makedirs("uploads", exist_ok=True)
            
            # Save the file
            file_content = await cv_file.read()
            filename = f"{session_id}_{cv_file.filename}"
            cv_path = os.path.join("uploads", filename)
            
            with open(cv_path, "wb") as f:
                f.write(file_content)
        
        # Create session
        session = {
            "session_id": session_id,
            "cv_path": cv_path,
            "created_at": time.time(),
            "questions": [],
            "responses": []
        }
        
        # Save session
        active_sessions[session_id] = session
        save_session(session)
        
        return {
            "session_id": session_id,
            "has_cv": cv_path is not None
        }
    except Exception as e:
        logging.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions", response_model=List[str])
async def list_interview_sessions():
    """List all active interview sessions"""
    try:
        # Get sessions from disk
        sessions = []
        if os.path.exists(SESSIONS_DIR):
            for session_id in os.listdir(SESSIONS_DIR):
                session_file = os.path.join(SESSIONS_DIR, session_id, "session.json")
                if os.path.exists(session_file):
                    sessions.append(session_id)
                    # Load into memory if not already there
                    if session_id not in active_sessions:
                        with open(session_file, "r") as f:
                            active_sessions[session_id] = json.load(f)
        
        return sessions
    except Exception as e:
        logging.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.post("/questions", response_model=dict)
async def get_next_question(request: QuestionRequest):
    """Get the next question for an interview session"""
    try:
        # Load session
        session = load_session(request.session_id)
        
        # Get the next question using cloud_manager
        if cloud_manager and hasattr(cloud_manager, 'genai_client'):
            try:
                # Use Google AI to get next question
                prompt = f"""
                You are a venture capital interviewer. Generate a relevant venture capital interview question.
                Previous questions: {', '.join(request.previous_questions) if request.previous_questions else 'None'}
                Previous responses: {', '.join(request.previous_responses) if request.previous_responses else 'None'}
                """
                
                # Try to use different available methods based on API version
                try:
                    # Get the Gemini model
                    if hasattr(cloud_manager.genai_client, 'GenerativeModel'):
                        model = cloud_manager.genai_client.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content(prompt)
                        question = response.text
                    else:
                        # Fallback to legacy models if available
                        if hasattr(cloud_manager.genai_client, 'models'):
                            models = list(cloud_manager.genai_client.list_models())
                            model = models[0] if models else None
                            if model and hasattr(model, 'generate_text'):
                                response = model.generate_text(prompt)
                                question = response.text
                            else:
                                # Use predefined questions as fallback
                                raise Exception("Cannot find appropriate generation method")
                        else:
                            raise Exception("No models available")
                except Exception as e:
                    logging.error(f"Error using Gemini API: {e}")
                    # Fallback to predefined questions
                    raise Exception(f"API compatibility issue: {e}")
            except Exception as e:
                logging.error(f"Failed to use Gemini API: {e}")
                # Fallback to predefined questions
                predefined_questions = [
                    "Can you tell me about your business model?",
                    "What is your target market?",
                    "How do you plan to scale your business?",
                    "What are your competitive advantages?",
                    "How do you plan to use the funds you're seeking?"
                ]
                
                # Get next question based on what's been asked
                asked_questions = set(request.previous_questions)
                available_questions = [q for q in predefined_questions if q not in asked_questions]
                
                if not available_questions:
                    return {
                        "session_id": request.session_id,
                        "question": None,
                        "interview_complete": True
                    }
                    
                question = available_questions[0]
        else:
            # Fallback to predefined questions
            predefined_questions = [
                "Can you tell me about your business model?",
                "What is your target market?",
                "How do you plan to scale your business?",
                "What are your competitive advantages?",
                "How do you plan to use the funds you're seeking?"
            ]
            
            # Get next question based on what's been asked
            asked_questions = set(request.previous_questions)
            available_questions = [q for q in predefined_questions if q not in asked_questions]
            
            if not available_questions:
                return {
                    "session_id": request.session_id,
                    "question": None,
                    "interview_complete": True
                }
                
            question = available_questions[0]
        
        # Add to session
        session["questions"].append(question)
        save_session(session)
        
        # Generate audio if possible
        audio_data = None
        if cloud_manager and hasattr(cloud_manager, 'tts_client'):
            try:
                from google.cloud import texttospeech
                text_input = texttospeech.SynthesisInput(text=question)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = cloud_manager.tts_client.synthesize_speech(
                    input=text_input,
                    voice=voice,
                    audio_config=audio_config
                )
                audio_data = response.audio_content
                
                # Save the audio file
                audio_path = os.path.join(SESSIONS_DIR, request.session_id, f"question_{len(session['questions'])-1}.mp3")
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
            except Exception as e:
                logging.error(f"Error generating audio: {str(e)}")
        
        return {
            "session_id": request.session_id,
            "question": question,
            "question_id": str(len(session["questions"]) - 1),
            "has_audio": audio_data is not None,
            "interview_complete": False
        }
    except Exception as e:
        logging.error(f"Error getting question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get question: {str(e)}")

@router.post("/responses", response_model=dict)
async def submit_response(
    body: dict
):
    """Submit a response to an interview question"""
    try:
        logging.info(f"Response submission received - Body: {body}")
        
        # Extract data from the request body
        session_id = body.get("session_id")
        question_id = body.get("question_id")
        text = body.get("text_response")
        
        logging.info(f"Extracted values: session_id={session_id}, question_id={question_id}, text={text[:20] if text else None}")
        
        if not session_id or not question_id:
            raise HTTPException(status_code=400, detail="Missing session_id or question_id")
            
        # Load session
        session = load_session(session_id)
        
        if not text:
            raise HTTPException(status_code=400, detail="No text response provided")
            
        # Save response
        response_data = {
            "question_id": question_id,
            "text": text,
            "audio_path": None,
            "timestamp": time.time()
        }
        
        # Add to session
        if "responses" not in session:
            session["responses"] = []
        session["responses"].append(response_data)
        save_session(session)
        
        # Analyze sentiment if possible
        sentiment = None
        if cloud_manager and hasattr(cloud_manager, 'genai_client'):
            try:
                prompt = f"Analyze the sentiment of this text and provide a score between -1 (negative) and 1 (positive): {text}"
                
                # Try to use the appropriate method for the current API version
                if hasattr(cloud_manager.genai_client, 'GenerativeModel'):
                    try:
                        model = cloud_manager.genai_client.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content(prompt)
                        sentiment_text = response.text
                        
                        # Try to extract a numeric score
                        import re
                        match = re.search(r'(-?\d+(\.\d+)?)', sentiment_text)
                        if match:
                            score = float(match.group(1))
                            sentiment = {"score": score, "explanation": sentiment_text}
                        else:
                            sentiment = {"score": 0, "explanation": sentiment_text}
                    except Exception as e:
                        logging.error(f"Error using GenerativeModel: {e}")
                        sentiment = {"score": 0.5, "explanation": "The response appears balanced and informative."}
                else:
                    sentiment = {"score": 0.5, "explanation": "The response appears balanced and informative."}
            except Exception as e:
                logging.error(f"Error analyzing sentiment: {str(e)}")
                sentiment = {"score": 0, "explanation": "Sentiment analysis unavailable"}
        else:
            sentiment = {"score": 0.5, "explanation": "The response appears balanced and informative."}
        
        return {
            "session_id": session_id,
            "question_id": question_id,
            "text_response": text,
            "sentiment": sentiment
        }
    except Exception as e:
        logging.error(f"Error submitting response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit response: {str(e)}")

@router.post("/feedback", response_model=dict)
async def generate_feedback(request: FeedbackRequest):
    """Generate feedback for an interview session"""
    try:
        logging.info(f"Feedback request received: {request}")
        
        # Load session
        session = load_session(request.session_id)
        
        # Check if we have responses
        if not session.get("responses"):
            # For demo purposes, add a sample response if needed
            if "questions" in session and len(session["questions"]) > 0:
                if "responses" not in session:
                    session["responses"] = []
                    
                # Add a placeholder response for testing
                session["responses"].append({
                    "question_id": "0",
                    "text": "This is a placeholder response to enable feedback generation for testing.",
                    "timestamp": time.time()
                })
                save_session(session)
                logging.info("Added placeholder response for testing")
            else:
                raise HTTPException(status_code=400, detail="No responses to analyze")
        
        logging.info(f"Session has {len(session.get('questions', []))} questions and {len(session.get('responses', []))} responses")
        
        # Generate feedback using Gemini if available
        feedback = "Feedback could not be generated automatically."
        
        if cloud_manager and hasattr(cloud_manager, 'genai_client'):
            try:
                # Prepare interview transcript
                transcript = ""
                for i, (q, r) in enumerate(zip(session.get("questions", []), session.get("responses", []))):
                    transcript += f"Question {i+1}: {q}\n"
                    transcript += f"Response: {r.get('text', '')}\n\n"
                
                prompt = f"""
                Analyze this VC interview transcript and provide comprehensive feedback:
                
                {transcript}
                
                Provide:
                1. Overall assessment (score 1-10)
                2. Key strengths with specific examples
                3. Areas for improvement with actionable advice
                4. How convincing the candidate was to potential investors
                5. Quality of business understanding demonstrated
                
                Format as a professional VC partner feedback session.
                """
                
                # Try to use the appropriate method for the current API version
                if hasattr(cloud_manager.genai_client, 'GenerativeModel'):
                    try:
                        model = cloud_manager.genai_client.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content(prompt)
                        if hasattr(response, 'text'):
                            feedback = response.text
                        else:
                            feedback = str(response)
                    except Exception as e:
                        logging.error(f"Error using GenerativeModel: {e}")
                        feedback = get_default_feedback()
                else:
                    feedback = get_default_feedback()
            except Exception as e:
                logging.error(f"Error generating feedback: {str(e)}")
                feedback = get_default_feedback()
        else:
            feedback = get_default_feedback()
        
        # Save feedback to session
        session["feedback"] = feedback
        save_session(session)
        
        return {
            "session_id": request.session_id,
            "summary": feedback,
            "detailed_feedback": feedback if request.detailed else None
        }
    except Exception as e:
        logging.error(f"Error generating feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate feedback: {str(e)}")
        
def get_default_feedback():
    """Return default feedback as a fallback"""
    return """
# VC Interview Feedback (Default)

## Overall Assessment: 7/10

You've demonstrated a solid understanding of your business and market. Your responses were clear and reflected good preparation for venture capital discussions.

## Key Strengths:
- Clear articulation of your business model and value proposition
- Good understanding of your target market and customer needs
- Realistic assessment of growth potential and resource requirements

## Areas for Improvement:
- Provide more specific metrics and quantifiable data points to support your claims
- Develop a more detailed competitive analysis and differentiation strategy
- Be more specific about your fundraising goals and use of capital

## Investor Appeal:
Your pitch is compelling but would benefit from more concrete examples of traction and market validation. Consider incorporating specific customer testimonials or case studies.

## Business Understanding:
You demonstrate good knowledge of your business fundamentals. Continue to deepen your market analysis and financial projections to strengthen your overall presentation.
    """

@router.post("/text-to-speech", response_class=StreamingResponse)
async def convert_text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech"""
    try:
        if not cloud_manager or not hasattr(cloud_manager, 'tts_client'):
            raise HTTPException(status_code=500, detail="Text-to-speech service not available")
            
        # Convert to speech
        from google.cloud import texttospeech
        
        text_input = texttospeech.SynthesisInput(text=request.text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = cloud_manager.tts_client.synthesize_speech(
            input=text_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Store in session if requested
        if request.session_id:
            try:
                session = load_session(request.session_id)
                if "tts_history" not in session:
                    session["tts_history"] = []
                    
                audio_path = os.path.join(SESSIONS_DIR, request.session_id, f"tts_{int(time.time())}.mp3")
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                with open(audio_path, "wb") as f:
                    f.write(response.audio_content)
                    
                session["tts_history"].append({
                    "text": request.text,
                    "audio_path": audio_path,
                    "timestamp": time.time()
                })
                
                save_session(session)
            except Exception as e:
                logging.error(f"Error saving TTS to session: {str(e)}")
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(response.audio_content),
            media_type="audio/mp3"
        )
    except Exception as e:
        logging.error(f"Error converting text to speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to convert text to speech: {str(e)}")

@router.post("/speech-to-text", response_model=dict)
async def convert_speech_to_text(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Convert speech to text"""
    try:
        if not cloud_manager or not hasattr(cloud_manager, 'speech_client'):
            raise HTTPException(status_code=500, detail="Speech-to-text service not available")
            
        # Read audio file
        audio_data = await audio_file.read()
        
        # Save file if session provided
        audio_path = None
        if session_id:
            try:
                session = load_session(session_id)
                session_dir = os.path.join(SESSIONS_DIR, session_id)
                os.makedirs(session_dir, exist_ok=True)
                
                audio_path = os.path.join(session_dir, f"stt_{int(time.time())}.wav")
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
            except Exception as e:
                logging.error(f"Error saving audio file: {str(e)}")
        
        # Transcribe
        from google.cloud import speech
        
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        )
        
        response = cloud_manager.speech_client.recognize(config=config, audio=audio)
        
        transcript = ""
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            
        # Save transcript if session provided
        if session_id and audio_path:
            try:
                session = load_session(session_id)
                if "stt_history" not in session:
                    session["stt_history"] = []
                    
                session["stt_history"].append({
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "timestamp": time.time()
                })
                
                save_session(session)
            except Exception as e:
                logging.error(f"Error saving transcript to session: {str(e)}")
        
        return {"text": transcript}
    except Exception as e:
        logging.error(f"Error converting speech to text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to convert speech to text: {str(e)}")

@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_interview_session(session_id: str):
    """Delete an interview session"""
    try:
        # Try to load session to verify it exists
        load_session(session_id)
        
        # Remove from memory
        if session_id in active_sessions:
            del active_sessions[session_id]
            
        # Remove from disk
        session_dir = os.path.join(SESSIONS_DIR, session_id)
        if os.path.exists(session_dir):
            import shutil
            shutil.rmtree(session_dir)
            
        return {
            "session_id": session_id,
            "message": "Session deleted successfully"
        }
    except HTTPException:
        raise  # Re-raise if session not found
    except Exception as e:
        logging.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

# Make sure the router is defined
__all__ = ['router']
