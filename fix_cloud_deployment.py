import subprocess
import os
import json
import sys

def run_command(command):
    """Run a shell command and return the output"""
    process = subprocess.Popen(
        command, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True, 
        text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def get_current_service_config():
    """Get the current Cloud Run service configuration"""
    print("Getting current Cloud Run service configuration...")
    
    # Get the deployed Cloud Run service name
    service_name = "ventureai"  # Default name, replace if different
    project_id = os.environ.get("PROJECT_ID", "vc-interview-agent")
    region = os.environ.get("LOCATION", "us-central1")
    
    cmd = f"gcloud run services describe {service_name} --platform managed --region {region} --format json"
    stdout, stderr, return_code = run_command(cmd)
    
    if return_code != 0:
        print(f"Error retrieving service configuration: {stderr}")
        return None
    
    try:
        config = json.loads(stdout)
        return config
    except json.JSONDecodeError:
        print(f"Error parsing service configuration JSON: {stdout}")
        return None

def update_env_variables():
    """Update environment variables for the Cloud Run service"""
    # Get the current config first
    config = get_current_service_config()
    if not config:
        print("Failed to get current service configuration. Aborting.")
        return False
    
    # Extract current service name, project ID, and region
    service_name = config.get("metadata", {}).get("name", "ventureai")
    project_id = os.environ.get("PROJECT_ID", "vc-interview-agent")
    region = os.environ.get("LOCATION", "us-central1")
    
    # Define the variables we want to set
    env_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "vc-interview-service-account.json",
        "PROJECT_ID": project_id,
        "LOCATION": region,
        "API_KEY": os.environ.get("API_KEY", ""),  # Use local value if available
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),  # Use local value if available
        "ENVIRONMENT": "production",
        "QUESTIONS_CSV_PATH": "vc_interview_questions_full.csv",
        "SESSIONS_DIR": "sessions",
        "GENERATIVE_MODEL_NAME": "gemini-1.5-pro-latest"
    }
    
    # Build the update command with environment variables
    env_flags = " ".join([f"--set-env-vars={key}={value}" for key, value in env_vars.items() if value])
    
    update_cmd = f"gcloud run services update {service_name} --platform managed --region {region} {env_flags}"
    
    print(f"Updating Cloud Run service {service_name} with environment variables...")
    stdout, stderr, return_code = run_command(update_cmd)
    
    if return_code != 0:
        print(f"Error updating service: {stderr}")
        return False
    
    print(f"Successfully updated Cloud Run service environment variables.")
    print(stdout)
    return True

def upload_service_account_file():
    """Upload the service account JSON file to the Cloud Run service"""
    print("Checking for service account file...")
    
    # Check if service account file exists
    sa_file = "vc-interview-service-account.json"
    if not os.path.exists(sa_file):
        print(f"Service account file {sa_file} not found!")
        return False
    
    # Get current config
    config = get_current_service_config()
    if not config:
        print("Failed to get current service configuration. Aborting.")
        return False
    
    # Extract current image
    image = config.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("image", "")
    if not image:
        print("Failed to get current image URL. Aborting.")
        return False
    
    service_name = config.get("metadata", {}).get("name", "ventureai")
    project_id = os.environ.get("PROJECT_ID", "vc-interview-agent")
    region = os.environ.get("LOCATION", "us-central1")
    
    # Unfortunately, there's no direct way to upload just a file to Cloud Run
    # We need to:
    # 1. Create a new Dockerfile that includes the service account file
    # 2. Build a new container
    # 3. Deploy it
    
    print("Creating temporary Dockerfile...")
    with open("Dockerfile.temp", "w") as f:
        f.write(f"""FROM {image}
COPY {sa_file} /app/{sa_file}
""")
    
    # Build and push new image
    new_image = f"gcr.io/{project_id}/{service_name}-with-sa:latest"
    build_cmd = f"gcloud builds submit --tag {new_image} ."
    
    print(f"Building new container with service account file...")
    stdout, stderr, return_code = run_command(build_cmd)
    
    if return_code != 0:
        print(f"Error building new container: {stderr}")
        return False
    
    # Deploy the new image
    deploy_cmd = f"gcloud run services update {service_name} --platform managed --region {region} --image {new_image}"
    
    print(f"Deploying new container to Cloud Run...")
    stdout, stderr, return_code = run_command(deploy_cmd)
    
    if return_code != 0:
        print(f"Error deploying new container: {stderr}")
        return False
    
    # Clean up
    os.remove("Dockerfile.temp")
    
    print(f"Successfully updated service with service account file.")
    return True

