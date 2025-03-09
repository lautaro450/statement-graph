"""
Utility script to verify LangSmith connection and setup
"""
import os
import logging
from dotenv import load_dotenv
from langsmith import Client as LangSmithClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_langsmith_connection():
    """
    Verify connection to LangSmith and check if project exists
    """
    # Get environment variables
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "statement-graph")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    
    if not langsmith_api_key:
        logger.error("LANGSMITH_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize LangSmith client
        langsmith = LangSmithClient(
            api_key=langsmith_api_key,
            api_url=langsmith_endpoint
        )
        
        # Check connection by listing projects
        projects = list(langsmith.list_projects())
        logger.info(f"Successfully connected to LangSmith. Found {len(projects)} projects.")
        
        # Check if project exists
        project_exists = any(p.name == langsmith_project for p in projects)
        
        if project_exists:
            logger.info(f"Project '{langsmith_project}' exists")
        else:
            logger.warning(f"Project '{langsmith_project}' does not exist. Creating it...")
            langsmith.create_project(langsmith_project, description="Statement Graph Project")
            logger.info(f"Created project '{langsmith_project}'")
        
        return True
    except Exception as e:
        logger.error(f"Failed to connect to LangSmith: {e}")
        return False


def create_simple_trace():
    """
    Create a simple LangSmith trace to test tracing functionality
    """
    # Get environment variables
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "statement-graph")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    
    if not langsmith_api_key:
        logger.error("LANGSMITH_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize LangSmith client
        langsmith = LangSmithClient(
            api_key=langsmith_api_key,
            api_url=langsmith_endpoint
        )
        
        # Import here to avoid circular import issues
        from langsmith.run_trees import RunTree
        
        # Create a simple run tree without using context manager
        run_tree = RunTree(
            name="test_trace",
            run_type="chain",
            project_name=langsmith_project,
            metadata={"test": True},
            client=langsmith
        )
        
        # Add some test data
        run_tree.add_metadata({"step": "test"})
        
        # Simulate an operation
        result = "Hello, LangSmith!"
        
        # End the run
        run_tree.end(outputs={"result": result})
        
        logger.info(f"Created test trace with ID: {run_tree.id}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create LangSmith trace: {e}")
        return False


def verify_configurations():
    """
    Verify all necessary configurations are present
    """
    # Check Anthropic API key
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return False
    
    logger.info(f"Anthropic API key is set")
    logger.info(f"Using Anthropic model: {anthropic_model}")
    
    # Check LangSmith API key
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "statement-graph")
    langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    
    if not langsmith_api_key:
        logger.error("LANGSMITH_API_KEY not found in environment variables")
        return False
    
    logger.info(f"LangSmith API key is set")
    logger.info(f"LangSmith project: {langsmith_project}")
    logger.info(f"LangSmith endpoint: {langsmith_endpoint}")
    logger.info(f"LangSmith tracing enabled: {langsmith_tracing}")
    
    return True


if __name__ == "__main__":
    logger.info("Verifying configurations...")
    configs_ok = verify_configurations()
    
    if not configs_ok:
        logger.error("Configuration verification failed")
        exit(1)
    
    logger.info("Verifying LangSmith connection...")
    connection_ok = verify_langsmith_connection()
    
    if connection_ok:
        logger.info("Creating test trace...")
        trace_ok = create_simple_trace()
        
        if trace_ok:
            logger.info("LangSmith tracing is working correctly!")
        else:
            logger.error("Failed to create test trace. Check your LangSmith configuration.")
    else:
        logger.error("Failed to connect to LangSmith. Check your API key and endpoint.")
