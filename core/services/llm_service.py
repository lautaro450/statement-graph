"""
LLM Service for processing statements and matching them to topics
"""
import os
import re
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import anthropic

# Only import LangSmith if tracing is enabled
load_dotenv()
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

if LANGSMITH_TRACING:
    from langsmith import Client as LangSmithClient
    from langsmith.run_helpers import traceable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMService:
    """
    Service for integrating with Claude LLM for semantic analysis
    """
    
    def __init__(self):
        """
        Initialize the LLM service with API keys
        """
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-latest")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "statement-graph")
        self.langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
        self.langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        
        # Set reasonable timeout values
        self.timeout = 60  # 60 seconds timeout for API calls
        
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
        
        if not self.langsmith_api_key or self.langsmith_api_key == "<your-api-key>":
            logger.warning("LANGSMITH_API_KEY not found or not set in environment variables")
            self.langsmith_api_key = None
        
        # Client initialization
        self.anthropic = None
        self.langsmith = None
        
        if self.anthropic_api_key:
            self.anthropic = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
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
        
        # Log initialization status
        if self.anthropic:
            logger.info(f"Claude LLM initialized with model: {self.anthropic_model}")
        else:
            logger.error("Failed to initialize Claude LLM - missing API key")
        
        if not self.langsmith_tracing:
            logger.info("LangSmith tracing is disabled")
    
    def match_statements_to_topics(
        self, 
        statements: List[Dict[str, Any]], 
        topics: List[Dict[str, Any]], 
        intent: Optional[str] = None,
        batch_size: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Match statements to pre-defined topics based on semantic similarity.
        
        Args:
            statements: List of statements to match
            topics: List of topics to match against
            intent: Optional intent to guide topic matching
            batch_size: Number of statements to process in each batch
            
        Returns:
            List of statements with matched topics
        """
        # Check if statements or topics are empty
        if not statements:
            logger.warning("No statements provided for topic matching")
            return []
            
        if not topics:
            logger.warning("No topics provided for matching. Creating an open-ended prompt for topic generation.")
            # Instead of just returning statements, modify the prompt to allow the LLM to create topics
            topics_text = "No pre-defined topics available. Please create appropriate topics based on the statement content."
        else:
            # Format topics as text
            topics_text = "\n".join([
                f"Topic: {topic.get('label', 'Unnamed')} (ID: {topic.get('id', 'none')})"
                for topic in topics
            ])
        
        # Process statements in batches
        results = []
        batches = [statements[i:i + batch_size] for i in range(0, len(statements), batch_size)]
        
        logger.info(f"Processing {len(statements)} statements in {len(batches)} batches of {batch_size}")
        
        for batch_index, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_index + 1}/{len(batches)} with {len(batch)} statements")
            
            try:
                # Process batch with or without LangSmith tracing
                if self.langsmith_tracing and self.langsmith:
                    try:
                        logger.info("Using LangSmith tracing for topic matching batch")
                        # Create a run tree without context manager
                        run_tree = traceable(
                            name="match_statements_batch",
                            run_type="llm",
                            project_name=self.langsmith_project,
                            client=self.langsmith,
                            metadata={
                                "batch_index": batch_index,
                                "batch_size": len(batch),
                                "total_batches": len(batches)
                            }
                        )
                        batch_results = run_tree(self._process_statements_batch)(batch, topics_text, intent)
                        results.extend(batch_results)
                    except Exception as e:
                        logger.error(f"Error with LangSmith tracing in batch {batch_index}: {e}")
                        # Fall back to processing without tracing
                        logger.info("Falling back to processing without LangSmith tracing")
                        batch_results = self._process_statements_batch(batch, topics_text, intent)
                        results.extend(batch_results)
                else:
                    # Process without LangSmith tracing
                    logger.info("Processing without LangSmith tracing")
                    batch_results = self._process_statements_batch(batch, topics_text, intent)
                    results.extend(batch_results)
                    
                # Log successful batch processing
                logger.info(f"Successfully processed batch {batch_index + 1}/{len(batches)}")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_index + 1}: {e}")
                # Continue with next batch instead of failing entirely
                logger.info("Continuing with next batch...")
                continue
        
        logger.info(f"Finished processing all batches. Matched {len(results)} statements to topics.")
        return results

    def _process_statements_batch(
        self, 
        batch_statements: List[Dict[str, Any]], 
        topics_text: str,
        intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of statements for topic matching
        
        Args:
            batch_statements: A batch of statements to process
            topics_text: Formatted text of topics
            intent: Optional intent to guide topic matching
            
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
        {topics_text}

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
        
        if intent:
            system_prompt += f"""
        IMPORTANT INTENT GUIDANCE: {intent}
        
        You must prioritize this intent when matching statements to topics. The matched topics should directly support this objective.
        """
        
        try:
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
            
            # Extract and parse response
            result_text = response.content[0].text
            
            try:
                # Try to extract JSON from the response
                result_json = self._extract_json(result_text)
                statements = result_json.get("statements", [])
                
                # Ensure all statements have a topics field
                for statement in statements:
                    if "topics" not in statement:
                        statement["topics"] = []
                        
                        # Try to create a topic from the subject
                        if "subject" in statement and statement["subject"]:
                            statement["topics"].append({
                                "name": statement["subject"],
                                "tags": [statement["subject"]]
                            })
                
                return statements
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from batch response: {e}")
                return batch_statements
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return batch_statements

    def ingest_statements_from_transcript(self, transcript_text: str, intent: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a full transcript and extract semantic statements.
        
        Args:
            transcript_text: The full transcript text
            intent: Optional intent to guide statement extraction
            
        Returns:
            List of extracted statements with subject, predicate, object, and context
            
        Raises:
            Exception: If processing fails
        """
        system_prompt = """You are a knowledge organization expert specializing in semantic categorization and taxonomy development.

        Analyze the given transcript and extract structured knowledge statements.
        """
        
        # Add intent-specific guidance if provided
        if intent:
            system_prompt += f"""
        IMPORTANT INTENT GUIDANCE: {intent}
        
        You must prioritize this intent when extracting statements. The statements should directly support this objective.
        """
            
        system_prompt += """
        Follow this exact process to extract high-quality, non-generic statements:
        
        1. IDENTIFY KEY ENTITIES AND ACTIONS:
        - Extract entities (people, organizations, technologies, methodologies, frameworks)
        - Identify actions (verbs) associated with these entities
        - Determine the context in which these actions occur
        
        2. CREATE STRUCTURED STATEMENTS:
        - Format statements as subject-predicate-object triples
        - Include context and confidence scores for each statement
        - Ensure statements are specific, accurate, and relevant
        
        3. ENSURE STATEMENTS ARE SPECIFIC AND USEFUL:
        - Avoid overly generic statements
        - Statements should be specific enough that a user would immediately recognize its relevance
        - Ask yourself: "Would a user searching for exactly this content find this statement helpful?"
        - Phrase statements as a user would search for them, not as academic classifications
        
        4. APPLY CONTRASTIVE ANALYSIS:
        - For each statement, explicitly consider what makes it distinct from other statements
        - If you cannot clearly articulate how a statement differs from others, refine or discard it
        
        Return ONLY a JSON response in this exact format:
        {
        "statements": [
            {
            "subject": "Entity performing action",
            "predicate": "Action verb",
            "object": "Information or concept",
            "context": "Optional qualifying information",
            "confidence": number between 0.7 and 1.0,
            "source": "Original text snippet",
            "id": "Unique identifier"
            },
            # Additional statements...
        ]
        }
        
        IMPORTANT: Ensure statements are truly distinctive and non-generic. Statements should be immediately recognizable and useful to end users.
            """
        
        # Initialize Anthropic client if not already initialized
        if not hasattr(self, 'anthropic') or not self.anthropic:
            self.anthropic = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        # Create a new run tree if LangSmith tracing is enabled
        if self.langsmith_tracing and self.langsmith:
            with traceable(
                name="statement_ingestion",
                run_type="llm",
                client=self.langsmith,
                project_name=self.langsmith_project
            ) as run_tree:
                try:
                    # Add metadata to the run
                    run_tree.add_metadata({
                        "transcript_length": len(transcript_text),
                        "model": self.anthropic_model
                    })
                    
                    # Call Claude API
                    response = self.anthropic.messages.create(
                        model=self.anthropic_model,
                        system=system_prompt,
                        max_tokens=16000,
                        messages=[
                            {"role": "user", "content": "Extract statements from this transcript:\n\n" + transcript_text}
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
                        {"role": "user", "content": "Extract statements from this transcript:\n\n" + transcript_text}
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

    def generate_topics_from_statements(self, statements: List[Dict[str, Any]], intent: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate a list of topics by analyzing statements when no topics exist in the database.
        
        Args:
            statements: List of statements to analyze
            intent: Optional intent to guide topic generation
            
        Returns:
            List of generated topics with id, label, and tags
        """
        logger.info(f"Generating topics from {len(statements)} statements")
        
        if not statements:
            logger.warning("No statements provided for topic generation")
            return []
            
        system_prompt = """You are a knowledge organization expert specializing in semantic categorization and taxonomy development.

        Analyze the given statements and create a coherent set of distinctive topics that effectively categorize them.
        """
        
        # Add intent-specific guidance if provided
        if intent:
            system_prompt += f"""
        IMPORTANT INTENT GUIDANCE: {intent}
        
        You must prioritize this intent when creating topics. The topics should directly support this objective.
        """
            
        system_prompt += """
        Follow this exact process to generate high-quality, non-generic topics:
        
        1. IDENTIFY DISTINCTIVE TERMINOLOGY:
        - List terms that appear frequently in clusters of related statements
        - Prioritize terms that are distinctive to specific clusters and rarely appear across all statements
        - Pay special attention to named entities (people, organizations, technologies, methodologies, frameworks)
        
        2. CREATE HIERARCHICAL STRUCTURE:
        - Organize topics into primary categories and more specific subcategories
        - Ensure each topic has clearly defined boundaries that distinguish it from others
        - For each topic, provide both broader categories and specific subtopics
        
        3. ENSURE TOPICS ARE SPECIFIC AND USEFUL:
        - Avoid overly generic topics like "General Information" or "Miscellaneous"
        - Topics should be specific enough that a user would immediately recognize its relevance
        - Ask yourself: "Would a user searching for exactly this content find this label helpful?"
        - Phrase topics as a user would search for them, not as academic classifications
        
        4. APPLY CONTRASTIVE ANALYSIS:
        - For each topic, explicitly consider what makes statements in this topic distinct from other topics
        - If you cannot clearly articulate how a topic differs from others, refine or discard it
        
        Return ONLY a JSON response in this exact format:
        {
        "topics": [
            {
            "id": "topic_1",
            "label": "Specific Topic Name",  # 1-3 words, specific not generic
            "distinctive_terms": ["term1", "term2"],  # Key terms distinctive to this topic
            "description": "Brief explanation of what distinguishes this topic"  # 1-2 sentences
            },
            # Additional topics...
        ]
        }
        
        IMPORTANT: Ensure topics are truly distinctive and non-generic. Topics should be immediately recognizable and useful to end users.
            """
        
        # Format statements for the prompt
        statements_text = json.dumps(statements, indent=2)
        
        try:
            # Call Claude API
            response = self.anthropic.messages.create(
                model=self.anthropic_model,
                system=system_prompt,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": f"Generate topics for these statements:\n\n{statements_text}"}
                ],
                timeout=self.timeout
            )
            
            # Extract and parse response
            result_text = response.content[0].text
            
            try:
                # Extract JSON from response
                result_json = self._extract_json(result_text)
                topics = result_json.get("topics", [])
                
                if not topics:
                    logger.warning("No topics were generated by LLM")
                    return []
                
                # Convert to the expected format with tags field
                processed_topics = []
                for topic in topics:
                    processed_topic = {
                        "id": topic.get("id", ""),
                        "label": topic.get("label", ""),
                        "tags": topic.get("distinctive_terms", [])  # Use distinctive_terms as tags
                    }
                    
                    # Add description as a tag if it exists
                    description = topic.get("description", "")
                    if description and description not in processed_topic["tags"]:
                        processed_topic["tags"].append(description)
                        
                    processed_topics.append(processed_topic)
                    
                logger.info(f"Successfully generated {len(processed_topics)} topics")
                return processed_topics
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from topic generation response: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating topics: {e}")
            return []

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
