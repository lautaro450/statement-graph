"""
Service layer for the Statement Graph API
"""
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from helpers.models import Statement, Topic
from core.services.llm_service import LLMService
from core.schemas.schemas import IngestionRequest, StatementWithTopics, TopicMatchingResult, IngestionResponse

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
    def process_ingestion_request(
        request: IngestionRequest, 
        intent: Optional[str] = None
    ) -> IngestionResponse:
        """
        Process an ingestion request by extracting statements and matching them to topics
        
        Args:
            request: The ingestion request containing text and metadata
            intent: Optional intent to guide topic generation and matching
            
        Returns:
            Response with processed statements and topic matches
        """
        logger.info(f"Processing ingestion request with metadata: {request.metadata}")
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Extract statements from text
        logger.info("Extracting statements from text")
        try:
            statements = llm_service.ingest_statements_from_transcript(request.text, intent=intent)
            logger.info(f"Successfully extracted {len(statements)} statements from text")
        except Exception as e:
            logger.error(f"Error extracting statements: {e}")
            raise Exception(f"Statement extraction failed: {str(e)}")
        
        # Get all topics for matching
        logger.info("Getting topics for matching")
        try:
            topics = Topic.nodes.all()
            topic_list = [{"id": str(topic.uuid), "label": topic.label} for topic in topics]
            logger.info(f"Found {len(topic_list)} topics for matching")
            
            # If no topics found in database, generate them from statements
            if not topic_list:
                logger.info("No topics found in database. Generating topics from statements.")
                generated_topics = llm_service.generate_topics_from_statements(statements, intent=intent)
                
                # Save generated topics to database
                for topic_data in generated_topics:
                    topic_label = topic_data.get("label")
                    topic_tags = topic_data.get("tags", [])
                    
                    # Create the topic in the database
                    try:
                        topic = IngestionService._create_or_get_topic(topic_label)
                        
                        # Add the topic to the list for matching
                        topic_list.append({
                            "id": str(topic.uuid),
                            "label": topic.label
                        })
                        
                        logger.info(f"Created new topic: {topic_label}")
                    except Exception as e:
                        logger.error(f"Error creating topic '{topic_label}': {e}")
                
                logger.info(f"Generated and saved {len(topic_list)} topics")
        except Exception as e:
            logger.error(f"Error getting topics: {e}")
            raise Exception(f"Topic retrieval failed: {str(e)}")
        
        # Match statements to topics
        logger.info("Matching statements to topics")
        try:
            # Perform batch processing for topic matching
            statements_with_topics = llm_service.match_statements_to_topics(
                statements, 
                topic_list, 
                intent=intent,
                batch_size=30
            )
            logger.info(f"Successfully matched {len(statements_with_topics)} statements to topics")
        except Exception as e:
            logger.error(f"Error matching statements to topics: {e}")
            raise Exception(f"Topic matching failed: {str(e)}")
        
        # Save statements to database
        logger.info("Saving statements to database")
        saved_statements = []
        try:
            for stmt in statements_with_topics:
                statement = Statement(
                    label=stmt.get("label", "Statement"),
                    subject=stmt.get("subject", ""),
                    predicate=stmt.get("predicate", ""),
                    object=stmt.get("object", ""),
                    context=stmt.get("context", "")
                ).save()
                
                # Connect to topics if any were matched
                for topic_info in stmt.get("topics", []):
                    try:
                        # Topics are now dictionaries with 'name' and 'tags'
                        if isinstance(topic_info, dict) and 'name' in topic_info:
                            # Create or get the topic by name
                            topic_name = topic_info['name']
                            topic = IngestionService._create_or_get_topic(topic_name)
                            
                            # Connect topic to statement using optimized method
                            topic.connect_to_statement(statement)
                            logger.debug(f"Connected topic {topic.uuid} to statement {statement.uuid} via HAS_STATEMENT")
                        else:
                            # Fallback for backward compatibility - if topic is a UUID string
                            try:
                                topic = Topic.nodes.get(uuid=topic_info)
                                topic.connect_to_statement(statement)
                                logger.debug(f"Connected topic {topic.uuid} to statement {statement.uuid} via HAS_STATEMENT")
                            except:
                                logger.warning(f"Invalid topic format: {topic_info}")
                    except Exception as e:
                        logger.error(f"Error connecting topic to statement: {e}")
                
                # If no topics were matched, try to create a default topic from the subject
                if not stmt.get("topics"):
                    try:
                        # Use the statement subject as a fallback topic
                        subject = stmt.get("subject", "").strip()
                        if subject and len(subject) > 2:  # Ensure it's not empty or very short
                            default_topic = IngestionService._create_or_get_topic(subject)
                            
                            # Connect using optimized method
                            default_topic.connect_to_statement(statement)
                            
                            logger.info(f"Created default topic from subject: {subject}")
                            
                            # Add the topic to the statement for response generation
                            if "topics" not in stmt:
                                stmt["topics"] = []
                            stmt["topics"].append({"name": subject})
                    except Exception as e:
                        logger.error(f"Error creating default topic from subject: {e}")
                
                saved_statements.append(statement)
            
            logger.info(f"Successfully saved {len(saved_statements)} statements to database")
        except Exception as e:
            logger.error(f"Error saving statements: {e}")
            raise Exception(f"Statement saving failed: {str(e)}")
        
        # Create response with statements and topics
        statement_responses = []
        for statement, processed in zip(saved_statements, statements_with_topics):
            # Map the matched topic info to proper TopicTag objects
            topic_tags = []
            for topic_info in processed.get("topics", []):
                if isinstance(topic_info, dict) and 'name' in topic_info:
                    # Create TopicTag from the topic info with or without tags
                    topic_tag = {
                        "name": topic_info['name']
                    }
                    
                    # Add tags if they exist
                    if 'tags' in topic_info and isinstance(topic_info['tags'], list):
                        topic_tag["tags"] = topic_info['tags'][:4]  # Limit to 4 tags
                    else:
                        # Default tags based on topic name
                        words = topic_info['name'].split()
                        topic_tag["tags"] = words[:4] if len(words) > 1 else [topic_info['name']]
                    
                    topic_tags.append(topic_tag)
                elif isinstance(topic_info, str):
                    # Handle string topics (older format or simple strings)
                    topic_tags.append({
                        "name": topic_info,
                        "tags": [topic_info]
                    })
            
            statement_responses.append(
                StatementWithTopics(
                    id=str(statement.uuid),
                    label=statement.label,
                    subject=statement.subject,
                    predicate=statement.predicate,
                    object=statement.object,
                    context=statement.context,
                    topics=topic_tags
                )
            )
        
        # Build final response
        response = IngestionResponse(
            status="success",
            message="Data ingested successfully",
            data={
                "original_request_metadata": request.metadata.dict(),
                "statement_count": len(statement_responses),
                "timestamp": datetime.now().isoformat()
            },
            topic_matches=TopicMatchingResult(statements=statement_responses)
        )
        
        logger.info("Ingestion request processing completed successfully")
        return response
    
    @staticmethod
    def _create_or_get_topic(label: str) -> Topic:
        """
        Create a new topic or get existing one with the given label
        
        If the label contains "/" characters, it will be treated as a hierarchical path
        and will create parent-child relationships between topics.
        
        Args:
            label: The topic label (e.g., "Parent" or "Parent/Child/Grandchild")
            
        Returns:
            The Topic object (the leaf node in case of hierarchical topics)
        """
        # Check if we have a hierarchical topic
        if "/" in label:
            parts = label.split("/")
            parent_label = parts[0]
            
            # Get or create the parent topic
            try:
                parent_topic = Topic.nodes.get(label=parent_label)
            except Topic.DoesNotExist:
                logger.info(f"Creating parent topic with label: {parent_label}")
                parent_topic = Topic(label=parent_label)
                parent_topic.save()
            
            # Process each level of the hierarchy
            current_topic = parent_topic
            for i in range(1, len(parts)):
                child_label = parts[i]
                
                # Try to find an existing child topic
                child_found = False
                for child in current_topic.children:
                    if child.label == child_label:
                        current_topic = child
                        child_found = True
                        break
                
                # Create the child if not found
                if not child_found:
                    logger.info(f"Creating child topic with label: {child_label} under {current_topic.label}")
                    child_topic = Topic(label=child_label)
                    child_topic.save()
                    
                    # Connect the child to the parent with optimized method
                    current_topic.connect_to_child(child_topic)
                    current_topic = child_topic
            
            return current_topic
        else:
            # Non-hierarchical topic - original behavior
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