def fix_numpy_issue():
    """Fix the numpy binary incompatibility issue"""
    # Get current config
    config = get_current_service_config()
    if not config:
        print("Failed to get current service configuration. Aborting.")
        return False
    
    service_name = config.get("metadata", {}).get("name", "ventureai")
    project_id = os.environ.get("PROJECT_ID", "vc-interview-agent")
    region = os.environ.get("LOCATION", "us-central1")
    
    # Create a startup script to fix numpy
    print("Creating startup script to fix numpy...")
    with open("fix_numpy.sh", "w") as f:
        f.write("""#!/bin/bash
pip uninstall -y numpy
pip install numpy==1.24.3
exec "$@"
""")
    
    # Make it executable
    os.chmod("fix_numpy.sh", 0o755)
    
    # Create a new Dockerfile
    print("Creating Dockerfile with numpy fix...")
    with open("Dockerfile.numpy_fix", "w") as f:
        f.write("""FROM gcr.io/vc-interview-agent/ventureai:latest
COPY fix_numpy.sh /fix_numpy.sh
ENTRYPOINT ["/fix_numpy.sh"]
CMD ["python", "main.py"]
""")
    
    # Build and push new image
    new_image = f"gcr.io/{project_id}/{service_name}-numpy-fix:latest"
    build_cmd = f"gcloud builds submit --tag {new_image}"
    
    print(f"Building new container with numpy fix...")
    stdout, stderr, return_code = run_command(build_cmd)
    
    if return_code != 0:
        print(f"Error building new container: {stderr}")
        return False
    
    # Deploy the new image
    deploy_cmd = f"gcloud run services update {service_name} --platform managed --region {region} --image {new_image}"
    
    print(f"Deploying new container to Cloud Run...")
    stdout, stderr, return_code = run_command(deploy_cmd)
    
    if return_code != 0:
        print(f"Error deploying new container: {stderr}")
        return False
    
    # Clean up
    os.remove("Dockerfile.numpy_fix")
    os.remove("fix_numpy.sh")
    
    print(f"Successfully updated service with numpy fix.")
    return True

def main():
    print("VentureAI Cloud Run Deployment Fix")
    print("================================\n")
    
    # Check if gcloud is installed
    print("Checking if gcloud command line tool is installed...")
    _, _, return_code = run_command("gcloud --version")
    if return_code != 0:
        print("Error: gcloud command-line tool is not installed or not in PATH. Please install it first.")
        sys.exit(1)
    
    # Check if user is logged in
    print("Checking if user is logged in to Google Cloud...")
    stdout, _, return_code = run_command("gcloud auth list --filter=status=ACTIVE --format=\"value(account)\"")
    if return_code != 0 or not stdout.strip():
        print("Error: You are not logged in to Google Cloud. Please run 'gcloud auth login' first.")
        sys.exit(1)
    
    print(f"Logged in as: {stdout.strip()}")
    
    # Menu
    print("\nWhat would you like to fix?")
    print("1. Update environment variables in Cloud Run")
    print("2. Upload service account credentials file")
    print("3. Fix numpy binary incompatibility issue")
    print("4. Run all fixes")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == "1":
        update_env_variables()
    elif choice == "2":
        upload_service_account_file()
    elif choice == "3":
        fix_numpy_issue()
    elif choice == "4":
        update_env_variables()
        upload_service_account_file()
        fix_numpy_issue()
    elif choice == "5":
        print("Exiting.")
        return
    else:
        print("Invalid choice.")
        return
    
    print("\nFix completed. Please check the Cloud Run console for the status of your deployment.")
    print("Once the new revision is deployed, test the API again to verify the fixes.")

if __name__ == "__main__":
    main() 