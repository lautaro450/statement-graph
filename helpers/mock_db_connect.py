"""
Mock Neo4j database connection for testing
This module provides the same interface as db_connect.py but doesn't actually
connect to a database, allowing for testing without a live Neo4j instance.
"""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simulate configuration
class MockConfig:
    def __init__(self):
        self.DATABASE_URL = "bolt://mock:mock@localhost:7687"
        self.AUTO_INSTALL_LABELS = True
        self.ENCRYPTED = False

config = MockConfig()

# Mock DB class
class MockDB:
    def cypher_query(self, query, params=None):
        logger.info(f"Mock cypher query: {query}")
        # Return a mock result (count of 5 nodes for the verification query)
        if "COUNT" in query.upper():
            return [[5]], None
        return [], None

db = MockDB()

def verify_connection():
    """
    Mock version of verify_connection that always succeeds
    """
    logger.info("Mock database connection verification - always succeeds")
    print("Mock database connection successful! (Not actually connecting to Neo4j)")
    return True

if __name__ == "__main__":
    print("Testing mock database connection")
    result = verify_connection()
    print(f"Connection result: {result}")
