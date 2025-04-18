import requests
import json
import sys

def test_endpoint(base_url, path, method="GET", data=None, files=None, form=False):
    """Test a specific API endpoint"""
    url = f"{base_url}/{path}"
    print(f"\nTesting: {url}")
    print(f"Method: {method}")
    
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            elif form:
                response = requests.post(url, data=data)  # Send as form data
            else:
                response = requests.post(url, json=data)  # Send as JSON
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                resp_data = response.json()
                print("Response data:")
                print(json.dumps(resp_data, indent=2))
            except:
                print("Response text:")
                print(response.text[:200])  # Show first 200 chars
        else:
            print("Error response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def run_local_tests():
    """Run tests against a locally running API"""
    # Default to localhost, but allow command line override
    base_url = "http://localhost:8080"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Test root endpoint
    test_endpoint(base_url, "")
    
    # Test health endpoint
    test_endpoint(base_url, "health")
    
    # Test interview info
    test_endpoint(base_url, "interview")
    
    # Test sessions endpoint
    test_endpoint(base_url, "interview/sessions", method="POST")
    
    # Create a session and get a session ID
    print("\n\nCreating interview session...")
    try:
        response = requests.post(f"{base_url}/interview/sessions")
        session_id = None
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"Created session ID: {session_id}")
            
            if session_id:
                # Test getting questions
                question_data = {
                    "session_id": session_id,
                    "previous_questions": [],
                    "previous_responses": []
                }
                test_endpoint(base_url, "interview/questions", method="POST", data=question_data)
                
                # Test direct response with form data for maximum compatibility
                print("\nTesting direct response with form data")
                response_text = "I've built a SaaS platform that helps companies manage their customer relationships more effectively. We've gained significant traction with mid-sized businesses in the financial sector."
                
                url = f"{base_url}/interview/responses"
                form_data = {
                    "session_id": session_id,
                    "question_id": "0",
                    "text_response": response_text
                }
                
                form_response = requests.post(url, data=form_data)
                print(f"Status code: {form_response.status_code}")
                if form_response.status_code == 200:
                    try:
                        print("Response data:")
                        print(json.dumps(form_response.json(), indent=2))
                    except:
                        print("Response text:")
                        print(form_response.text[:200])
                else:
                    print("Error response:")
                    print(form_response.text)
                
                # Test with JSON format
                print("\nTesting with JSON format")
                json_data = {
                    "session_id": session_id,
                    "question_id": "0",
                    "text_response": response_text
                }
                
                json_response = requests.post(url, json=json_data)
                print(f"Status code: {json_response.status_code}")
                if json_response.status_code == 200:
                    try:
                        print("Response data:")
                        print(json.dumps(json_response.json(), indent=2))
                    except:
                        print("Response text:")
                        print(json_response.text[:200])
                else:
                    print("Error response:")
                    print(json_response.text)
                
                # Test getting feedback
                feedback_data = {
                    "session_id": session_id,
                    "detailed": True
                }
                test_endpoint(base_url, "interview/feedback", method="POST", data=feedback_data)
            
    except Exception as e:
        print(f"Error during session tests: {e}")

if __name__ == "__main__":
    run_local_tests() 