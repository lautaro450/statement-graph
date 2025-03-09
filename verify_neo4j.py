"""
Verify Neo4j connection using the official Neo4j Python driver
"""
import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection using the official Neo4j driver"""
    # Get credentials from environment variables
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    # Log connection attempt (with masked password)
    logger.info(f"Connecting to Neo4j at {neo4j_uri} with username: {neo4j_username}")
    
    # Convert URI format if needed
    driver_uri = neo4j_uri
    if neo4j_uri.startswith("neo4j+s://"):
        # Handle Aura DB format
        driver_uri = neo4j_uri.replace("neo4j+s://", "neo4j+s://")
    
    # Initialize driver
    driver = None
    try:
        logger.info(f"Attempting to connect with URI: {driver_uri}")
        driver = GraphDatabase.driver(
            driver_uri,
            auth=(neo4j_username, neo4j_password)
        )
        
        # Verify connectivity
        with driver.session() as session:
            # Run a simple query
            result = session.run("MATCH (n) RETURN count(n) AS count LIMIT 1")
            count = result.single()["count"]
            logger.info(f"Successfully connected to Neo4j. Database contains {count} nodes.")
            return True
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        if "Unauthorized" in str(e):
            logger.error("Authentication failed. Please check your Neo4j username and password.")
        
        # For Aura databases, suggest checking the connection string format
        if neo4j_uri.startswith("neo4j+s://"):
            logger.info("For Neo4j Aura, make sure you're using the correct connection string format:")
            logger.info("Example: neo4j+s://xxxxxxxx.databases.neo4j.io")
        return False
    finally:
        # Close driver if it was initialized
        if driver:
            driver.close()

if __name__ == "__main__":
    logger.info("Testing Neo4j connection...")
    if test_connection():
        logger.info("Neo4j connection test was successful!")
    else:
        logger.error("Neo4j connection test failed.")
        import sys
        sys.exit(1)
