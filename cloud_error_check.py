import os
import sys
import json
import requests

def check_environ_variables():
    """Check if all required environment variables are present"""
    required_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "PROJECT_ID",
        "LOCATION",
        "API_KEY",
        "GOOGLE_API_KEY"
    ]
    
    print("Environment Variables Check:")
    print("----------------------------")
    
    all_present = True
    for var in required_vars:
        value = os.environ.get(var)
        status = "✓ Present" if value else "✗ Missing"
        masked_value = "[MASKED]" if value and ("KEY" in var or "CREDENTIALS" in var) else value
        print(f"{var}: {status} - {masked_value}")
        if not value:
            all_present = False
    
    if all_present:
        print("\nAll required environment variables are present.")
    else:
        print("\nWARNING: Some required environment variables are missing.")
    
    return all_present

def check_credentials_file():
    """Check if the credentials file exists and is valid"""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    print("\nCredentials File Check:")
    print("----------------------")
    
    if not creds_path:
        print("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        return False
    
    print(f"Credentials path: {creds_path}")
    
    if not os.path.exists(creds_path):
        print(f"Credentials file does not exist at: {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds_content = json.load(f)
            
        required_keys = ["type", "project_id", "private_key", "client_email"]
        for key in required_keys:
            if key not in creds_content:
                print(f"Credentials file is missing required key: {key}")
                return False
        
        print(f"Credentials file is valid.")
        print(f"Project ID in credentials: {creds_content.get('project_id')}")
        print(f"Service account: {creds_content.get('client_email')}")
        
        # Check if project ID matches
        env_project_id = os.environ.get("PROJECT_ID")
        if env_project_id and env_project_id != creds_content.get("project_id"):
            print(f"WARNING: PROJECT_ID environment variable ({env_project_id}) does not match the project_id in credentials ({creds_content.get('project_id')})")
        
        return True
    except json.JSONDecodeError:
        print(f"Credentials file is not valid JSON.")
        return False
    except Exception as e:
        print(f"Error reading credentials file: {str(e)}")
        return False

def check_api_connectivity():
    """Test API connectivity with the provided API key"""
    api_key = os.environ.get("API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    print("\nAPI Connectivity Check:")
    print("----------------------")
    
    if not api_key:
        print("No API key found in environment variables.")
        return False
    
    # Test Gemini API connectivity
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        print("Testing connection to Gemini API...")
        response = requests.get(gemini_url)
        if response.status_code == 200:
            print("✓ Successfully connected to Gemini API")
            return True
        else:
            print(f"✗ Failed to connect to Gemini API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error connecting to Gemini API: {str(e)}")
        return False

def check_numpy_version():
    """Check the installed NumPy version to address potential binary incompatibility"""
    print("\nNumPy Version Check:")
    print("------------------")
    
    try:
        import numpy
        print(f"NumPy version: {numpy.__version__}")
        print("This looks good. If you're seeing 'numpy.dtype size changed' errors, you may need to reinstall numpy.")
    except ImportError:
        print("NumPy is not installed.")
    except Exception as e:
        print(f"Error checking NumPy version: {str(e)}")

def check_library_versions():
    """Check versions of key libraries"""
    libraries = [
        "google-cloud-aiplatform",
        "google-cloud-speech", 
        "google-cloud-texttospeech",
        "google-generativeai",
        "fastapi",
        "uvicorn",
        "numpy",
        "pandas"
    ]
    
    print("\nLibrary Version Check:")
    print("--------------------")
    
    for lib in libraries:
        module_name = lib.replace("-", "_").split("_")[0]
        try:
            if module_name == "google":
                if "aiplatform" in lib:
                    import google.cloud.aiplatform
                    version = google.cloud.aiplatform.__version__
                elif "speech" in lib:
                    import google.cloud.speech
                    version = google.cloud.speech.__version__
                elif "texttospeech" in lib:
                    import google.cloud.texttospeech
                    version = google.cloud.texttospeech.__version__
                elif "generativeai" in lib:
                    import google.generativeai
                    version = google.generativeai.__version__
            else:
                module = __import__(module_name)
                version = getattr(module, "__version__", "Unknown")
            
            print(f"{lib}: {version}")
        except ImportError:
            print(f"{lib}: Not installed")
        except Exception as e:
            print(f"{lib}: Error - {str(e)}")

def main():
    """Run all checks"""
    print("VentureAI Google Cloud Configuration Check")
    print("=========================================\n")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Running on: {sys.platform}\n")
    
    # Run all checks
    check_environ_variables()
    check_credentials_file()
    check_api_connectivity()
    check_numpy_version()
    check_library_versions()
    
    print("\nComplete! Please review the results above for any issues.")

if __name__ == "__main__":
    main() 