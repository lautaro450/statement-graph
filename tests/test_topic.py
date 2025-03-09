"""
import sys
import os
Test script for Topic schema validation
"""
import logging
from helpers.db_connect import verify_connection
from helpers.models import Topic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

)
logger = logging.getLogger(__name__)

def test_topic_schema_validation():
    """Test schema validation for Topic model"""
    
    # Test case 1: Valid topic
    try:
        topic = Topic(label="Test Topic")
        topic.save()
        logger.info(f"Test case 1 (Valid topic): SUCCESS - {topic}")
    except Exception as e:
        logger.error(f"Test case 1 (Valid topic): FAILED - {e}")
    
    # Test case 2: Missing required property
    try:
        topic = Topic()  # Missing label
        topic.save()
        logger.error("Test case 2 (Missing required property): FAILED - Validation should have failed")
    except Exception as e:
        logger.info(f"Test case 2 (Missing required property): SUCCESS - Validation correctly failed: {e}")
    
    # Test case 3: Duplicate label (should fail due to unique_index=True)
    try:
        topic1 = Topic(label="Duplicate Topic").save()
        topic2 = Topic(label="Duplicate Topic").save()
        logger.error("Test case 3 (Duplicate label): FAILED - Should not allow duplicate labels")
    except Exception as e:
        logger.info(f"Test case 3 (Duplicate label): SUCCESS - Validation correctly failed: {e}")
    
    # Test case 4: Retrieve topic by label
    try:
        topic = Topic.nodes.get(label="Test Topic")
        if topic:
            logger.info(f"Test case 4 (Retrieve by label): SUCCESS - Retrieved topic: {topic}")
        else:
            logger.error("Test case 4 (Retrieve by label): FAILED - Topic not found")
    except Exception as e:
        logger.error(f"Test case 4 (Retrieve by label): FAILED - {e}")

if __name__ == "__main__":
    # Verify connection to the database
    if verify_connection():
        test_topic_schema_validation()
    else:
        logger.error("Failed to connect to the database. Check your credentials and connection.")
