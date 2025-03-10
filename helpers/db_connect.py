"""
Neo4j database connection setup with neomodel
"""
import os
import logging
import sys
from dotenv import load_dotenv
from neomodel import config, db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure the .env file is loaded from the correct location
# Go up one directory from helpers to find the .env file in the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up one directory to project root
env_path = os.path.join(project_root, '.env')
logger.info(f"Loading .env file from: {env_path}")
print(f"Looking for .env file at: {env_path}")

# Load environment variables from .env file with force reload
load_dotenv(env_path, override=True)

# Get credentials from environment variables - print for debugging
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Print with masked password for debugging
print(f"NEO4J_URI: {NEO4J_URI}")
print(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
print(f"NEO4J_PASSWORD: {'*' * (len(NEO4J_PASSWORD) if NEO4J_PASSWORD else 0)}")

# Check if all required environment variables are set
missing_vars = []
if not NEO4J_URI:
    missing_vars.append("NEO4J_URI")
if not NEO4J_USERNAME:
    missing_vars.append("NEO4J_USERNAME")
if not NEO4J_PASSWORD:
    missing_vars.append("NEO4J_PASSWORD")

if missing_vars:
    error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_message)
    print(f"ERROR: {error_message}")
else:
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
if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
    logger.error("Missing Neo4j credentials. Check your .env file.")
    sys.exit(1)

# Properly format the connection URL based on URI format - always use bolt+s protocol
host_port = NEO4J_URI.replace("neo4j+s://", "")
config.DATABASE_URL = f"neo4j+s://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{host_port}"

# Set other neomodel configurations    
config.AUTO_INSTALL_LABELS = True  # Install labels automatically
config.ENCRYPTED = True  # Always use encryption for Neo4j connections

def verify_connection():
    """
    Verify connection to Neo4j database using neomodel
    """
    print("Starting verify_connection function")
    try:
        # Log connection details (masked password)
        masked_url = config.DATABASE_URL.replace(NEO4J_PASSWORD, "********") if NEO4J_PASSWORD else config.DATABASE_URL
        logger.info(f"Attempting to connect to Neo4j with URL: {masked_url}")
        print(f"Attempting Neo4j connection with URL: {masked_url}")
        
        # Set a timeout for the connection to avoid hanging
        # This configures the socket timeout to 5 seconds
        import socket
        socket.setdefaulttimeout(5.0)
        
        # Run a simple Cypher query to check connection
        results, meta = db.cypher_query("MATCH (n) RETURN count(n) AS count LIMIT 1")
        count = results[0][0]
        logger.info(f"Connection to Neo4j database established successfully. Database contains {count} nodes.")
        print(f"Neo4j connection successful! Database contains {count} nodes.")
        return True
    except Exception as e:
        error_message = f"Failed to connect to Neo4j database: {str(e)}"
        logger.error(error_message)
        print(f"ERROR: {error_message}")
        
        # Additional troubleshooting information
        if "Unauthorized" in str(e):
            logger.error("Authentication failed. Please check your Neo4j username and password.")
            print("Authentication failed. Please check your Neo4j username and password.")
        elif "Connection refused" in str(e):
            logger.error("Connection refused. Please check that Neo4j is running and the URI is correct.")
            print("Connection refused. Please check that Neo4j is running and the URI is correct.")
        elif "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            logger.error("Could not resolve hostname. Please check the Neo4j URI.")
            print("Could not resolve hostname. Please check the Neo4j URI.")
        
        logger.debug(f"Connection details (credentials masked): {config.DATABASE_URL.replace(NEO4J_PASSWORD, '********') if NEO4J_PASSWORD else config.DATABASE_URL}")
        print("Verify connection failed, but continuing with app startup...")
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
        
    # Check connection
    if verify_connection():
        logger.info("Connection test successful!")
    else:
        logger.error("Connection test failed!")
