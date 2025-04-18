import requests
import json
import time
import sys
import os

class InteractiveVentureAIClient:
    """Interactive client for VentureAI interviews"""
    
    def __init__(self, base_url="https://ventureai-840537625469.us-central1.run.app"):
        self.base_url = base_url
        self.session_id = None
        self.questions = []
        self.responses = []
    
    def call_api(self, endpoint, method="GET", data=None, files=None):
        """Make an API call and handle errors"""
        url = f"{self.base_url}/{endpoint}"
        print(f"📡 Calling API: {url}")
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
                print(f"❌ API error: {response.status_code}")
                print(response.text)
                return None
                
            print(f"✅ API response received (status {response.status_code})")
            return response.json()
            
        except Exception as e:
            print(f"❌ Error calling API: {e}")
            return None
    
    def create_session(self):
        """Create a new interview session, optionally with a CV"""
        print("\n🚀 Creating new interview session...")
        
        # Ask if user wants to upload CV
        use_cv = input("Do you want to upload a CV/resume? (y/n): ").lower().startswith('y')
        
        files = None
        if use_cv:
            cv_path = input("Enter the path to your CV/resume file: ")
            if os.path.exists(cv_path):
                files = {'cv_file': open(cv_path, 'rb')}
                print(f"Uploading CV: {cv_path}")
            else:
                print(f"File not found: {cv_path}")
                if not input("Continue without CV? (y/n): ").lower().startswith('y'):
                    return False
        
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
            "previous_responses": self.responses,
            "question_type": "standard"
        }
        
        response = self.call_api("interview/questions", method="POST", data=data)
        
        if response:
            question = response.get('question')
            if question:
                self.questions.append(question)
                print(f"\n👨‍💼 Interviewer: {question}")
                return question
            else:
                print("\n🏁 No more questions (interview complete)")
                return None
        
        return None
    
    def submit_response(self, response_text):
        """Submit a text response to a question"""
        print("\n💬 Submitting your response for analysis...")
        
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
                print(f"🧠 Sentiment analysis: {sentiment_text} (score: {score})")
            
            # Check for follow-up
            if response.get('need_follow_up'):
                follow_up = response.get('follow_up', {}).get('text')
                if follow_up:
                    print(f"\n👨‍💼 Follow-up: {follow_up}")
                    # Get response to follow-up
                    follow_up_response = input("\n🧑‍💼 Your follow-up response: ")
                    self.questions.append(follow_up)
                    self.submit_response(follow_up_response)
                    
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
                print("\n==============================")
                return feedback
        else:
            print("❌ Failed to get feedback")
            
        return None
    
    def run_interactive_interview(self):
        """Run an interactive interview where the user provides responses"""
        print("\n🎯 Starting Interactive VC Interview")
        print("===================================")
        
        if not self.create_session():
            print("Failed to create interview session")
            return False
        
        # Explain the process
        print("\nYou'll be asked a series of venture capital interview questions.")
        print("Type your responses and press ENTER to submit.")
        print("The system will analyze your responses and provide feedback at the end.")
        input("\nPress ENTER to begin the interview...")
        
        # Number of questions to ask
        num_questions = 3
        print(f"\nThis interview will consist of {num_questions} questions.")
        
        for i in range(num_questions):
            question = self.get_next_question()
            if not question:
                print("No more questions available")
                break
            
            # Get user input
            response_text = input("\n🧑‍💼 Your response: ")
            
            if not self.submit_response(response_text):
                print("Failed to submit response")
                break
            
            if i < num_questions - 1:
                print("\nPreparing next question...")
                time.sleep(1)
        
        print("\n🎬 Interview complete!")
        # Get feedback
        self.get_feedback()
        
        print("\nThank you for participating in the VentureAI interview.")
        return True

# Run the interactive interview if executed directly
if __name__ == "__main__":
    print("VentureAI Interactive Interview")
    print("===============================")
    print("This program will simulate a venture capital interview using the VentureAI API.")
    
    client = InteractiveVentureAIClient()
    client.run_interactive_interview() 