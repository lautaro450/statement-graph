"""
Debug version of the app.py file with additional logging
"""
import logging
import os
import traceback
import sys
import time

print("Debug app starting at:", time.time())

try:
    print("About to import FastAPI and other core modules")
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import RedirectResponse
    print("Successfully imported FastAPI modules")
except Exception as e:
    print(f"Error importing FastAPI: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configure logging
print("Setting up logging")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    print("About to import helpers.db_connect")
    from helpers.db_connect import verify_connection
    print("Successfully imported verify_connection")
except Exception as e:
    print(f"Error importing verify_connection: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("About to import schemas")
    from core.schemas.schemas import IngestionRequest, IngestionResponse, TopicMatchingResult
    print("Successfully imported schemas")
except Exception as e:
    print(f"Error importing schemas: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("About to import services")
    from core.services.services import IngestionService
    print("Successfully imported IngestionService")
except Exception as e:
    print(f"Error importing IngestionService: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Creating FastAPI app")
# Create the FastAPI app with detailed documentation
app = FastAPI(
    title="Statement Graph API (DEBUG)",
    description="Debug version of the Statement Graph API",
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
    """Initialize database connection on startup"""
    print("Starting debug startup_event function at:", time.time())
    logger.info("Starting up Debug Statement Graph API...")
    
    # Verify database connection
    print("About to verify database connection")
    try:
        start_time = time.time()
        print(f"Starting verify_connection at {start_time}")
        connection_result = verify_connection()
        end_time = time.time()
        print(f"verify_connection completed in {end_time - start_time:.2f} seconds, result: {connection_result}")
        
        if connection_result:
            logger.info("Successfully connected to Neo4j database")
            app.state.db_connected = True
        else:
            logger.warning("Failed to connect to Neo4j database, but continuing startup")
            app.state.db_connected = False
    except Exception as e:
        print(f"Exception during database connection verification: {str(e)}")
        traceback.print_exc()
        logger.error(f"Exception during startup: {str(e)}")
        app.state.db_connected = False
        logger.warning("Continuing app startup despite database connection failure")
    
    print("Completed debug startup_event function at:", time.time())

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
        "db_connected": getattr(app.state, "db_connected", False),
        "mode": "debug"
    }

if __name__ == "__main__":
    """
    Run the application with Uvicorn
    """
    import uvicorn
    
    print("Starting debug Uvicorn server")
    # Run the FastAPI application with Uvicorn
    uvicorn.run(
        "debug_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
