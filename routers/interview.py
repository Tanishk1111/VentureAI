from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import io
import os
from typing import Optional, List

from models.schemas import (
    InterviewSession, 
    QuestionRequest, 
    ResponseSubmission, 
    FeedbackRequest, 
    FeedbackResponse,
    TextToSpeechRequest,
    SpeechToTextRequest
)
from services import interview_service, cv_service, speech_service, analysis_service
from utils import audio_utils

router = APIRouter(prefix="/interview", tags=["interview"])

# Helper function to get interview information
async def get_interview_info():
    """Get basic information about the interview functionality"""
    return {
        "status": "available",
        "endpoints": ["/sessions", "/questions", "/responses", "/feedback"],
        "documentation": "See /docs for full API documentation"
    }

# Root endpoint for interview module
@router.get("/", response_model=dict)
async def interview_root():
    """Get information about the interview API"""
    return await get_interview_info()

@router.post("/sessions", response_model=dict)
async def create_interview_session(
    cv_file: Optional[UploadFile] = File(None)
):
    """Create a new interview session"""
    cv_path = None
    
    # Process CV if provided
    if cv_file:
        file_content = await cv_file.read()
        cv_path = cv_service.save_uploaded_cv(file_content, cv_file.filename)
    
    # Create session
    session = interview_service.create_session(cv_path)
    
    return {
        "session_id": session.session_id,
        "has_cv": cv_path is not None,
        "cv_questions_count": len(session.cv_questions) if hasattr(session, "cv_questions") else 0
    }

@router.get("/sessions", response_model=List[str])
async def list_interview_sessions():
    """List all active interview sessions"""
    return interview_service.list_sessions()

@router.get("/sessions/{session_id}", response_model=dict)
async def get_session_details(session_id: str):
    """Get details for a specific interview session"""
    session = interview_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    transcript = session.get_full_transcript()
    
    return {
        "session_id": session_id,
        "transcript": transcript,
        "has_cv": session.cv_path is not None,
        "cv_questions": session.cv_questions
    }

@router.post("/questions", response_model=dict)
async def get_next_question(request: QuestionRequest):
    """Get the next question for an interview session"""
    session = interview_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    question = session.get_next_question(
        previous_questions=request.previous_questions,
        previous_responses=request.previous_responses
    )
    
    if not question:
        return {
            "session_id": request.session_id,
            "question": None,
            "interview_complete": True
        }
    
    # Convert question to audio
    audio_data = speech_service.text_to_speech(question)
    
    # Record the question in the session
    session.record_interaction("interviewer", question, audio_data)
    
    return {
        "session_id": request.session_id,
        "question": question,
        "question_id": str(len(session.transcript) - 1),
        "interview_complete": False
    }

