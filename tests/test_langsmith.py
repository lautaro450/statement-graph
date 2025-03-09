"""
import sys
Tests for LangSmith integration in the LLM service
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock
import logging
from dotenv import load_dotenv

from langsmith import Client as LangSmithClient
from langsmith.run_trees import RunTree
# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from core.services.llm_service import LLMService

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestLangSmithIntegration(unittest.TestCase):
    """
    Test LangSmith tracing in the LLM service
    """

    def setUp(self):
        """
        Set up test environment variables
        """
        # Save original environment variables
        self.original_env = {
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY"),
            "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING"),
            "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT"),
            "LANGSMITH_ENDPOINT": os.getenv("LANGSMITH_ENDPOINT")
        }
        
    def tearDown(self):
        """
        Restore original environment variables
        """
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                if key in os.environ:
                    del os.environ[key]

    @patch('llm_service.LangSmithClient')
    @patch('llm_service.Anthropic')
    def test_langsmith_client_initialization(self, mock_anthropic, mock_langsmith):
        """
        Test that LangSmith client is properly initialized
        """
        # Setup mock
        mock_langsmith_instance = MagicMock()
        projects = [MagicMock()]
        projects[0].name = "some-other-project"
        mock_langsmith_instance.list_projects.return_value = projects
        mock_langsmith.return_value = mock_langsmith_instance
        
        # Initialize LLM service - will use real environment variables from .env
        llm_service = LLMService()
        
        # Verify LangSmith client was initialized
        self.assertIsNotNone(llm_service.langsmith)
        mock_langsmith.assert_called_once_with(
            api_key=os.getenv("LANGSMITH_API_KEY"),
            api_url=os.getenv("LANGSMITH_ENDPOINT")
        )
        
        # Verify attempt to create project
        mock_langsmith_instance.list_projects.assert_called_once()
        mock_langsmith_instance.create_project.assert_called_once_with(
            os.getenv("LANGSMITH_PROJECT", "statement-graph"), 
            description="Statement Graph Project"
        )

    @patch('llm_service.RunTree')
    @patch('llm_service.LangSmithClient')
    @patch('llm_service.Anthropic')
    def test_match_statements_with_langsmith_tracing(self, mock_anthropic, mock_langsmith, mock_run_tree):
        """
        Test the match_statements_to_topics method with LangSmith tracing
        """
        # Setup mocks
        mock_langsmith_instance = MagicMock()
        mock_langsmith_instance.list_projects.return_value = projects = [MagicMock()]
        projects[0].name = "some-other-project"
        mock_langsmith.return_value = mock_langsmith_instance
        
        mock_anthropic_instance = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """```json
        {
          "statements": [
            {
              "subject": "User",
              "predicate": "likes",
              "object": "coffee",
              "context": "morning routine",
              "confidence": 0.95,
              "source": "conversation",
              "_id": "123",
              "topics": [
                {
                  "name": "Beverages",
                  "tags": ["coffee", "drinks", "caffeine", "morning"]
                }
              ]
            }
          ]
        }
        ```"""
        mock_response.content = [mock_content]
        mock_anthropic_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Setup RunTree mock
        mock_run_tree_instance = MagicMock()
        mock_run_tree.return_value = mock_run_tree_instance
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Test data
        statements = [
            {
                "subject": "User",
                "predicate": "likes",
                "object": "coffee",
                "context": "morning routine",
                "confidence": 0.95,
                "source": "conversation",
                "_id": "123"
            }
        ]
        
        topics = [
            {
                "name": "Beverages",
                "tags": ["coffee", "tea", "water", "juice", "soda", "drinks", "caffeine", "morning"]
            }
        ]
        
        # Call the method
        result = llm_service.match_statements_to_topics(statements, topics)
        
        # Verify results
        self.assertIn("statements", result)
        self.assertEqual(len(result["statements"]), 1)
        self.assertIn("topics", result["statements"][0])
        self.assertEqual(result["statements"][0]["topics"][0]["name"], "Beverages")
        
        # Verify LangSmith tracing was used
        mock_run_tree.assert_called()
        mock_run_tree_instance.end.assert_called()
        mock_run_tree_instance.add_metadata.assert_called()

    @patch('llm_service.RunTree')
    @patch('llm_service.LangSmithClient')
    @patch('llm_service.Anthropic')
    def test_ingest_statements_from_transcript(self, mock_anthropic, mock_langsmith, mock_run_tree):
        """
        Test the ingest_statements_from_transcript method with LangSmith tracing
        """
        # Setup mocks
        mock_langsmith_instance = MagicMock()
        mock_langsmith_instance.list_projects.return_value = projects = [MagicMock()]
        projects[0].name = "some-other-project"
        mock_langsmith.return_value = mock_langsmith_instance
        
        mock_anthropic_instance = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """```json
        [
          {
            "subject": "John",
            "predicate": "mentioned",
            "object": "quarterly budget",
            "context": "during planning meeting",
            "confidence": 0.95,
            "source": "John said we need to review the quarterly budget figures."
          },
          {
            "subject": "Team",
            "predicate": "agreed",
            "object": "project timeline",
            "context": "after discussion",
            "confidence": 0.89,
            "source": "After some back and forth, the team agreed on the project timeline."
          }
        ]
        ```"""
        mock_response.content = [mock_content]
        mock_anthropic_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Setup RunTree mock
        mock_run_tree_instance = MagicMock()
        mock_run_tree.return_value = mock_run_tree_instance
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Test data
        transcript = """
        Meeting Transcript - Project Planning
        
        John: Good morning everyone. We need to review the quarterly budget figures.
        Sarah: I've prepared the spreadsheet with all the data.
        John: Great, thank you Sarah.
        Alex: After looking at these numbers, I think we might need to adjust our timeline.
        Sarah: I agree with Alex, the current schedule seems tight given our resources.
        John: Let's discuss options then.
        [discussion continues for 15 minutes]
        John: So we're all on the same page now?
        Sarah: Yes, I think so.
        Alex: After some back and forth, the team agreed on the project timeline.
        """
        
        # Call the method
        result = llm_service.ingest_statements_from_transcript(transcript)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["subject"], "John")
        self.assertEqual(result[0]["predicate"], "mentioned")
        self.assertEqual(result[0]["object"], "quarterly budget")
        
        # Verify LangSmith tracing was used
        mock_run_tree.assert_called()
        mock_run_tree_instance.end.assert_called()
        mock_run_tree_instance.add_metadata.assert_called()

    @patch('llm_service.LangSmithClient')
    @patch('llm_service.Anthropic')
    def test_error_handling_in_langsmith_tracing(self, mock_anthropic, mock_langsmith):
        """
        Test error handling when LangSmith tracing fails
        """
        # Setup mock for LangSmith to raise an exception
        mock_langsmith_instance = MagicMock()
        mock_langsmith_instance.list_projects.side_effect = Exception("LangSmith connection error")
        mock_langsmith.return_value = mock_langsmith_instance
        
        # Setup mock for Anthropic to return valid response
        mock_anthropic_instance = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """```json
        {
          "statements": [
            {
              "subject": "User",
              "predicate": "likes",
              "object": "coffee",
              "context": "morning routine",
              "confidence": 0.95,
              "source": "conversation",
              "_id": "123",
              "topics": [
                {
                  "name": "Beverages",
                  "tags": ["coffee", "drinks", "caffeine", "morning"]
                }
              ]
            }
          ]
        }
        ```"""
        mock_response.content = [mock_content]
        mock_anthropic_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Test data
        statements = [
            {
                "subject": "User",
                "predicate": "likes",
                "object": "coffee",
                "context": "morning routine",
                "confidence": 0.95,
                "source": "conversation",
                "_id": "123"
            }
        ]
        
        topics = [
            {
                "name": "Beverages",
                "tags": ["coffee", "tea", "water", "juice", "soda", "drinks", "caffeine", "morning"]
            }
        ]
        
        # Call the method - it should fall back to non-traced execution
        result = llm_service.match_statements_to_topics(statements, topics)
        
        # Verify results still contain expected data
        self.assertIn("statements", result)
        self.assertEqual(len(result["statements"]), 1)

    def test_integration_with_real_apis(self):
        """
        Test with real APIs if environment variables are properly set
        """
        # Skip test if API keys are not set or if we're in CI
        if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("LANGSMITH_API_KEY"):
            self.skipTest("API keys not set")
            
        # Initialize real LLM service
        llm_service = LLMService()
        
        # Test data
        statements = [
            {
                "subject": "User",
                "predicate": "likes",
                "object": "coffee",
                "context": "morning routine",
                "confidence": 0.95,
                "source": "conversation",
                "_id": "123"
            }
        ]
        
        topics = [
            {
                "name": "Beverages",
                "tags": ["coffee", "tea", "water", "juice", "soda", "drinks", "caffeine", "morning"]
            }
        ]
        
        # Call the method with real APIs
        try:
            result = llm_service.match_statements_to_topics(statements, topics)
            
            # Verify results
            self.assertIn("statements", result)
            self.assertEqual(len(result["statements"]), 1)
            self.assertIn("topics", result["statements"][0])
        except Exception as e:
            self.fail(f"Integration test failed: {e}")


if __name__ == "__main__":
    unittest.main()
