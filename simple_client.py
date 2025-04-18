import requests
import json
import time
import sys
import argparse

class SimpleVentureAIClient:
    """A simplified client for the VentureAI API that works with the available endpoints"""
    
    def __init__(self, base_url="https://ventureai-840537625469.us-central1.run.app"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_api_info(self):
        """Get basic API information"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_status(self):
        """Get API health status"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_cloud_status(self):
        """Get cloud service status"""
        try:
            response = self.session.get(f"{self.base_url}/cloud")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_openapi_spec(self):
        """Get the OpenAPI specification to see available endpoints"""
        try:
            response = self.session.get(f"{self.base_url}/openapi.json")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_api_docs_url(self):
        """Get the URL for API documentation"""
        return f"{self.base_url}/docs"
    
    def list_available_endpoints(self):
        """List all available endpoints from the OpenAPI spec"""
        spec = self.get_openapi_spec()
        if "error" in spec:
            return {"error": spec["error"]}
        
        endpoints = {}
        if "paths" in spec:
            for path, methods in spec["paths"].items():
                endpoints[path] = list(methods.keys())
        
        return endpoints
    
    def test_endpoint(self, endpoint):
        """Test a specific API endpoint"""
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]  # Remove leading slash if present
        
        url = f"{self.base_url}/{endpoint}"
        print(f"Testing endpoint: {url}")
        
        try:
            response = self.session.get(url)
            try:
                return response.json()
            except:
                return {"status_code": response.status_code, "text": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def explain_api_status(self, verbose=False):
        """Explain the current API status with all available information"""
        print("VentureAI API Status Check")
        print("==========================\n")
        
        print("===== VentureAI API Status =====\n")
        
        # Get and print API info
        api_info = self.get_api_info()
        if "error" not in api_info:
            print("API Information:")
            for key, value in api_info.items():
                print(f"  {key.capitalize()}: {value}")
        else:
            print(f"Error getting API info: {api_info['error']}")
        
        print()
        
        # Get and print health status
        health = self.get_health_status()
        if "error" not in health:
            print("Health Status:")
            for key, value in health.items():
                if key != "services":
                    print(f"  {key.capitalize()}: {value}")
            
            if "services" in health:
                print("\n  Cloud Services:")
                for service in health["services"]:
                    print(f"    - {service}")
        else:
            print(f"Error getting health status: {health['error']}")
        
        print()
        
        # Get and print cloud status
        cloud = self.get_cloud_status()
        if "error" not in cloud:
            print("Cloud Status:")
            for key, value in cloud.items():
                print(f"  {key}: {value}")
        else:
            print(f"Error getting cloud status: {cloud['error']}")
        
        # Print API docs URL
        print(f"API Documentation: {self.get_api_docs_url()}")
        
        # List available endpoints
        if verbose:
            print("\n===== Available API Endpoints =====\n")
            endpoints = self.list_available_endpoints()
            if "error" not in endpoints:
                for path, methods in endpoints.items():
                    print(f"Endpoint: {path}")
                    print(f"  Methods: {', '.join(methods).upper()}")
                    print()
            else:
                print(f"Error getting available endpoints: {endpoints['error']}")
        
        print("\n==================================")

def main():
    parser = argparse.ArgumentParser(description="Simple VentureAI API Client")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output including all available endpoints")
    parser.add_argument("--endpoint", help="Test a specific API endpoint")
    parser.add_argument("--url", default="https://ventureai-840537625469.us-central1.run.app", help="API base URL")
    
    args = parser.parse_args()
    
    client = SimpleVentureAIClient(base_url=args.url)
    
    if args.endpoint:
        result = client.test_endpoint(args.endpoint)
        print("\nEndpoint Test Result:")
        print(json.dumps(result, indent=2))
    else:
        client.explain_api_status(verbose=args.verbose)

if __name__ == "__main__":
    main() 