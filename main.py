import os
import logging
import time
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file




# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vc_interview_api")

# Create necessary directories with error handling - do this early
try:
    os.makedirs("sessions", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("keys", exist_ok=True)
    logger.info("Created necessary directories")
except Exception as e:
    logger.error(f"Error creating directories: {e}")
    logger.error(traceback.format_exc())

# Import config - but with error handling
try:
    from config import settings
    logger.info("Config loaded successfully")
except Exception as e:
    logger.error(f"Error loading config: {e}")
    logger.error(traceback.format_exc())
    
    # Provide fallback settings if config fails to load
    from pydantic import BaseModel
    class FallbackSettings(BaseModel):
        ENVIRONMENT: str = "production"
        API_KEY: str = os.getenv("API_KEY", "")
        PROJECT_ID: str = os.getenv("PROJECT_ID", "ventureai-project")
        LOCATION: str = os.getenv("LOCATION", "us-central1")
    
    settings = FallbackSettings()
    logger.warning("Using fallback settings due to config load error")

# Initialize Google Cloud services
try:
    from utils.google_cloud import cloud_manager
    cloud_manager.initialize()
    logger.info(f"Google Cloud services status: {cloud_manager.get_status()}")
except Exception as e:
    logger.error(f"Error initializing Google Cloud manager: {e}")
    logger.error(traceback.format_exc())

# Create FastAPI app
app = FastAPI(
    title="VC Interview API",
    description="API for conducting virtual VC interviews with AI-powered analysis and feedback",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Root endpoint
@app.get("/")
async def root():
    """API root - returns basic information about the API"""
    # Check Google Cloud status
    google_cloud_status = "not initialized"
    try:
        from utils.google_cloud import cloud_manager
        google_cloud_status = "initialized" if cloud_manager.is_initialized() else "not available"
    except Exception:
        pass
        
    return {
        "name": "VC Interview API",
        "version": "1.0.0",
        "status": "running",
        "environment": getattr(settings, "ENVIRONMENT", "production"),
        "google_cloud_status": google_cloud_status
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    # Check Google API connection
    google_cloud_status = "not configured"
    cloud_details = {}
    
    try:
        from utils.google_cloud import cloud_manager
        cloud_details = cloud_manager.get_status()
        google_cloud_status = "connected" if cloud_manager.is_initialized() else "error"
    except Exception as e:
        logger.error(f"Google Cloud health check failed: {e}")
        google_cloud_status = "error"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "google_cloud": google_cloud_status,
        "cloud_services": cloud_details,
        "environment": getattr(settings, "ENVIRONMENT", "production")
    }

# Get detailed cloud service status
@app.get("/cloud-status")
async def cloud_status():
    """Get detailed status of all cloud services"""
    try:
        from utils.google_cloud import cloud_manager
        return {
            "status": cloud_manager.get_status(),
            "initialized": cloud_manager.is_initialized(),
            "credentials_path": cloud_manager.credentials_path,
            "credentials_exist": os.path.exists(cloud_manager.credentials_path),
            "project_id": cloud_manager.project_id,
            "location": cloud_manager.location
        }
    except Exception as e:
        logger.error(f"Error getting cloud status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )

# Attempt to import routers - but make it optional
try:
    # Import interview router
    from routers import interview
    app.include_router(interview.router)
    # Register compatibility routes
    interview.add_compatibility_routes(app)
    logger.info("Successfully loaded interview router with compatibility routes")
except Exception as e:
    logger.error(f"Error importing interview router: {e}")
    logger.error(traceback.format_exc())
    # Add a placeholder endpoint to indicate the feature would be here
    @app.get("/interview")
    async def interview_placeholder():
        return {"status": "Interview module not available", "message": "The interview functionality is not fully configured", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting VC Interview API in {getattr(settings, 'ENVIRONMENT', 'production')} mode")
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port,
        reload=getattr(settings, "ENVIRONMENT", "production") != "production"
    )
