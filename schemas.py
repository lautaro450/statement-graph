"""
Pydantic schemas for API request/response models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Utterance(BaseModel):
    """
    Representation of a single utterance in a transcription
    """
    speaker: str = Field(..., description="Speaker identifier (e.g., 'A', 'B', 'Speaker 1')")
    text: str = Field(..., description="Utterance text content")
    start: int = Field(..., description="Start time of utterance in milliseconds")
    end: int = Field(..., description="End time of utterance in milliseconds")
    confidence: float = Field(..., description="Transcription confidence score (0.0-1.0)")


class Metadata(BaseModel):
    """
    Metadata associated with the transcription
    """
    transcription_id: int = Field(..., description="Unique identifier for the transcription")
    audio_file_id: int = Field(..., description="Identifier for the source audio file")
    language: str = Field(..., description="Language code of transcription (e.g., 'en-US')")
    service: str = Field(..., description="Service used for transcription (e.g., 'assembly', 'whisper')")
    speakers_count: int = Field(..., description="Number of distinct speakers detected")


class IngestionRequest(BaseModel):
    """
    Schema for the ingestion endpoint request
    """
    text: str = Field(..., description="Full text of the transcription")
    utterances: List[Utterance] = Field(..., description="List of individual utterances with speaker and timing information")
    metadata: Metadata = Field(..., description="Additional information about the transcription")

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "A: Hello, how are you today? B: I'm doing well, thank you for asking.",
                "utterances": [
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
                ],
                "metadata": {
                    "transcription_id": 12345,
                    "audio_file_id": 67890,
                    "language": "en-US",
                    "service": "assembly",
                    "speakers_count": 2
                }
            }
        }
    }


class TopicTag(BaseModel):
    """
    Topic with tags for statement matching
    """
    name: str = Field(..., description="Name of the matched topic")
    tags: List[str] = Field(..., description="List of relevant tags associated with this topic (up to 4)")


class StatementWithTopics(BaseModel):
    """
    Statement with matched topics
    """
    subject: str = Field(..., description="Subject of the statement (who/what)")
    predicate: str = Field(..., description="Predicate of the statement (action/relation)")
    object: str = Field(..., description="Object of the statement (target of action/relation)")
    context: str = Field(..., description="Additional context for the statement")
    confidence: Optional[float] = Field(None, description="Confidence score for statement extraction (0.0-1.0)")
    source: Optional[str] = Field(None, description="Source of the statement (e.g., 'transcription', 'document')")
    id: str = Field(..., description="Unique identifier for the statement")  # Changed from _id to id
    topics: List[TopicTag] = Field(default_factory=list, description="Topics matched to this statement (up to 2)")


class TopicMatchingResult(BaseModel):
    """
    Result from topic matching
    
    Note: For large datasets, topic matching is performed in batches of 30 statements
    to optimize performance and prevent timeout issues.
    """
    statements: List[StatementWithTopics] = Field(..., description="List of statements with their matched topics")


class IngestionResponse(BaseModel):
    """
    Schema for the ingestion endpoint response
    """
    status: str = Field(..., description="Status of the request ('success' or 'error')")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data related to the ingestion process")
    topic_matches: Optional[TopicMatchingResult] = Field(None, description="Results of topic matching if available")
