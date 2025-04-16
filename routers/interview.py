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
    request: ResponseSubmission = None,
    audio_file: UploadFile = File(None),
    session_id: str = Form(...),
    question_id: str = Form(...)
):
    """Submit a response to an interview question"""
    session = interview_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    audio_data = None
    text_response = None
    
    # Process audio file if provided
    if audio_file:
        audio_data = await audio_file.read()
        # Transcribe the audio
        text_response = speech_service.speech_to_text(audio_data)
    elif request and request.audio_data:
        audio_data = request.audio_data
        # Transcribe the audio
        text_response = speech_service.speech_to_text(audio_data)
    elif request and request.text_response:
        text_response = request.text_response
    else:
        raise HTTPException(status_code=400, detail="No response provided")
    
    # Record the response in the session
    session.record_interaction("candidate", text_response, audio_data)
    
    # Analyze sentiment
    sentiment = analysis_service.analyze_sentiment(text_response)
    
    need_follow_up = sentiment["score"] < -0.3
    
    response_data = {
        "session_id": session_id,
        "question_id": question_id,
        "text_response": text_response,
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
