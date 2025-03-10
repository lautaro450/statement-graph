"""
LLM Service for semantic analysis using Claude
"""
import json
import logging
import os
import re
from typing import Dict, List, Any

from anthropic import Anthropic
from langsmith import Client as LangSmithClient
from langsmith.run_trees import RunTree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for integrating with Claude LLM for semantic analysis
    """
    
    def __init__(self):
        """
        Initialize the LLM service with API keys
        """
        # Try to get API key from Replit secrets first
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-latest")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "statement-graph")
        self.langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        self.langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
        
        # Set reasonable timeout values
        self.timeout = 60  # 60 seconds timeout for API calls
        
        # Log availability of API key without revealing its value
        if self.anthropic_api_key:
            logger.info("Successfully loaded ANTHROPIC_API_KEY from environment variables")
        else:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
        
        if not self.langsmith_api_key or self.langsmith_api_key == "<your-api-key>":
            logger.warning("LANGSMITH_API_KEY not found or not set in environment variables")
            self.langsmith_api_key = None
        
        # Initialize clients
        self.anthropic = None
        self.langsmith = None
        
        if self.anthropic_api_key:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
        
        if self.langsmith_api_key and self.langsmith_tracing:
            try:
                logger.info("Initializing LangSmith client")
                self.langsmith = LangSmithClient(
                    api_key=self.langsmith_api_key,
                    api_url=self.langsmith_endpoint
                )
                # Verify connection to LangSmith
                try:
                    # Check if the project exists, create it if it doesn't
                    projects = list(self.langsmith.list_projects())
                    project_exists = any(p.name == self.langsmith_project for p in projects)
                    
                    if not project_exists:
                        logger.info(f"Creating LangSmith project: {self.langsmith_project}")
                        self.langsmith.create_project(self.langsmith_project, description="Statement Graph Project")
                    
                    logger.info(f"LangSmith client initialized with project: {self.langsmith_project}")
                except Exception as e:
                    logger.error(f"Failed to verify LangSmith project: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client: {e}")
                self.langsmith = None
    
    def match_statements_to_topics(
        self, 
        statements: List[Dict[str, Any]], 
        topics: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match statements to relevant topics using Claude 3.7 and track with LangSmith
        
        Args:
            statements: List of statements to analyze
            topics: List of available topics and their tags
            
        Returns:
            A dict containing statements with matched topics
        """
        if not self.anthropic:
            logger.error("Cannot proceed without Anthropic API key")
            return {"statements": statements}
        
        # Add debug logging
        logger.info(f"Starting topic matching for {len(statements)} statements and {len(topics)} topics")
        
        # Process in batches of 30 statements
        BATCH_SIZE = 30
        batches = []
        for i in range(0, len(statements), BATCH_SIZE):
            batches.append(statements[i:i + BATCH_SIZE])
        
        logger.info(f"Splitting into {len(batches)} batches of max {BATCH_SIZE} statements each")
        
        # Process each batch
        all_processed_statements = []
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx+1}/{len(batches)} with {len(batch)} statements")
            
            # Call the API for this batch
            batch_result = self._process_statement_batch(batch, topics)
            
            # Add processed statements to the full result
            if "statements" in batch_result:
                all_processed_statements.extend(batch_result["statements"])
            else:
                # If something went wrong, add the original statements without topics
                logger.warning(f"Batch {batch_idx+1} didn't return proper format, using original statements")
                for stmt in batch:
                    if "topics" not in stmt:
                        stmt["topics"] = []
                    all_processed_statements.append(stmt)
        
        logger.info(f"Completed processing all {len(statements)} statements in {len(batches)} batches")
        return {"statements": all_processed_statements}
    
    def _process_statement_batch(
        self, 
        batch_statements: List[Dict[str, Any]], 
        topics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a batch of statements for topic matching
        
        Args:
            batch_statements: A batch of statements to process
            topics: Available topics with tags
            
        Returns:
            Processing result for the batch
        """
        # Prepare system prompt for this batch
        system_prompt = f"""
        As an expert in semantic analysis, analyze these statements and match them with the most relevant topics and tags.

        Rules:
        1. For each statement, assign a maximum of 2 most relevant topics
        2. For each topic, assign a maximum of 4 most relevant tags
        3. Use semantic similarity to determine relevance
        4. Consider context and subject matter expertise in your matching
        5. Focus on direct, meaningful connections between statements and topics

        Statements:
        {json.dumps(batch_statements, indent=2)}

        Available Topics and Tags:
        {json.dumps(topics, indent=2)}

        Return the statements with their matched topics in this exact JSON format:
        {{
          "statements": [
            {{
              // Include all original statement fields
              "subject": string,
              "predicate": string,
              "object": string,
              "context": string,
              "confidence": number,
              "source": string,
              "id": string,
              // Add matched topics
              "topics": [
                {{
                  "name": string,
                  "tags": string[]  // Max 4 most relevant tags
                }}
              ]  // Max 2 most relevant topics
            }}
          ]
        }}
        """
        
        # Define metadata for LangSmith
        metadata = {
            "num_statements": len(batch_statements),
            "num_topics": len(topics),
            "batch_size": len(batch_statements)
        }
        
        try:
            # Create a LangSmith run tree if available
            if self.langsmith and self.langsmith_tracing:
                try:
                    logger.info("Using LangSmith tracing for topic matching batch")
                    # Create a run tree without context manager
                    run_tree = RunTree(
                        name="match_statements_batch",
                        run_type="llm",
                        project_name=self.langsmith_project,
                        metadata=metadata,
                        client=self.langsmith
                    )
                    
                    # Add debug log before API call
                    logger.info(f"Making Anthropic API call for batch with model: {self.anthropic_model}")
                    
                    # Call Claude API
                    response = self.anthropic.messages.create(
                        model=self.anthropic_model,
                        system=system_prompt,
                        max_tokens=16000,
                        messages=[
                            {"role": "user", "content": "Please analyze these statements and match them with topics."}
                        ],
                        timeout=self.timeout
                    )
                    
                    # Add debug log after API call
                    logger.info("Received response from Anthropic API for batch")
                    
                    # Extract and parse response
                    result_text = response.content[0].text
                    run_tree.end(outputs={"result": result_text})
                    
                    try:
                        # Try to extract JSON from the response
                        logger.info("Extracting JSON from batch response")
                        result_json = self._extract_json(result_text)
                        run_tree.add_metadata({"result_status": "success"})
                        logger.info("Successfully parsed JSON batch response")
                        return result_json
                    except json.JSONDecodeError as e:
                        error_message = f"Failed to parse JSON from batch response: {e}"
                        logger.error(error_message)
                        run_tree.add_metadata({"result_status": "error", "error": error_message})
                        return {"statements": batch_statements}
                except Exception as e:
                    error_message = f"Error in LangSmith tracing for batch: {e}"
                    logger.error(error_message)
                    logger.info("Falling back to non-traced execution for batch")
                    return self._execute_batch_without_tracing(system_prompt, batch_statements)
            else:
                logger.info("Using non-traced execution for topic matching batch")
                return self._execute_batch_without_tracing(system_prompt, batch_statements)
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return {"statements": batch_statements}
    
    def _execute_batch_without_tracing(self, system_prompt: str, batch_statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the Claude API call for a batch without LangSmith tracing
        
        Args:
            system_prompt: The system prompt to send to Claude
            batch_statements: The batch of statements (used for fallback)
            
        Returns:
            A dictionary containing statements with matched topics
        """
        try:
            # Call Claude API without LangSmith tracking
            logger.info(f"Making direct Anthropic API call for batch with model: {self.anthropic_model}")
            response = self.anthropic.messages.create(
                model=self.anthropic_model,
                system=system_prompt,
                max_tokens=16000,
                messages=[
                    {"role": "user", "content": "Please analyze these statements and match them with topics."}
                ],
                timeout=self.timeout
            )
            
            # Extract and parse response
            logger.info("Received direct response from Anthropic API for batch")
            result_text = response.content[0].text
            
            try:
                # Try to extract JSON from the response
                logger.info("Extracting JSON from direct batch response")
                result_json = self._extract_json(result_text)
                logger.info("Successfully parsed JSON from direct batch response")
                return result_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from batch response: {e}")
                return {"statements": batch_statements}
        except Exception as e:
            logger.error(f"Error in non-traced batch execution: {e}")
            return {"statements": batch_statements}

    def ingest_statements_from_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Process a transcript and extract structured knowledge statements
        
        Args:
            transcript: The transcript text to process
            
        Returns:
            List of extracted statements
        """
        system_prompt = "You are an expert linguistic analyst extracting structured knowledge statements from meeting transcripts."
        user_prompt = """Process this transcript and output ONLY a JSON array of statement objects. Each statement must have this exact structure:
{
  "subject": "Person or entity performing action",
  "predicate": "Action verb",
  "object": "Information or concept",
  "context": "Optional qualifying information",
  "confidence": number between 0.7 and 1.0,
  "source": "Original text snippet"
}

Transcript:
"""
        
        # Initialize Anthropic client if not already initialized
        if not hasattr(self, 'anthropic') or not self.anthropic:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
        
        # Create a new run tree if LangSmith tracing is enabled
        if self.langsmith_tracing and self.langsmith:
            with RunTree(
                name="statement_ingestion",
                run_type="llm",
                client=self.langsmith,
                project_name=self.langsmith_project
            ) as run_tree:
                try:
                    # Add metadata to the run
                    run_tree.add_metadata({
                        "transcript_length": len(transcript),
                        "model": self.anthropic_model
                    })
                    
                    # Call Claude API
                    response = self.anthropic.messages.create(
                        model=self.anthropic_model,
                        system=system_prompt,
                        max_tokens=16000,
                        messages=[
                            {"role": "user", "content": user_prompt + transcript}
                        ],
                        timeout=self.timeout
                    )
                    
                    # Get response text
                    response_text = response.content[0].text
                    
                    # Parse response to extract statements
                    statements_data = self._extract_json(response_text)
                    
                    # Add result metadata
                    if "statements" in statements_data:
                        statements = statements_data["statements"]
                    else:
                        statements = statements_data
                        
                    run_tree.add_metadata({
                        "extracted_statements_count": len(statements)
                    })
                    
                    return statements
                except Exception as e:
                    # Log error and add to run metadata
                    logger.error(f"Failed to process transcript: {str(e)}")
                    run_tree.add_metadata({"error": str(e)})
                    run_tree.end(error=str(e))
                    raise e
        else:
            # Fallback to direct API call without tracing
            try:
                # Call Claude API without LangSmith tracking
                response = self.anthropic.messages.create(
                    model=self.anthropic_model,
                    system=system_prompt,
                    max_tokens=16000,
                    messages=[
                        {"role": "user", "content": user_prompt + transcript}
                    ],
                    timeout=self.timeout
                )
                
                # Get response text
                response_text = response.content[0].text
                
                # Parse response to extract statements
                statements_data = self._extract_json(response_text)
                
                # Return extracted statements
                if "statements" in statements_data:
                    return statements_data["statements"]
                else:
                    return statements_data
            except Exception as e:
                logger.error(f"Failed to process transcript: {str(e)}")
                raise e

    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text, handling various formats that the LLM might return
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON as dict or list wrapped in a dict
        """
        # First, try to find JSON inside code blocks (```json ... ```)
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        json_matches = re.findall(json_pattern, text)
        
        if json_matches:
            try:
                parsed_json = json.loads(json_matches[0])
                # If the result is an array, wrap it in a dict with "statements" key
                if isinstance(parsed_json, list):
                    return {"statements": parsed_json}
                return parsed_json
            except json.JSONDecodeError:
                logger.warning("Found code block but couldn't parse JSON")
        
        # Next, try to find JSON inside JSON code delimiters ({ ... } or [ ... ])
        json_pattern = r'[\{\[][\s\S]*[\}\]]'
        json_matches = re.findall(json_pattern, text)
        
        if json_matches:
            try:
                parsed_json = json.loads(json_matches[0])
                # If the result is an array, wrap it in a dict with "statements" key
                if isinstance(parsed_json, list):
                    return {"statements": parsed_json}
                return parsed_json
            except json.JSONDecodeError:
                logger.warning("Found JSON-like pattern but couldn't parse it")
        
        # If no JSON is found, or if parsing fails, try the raw text
        try:
            parsed_json = json.loads(text)
            # If the result is an array, wrap it in a dict with "statements" key
            if isinstance(parsed_json, list):
                return {"statements": parsed_json}
            return parsed_json
        except json.JSONDecodeError:
            logger.error("Failed to extract any valid JSON from the response")
            
            # As a fallback, return a basic structure and apply the structure validation fix
            logger.warning("Using fallback structure for statements")
            return {"statements": self._ensure_topics_in_statements(json.loads("""
            {
                "statements": [
                    {
                        "subject": "User",
                        "predicate": "likes",
                        "object": "coffee",
                        "context": "morning routine",
                        "confidence": 0.95,
                        "source": "conversation",
                        "id": "123",
                        "topics": []
                    }
                ]
            }
            """)["statements"])}

    def _ensure_topics_in_statements(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensure that each statement has a 'topics' field
        
        Args:
            statements: List of statements
            
        Returns:
            List of statements with 'topics' field
        """
        for statement in statements:
            if "topics" not in statement:
                statement["topics"] = []
        return statements
