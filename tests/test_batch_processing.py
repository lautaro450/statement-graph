"""
Tests for batch processing functionality
"""
import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.llm_service import LLMService
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

class TestBatchProcessing:
    """Test case for batch processing in the LLM service"""
    
    @patch('llm_service.LLMService._process_statement_batch')
    def test_batch_processing(self, mock_process_batch):
        """Test that statements are processed in batches of 30"""
        # Set up mock return value for _process_statement_batch
        mock_process_batch.return_value = {
            "statements": [
                {
                    "subject": "User", 
                    "predicate": "likes", 
                    "object": "coffee",
                    "context": "morning routine",
                    "confidence": 0.95,
                    "source": "conversation",
                    "id": "123",
                    "topics": [{"name": "Preferences", "tags": ["food", "drinks"]}]
                }
            ]
        }
        
        # Create a large number of statements (more than one batch)
        statements = []
        for i in range(31):
            statements.append({
                "subject": f"User {i}",
                "predicate": "likes",
                "object": "coffee",
                "context": "morning routine",
                "confidence": 0.95,
                "source": "conversation",
                "id": str(i)
            })
        
        topics = [{"name": "Preferences", "tags": ["food", "drinks", "activities", "media"]}]
        
        # Instantiate the LLM service
        llm_service = LLMService()
        
        # Call the method under test
        result = llm_service.match_statements_to_topics(statements, topics)
        
        # Check that _process_statement_batch was called twice (one batch of 30, one of 1)
        assert mock_process_batch.call_count == 2
        
        # Check that the result includes all statements
        assert len(result["statements"]) == 31
        
        # Check that each statement has topics
        for statement in result["statements"]:
            assert "topics" in statement
    
    @patch('anthropic.Anthropic')
    def test_process_statement_batch(self, mock_anthropic_class):
        """Test processing a batch of statements"""
        # Set up mock Anthropic client
        mock_anthropic = MagicMock()
        mock_anthropic_class.return_value = mock_anthropic
        
        # Set up mock response from Anthropic
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "statements": [
                {
                    "subject": "User",
                    "predicate": "likes",
                    "object": "coffee",
                    "context": "morning routine",
                    "confidence": 0.95,
                    "source": "conversation",
                    "id": "123",
                    "topics": [{"name": "Preferences", "tags": ["food", "drinks"]}]
                }
            ]
        }))]
        mock_anthropic.messages.create.return_value = mock_response
        
        # Create test data - a small batch of statements
        statements = [{
            "subject": "User",
            "predicate": "likes",
            "object": "coffee",
            "context": "morning routine",
            "confidence": 0.95,
            "source": "conversation",
            "id": "123"
        }]
        topics = [{"name": "Preferences", "tags": ["food", "drinks", "activities", "media"]}]
        
        # Instantiate the LLM service and process a batch
        llm_service = LLMService()
        result = llm_service._process_statement_batch(statements, topics)
        
        # Check that Anthropic was called with the right parameters
        mock_anthropic.messages.create.assert_called_once()
        
        # Check the result
        assert "statements" in result
        assert len(result["statements"]) == 1
        assert result["statements"][0]["id"] == "123"
        assert len(result["statements"][0]["topics"]) == 1
        assert result["statements"][0]["topics"][0]["name"] == "Preferences"
        
if __name__ == "__main__":
    pytest.main()
