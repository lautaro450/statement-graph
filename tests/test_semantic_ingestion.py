"""
import sys
Tests for the semantic ingestion endpoint with Claude integration
"""
import json
import logging
import os
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from dotenv import load_dotenv
# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app import app
from core.services.llm_service import LLMService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)


class TestSemanticIngestion(unittest.TestCase):
    """
    Test cases for the semantic ingestion endpoint
    """
    
    def setUp(self):
        """
        Set up test environment
        """
        # Sample ingestion data
        self.sample_data = {
            "text": "We discussed machine learning and neural networks. Then we talked about database indexing and query optimization.",
            "utterances": [
                {
                    "speaker": "Speaker1",
                    "text": "I've been working on a neural network model for image classification.",
                    "start": 0,
                    "end": 5000,
                    "confidence": 0.95
                },
                {
                    "speaker": "Speaker2",
                    "text": "That's interesting. We're optimizing our database queries for better performance.",
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
        
        # Sample LLM response
        self.sample_llm_response = {
            "statements": [
                {
                    "subject": "Speaker1",
                    "predicate": "said",
                    "object": "I've been working on a neural network model for image classification.",
                    "context": "Transcription 12345",
                    "confidence": 0.95,
                    "source": "test_service",
                    "_id": "test_id_1",
                    "topics": [
                        {
                            "name": "Machine Learning",
                            "tags": ["neural networks", "deep learning", "algorithms", "data science"]
                        }
                    ]
                },
                {
                    "subject": "Speaker2",
                    "predicate": "said",
                    "object": "That's interesting. We're optimizing our database queries for better performance.",
                    "context": "Transcription 12345",
                    "confidence": 0.92,
                    "source": "test_service",
                    "_id": "test_id_2", 
                    "topics": [
                        {
                            "name": "Database Systems",
                            "tags": ["query optimization", "indexing", "performance", "SQL"]
                        }
                    ]
                }
            ]
        }
    
    @patch.object(LLMService, 'match_statements_to_topics')
    def test_ingestion_endpoint_with_topic_matching(self, mock_match_topics):
        """
        Test that the ingestion endpoint correctly performs semantic analysis
        """
        # Mock the LLM service response
        mock_match_topics.return_value = self.sample_llm_response
        
        # Send request to the endpoint
        response = client.post(
            "/ingestion/v1",
            json=self.sample_data
        )
        
        # Log response for debugging
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        
        # Assert response status code
        self.assertEqual(response.status_code, 200)
        
        # Parse response content
        response_data = response.json()
        
        # Verify response structure
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["message"], "Data ingested successfully")
        self.assertIn("data", response_data)
        self.assertIn("topic_matches", response_data)
        
        # Verify topic matches
        topic_matches = response_data["topic_matches"]
        self.assertIn("statements", topic_matches)
        self.assertEqual(len(topic_matches["statements"]), 2)
        
        # Check that topic assignments are as expected
        first_statement = topic_matches["statements"][0]
        self.assertEqual(first_statement["topics"][0]["name"], "Machine Learning")
        self.assertIn("neural networks", first_statement["topics"][0]["tags"])
        
        second_statement = topic_matches["statements"][1]
        self.assertEqual(second_statement["topics"][0]["name"], "Database Systems")
        self.assertIn("query optimization", second_statement["topics"][0]["tags"])
        
        # Verify the LLM service was called correctly
        mock_match_topics.assert_called_once()
    
    @patch.object(LLMService, 'match_statements_to_topics')
    def test_ingestion_endpoint_without_api_keys(self, mock_match_topics):
        """
        Test that the ingestion endpoint handles missing API keys gracefully
        """
        # Mock the LLM service to return None (indicating API key issues)
        mock_match_topics.return_value = None
        
        # Send request to the endpoint
        response = client.post(
            "/ingestion/v1",
            json=self.sample_data
        )
        
        # Assert response status code is still successful
        self.assertEqual(response.status_code, 200)
        
        # Parse response content
        response_data = response.json()
        
        # Verify basic response structure
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["message"], "Data ingested successfully")
        self.assertIn("data", response_data)
        
        # Topic matches should be None
        self.assertIsNone(response_data.get("topic_matches"))


if __name__ == "__main__":
    unittest.main()
