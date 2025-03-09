"""
Services for processing ingestion data
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from schemas import IngestionRequest
from helpers.models import Statement, Topic
from llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for processing ingestion data and storing in Neo4j
    """
    
    @staticmethod
    def process_ingestion(data: IngestionRequest) -> Dict[str, Any]:
        """
        Process the ingestion data and store in Neo4j
        
        Args:
            data: The ingestion request data
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Create a topic for the transcription
            topic_label = f"Transcription-{data.metadata.transcription_id}"
            topic = IngestionService._create_or_get_topic(topic_label)
            
            # Process utterances
            statement_ids = []
            statements = []
            for utterance in data.utterances:
                statement = IngestionService._create_statement_from_utterance(utterance, data.metadata)
                if statement:
                    statement_ids.append(str(statement.uuid))
                    # Convert statement to dictionary for topic matching
                    statements.append({
                        "subject": statement.subject,
                        "predicate": statement.predicate,
                        "object": statement.object,
                        "context": statement.context,
                        "confidence": utterance.confidence,
                        "source": data.metadata.service,
                        "id": str(statement.uuid)
                    })
            
            # Match statements with topics
            topic_matches = None
            if statements:
                topic_matches = IngestionService.match_topics(statements)
            
            result = {
                "topic_id": str(topic.uuid),
                "topic_label": topic.label,
                "statements_count": len(statement_ids),
                "statement_ids": statement_ids,
                "statements": statements
            }
            
            # Add topic matches if available
            if topic_matches:
                result["topic_matches"] = topic_matches
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing ingestion data: {e}")
            raise
    
    @staticmethod
    def match_topics(statements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Match statements with relevant topics using the LLM service
        
        Args:
            statements: List of statements to match with topics
            
        Returns:
            A dictionary with topic matching results or None if no matches
        """
        try:
            # Get all available topics
            topics = IngestionService._get_all_topics_with_tags()
            
            if not topics:
                logger.warning("No topics available for matching")
                return None
            
            # Initialize LLM service
            llm_service = LLMService()
            
            # Log the number of statements to be processed
            statement_count = len(statements) 
            logger.info(f"Starting topic matching for {statement_count} statements with {len(topics)} topics")
            
            # Match statements to topics using batch processing
            matches = llm_service.match_statements_to_topics(statements, topics)
            
            # Ensure each statement has a 'topics' field, even if empty
            if 'statements' in matches:
                for statement in matches['statements']:
                    if 'topics' not in statement:
                        statement['topics'] = []
            
            logger.info(f"Matched {len(matches.get('statements', []))} statements with topics")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching topics: {e}")
            # Return a safe fallback
            for statement in statements:
                if 'topics' not in statement:
                    statement['topics'] = []
            return {"statements": statements}
    
    @staticmethod
    def _create_or_get_topic(label: str) -> Topic:
        """
        Create a new topic or get existing one with the given label
        
        Args:
            label: The topic label
            
        Returns:
            The Topic object
        """
        try:
            # Try to get existing topic
            return Topic.nodes.get(label=label)
        except Topic.DoesNotExist:
            # Create new topic if not exists
            logger.info(f"Creating new topic with label: {label}")
            topic = Topic(label=label)
            topic.save()
            return topic
    
    @staticmethod
    def _create_statement_from_utterance(utterance: Any, metadata: Any) -> Statement:
        """
        Create a statement from an utterance
        
        Args:
            utterance: The utterance data
            metadata: The metadata associated with the utterance
            
        Returns:
            The created Statement object
        """
        try:
            # Create a statement for the utterance
            statement = Statement(
                label="Utterance",
                subject=utterance.speaker,
                predicate="said",
                object=utterance.text,
                context=f"Transcription {metadata.transcription_id}"
            )
            statement.save()
            logger.info(f"Created statement: {statement}")
            return statement
        except Exception as e:
            logger.error(f"Error creating statement from utterance: {e}")
            return None
    
    @staticmethod
    def _get_all_topics_with_tags() -> List[Dict[str, Any]]:
        """
        Get all topics with their tags for topic matching
        
        Returns:
            List of topics with tags
        """
        # In a real implementation, this would fetch topics and tags from the database
        # For now, we'll return a sample set of topics with tags
        return [
            {
                "name": "Machine Learning",
                "tags": ["neural networks", "deep learning", "algorithms", "data science", "AI", "supervised learning", "unsupervised learning"]
            },
            {
                "name": "Database Systems",
                "tags": ["SQL", "NoSQL", "indexing", "query optimization", "ACID", "transactions", "data modeling"]
            },
            {
                "name": "Web Development",
                "tags": ["HTML", "CSS", "JavaScript", "React", "Angular", "Node.js", "frontend", "backend", "REST API"]
            },
            {
                "name": "DevOps",
                "tags": ["CI/CD", "Docker", "Kubernetes", "automation", "deployment", "monitoring", "cloud"]
            },
            {
                "name": "Cybersecurity",
                "tags": ["encryption", "authentication", "authorization", "vulnerabilities", "penetration testing", "firewalls", "security"]
            }
        ]
