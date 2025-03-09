"""
Simplified version of the Statement Graph API
"""
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Simplified Statement Graph API",
    description="Simplified API for testing startup issues",
    version="1.0.0",
)

print("FastAPI app created, about to add CORS middleware")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Starting simplified startup_event function")
    logger.info("Starting up Simplified Statement Graph API...")
    print("Completed simplified startup_event function")

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that returns a simple message
    """
    return {"message": "Simplified Statement Graph API is running"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting simplified FastAPI server...")
    uvicorn.run(
        "simple_app:app",
        host="localhost",
        port=8888,
        reload=True
    )
    print("Server started!")
