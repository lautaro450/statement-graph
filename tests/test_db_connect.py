"""
import sys
Test the database connection module
"""
import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

# Add parent directory to path to allow imports from parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDatabaseConnection(unittest.TestCase):
    """Tests for database connection functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Save original environment variables to restore later
        self.original_env = {}
        for key in ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]:
            self.original_env[key] = os.environ.get(key)
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
    
    @patch('neomodel.db.cypher_query')
    def test_verify_connection_success(self, mock_cypher_query):
        """Test successful database connection verification"""
        from helpers.db_connect import verify_connection
        
        # Mock successful response
        mock_cypher_query.return_value = ([[5]], None)
        
        # Verify connection
        result = verify_connection()
        
        # Check assertions
        self.assertTrue(result)
        mock_cypher_query.assert_called_once_with("MATCH (n) RETURN count(n) AS count LIMIT 1")
    
    @patch('neomodel.db.cypher_query')
    def test_verify_connection_failure(self, mock_cypher_query):
        """Test database connection verification failure"""
        from helpers.db_connect import verify_connection
        
        # Mock failure
        mock_cypher_query.side_effect = Exception("Connection error")
        
        # Verify connection
        result = verify_connection()
        
        # Check assertions
        self.assertFalse(result)
    
    @patch('neomodel.config')
    def test_connection_url_neo4j_plus_s(self, mock_config):
        """Test construction of connection URL for neo4j+s:// format"""
        # Set environment variables
        os.environ["NEO4J_URI"] = "neo4j+s://test-instance.databases.neo4j.io"
        os.environ["NEO4J_USERNAME"] = "testuser"
        os.environ["NEO4J_PASSWORD"] = "testpass"
        
        # Import db_connect to trigger URL construction
        import importlib
        import helpers.db_connect
        importlib.reload(db_connect)
        
        # Verify URL construction
        expected_url = "bolt+s://testuser:testpass@test-instance.databases.neo4j.io"
        self.assertEqual(mock_config.DATABASE_URL, expected_url)
    
    @patch('neomodel.config')
    def test_connection_url_neo4j(self, mock_config):
        """Test construction of connection URL for neo4j:// format"""
        # Set environment variables
        os.environ["NEO4J_URI"] = "neo4j://localhost:7687"
        os.environ["NEO4J_USERNAME"] = "testuser"
        os.environ["NEO4J_PASSWORD"] = "testpass"
        
        # Import db_connect to trigger URL construction
        import importlib
        import helpers.db_connect
        importlib.reload(db_connect)
        
        # Verify URL construction
        expected_url = "bolt://testuser:testpass@localhost:7687"
        self.assertEqual(mock_config.DATABASE_URL, expected_url)
    
    @patch('neomodel.config')
    def test_connection_url_bolt(self, mock_config):
        """Test construction of connection URL for bolt:// format"""
        # Set environment variables
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
        os.environ["NEO4J_USERNAME"] = "testuser"
        os.environ["NEO4J_PASSWORD"] = "testpass"
        
        # Import db_connect to trigger URL construction
        import importlib
        import helpers.db_connect
        importlib.reload(db_connect)
        
        # Verify URL construction
        expected_url = "bolt://testuser:testpass@localhost:7687"
        self.assertEqual(mock_config.DATABASE_URL, expected_url)

if __name__ == "__main__":
    unittest.main()
