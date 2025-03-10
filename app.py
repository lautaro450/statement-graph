"""
FastAPI application for the Statement Graph API

This API provides endpoints for ingesting text data, extracting semantic statements,
and matching them to relevant topics. It uses a batch processing approach to optimize
performance when processing large volumes of statements.
"""
import logging
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os

from helpers.db_connect import verify_connection
from core.schemas.schemas import IngestionRequest, IngestionResponse, TopicMatchingResult
from core.services.services import IngestionService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app with detailed documentation
app = FastAPI(
    title="Statement Graph API",
    description="""
    API for extracting semantic statements from text and matching them to topics.
    
    Features:
    - Text ingestion and statement extraction
    - Topic matching with batch processing
    - Neo4j graph database integration
    
    The API implements a batch processing approach for topic matching, which processes
    statements in batches of 30 to optimize performance and prevent timeouts.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
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
    """Initialize database connection on startup"""
    print("Starting startup_event function")
    logger.info("Starting up Statement Graph API...")
    
    # Verify database connection
    print("About to verify database connection")
    try:
        if verify_connection():
            logger.info("Successfully connected to Neo4j database")
            app.state.db_connected = True
        else:
            logger.warning("Failed to connect to Neo4j database, but continuing startup")
            app.state.db_connected = False
            # Don't exit here, as the app might still be useful for documentation/testing
            # and we might reconnect later if the database becomes available
    except Exception as e:
        print(f"Exception during database connection verification: {str(e)}")
        logger.error(f"Exception during startup: {str(e)}")
        app.state.db_connected = False
        logger.warning("Continuing app startup despite database connection failure")
    
    print("Completed startup_event function")

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to the API documentation
    """
    return RedirectResponse(url="/docs")


@app.post(
    "/ingestion/v1",
    response_model=IngestionResponse,
    summary="Ingest transcription data",
    description="""
    Ingest transcription data and store it in the statement graph. 
    
    The service performs the following steps:
    1. Extracts statements from the transcription using Claude 3.7
    2. Stores statements in the Neo4j database
    3. Matches statements with relevant topics using batch processing
    4. Returns the processed results with topic matches
    
    The batch processing approach ensures efficient handling of large volumes of statements by processing them in smaller batches (30 statements per batch) to avoid timeouts and optimize API performance.
    """,
    tags=["Ingestion"],
    status_code=200,

@app.post(
    "/ingestion/v2",
    response_model=IngestionResponse,
    summary="Ingest transcription data with Voyage AI embeddings",
    description="""
    Ingest transcription data with Voyage AI embeddings and store it in the statement graph.
    
    The service performs the following steps:
    1. Extracts statements from the transcription
    2. Generates embeddings for statements using Voyage AI
    3. Stores statements and embeddings in the Neo4j database
    4. Matches statements with relevant topics using batch processing
    5. Returns the processed results with embeddings and topic matches
    
    This endpoint utilizes Voyage AI's state-of-the-art embedding models to enhance semantic search capabilities.
    """,
    tags=["Ingestion"],
    status_code=200,
    response_description="Successfully processed ingestion request with embeddings and topic matches",
)
async def ingest_data_v2(request: IngestionRequest) -> IngestionResponse:
    """
    Ingest transcription data with Voyage AI embeddings
    
    Args:
        request: The ingestion request data
        
    Returns:
        Response with status, embeddings and processing results
    """
    logger.info("Received ingestion v2 request (with embeddings)")
    
    # Check if VOYAGE_API_KEY is set
    if not os.getenv("VOYAGE_API_KEY"):
        logger.warning("VOYAGE_API_KEY environment variable not set")
        raise HTTPException(
            status_code=400,
            detail="Voyage AI API key not configured. Please set the VOYAGE_API_KEY environment variable."
        )
    
    # Log basic request information
    logger.info(f"Text length: {len(request.text)} chars")
    logger.info(f"Utterances: {len(request.utterances)}")
    logger.info(f"Transcription ID: {request.metadata.transcription_id}")
    
    # Log intent if specified
    if request.intent:
        logger.info(f"Intent specified: {request.intent}")
    
    # Check database connection status
    if not hasattr(app.state, 'db_connected') or not app.state.db_connected:
        logger.warning("Database not connected, will attempt to reconnect")
        try:
            if verify_connection():
                logger.info("Successfully reconnected to Neo4j database")
                app.state.db_connected = True
            else:
                logger.error("Still unable to connect to Neo4j database")
                raise HTTPException(
                    status_code=503,
                    detail="Database connection is unavailable. Please try again later."
                )
        except Exception as e:
            logger.error(f"Error reconnecting to database: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Database connection error: {str(e)}"
            )
    
    try:
        # Process the ingestion request with embeddings
        result = IngestionService.process_ingestion_v2(
            request,
            intent=request.intent
        )
        logger.info("Ingestion v2 request processing completed successfully with embeddings")
        return result
    except Exception as e:
        logger.error(f"Error processing ingestion v2 request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ingestion request: {str(e)}"
        )

    response_description="Successfully processed ingestion request with extracted statements and topic matches",
)
async def ingest_data(request: IngestionRequest) -> IngestionResponse:
    """
    Ingest transcription data endpoint
    
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
    
    # Check database connection status
    if not hasattr(app.state, 'db_connected') or not app.state.db_connected:
        logger.warning("Database not connected, will attempt to reconnect")
        try:
            if verify_connection():
                logger.info("Successfully reconnected to Neo4j database")
                app.state.db_connected = True
            else:
                logger.error("Still unable to connect to Neo4j database")
                raise HTTPException(
                    status_code=503,
                    detail="Database connection is unavailable. Please try again later."
                )
        except Exception as e:
            logger.error(f"Error reconnecting to database: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Database connection error: {str(e)}"
            )
    
    try:
        # Process the ingestion request
        result = IngestionService.process_ingestion_request(
            request,
            intent=request.intent
        )
        logger.info("Ingestion request processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing ingestion request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing ingestion request: {str(e)}"
        )


if __name__ == "__main__":
    """
    Run the application with Uvicorn
    """
    import uvicorn
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
