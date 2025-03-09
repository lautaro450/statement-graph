"""
FastAPI application for the Statement Graph API using mock database connections
for testing and development without requiring a live Neo4j instance.
"""
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import the mock database connection instead of the real one
from helpers.mock_db_connect import verify_connection
from core.schemas.schemas import IngestionRequest, IngestionResponse, TopicMatchingResult

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="Statement Graph API (MOCK MODE)",
    description="""
    API for extracting semantic statements from text and matching them to topics.
    
    RUNNING IN MOCK MODE - No database connection required.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

print("FastAPI app created, about to add CORS middleware")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize mock environment on startup"""
    print("Starting mock_app startup function")
    logger.info("Starting up Statement Graph API in MOCK mode...")
    
    # Verify mock database connection
    try:
        if verify_connection():
            logger.info("Successfully initialized mock database")
            app.state.db_connected = True
        else:
            logger.warning("Failed to initialize mock database")
            app.state.db_connected = False
    except Exception as e:
        print(f"Exception during mock setup: {str(e)}")
        logger.error(f"Exception during mock startup: {str(e)}")
        app.state.db_connected = False
    
    print("Completed mock_app startup function")

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
    return {
        "status": "healthy", 
        "mode": "mock",
        "database_connected": app.state.db_connected
    }

@app.post(
    "/ingestion/v1",
    response_model=IngestionResponse,
    summary="Ingest transcription data (MOCK)",
    description="Mock endpoint for ingestion that returns sample data",
    tags=["Ingestion"],
)
async def ingest_data(request: IngestionRequest) -> IngestionResponse:
    """
    Mock ingestion endpoint that returns sample data
    """
    logger.info("Received mock ingestion request")
    
    # Return a mock response
    return IngestionResponse(
        success=True,
        message="Data processed successfully (MOCK MODE)",
        metadata=request.metadata,
        statements=[
            {
                "subject": "User",
                "predicate": "requested",
                "object": "information",
                "context": "conversation",
                "confidence": 0.95,
                "source": request.metadata.transcription_id,
                "id": "mock-123",
                "topics": [{"name": "General", "tags": ["request", "information"]}]
            }
        ]
    )

if __name__ == "__main__":
    """
    Run the application with Uvicorn
    """
    import uvicorn
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run(
        "mock_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
