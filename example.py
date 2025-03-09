"""
Example usage of the Statement model with neomodel
"""
import logging
from helpers.db_connect import verify_connection
from helpers.models import Statement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_statement(label, subject, predicate, obj, context):
    """
    Create a new Statement node in the database
    """
    try:
        statement = Statement(
            label=label,
            subject=subject,
            predicate=predicate,
            object=obj,
            context=context
        )
        statement.save()
        logger.info(f"Created statement: {statement}")
        return statement
    except Exception as e:
        logger.error(f"Failed to create statement: {e}")
        return None

def get_all_statements():
    """
    Retrieve all Statement nodes from the database
    """
    try:
        statements = Statement.nodes.all()
        logger.info(f"Retrieved {len(statements)} statements")
        return statements
    except Exception as e:
        logger.error(f"Failed to retrieve statements: {e}")
        return []

def get_statements_by_subject(subject):
    """
    Retrieve all Statement nodes with a specific subject
    """
    try:
        statements = Statement.nodes.filter(subject=subject)
        logger.info(f"Retrieved {len(statements)} statements with subject '{subject}'")
        return statements
    except Exception as e:
        logger.error(f"Failed to retrieve statements with subject '{subject}': {e}")
        return []

if __name__ == "__main__":
    # Verify connection to the database
    if verify_connection():
        # Create some example statements
        create_statement(
            label="PersonHasPet",
            subject="Alice",
            predicate="has_pet",
            obj="Dog",
            context="Example"
        )
        
        create_statement(
            label="PersonLivesIn",
            subject="Alice",
            predicate="lives_in",
            obj="New York",
            context="Example"
        )
        
        create_statement(
            label="CityInCountry",
            subject="New York",
            predicate="in_country",
            obj="USA",
            context="Example"
        )
        
        # Retrieve all statements
        all_statements = get_all_statements()
        for statement in all_statements:
            print(f"Statement: {statement.to_dict()}")
        
        # Retrieve statements by subject
        alice_statements = get_statements_by_subject("Alice")
        print(f"\nAlice's statements:")
        for statement in alice_statements:
            print(f"- {statement}")
    else:
        logger.error("Failed to connect to the database. Check your credentials and connection.")
