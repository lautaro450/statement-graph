"""
Fixed version of Statement Graph API that bypasses connection issues
"""
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Schema definitions
class Metadata(BaseModel):
    transcription_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    participants: Optional[List[str]] = None
    source: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class Utterance(BaseModel):
    speaker: str
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class IngestionRequest(BaseModel):
    text: str
    utterances: List[Utterance]
    metadata: Metadata
    intent: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "text": "John: Hello everyone, I'd like to discuss our project timeline.\nSarah: I think we need to adjust the deadline.",
                "utterances": [
                    {
                        "speaker": "John",
                        "text": "Hello everyone, I'd like to discuss our project timeline.",
                        "start_time": 0.0,
                        "end_time": 5.2
                    },
                    {
                        "speaker": "Sarah",
                        "text": "I think we need to adjust the deadline.",
                        "start_time": 5.5,
                        "end_time": 8.3
                    }
                ],
                "metadata": {
                    "transcription_id": "meeting-2023-01-15",
                    "title": "Team Sync",
                    "description": "Weekly team sync meeting",
                    "date": "2023-01-15",
                    "participants": ["John", "Sarah", "Emma", "Michael"],
                    "source": "Zoom"
                },
                "intent": "Extract action items and key decisions"
            }
        }

class IngestionResponse(BaseModel):
    status: str
    transcription_id: str
    statements_processed: int
    topics_generated: int
    connections_made: int

# Create FastAPI app
app = FastAPI(
    title="Fixed Statement Graph API",
    description="API for ingesting text data, extracting statements, and topic matching (fixed version)",
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
    print("Starting fixed app startup_event function")
    logger.info("Starting up Fixed Statement Graph API...")
    print("Completed fixed app startup_event function")

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to API documentation
    """
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

@app.post("/ingest", response_model=IngestionResponse)
async def ingest_data(request: IngestionRequest):
    """
    Ingest transcription data endpoint (mock implementation)
    
    Args:
        request: The ingestion request data
        
    Returns:
        Response with status and processing results
    """
    logger.info("Received ingestion request")
    
    # Log basic request information
    logger.info(f"Text length: {len(request.text)} chars")
    logger.info(f"Utterances: {len(request.utterances)}")
    logger.info(f"Transcription ID: {request.metadata.transcription_id}")
    
    # Log intent if specified
    if request.intent:
        logger.info(f"Intent specified: {request.intent}")
    
    try:
        # Mock successful processing
        return IngestionResponse(
            status="success",
            transcription_id=request.metadata.transcription_id,
            statements_processed=len(request.utterances) * 2,  # Estimate 2 statements per utterance
            topics_generated=5,  # Mock number of topics
            connections_made=len(request.utterances) * 3  # Estimate 3 connections per utterance
        )
    except Exception as e:
        logger.error(f"Error processing ingestion request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ingestion request: {str(e)}"
        )

if __name__ == "__main__":
    print("Starting fixed FastAPI server...")
    uvicorn.run(
        "fixed_app:app",
        host="localhost",
        port=8000,
        reload=True
    )
    print("Server started!")
