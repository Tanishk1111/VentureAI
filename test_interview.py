import requests
import json
import time

# Base URL
base_url = "http://localhost:8080"

def test_interview_flow():
    # 1. Create a session
    print("1. Creating a new interview session...")
    session_response = requests.post(f"{base_url}/interview/sessions")
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(f"Session created with ID: {session_id}")
    print(f"Response: {json.dumps(session_data, indent=2)}")
    
    # 2. Get a question
    print("\n2. Getting a question...")
    question_request = {
        "session_id": session_id,
        "previous_questions": [],
        "previous_responses": []
    }
    question_response = requests.post(
        f"{base_url}/interview/questions", 
        json=question_request
    )
    question_data = question_response.json()
    question = question_data["question"]
    question_id = question_data["question_id"]
    print(f"Question ID: {question_id}")
    print(f"Question: {question}")
    print(f"Full response: {json.dumps(question_data, indent=2)}")
    
    # 3. Submit a response
    print("\n3. Submitting a response...")
    response_text = "Our company is revolutionizing healthcare with AI diagnostic tools. We have developed algorithms that provide higher accuracy than current methods and we maintain a large proprietary dataset. We are seeking funding to scale our operations and expand to new markets."
    response_request = {
        "session_id": session_id,
        "question_id": question_id,
        "text_response": response_text
    }
    
    # Debug info
    print(f"Request body: {json.dumps(response_request, indent=2)}")
    
    try:
        response_submission = requests.post(
            f"{base_url}/interview/responses", 
            json=response_request
        )
        print(f"Status code: {response_submission.status_code}")
        response_data = response_submission.json()
        print(f"Response submitted successfully.")
        print(f"Full response: {json.dumps(response_data, indent=2)}")
        sentiment_score = response_data.get('sentiment', {}).get('score', 'N/A')
        print(f"Sentiment score: {sentiment_score}")
    except Exception as e:
        print(f"Error submitting response: {e}")
        print(f"Response content: {response_submission.text}")
    
    time.sleep(1)  # Add a small delay
    
    # Get another question 
    print("\n4. Getting a second question...")
    question_request = {
        "session_id": session_id,
        "previous_questions": [question],
        "previous_responses": [response_text]
    }
    question_response = requests.post(
        f"{base_url}/interview/questions", 
        json=question_request
    )
    
    if question_response.status_code == 200:
        question_data = question_response.json()
        question2 = question_data["question"]
        question_id2 = question_data["question_id"]
        print(f"Question ID: {question_id2}")
        print(f"Question: {question2}")
        
        # Submit second response
        print("\n5. Submitting a second response...")
        response_text2 = "Our target market is healthcare providers, particularly hospitals and diagnostic labs. We've already secured partnerships with three major hospital networks and have a pipeline of 15 more interested clients. Our early trials show that we can reduce diagnostic time by 40% and improve accuracy by 25%, creating significant value for our customers."
        response_request = {
            "session_id": session_id,
            "question_id": question_id2,
            "text_response": response_text2
        }
        
        try:
            response_submission = requests.post(
                f"{base_url}/interview/responses", 
                json=response_request
            )
            print(f"Status code: {response_submission.status_code}")
            if response_submission.status_code == 200:
                response_data = response_submission.json()
                print(f"Response submitted successfully.")
                sentiment_score = response_data.get('sentiment', {}).get('score', 'N/A')
                print(f"Sentiment score: {sentiment_score}")
            else:
                print(f"Error response: {response_submission.text}")
        except Exception as e:
            print(f"Error submitting second response: {e}")
    else:
        print(f"Failed to get second question. Status code: {question_response.status_code}")
        print(f"Response: {question_response.text}")
    
    time.sleep(1)  # Add a small delay
    
    # 6. Generate feedback
    print("\n6. Generating interview feedback...")
    feedback_request = {
        "session_id": session_id,
        "detailed": True
    }
    
    try:
        feedback_response = requests.post(
            f"{base_url}/interview/feedback", 
            json=feedback_request
        )
        print(f"Status code: {feedback_response.status_code}")
        
        if feedback_response.status_code == 200:
            feedback_data = feedback_response.json()
            print("Feedback generated:")
            print("-" * 50)
            print(feedback_data.get("summary", "No feedback available"))
            print("-" * 50)
        else:
            print(f"Failed to generate feedback. Response: {feedback_response.text}")
    except Exception as e:
        print(f"Error generating feedback: {e}")
    
    return session_id

if __name__ == "__main__":
    session_id = test_interview_flow()
    print(f"\nTest completed for session: {session_id}") 