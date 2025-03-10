
"""
Test script to verify statement label concatenation
"""
import os
import sys
import logging
from helpers.db_connect import verify_connection
from helpers.models import Statement
from neomodel import db, config

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
        
        logger.info(f"Creating statement with expected label: '{expected_label}'")
        
        # Create a new statement
        statement = Statement(
            subject=subject,
            predicate=predicate,
            object=obj,
            context=context
        )
        
        # Log properties before save
        logger.info(f"Before save - Label: '{statement.label}'")
        logger.info(f"Before save - Subject: '{statement.subject}'")
        logger.info(f"Before save - Predicate: '{statement.predicate}'")
        logger.info(f"Before save - Object: '{statement.object}'")
        logger.info(f"Before save - Context: '{statement.context}'")
        
        # Save the statement
        statement.save()
        
        # Log properties after save
        logger.info(f"After save - Label: '{statement.label}'")
        logger.info(f"Statement UUID: {statement.uuid}")
        
        # Get the statement ID for direct verification
        statement_id = statement.id
        logger.info(f"Statement ID: {statement_id}")
        
        # Try to refresh from the database
        statement.refresh()
        logger.info(f"After refresh - Label: '{statement.label}'")
        
        # Verify the saved label through direct Cypher query
        query = "MATCH (s:Statement) WHERE s.uuid=$uuid RETURN s.label as label"
        results, meta = db.cypher_query(query, {"uuid": str(statement.uuid)})
        
        if not results:
            logger.error("Statement not found in database")
            return False
        
        actual_label = results[0][0]
        logger.info(f"Expected label: '{expected_label}'")
        logger.info(f"Actual label in database: '{actual_label}'")
        
        # Also try querying by ID
        query2 = "MATCH (s) WHERE id(s)=$id RETURN s.label as label"
        results2, meta2 = db.cypher_query(query2, {"id": statement_id})
        
        if results2:
            logger.info(f"Label by node ID query: '{results2[0][0]}'")
        else:
            logger.warning("Could not find node by ID")
        
        # Get all statements and check their labels
        all_statements = Statement.nodes.all()
        logger.info(f"Found {len(all_statements)} statements in database")
        
        for i, stmt in enumerate(all_statements):
            logger.info(f"Statement {i+1} - UUID: {stmt.uuid}, Label: '{stmt.label}'")
        
        if actual_label == expected_label:
            logger.info("SUCCESS: Label correctly concatenated and saved to database")
            return True
        else:
            logger.error(f"FAILED: Label mismatch. Database has '{actual_label}' instead of '{expected_label}'")
            return False
            
    except Exception as e:
        logger.error(f"Error testing statement label: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting statement label test...")
    test_statement_label()
