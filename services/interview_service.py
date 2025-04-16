import os
import json
import time
import pandas as pd
from datetime import datetime
from config import settings
from utils.gemini_utils import generate_content

class InterviewSession:
    def __init__(self, session_id=None, cv_path=None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.session_dir = os.path.join(settings.SESSION_DIR, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.cv_path = cv_path
        self.transcript = []
        self.questions_df = self._load_questions()
        self.cv_questions = []
        
        # If CV provided, generate CV-based questions
        if cv_path:
            from services.cv_service import extract_text_from_cv, generate_cv_questions
            cv_text = extract_text_from_cv(cv_path)
            if cv_text:
                self.cv_questions = generate_cv_questions(cv_text)
    
    def _load_questions(self):
        """Load interview questions from CSV"""
        try:
            return pd.read_csv(settings.QUESTIONS_CSV)
        except Exception as e:
            print(f"Error loading questions: {e}")
            # Create a default dataframe with sample questions
            return pd.DataFrame({
                'Question': [
                    'Can you explain your business model?',
                    'What is your target market?',
                    'How do you plan to scale your business?'
                ],
                'Expected Response': [
                    'Clear explanation of value proposition and revenue generation.',
                    'Specific demographic or market segment with justification.',
                    "Detailed growth strategy that's realistic and achievable."
                ]
            })
    
    def record_interaction(self, speaker, text, audio_data=None):
        """Record an interaction in the session transcript"""
        timestamp = time.time()
        interaction = {
            "timestamp": timestamp,
            "speaker": speaker,
            "text": text
        }
        
        if audio_data:
            audio_file = f"{self.session_id}_{timestamp}.wav"
            audio_path = os.path.join(self.session_dir, audio_file)
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            interaction["audio_file"] = audio_file
        
        self.transcript.append(interaction)
        
        # Save updated transcript
        with open(os.path.join(self.session_dir, "transcript.json"), 'w') as f:
            json.dump(self.transcript, f)
        
        return interaction
    
    def get_full_transcript(self):
        """Return the full session transcript"""
        return self.transcript
    
    def get_next_question(self, previous_questions=None, previous_responses=None):
        """Get the next best question based on previous responses"""
        if not previous_questions:
            previous_questions = []
        
        if not previous_responses:
            previous_responses = []
        
        # If we have CV questions and haven't asked them all yet
        if self.cv_questions and len(previous_questions) < len(self.cv_questions):
            return self.cv_questions[len(previous_questions)]
        
        # Get standard questions
        standard_questions = self.questions_df['Question'].tolist()
        
        # If we've asked all CV questions but no standard questions yet
        if len(previous_questions) == len(self.cv_questions) and len(previous_questions) < len(self.cv_questions) + len(standard_questions):
            return standard_questions[0]
        
        # Use Gemini to determine the best follow-up question
        remaining_questions = [q for q in standard_questions if q not in previous_questions]
        
        if not remaining_questions:
            return None  # No more questions to ask
        
        if not previous_responses:
            return remaining_questions[0]  # First standard question
        
        # Use Gemini to select next question
        prompt = f"""
        Based on the candidate's previous responses:
        {' '.join(previous_responses)}
        
        Which of these remaining questions would be most valuable to ask next?
        Options: {remaining_questions}
        
        Return only the question text.
        """
        
        suggested_question = generate_content(prompt)
        
        # Ensure the question exists in our list
        if suggested_question in remaining_questions:
            return suggested_question
        else:
            # Default to the next sequential question
            for q in standard_questions:
                if q not in previous_questions:
                    return q

# Session management
active_sessions = {}

def create_session(cv_path=None):
    """Create a new interview session"""
    session = InterviewSession(cv_path=cv_path)
    active_sessions[session.session_id] = session
    return session

def get_session(session_id):
    """Get an existing interview session"""
    return active_sessions.get(session_id)

def list_sessions():
    """List all active interview sessions"""
    return list(active_sessions.keys())

def delete_session(session_id):
    """Delete an interview session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return True
    return False