@router.post("/responses", response_model=dict)
async def submit_response(
    background_tasks: BackgroundTasks,
    response_data: Optional[ResponseSubmission] = None,
    audio_file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
    question_id: Optional[str] = Form(None),
    text_response: Optional[str] = Form(None)
):
    """Submit a response to an interview question"""
    print(f"Form data - session_id: {session_id}, question_id: {question_id}")
    print(f"JSON data: {response_data}")
    
    # Extract data from either JSON body or form data
    actual_session_id = None
    actual_question_id = None
    actual_text_response = None
    actual_audio_data = None
    
    # If using JSON request body
    if response_data:
        print(f"Using JSON data: {response_data}")
        actual_session_id = response_data.session_id
        actual_question_id = response_data.question_id
        if response_data.text_response:
            actual_text_response = response_data.text_response
        if response_data.audio_data:
            actual_audio_data = response_data.audio_data
    # If using form data
    else:
        print(f"Using form data")
        actual_session_id = session_id
        actual_question_id = question_id
        actual_text_response = text_response
    
    print(f"Processed data - session_id: {actual_session_id}, question_id: {actual_question_id}")
    
    if not actual_session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    if not actual_question_id:
        raise HTTPException(status_code=400, detail="Missing question_id")
    
    # Get the session
    session = interview_service.get_session(actual_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Process audio file if provided
    if audio_file:
        actual_audio_data = await audio_file.read()
        # Transcribe the audio
        actual_text_response = speech_service.speech_to_text(actual_audio_data)
    elif actual_audio_data:
        # Transcribe the audio from JSON request
        actual_text_response = speech_service.speech_to_text(actual_audio_data)
    elif not actual_text_response:
        raise HTTPException(status_code=400, detail="No response provided")
    
    # Record the response in the session
    session.record_interaction("candidate", actual_text_response, actual_audio_data)
    
    # Analyze sentiment
    sentiment = analysis_service.analyze_sentiment(actual_text_response)
    
    need_follow_up = sentiment["score"] < -0.3
    
    response_data = {
        "session_id": actual_session_id,
        "question_id": actual_question_id,
        "text_response": actual_text_response,
        "sentiment": sentiment,
        "need_follow_up": need_follow_up
    }
    
    if need_follow_up:
        follow_up_text = "I notice you seem concerned about this topic. Would you like to elaborate further?"
        follow_up_audio = speech_service.text_to_speech(follow_up_text)
        session.record_interaction("interviewer", follow_up_text, follow_up_audio)
        response_data["follow_up"] = {
            "text": follow_up_text,
            "follow_up_id": str(len(session.transcript) - 1)
        }
    
    return response_data

@router.post("/feedback", response_model=FeedbackResponse)
async def generate_feedback(request: FeedbackRequest):
    """Generate feedback for an interview session"""
    session = interview_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    feedback_data = analysis_service.generate_interview_feedback(session)
    
    response = FeedbackResponse(
        session_id=request.session_id,
        summary=feedback_data["feedback"],
        detailed_feedback=feedback_data["feedback"] if request.detailed else None
    )
    
    # Generate audio version of the feedback
    audio_data = speech_service.text_to_speech(
        "Here's my feedback on your interview performance. " + feedback_data["feedback"][:500]
    )
    
    # Record the feedback in the session
    session.record_interaction("interviewer", feedback_data["feedback"], audio_data)
    
    return response

@router.post("/text-to-speech", response_class=StreamingResponse)
async def convert_text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech"""
    audio_data = speech_service.text_to_speech(request.text)
    
    # If session ID provided, record in session
    if request.session_id:
        session = interview_service.get_session(request.session_id)
        if session:
            session.record_interaction("system", request.text, audio_data)
    
    # Return audio as streaming response
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav"
    )

@router.get("/text-to-speech", response_class=StreamingResponse)
async def get_text_to_speech(text: str, session_id: Optional[str] = None):
    """Convert text to speech (GET endpoint)"""
    audio_data = speech_service.text_to_speech(text)
    
    # If session ID provided, record in session
    if session_id:
        session = interview_service.get_session(session_id)
        if session:
            session.record_interaction("system", text, audio_data)
    
    # Return audio as streaming response
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/wav"
    )

@router.post("/speech-to-text", response_model=dict)
async def convert_speech_to_text(
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Convert speech to text"""
    audio_data = await audio_file.read()
    text = speech_service.speech_to_text(audio_data)
    
    # If session ID provided, record in session
    if session_id:
        session = interview_service.get_session(session_id)
        if session:
            session.record_interaction("system", text, audio_data)
    
    return {"text": text}

@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_interview_session(session_id: str):
    """Delete an interview session"""
    success = interview_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully", "session_id": session_id}

# Add aliases for client compatibility - these will be added to the main app
def add_compatibility_routes(app):
    """Add compatibility routes for clients using different endpoint patterns"""
    
    @app.get("/api/interview/info", tags=["interview-compat"])
    async def api_interview_info():
        """Get information about the interview API (compatibility endpoint)"""
        return await get_interview_info()
    
    @app.post("/interview/sessions", tags=["interview-compat"])
    async def create_interview_session_compat(cv_file: Optional[UploadFile] = File(None)):
        """Create a new interview session (compatibility endpoint)"""
        return await create_interview_session(cv_file)
    
    @app.get("/interview/sessions", tags=["interview-compat"])
    async def list_interview_sessions_compat():
        """List all active interview sessions (compatibility endpoint)"""
        return await list_interview_sessions()
    
    @app.get("/interview/sessions/{session_id}", tags=["interview-compat"])
    async def get_session_details_compat(session_id: str):
        """Get details for a specific interview session (compatibility endpoint)"""
        return await get_session_details(session_id)
    
    @app.post("/interview/questions", tags=["interview-compat"])
    async def get_next_question_compat(request: QuestionRequest):
        """Get the next question for an interview session (compatibility endpoint)"""
        return await get_next_question(request)
    
    @app.post("/interview/responses", tags=["interview-compat"])
    async def submit_response_compat(
        background_tasks: BackgroundTasks,
        response_data: Optional[ResponseSubmission] = None,
        audio_file: Optional[UploadFile] = File(None),
        session_id: Optional[str] = Form(None),
        question_id: Optional[str] = Form(None),
        text_response: Optional[str] = Form(None)
    ):
        """Submit a response to an interview question (compatibility endpoint)"""
        return await submit_response(background_tasks, response_data, audio_file, session_id, question_id, text_response)
    
    @app.post("/interview/feedback", tags=["interview-compat"])
    async def generate_feedback_compat(request: FeedbackRequest):
        """Generate feedback for an interview session (compatibility endpoint)"""
        return await generate_feedback(request)
