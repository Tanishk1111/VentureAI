import requests
import json

BASE_URL = "https://ventureai-840537625469.us-central1.run.app"

def test_endpoint(path):
    """Test a specific API endpoint"""
    url = f"{BASE_URL}/{path}"
    print(f"\nTesting: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("Response data:")
                print(json.dumps(data, indent=2))
            except:
                print("Response text:")
                print(response.text[:200])  # Show first 200 chars
        else:
            print("Error response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

# Test root endpoint
test_endpoint("")

# Test health endpoint
test_endpoint("health")

# Test cloud status endpoint
test_endpoint("cloud-status")

# Test OpenAPI endpoint
test_endpoint("openapi.json")

# Try to find the interview endpoint 
test_endpoint("interview")

# Try alternative paths for interview endpoints
potential_paths = [
    "api/interview/sessions",
    "v1/interview/sessions",
    "sessions",
    "session",
]

for path in potential_paths:
    test_endpoint(path) 