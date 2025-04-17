import os
import logging
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Create FastAPI app with docs enabled
app = FastAPI(
    title="VentureAI API",
    description="API for VC interviews with AI feedback",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create minimal health check endpoints
@app.get("/")
async def root():
    """API root - returns basic information"""
    return {
        "name": "VentureAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting API on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
