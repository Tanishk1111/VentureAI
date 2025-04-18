import requests
import json
import time

# API base URL
BASE_URL = "https://ventureai-840537625469.us-central1.run.app"

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an API endpoint and print the response"""
    url = f"{BASE_URL}/{endpoint}"
    print(f"\n\n===== Testing {method} {url} =====")
    
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.3f} seconds")
        print("Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Print response body if present
        if response.text:
            try:
                # Try to parse as JSON
                json_data = response.json()
                print("\nResponse Body (JSON):")
                print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                # If not JSON, print as text
                print("\nResponse Body (Text):")
                print(response.text[:500])  # Limit to first 500 chars
                if len(response.text) > 500:
                    print("... (truncated)")
        
        return response
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Run tests
if __name__ == "__main__":
    print("Starting API tests...")
    
    # Test root endpoint
    test_endpoint("")
    
    # Test health endpoint
    test_endpoint("health")
    
    # Test cloud status endpoint
    test_endpoint("cloud-status")
    
    # Check API documentation
    test_endpoint("docs")
    
    # Test OpenAPI schema
    test_endpoint("openapi.json")
    
    # Test interview placeholder endpoint - should show either placeholder or actual route
    test_endpoint("interview")
    
    print("\nAll tests completed!") 