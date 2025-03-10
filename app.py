
"""
Statement Graph API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Statement Graph API",
    description="API for Statement Graph",
    version="1.0.0",
)

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
    logger.info("Starting up Statement Graph API...")

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to the API documentation
    """
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
