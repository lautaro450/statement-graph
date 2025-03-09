"""
Pytest fixtures for Statement Graph tests
"""
import os
import sys
import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import from the root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client for testing"""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="""
    {
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
    """)]
    mock.messages.create.return_value = mock_response
    return mock

@pytest.fixture
def sample_utterances():
    """Sample utterances for testing"""
    return [
        {
            "speaker": "A",
            "text": "Hello, how are you today?",
            "start": 0,
            "end": 2500,
            "confidence": 0.95
        },
        {
            "speaker": "B",
            "text": "I'm doing well, thank you for asking.",
            "start": 3000,
            "end": 5500,
            "confidence": 0.92
        }
    ]

@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        "transcription_id": 12345,
        "audio_file_id": 67890,
        "language": "en-US",
        "service": "assembly",
        "speakers_count": 2
    }
