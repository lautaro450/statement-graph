"""
Example usage of the Topic model with neomodel
"""
import logging
from helpers.db_connect import verify_connection
from helpers.models import Topic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_topic(label):
    """
    Create a new Topic node in the database
    """
    try:
        topic = Topic(label=label)
        topic.save()
        logger.info(f"Created topic: {topic}")
        return topic
    except Exception as e:
        logger.error(f"Failed to create topic: {e}")
        return None

def get_all_topics():
    """
    Retrieve all Topic nodes from the database
    """
    try:
        topics = Topic.nodes.all()
        logger.info(f"Retrieved {len(topics)} topics")
        return topics
    except Exception as e:
        logger.error(f"Failed to retrieve topics: {e}")
        return []

def get_topic_by_label(label):
    """
    Retrieve a Topic node by its label
    """
    try:
        topic = Topic.nodes.get(label=label)
        logger.info(f"Retrieved topic: {topic}")
        return topic
    except Topic.DoesNotExist:
        logger.error(f"Topic with label '{label}' not found")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve topic with label '{label}': {e}")
        return None

if __name__ == "__main__":
    # Verify connection to the database
    if verify_connection():
        # Create some example topics
        topics = [
            "Machine Learning",
            "Biology",
            "History",
            "Chemistry",
            "Physics"
        ]
        
        # Create each topic
        for topic_label in topics:
            create_topic(topic_label)
        
        # Retrieve all topics
        all_topics = get_all_topics()
        print("\nAll Topics:")
        for topic in all_topics:
            print(f"- {topic.to_dict()}")
        
        # Retrieve a specific topic
        ml_topic = get_topic_by_label("Machine Learning")
        if ml_topic:
            print(f"\nRetrieved Topic: {ml_topic.to_dict()}")
    else:
        logger.error("Failed to connect to the database. Check your credentials and connection.")
