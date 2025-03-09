"""
Example script for creating and querying statements
"""
import sys
import os
import logging

# Add project root to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.db_connect import verify_connection
from helpers.models import Statement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_statement():
    """Create a new statement node"""
    # Check database connection
    if not verify_connection():
        logger.error("Could not connect to the database")
        return False

    try:
        # Create a new statement
        statement = Statement(
            label="Example Statement",
            subject="Alice",
            predicate="works at",
            object="Acme Corp",
            context="Employment information"
        ).save()
        
        logger.info(f"Created statement: {statement.label}")
        logger.info(f"UUID: {statement.uuid}")
        logger.info(f"Subject: {statement.subject}")
        logger.info(f"Predicate: {statement.predicate}")
        logger.info(f"Object: {statement.object}")
        logger.info(f"Context: {statement.context}")
        logger.info(f"Created at: {statement.created_at}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating statement: {e}")
        return False

def get_statements_by_subject(subject):
    """Get statements by subject"""
    if not verify_connection():
        logger.error("Could not connect to the database")
        return []
    
    try:
        statements = Statement.nodes.filter(subject=subject)
        
        logger.info(f"Found {len(list(statements))} statements with subject '{subject}'")
        for statement in statements:
            logger.info(f"- {statement.subject} {statement.predicate} {statement.object} ({statement.context})")
        
        return statements
    except Exception as e:
        logger.error(f"Error retrieving statements: {e}")
        return []

if __name__ == "__main__":
    if create_statement():
        logger.info("Successfully created a statement")
        
    # Query statements
    get_statements_by_subject("Alice")
