import os
import logging
import time
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware

# Import config
from config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vc_interview_api")

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

# Create necessary directories
os.makedirs("sessions", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("keys", exist_ok=True)

# Global variable to track Google Cloud services status
google_cloud_initialized = False

try:
    # Initialize Google services
    import google.generativeai as genai
    
    # Try to use credentials file if it exists
    if os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
        genai.configure(api_key=settings.API_KEY)
        logger.info("Google Cloud services initialized with credentials file")
        google_cloud_initialized = True
    # Otherwise, fall back to API key only
    else:
        logger.warning(f"Credentials file not found: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
        logger.warning("Using API key authentication only")
        genai.configure(api_key=settings.API_KEY)
        google_cloud_initialized = True
except Exception as e:
    logger.error(f"Error initializing Google Cloud services: {e}")
    logger.error(traceback.format_exc())
    # Continue without Google services

# Import routers - but make it optional to allow API docs to work
try:
    from routers import interview
    app.include_router(interview.router)
    logger.info("Successfully loaded interview router")
except Exception as e:
    logger.error(f"Error importing routers: {e}")
    logger.error(traceback.format_exc())
    # Continue without routers

@app.get("/")
async def root():
    """API root - returns basic information about the API"""
    return {
        "name": "VC Interview API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "google_cloud_status": "initialized" if google_cloud_initialized else "not available"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    # Check Google API connection
    google_cloud_status = "not configured"
    
    if google_cloud_initialized:
        try:
            # Simple test call to Gemini
            import google.generativeai as genai
            genai.GenerativeModel("gemini-1.5-pro-latest")
            google_cloud_status = "connected"
        except Exception as e:
            logger.error(f"Google Cloud health check failed: {e}")
            google_cloud_status = "error"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "google_cloud": google_cloud_status,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting VC Interview API in {settings.ENVIRONMENT} mode")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8080)),
        reload=settings.ENVIRONMENT != "production"
    )
