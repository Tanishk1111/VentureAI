import requests
import json
import time
import sys
import os

class VentureAIClient:
    """Client for interacting with the VentureAI API"""
    
    def __init__(self, base_url="https://ventureai-840537625469.us-central1.run.app"):
        self.base_url = base_url
        self.session_id = None
        self.questions = []
        self.responses = []
    
    def call_api(self, endpoint, method="GET", data=None, files=None):
        """Make an API call and handle errors"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                if files:
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data)
            
            # Check if the request was successful
            if response.status_code >= 400:
                print(f"API error: {response.status_code}")
                print(response.text)
                return None
                
            return response.json()
            
        except Exception as e:
            print(f"Error calling API: {e}")
            return None
    
    def create_session(self, cv_path=None):
        """Create a new interview session, optionally with a CV"""
        print("\n🚀 Creating new interview session...")
        
        files = None
        if cv_path and os.path.exists(cv_path):
            files = {'cv_file': open(cv_path, 'rb')}
            print(f"Uploading CV: {cv_path}")
        
        response = self.call_api("interview/sessions", method="POST", files=files)
        
        if response:
            self.session_id = response.get('session_id')
            print(f"Session created with ID: {self.session_id}")
            print(f"CV uploaded: {'Yes' if response.get('has_cv') else 'No'}")
            if response.get('cv_questions_count'):
                print(f"Generated {response.get('cv_questions_count')} questions from CV")
            return True
        
        return False
    
    def get_next_question(self):
        """Get the next interview question"""
        print("\n🎤 Getting next question...")
        
        if not self.session_id:
            print("Error: No active session")
            return None
        
        data = {
            "session_id": self.session_id,
            "previous_questions": self.questions,
            "previous_responses": self.responses
        }
        
        response = self.call_api("interview/questions", method="POST", data=data)
        
        if response:
            question = response.get('question')
            if question:
                self.questions.append(question)
                print(f"Question: {question}")
                return question
            else:
                print("No more questions (interview complete)")
                return None
        
        return None
    
    def submit_response(self, response_text):
        """Submit a text response to a question"""
        print("\n💬 Submitting response...")
        
        if not self.session_id or not self.questions:
            print("Error: No active session or questions")
            return False
        
        question_id = str(len(self.questions) - 1)
        
        data = {
            "session_id": self.session_id,
            "question_id": question_id,
            "text_response": response_text
        }
        
        response = self.call_api("interview/responses", method="POST", data=data)
        
        if response:
            self.responses.append(response_text)
            print(f"Response submitted successfully")
            
            # Check sentiment
            if response.get('sentiment'):
                sentiment = response.get('sentiment')
                score = sentiment.get('score', 0)
                sentiment_text = sentiment.get('sentiment', 'neutral')
                print(f"Sentiment analysis: {sentiment_text} (score: {score})")
            
            # Check for follow-up
            if response.get('need_follow_up'):
                follow_up = response.get('follow_up', {}).get('text')
                if follow_up:
                    print(f"\nFollow-up: {follow_up}")
                    
            return True
        
        return False
    
    def get_feedback(self):
        """Get feedback on the interview"""
        print("\n📊 Generating interview feedback...")
        
        if not self.session_id:
            print("Error: No active session")
            return None
        
        data = {
            "session_id": self.session_id,
            "detailed": True
        }
        
        response = self.call_api("interview/feedback", method="POST", data=data)
        
        if response:
            feedback = response.get('summary')
            if feedback:
                print("\n===== INTERVIEW FEEDBACK =====")
                print(feedback)
                return feedback
        
        return None
    
    def run_mock_interview(self, num_questions=3):
        """Run a complete mock interview flow"""
        if not self.create_session():
            print("Failed to create interview session")
            return False
        
        for i in range(num_questions):
            question = self.get_next_question()
            if not question:
                print("No more questions available")
                break
            
            # In a real application, you would get user input here
            # For this demo, we'll use predefined responses
            mock_responses = [
                "I've founded a SaaS platform that helps early-stage startups organize their fundraising process. Our solution streamlines investor communications and due diligence.",
                "Our go-to-market strategy focuses on direct sales to accelerators and incubators, who then recommend us to their portfolio companies. We've partnered with three accelerators already.",
                "We're currently at $15K MRR with a 15% monthly growth rate. Our CAC is $500 with an LTV of approximately $3,000, giving us a healthy 6:1 LTV:CAC ratio."
            ]
            
            response_text = mock_responses[i % len(mock_responses)]
            print(f"Your response: {response_text}")
            
            if not self.submit_response(response_text):
                print("Failed to submit response")
                break
            
            # Pause between questions
            time.sleep(1)
        
        # Get feedback
        self.get_feedback()
        
        return True

# Run a demo interview if executed directly
if __name__ == "__main__":
    print("VentureAI Interview Client Demo")
    print("===============================")
    
    client = VentureAIClient()
    client.run_mock_interview(3) 