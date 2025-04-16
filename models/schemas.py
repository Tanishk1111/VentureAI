from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CVUpload(BaseModel):
    file_content: bytes
    filename: str

class QuestionRequest(BaseModel):
    session_id: str
    question_type: str = "standard"  # "standard" or "cv_based"
    previous_questions: List[str] = []
    previous_responses: List[str] = []

class ResponseSubmission(BaseModel):
    session_id: str
    question_id: str
    audio_data: Optional[bytes] = None
    text_response: Optional[str] = None

class InterviewSession(BaseModel):
    session_id: str
    cv_path: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    questions_asked: List[str] = []
    responses: List[Dict[str, Any]] = []

class FeedbackRequest(BaseModel):
    session_id: str
    detailed: bool = False

class FeedbackResponse(BaseModel):
    session_id: str
    summary: str
    detailed_feedback: Optional[str] = None
    score: Optional[float] = None

class TextToSpeechRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class SpeechToTextRequest(BaseModel):
    audio_data: bytes
    session_id: Optional[str] = None
