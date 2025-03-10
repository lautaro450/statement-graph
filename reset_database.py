
"""
Script to reset the database by removing all Statement nodes
"""
import os
import sys
import logging
from helpers.db_connect import verify_connection
from helpers.models import Statement
from neomodel import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_database():
    """Remove all Statement nodes from the database"""
    if not verify_connection():
        logger.error("Could not connect to the database")
        return False
    
    try:
        # Get count of statements before deletion
        count_before = len(Statement.nodes.all())
        logger.info(f"Found {count_before} Statement nodes before deletion")
        
        # Use Cypher query for efficient deletion
        query = "MATCH (s:Statement) DETACH DELETE s"
        db.cypher_query(query)
        
        # Verify deletion
        count_after = len(Statement.nodes.all())
        logger.info(f"Found {count_after} Statement nodes after deletion")
        
        if count_after == 0:
            logger.info("SUCCESS: All Statement nodes removed from the database")
            return True
        else:
            logger.error(f"FAILED: {count_after} Statement nodes still in the database")
            return False
    
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database reset...")
    reset_database()
