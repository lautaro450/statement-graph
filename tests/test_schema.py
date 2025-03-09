"""
Tests for schema validation
"""
import sys
import os
import json
import pytest
from pydantic import ValidationError
from helpers.db_connect import verify_connection
from helpers.models import Statement

# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas.schemas import (
    Utterance, 
    Metadata, 
    IngestionRequest, 
    TopicTag, 
    StatementWithTopics, 
    TopicMatchingResult, 
    IngestionResponse
)

def test_schema_validation():
    """Test schema validation"""
    # Test valid utterance
    utterance = Utterance(
        speaker="A",
        text="Hello, how are you today?",
        start=0,
        end=2500,
        confidence=0.95
    )
    assert utterance.speaker == "A"
    assert utterance.text == "Hello, how are you today?"
    assert utterance.start == 0
    assert utterance.end == 2500
    assert utterance.confidence == 0.95
    
    # Test valid metadata
    metadata = Metadata(
        transcription_id=12345,
        audio_file_id=67890,
        language="en-US",
        service="assembly",
        speakers_count=2
    )
    assert metadata.transcription_id == 12345
    assert metadata.audio_file_id == 67890
    assert metadata.language == "en-US"
    assert metadata.service == "assembly"
    assert metadata.speakers_count == 2
    
    # Test valid topic tag
    topic = TopicTag(
        name="Preferences",
        tags=["food", "drinks", "activities", "media"]
    )
    assert topic.name == "Preferences"
    assert len(topic.tags) == 4
    assert "food" in topic.tags
    
    # Test valid statement with topics
    statement = StatementWithTopics(
        subject="User",
        predicate="likes",
        object="coffee",
        context="morning routine",
        confidence=0.95,
        source="conversation",
        id="123",
        topics=[topic]
    )
    assert statement.subject == "User"
    assert statement.predicate == "likes"
    assert statement.object == "coffee"
    assert statement.context == "morning routine"
    assert statement.confidence == 0.95
    assert statement.source == "conversation"
    assert statement.id == "123"
    assert len(statement.topics) == 1
    assert statement.topics[0].name == "Preferences"
    
    # Test invalid topic tag (missing required field)
    with pytest.raises(ValidationError):
        TopicTag(tags=["food", "drinks"])
        
    # Test invalid topic tag (tags too long)
    with pytest.raises(ValidationError):
        TopicTag(
            name="Preferences",
            tags=["food", "drinks", "activities", "media", "too", "many", "tags"]
        )
    
    # Test case 1: Valid statement
    try:
        statement = Statement(
            label="PersonHasPet",
            subject="Bob",
            predicate="has_pet",
            object="Cat",
            context="Test"
        )
        statement.save()
        assert True
    except Exception as e:
        assert False, f"Test case 1 (Valid statement): FAILED - {e}"
    
    # Test case 2: Missing required property
    try:
        statement = Statement(
            label="PersonHasPet",
            # Missing subject
            predicate="has_pet",
            object="Cat"
        )
        statement.save()
        assert False, "Test case 2 (Missing required property): FAILED - Validation should have failed"
    except Exception as e:
        assert True, f"Test case 2 (Missing required property): SUCCESS - Validation correctly failed: {e}"
    
    # Test case 3: Missing context (now required)
    try:
        statement = Statement(
            label="PersonHasFriend",
            subject="Charlie",
            predicate="has_friend",
            object="Dave",
            # Missing context (now required)
        )
        statement.save()
        assert False, "Test case 3 (Missing context): FAILED - Validation should have failed"
    except Exception as e:
        assert True, f"Test case 3 (Missing context): SUCCESS - Validation correctly failed: {e}"
    
    # Test case 4: All required properties
    try:
        statement = Statement(
            label="PersonHasFriend",
            subject="Charlie",
            predicate="has_friend",
            object="Dave",
            context="Test"  # Context is now required
        )
        statement.save()
        assert True
    except Exception as e:
        assert False, f"Test case 4 (All required properties): FAILED - {e}"
    
    # Test case 5: Query by property
    try:
        statements = Statement.nodes.filter(subject="Charlie")
        if statements:
            assert True
        else:
            assert False, "Test case 5 (Query by property): FAILED - No statements found"
    except Exception as e:
        assert False, f"Test case 5 (Query by property): FAILED - {e}"

if __name__ == "__main__":
    # Verify connection to the database
    if verify_connection():
        test_schema_validation()
    else:
        print("Failed to connect to the database. Check your credentials and connection.")
