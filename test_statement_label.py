
"""
Test script to verify statement label concatenation
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

def test_statement_label():
    """Test statement label concatenation"""
    # Verify database connection
    if not verify_connection():
        logger.error("Could not connect to the database")
        return False
    
    try:
        # Create test data
        subject = "John"
        predicate = "works at"
        obj = "Acme Corp"
        context = "Employment"
        expected_label = f"{subject} {predicate} {obj} {context}"
        
        # Create a new statement
        statement = Statement(
            subject=subject,
            predicate=predicate,
            object=obj,
            context=context
        ).save()
        
        # Get the statement ID for direct verification
        statement_id = statement.id
        
        # Verify the saved label through direct Cypher query
        query = "MATCH (s:Statement) WHERE id(s)=$id RETURN s.label as label"
        results, meta = db.cypher_query(query, {"id": statement_id})
        
        if not results:
            logger.error("Statement not found in database")
            return False
        
        actual_label = results[0][0]
        logger.info(f"Expected label: {expected_label}")
        logger.info(f"Actual label in database: {actual_label}")
        
        if actual_label == expected_label:
            logger.info("SUCCESS: Label correctly concatenated and saved to database")
            return True
        else:
            logger.error(f"FAILED: Label mismatch. Database has '{actual_label}' instead of '{expected_label}'")
            return False
            
    except Exception as e:
        logger.error(f"Error testing statement label: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting statement label test...")
    test_statement_label()
