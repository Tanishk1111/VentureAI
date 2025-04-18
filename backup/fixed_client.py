import requests
import json
import sys
import time
import argparse

class FixedVentureAIClient:
    """A fixed client for the VentureAI API"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session_id = None
        self.questions = []
        self.responses = []
    
    def call_api(self, endpoint, method="GET", data=None, files=None, is_form=False):
        """Make an API call and handle errors"""
        url = f"{self.base_url}/{endpoint}"
        print(f"📡 Calling API: {url}")
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                if files:
                    response = requests.post(url, data=data, files=files)
                elif is_form:
                    response = requests.post(url, data=data)
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
    
    def create_session(self, cv_path=None):
        """Create a new interview session, optionally with a CV"""
        print("\n🚀 Creating new interview session...")
        
        files = None
        if cv_path:
            try:
                files = {'cv_file': open(cv_path, 'rb')}
                print(f"Uploading CV: {cv_path}")
            except Exception as e:
                print(f"Error opening CV file: {e}")
                files = None
        
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
        
        # Use form data submission 
        data = {
            "session_id": self.session_id,
            "question_id": question_id,
            "text_response": response_text
        }
        
        response = self.call_api("interview/responses", method="POST", data=data, is_form=True)
        
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
    
    def run_interactive_interview(self, num_questions=3):
        """Run an interactive interview where the user provides responses"""
        if not self.create_session():
            print("Failed to create interview session")
            return False
        
        # Number of questions to ask
        print(f"\nThis interview will consist of up to {num_questions} questions.")
        print("Type your responses and press ENTER to submit.")
        
        for i in range(num_questions):
            question = self.get_next_question()
            if not question:
                print("No more questions available")
                break
            
            # Get user input
            response_text = input("\n💬 Your response: ")
            
            if not self.submit_response(response_text):
                print("Failed to submit response")
                break
            
            if i < num_questions - 1:
                print("\nPreparing next question...")
                time.sleep(1)
        
        print("\n🎬 Interview complete!")
        # Get feedback
        self.get_feedback()
        
        return True

def main():
    """Main function to run the client"""
    parser = argparse.ArgumentParser(description="VentureAI Fixed Client")
    parser.add_argument("--url", default="http://localhost:8080", help="API base URL")
    parser.add_argument("--questions", type=int, default=3, help="Number of questions")
    parser.add_argument("--cv", help="Path to CV file")
    
    args = parser.parse_args()
    
    print("VentureAI Interview Client")
    print("===========================")
    print(f"API URL: {args.url}")
    
    client = FixedVentureAIClient(base_url=args.url)
    client.run_interactive_interview(num_questions=args.questions)

if __name__ == "__main__":
    main() 