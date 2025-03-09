"""
Direct Neo4j connection test with hardcoded credentials from .env
"""
import logging
from neomodel import db, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Direct credentials from .env
NEO4J_URI = "neo4j+s://d75dbf88.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Pusm4162mgGxj1faacyc9wCrOEsD3YemTjWuS7XuSSk"

# Configure neomodel directly with the credentials
connection_string = f"bolt+s://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@d75dbf88.databases.neo4j.io"
config.DATABASE_URL = connection_string
config.AUTO_INSTALL_LABELS = True
config.ENCRYPTED = True

def direct_test():
    """Test connection directly with the hardcoded credentials"""
    try:
        # Show the connection string (with masked password)
        masked_conn = connection_string.replace(NEO4J_PASSWORD, "********")
        logger.info(f"Trying direct connection with: {masked_conn}")
        
        # Run a simple query
        results, meta = db.cypher_query("MATCH (n) RETURN count(n) AS count LIMIT 1")
        count = results[0][0]
        logger.info(f"Connection successful! Database contains {count} nodes.")
        return True
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing direct Neo4j connection...")
    if direct_test():
        logger.info("Direct connection test successful!")
    else:
        logger.error("Direct connection test failed.")
