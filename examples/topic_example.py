"""
Example script for creating and querying topics
"""
import sys
import os
import logging

# Add project root to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.db_connect import verify_connection
from helpers.models import Topic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_topic(label):
    """Create a new topic node"""
    # Check database connection
    if not verify_connection():
        logger.error("Could not connect to the database")
        return False

    try:
        # Create a new topic
        topic = Topic(
            label=label
        ).save()
        
        logger.info(f"Created topic: {topic.label}")
        logger.info(f"UUID: {topic.uuid}")
        
        return topic
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
        return None

def get_all_topics():
    """Get all topics"""
    if not verify_connection():
        logger.error("Could not connect to the database")
        return []
    
    try:
        topics = Topic.nodes.all()
        
        logger.info(f"Found {len(topics)} topics")
        for topic in topics:
            logger.info(f"- {topic.label} (UUID: {topic.uuid})")
        
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics: {e}")
        return []

if __name__ == "__main__":
    # Create some example topics
    topics = [
        "Technology",
        "Business",
        "Health",
        "Science",
        "Politics"
    ]
    
    for topic_label in topics:
        created_topic = create_topic(topic_label)
        if created_topic:
            logger.info(f"Successfully created topic: {created_topic.label}")
    
    # Retrieve all topics
    get_all_topics()
