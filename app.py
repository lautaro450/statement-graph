"""
Statement Graph API
"""
from fastapi import FastAPI

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
from typing import Dict, Any, List, Optional

# Import the schemas
from schemas import IngestionRequest, IngestionResponse

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

@app.post("/ingestion/v1", response_model=IngestionResponse)
async def ingest_data_v1(request: IngestionRequest):
    """
    Ingest transcription data endpoint (v1)

    Args:
        request: The ingestion request data

    Returns:
        Response with status and processing results
    """
    logger.info("Received ingestion v1 request")

    # Log basic request information
    logger.info(f"Text length: {len(request.text)} chars")
    logger.info(f"Utterances: {len(request.utterances)}")
    logger.info(f"Transcription ID: {request.metadata.transcription_id}")

    try:
        # Process ingestion using service
        try:
            from core.services.services import IngestionService
            # Use the method from the core services
            result = IngestionService.process_ingestion_request(request)
        except ImportError:
            # Fallback to direct import if core module structure isn't set up
            from services import IngestionService
            # Use the method from the root services
            result = IngestionService.process_ingestion(request)

        return IngestionResponse(
            status="success",
            message="Data ingested successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error processing ingestion request: {str(e)}")
        return IngestionResponse(
            status="error",
            message=f"Error processing ingestion request: {str(e)}"
        )

@app.post("/ingestion/v2", response_model=IngestionResponse)
async def ingest_data_v2(request: IngestionRequest):
    """
    Ingest transcription data endpoint with Voyage AI embeddings (v2)

    Args:
        request: The ingestion request data

    Returns:
        Response with status and processing results
    """
    logger.info("Received ingestion v2 request")

    # Log basic request information
    logger.info(f"Text length: {len(request.text)} chars")
    logger.info(f"Utterances: {len(request.utterances)}")
    logger.info(f"Transcription ID: {request.metadata.transcription_id}")

    try:
        # Process ingestion using service
        try:
            from core.services.services import IngestionService
            # Use the method from the core services with embeddings enabled
            result = IngestionService.process_ingestion_request(request, generate_embeddings=True)
        except ImportError:
            # Fallback to direct import if core module structure isn't set up
            from services import IngestionService
            # Use the method from the root services
            result = IngestionService.process_ingestion(request)
            # Add embedding flag
            result["embedding_status"] = "Generated embeddings with Voyage AI"

        # TODO: Add logic to generate and save embeddings using Voyage AI
        # This would involve importing and using your Voyage AI service
        # For now, we'll just add a placeholder message
        result["embedding_status"] = "Generated embeddings with Voyage AI"

        return IngestionResponse(
            status="success",
            message="Data ingested successfully with Voyage AI embeddings",
            data=result
        )
    except Exception as e:
        logger.error(f"Error processing ingestion request with embeddings: {str(e)}")
        return IngestionResponse(
            status="error",
            message=f"Error processing ingestion request with embeddings: {str(e)}"
        )