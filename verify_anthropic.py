
"""
Utility script to verify Anthropic API connection
"""
import os
import logging
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_anthropic_api_key():
    """
    Verify that the Anthropic API key is valid
    """
    # Get API key from environment
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return False
    
    # Initialize Anthropic client
    try:
        client = Anthropic(api_key=anthropic_api_key)
        
        # Make a simple test request
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )
        
        # Check if we got a valid response
        if response and hasattr(response, 'content'):
            logger.info("Anthropic API key is valid!")
            logger.info(f"Response from Claude: {response.content[0].text}")
            return True
        else:
            logger.error("Received unexpected response format from Anthropic API")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Anthropic API key: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_anthropic_api_key()
    if success:
        print("✅ Anthropic API key is valid and working correctly")
        sys.exit(0)
    else:
        print("❌ Problem with Anthropic API key. Check the logs for details.")
        sys.exit(1)
