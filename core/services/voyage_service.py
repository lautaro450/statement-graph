
"""
Service for interacting with the Voyage AI API for embeddings and reranking
"""
import os
import logging
from typing import List, Dict, Any, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoyageService:
    """
    Service for generating embeddings and reranking using Voyage AI
    """
    
    def __init__(self):
        """
        Initialize the Voyage Service with API key
        """
        self.api_key = os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            logger.warning("VOYAGE_API_KEY environment variable not set")
        
        self.embedding_endpoint = "https://api.voyageai.com/v1/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_embeddings(self, texts: List[str], model: str = "voyage-2") -> Optional[List[List[float]]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to generate embeddings for
            model: The Voyage AI model to use (default: voyage-2)
            
        Returns:
            List of embeddings or None if API call fails
        """
        if not self.api_key:
            logger.error("Cannot generate embeddings: VOYAGE_API_KEY not set")
            return None
            
        try:
            payload = {
                "model": model,
                "input": texts
            }
            
            response = requests.post(
                self.embedding_endpoint,
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                logger.info(f"Successfully generated {len(embeddings)} embeddings")
                return embeddings
            else:
                logger.error(f"Error generating embeddings: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in generate_embeddings: {str(e)}")
            return None
    
    def generate_statement_embeddings(self, statements: List[Dict[str, Any]], model: str = "voyage-2") -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of statements
        
        Args:
            statements: List of statement dictionaries
            model: The Voyage AI model to use (default: voyage-2)
            
        Returns:
            The statements with added embeddings
        """
        # Extract the text from statements (use object field as the content)
        texts = [statement["object"] for statement in statements]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, model)
        
        # Add embeddings to statements
        if embeddings:
            for i, statement in enumerate(statements):
                statement["embedding"] = embeddings[i]
                
        return statements
