"""
Neo4j database connection setup with neomodel
"""
import os
import logging
from dotenv import load_dotenv
from neomodel import config, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure the .env file is loaded from the correct location
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
logger.info(f"Loading .env file from: {env_path}")

# Load environment variables from .env file with force reload
load_dotenv(env_path, override=True)

# Get credentials from environment variables - print for debugging
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Log that we got the variables
logger.info(f"Loaded NEO4J_URI: {NEO4J_URI}")
logger.info(f"Loaded NEO4J_USERNAME: {NEO4J_USERNAME}")
if NEO4J_PASSWORD:
    # Print partial password for security
    password_masked = NEO4J_PASSWORD[:4] + "*" * (len(NEO4J_PASSWORD) - 4)
    logger.info(f"Loaded NEO4J_PASSWORD (partial): {password_masked}")
else:
    logger.error("NEO4J_PASSWORD not loaded from .env file!")

# Configure neomodel
# Properly format the connection URL based on URI format
if NEO4J_URI.startswith("neo4j+s://"):
    # Handle neo4j+s:// format (cloud hosted Neo4j like Aura)
    # Format: bolt+s://username:password@hostname:port
    host_port = NEO4J_URI.replace("neo4j+s://", "")
    config.DATABASE_URL = f"bolt+s://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{host_port}"
elif NEO4J_URI.startswith("neo4j://"):
    # Handle neo4j:// format (local Neo4j without SSL)
    # Format: bolt://username:password@hostname:port
    host_port = NEO4J_URI.replace("neo4j://", "")
    config.DATABASE_URL = f"bolt://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{host_port}"
else:
    # Default case - just use the URI as is and add credentials
    # This handles bolt:// and other formats
    host_port = NEO4J_URI
    if "://" in host_port:
        host_port = host_port.split("://")[-1]
    config.DATABASE_URL = f"bolt://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{host_port}"

# Set other neomodel configurations    
config.AUTO_INSTALL_LABELS = True  # Install labels automatically
config.ENCRYPTED = True if NEO4J_URI.startswith("neo4j+s://") else False  # Use encryption only for secure connections

def verify_connection():
    """
    Verify connection to Neo4j database using neomodel
    """
    try:
        # Log connection details (masked password)
        masked_url = config.DATABASE_URL.replace(NEO4J_PASSWORD, "********")
        logger.info(f"Attempting to connect to Neo4j with URL: {masked_url}")
        
        # Run a simple Cypher query to check connection
        results, meta = db.cypher_query("MATCH (n) RETURN count(n) AS count LIMIT 1")
        count = results[0][0]
        logger.info(f"Connection to Neo4j database established successfully. Database contains {count} nodes.")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j database: {str(e)}")
        
        # Additional troubleshooting information
        if "Unauthorized" in str(e):
            logger.error("Authentication failed. Please check your Neo4j username and password.")
        elif "Connection refused" in str(e):
            logger.error("Connection refused. Please check that Neo4j is running and the URI is correct.")
        elif "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            logger.error("Could not resolve hostname. Please check the Neo4j URI.")
        
        logger.debug(f"Connection details (credentials masked): {masked_url}")
        return False

# Test the connection when this script is run directly
if __name__ == "__main__":
    # Print actual environment variables (for debugging)
    logger.info(f"NEO4J_URI from env: {os.getenv('NEO4J_URI')}")
    logger.info(f"NEO4J_USERNAME from env: {os.getenv('NEO4J_USERNAME')}")
    # Print partial password for security verification without exposing full credentials
    if NEO4J_PASSWORD:
        password_hint = NEO4J_PASSWORD[:4] + "*" * (len(NEO4J_PASSWORD) - 4)
        logger.info(f"NEO4J_PASSWORD from env (partial): {password_hint}")
    else:
        logger.info("NEO4J_PASSWORD from env: Not set")
    
    # Print configuration details (with masked password)
    masked_url = config.DATABASE_URL.replace(NEO4J_PASSWORD, "********") if NEO4J_PASSWORD else config.DATABASE_URL
    logger.info(f"Neo4j configuration: {masked_url}")
    logger.info(f"Encrypted connection: {config.ENCRYPTED}")
    logger.info(f"Auto-install labels: {config.AUTO_INSTALL_LABELS}")
    
    # Test connection
    connection_successful = verify_connection()
    
    if not connection_successful:
        logger.error("Database connection test failed.")
        import sys
        sys.exit(1)
    
    logger.info("Database connection test successful.")
