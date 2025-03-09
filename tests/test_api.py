"""
import sys
import os
Tests for the FastAPI endpoints
"""
import json
import logging
from fastapi.testclient import TestClient

from app import app

# Configure logging
logging.basicConfig(
# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)


def test_ingestion_endpoint():
    """
    Test the ingestion endpoint
    """
    # Sample ingestion data
    sample_data = {
        "text": "Hello, this is a test transcription.",
        "utterances": [
            {
                "speaker": "Speaker1",
                "text": "Hello, this is a test.",
                "start": 0,
                "end": 5000,
                "confidence": 0.95
            },
            {
                "speaker": "Speaker2",
                "text": "Yes, it's working.",
                "start": 5500,
                "end": 8000,
                "confidence": 0.92
            }
        ],
        "metadata": {
            "transcription_id": 12345,
            "audio_file_id": 67890,
            "language": "en",
            "service": "test_service",
            "speakers_count": 2
        }
    }
    
    # Send request to the endpoint
    response = client.post(
        "/ingestion/v1",
        json=sample_data
    )
    
    # Log response for debugging
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response content: {response.content}")
    
    # Assert response
    assert response.status_code == 200
    
    # Parse response content
    response_data = response.json()
    
    # Verify response structure
    assert response_data["status"] == "success"
    assert response_data["message"] == "Data ingested successfully"
    assert "data" in response_data
    
    # Verify ingestion results
    data = response_data["data"]
    assert "topic_id" in data
    assert "topic_label" in data
    assert data["topic_label"] == f"Transcription-{sample_data['metadata']['transcription_id']}"
    assert "statements_count" in data
    assert data["statements_count"] == len(sample_data["utterances"])
    assert "statement_ids" in data
    assert len(data["statement_ids"]) == len(sample_data["utterances"])


if __name__ == "__main__":
    """
    Run the tests
    """
    test_ingestion_endpoint()
    logger.info("All tests passed!")
