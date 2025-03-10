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

        # Log the process
        logger.info(f"Creating statement with expected label: '{expected_label}'")

        # Create a new statement
        statement = Statement(
            subject=subject,
            predicate=predicate,
            object=obj,
            context=context
        )

        # Log pre-save state
        logger.info(f"Before save, label is: '{statement.label}'")

        # Save the statement
        statement.save()

        # Log post-save state from the object
        logger.info(f"After save, in-memory label is: '{statement.label}'")

        # Get the statement ID for direct verification
        statement_id = statement.id
        statement_uuid = statement.uuid

        # Debug object attributes
        logger.info(f"Statement ID: {statement_id}, UUID: {statement_uuid}")
        logger.info(f"Statement object properties: {statement.__properties__}")

        # Verify the saved label through direct Cypher query using both ID and UUID
        query1 = "MATCH (s:Statement) WHERE ID(s)=$id RETURN s.label as label"
        results1, _ = db.cypher_query(query1, {"id": statement_id})

        query2 = "MATCH (s:Statement) WHERE s.uuid=$uuid RETURN s.label as label, s.subject, s.predicate, s.object, s.context"
        results2, _ = db.cypher_query(query2, {"uuid": str(statement_uuid)})

        if not results1 or not results2:
            logger.error("Statement not found in database")
            return False

        actual_label_by_id = results1[0][0]
        actual_label_by_uuid = results2[0][0]

        # Log all the results
        logger.info(f"Expected label: '{expected_label}'")
        logger.info(f"Actual label in DB (by ID): '{actual_label_by_id}'")
        logger.info(f"Actual label in DB (by UUID): '{actual_label_by_uuid}'")
        logger.info(f"DB values: subject='{results2[0][1]}', predicate='{results2[0][2]}', object='{results2[0][3]}', context='{results2[0][4]}'")

        # Double-check by refreshing from DB
        refreshed_statement = Statement.nodes.get(uuid=str(statement_uuid))
        logger.info(f"Refreshed statement label: '{refreshed_statement.label}'")

        if actual_label_by_uuid == expected_label:
            logger.info("SUCCESS: Label correctly concatenated and saved to database")
            return True
        else:
            logger.error(f"FAILED: Label mismatch. Database has '{actual_label_by_uuid}' instead of '{expected_label}'")

            # Let's try one more explicit update to see if it fixes the issue
            logger.info("Attempting direct Cypher update as a last resort...")
            direct_query = "MATCH (s:Statement) WHERE s.uuid=$uuid SET s.label=$label RETURN s.label"
            update_result, _ = db.cypher_query(direct_query, {"uuid": str(statement_uuid), "label": expected_label})

            if update_result and update_result[0][0] == expected_label:
                logger.info("Direct update successful! The issue might be with the save or pre_save mechanism.")
            else:
                logger.error("Even direct update failed.")

            return False

    except Exception as e:
        logger.error(f"Error testing statement label: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting statement label test...")
    test_statement_label()