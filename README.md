# Neo4j Statement Graph

A project to work with Neo4j graph database using neomodel for schema enforcement and FastAPI for API endpoints.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Neo4j credentials:
   ```
   NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
   NEO4J_USERNAME="your_username"
   NEO4J_PASSWORD="your_password"
   
   # Anthropic Claude API
   ANTHROPIC_API_KEY="your-anthropic-api-key"
   ANTHROPIC_MODEL="claude-3-opus-20240229"
   
   # LangSmith API (for tracing and monitoring)
   LANGSMITH_TRACING=true
   LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
   LANGSMITH_API_KEY="your-langsmith-api-key"
   LANGSMITH_PROJECT="statement-graph"
   ```

5. Test the connection:
   ```
   python db_connect.py
   ```

6. Verify LangSmith integration (optional):
   ```
   python verify_langsmith.py
   ```

## Project Structure

- `db_connect.py` - Database connection configuration
- `models.py` - Schema definitions using neomodel
- `example.py` - Example usage of the Statement model
- `schemas.py` - Pydantic schemas for API request/response models
- `services.py` - Services for processing ingestion data
- `app.py` - FastAPI application
- `llm_service.py` - Service for integrating with Claude LLM
- `test_*.py` - Test files for various components
- `verify_langsmith.py` - Utility to verify LangSmith integration

## Schema

### Node Types

#### Statement

The project uses neomodel to enforce schemas for Neo4j nodes. The main node type is `Statement` with the following properties:

- `uuid` - Unique identifier (automatically generated)
- `label` - String label for the statement
- `subject` - Subject of the statement
- `predicate` - Predicate (relationship) of the statement
- `object` - Object of the statement
- `context` - Context information
- `created_at` - Timestamp when the statement was created

#### Topic

The `Topic` node type represents a subject area or category with the following properties:

- `uuid` - Unique identifier (automatically generated)
- `label` - String label for the topic (unique)

## Usage

### Basic Connection

```python
from db_connect import verify_connection

# Test connection
if verify_connection():
    # Database is connected
    pass
```

### Working with Statements

```python
from models import Statement

# Create a statement
statement = Statement(
    label="PersonHasPet",
    subject="Alice",
    predicate="has_pet",
    object="Dog",
    context="Example"
).save()

# Query statements
all_statements = Statement.nodes.all()
filtered_statements = Statement.nodes.filter(subject="Alice")
```

### Working with Topics

```python
from models import Topic

# Create a topic
topic = Topic(label="Science").save()

# Query topics
all_topics = Topic.nodes.all()
science_topic = Topic.nodes.get(label="Science")
```

## LangSmith Integration

The project uses LangSmith for tracing and monitoring LLM calls. This provides:

1. **Tracing**: Track all LLM requests and responses in a centralized dashboard
2. **Monitoring**: Monitor latency, token usage, and errors
3. **Debugging**: Debug issues with LLM responses
4. **Analytics**: Analyze patterns and improve prompts

To use LangSmith:

1. Sign up for a LangSmith account at [smith.langchain.com](https://smith.langchain.com/)
2. Get your API key from the LangSmith dashboard
3. Add the API key to your `.env` file (see Setup section)
4. Set `LANGSMITH_TRACING=true` to enable tracing

You can verify your LangSmith integration by running:

```bash
python verify_langsmith.py
```

For more information, see the [LangSmith documentation](https://docs.smith.langchain.com/).

## API Documentation

The FastAPI application automatically generates Swagger documentation at the `/docs` endpoint.

```
http://localhost:8000/docs
```

### API Endpoints

#### POST /ingestion/v1

Ingest transcription data and store it in the statement graph.

- **Request Body**: `IngestionRequest` - Contains transcription text, utterances, and metadata
- **Response**: `IngestionResponse` - Contains processing status and matched topics

## Performance Optimizations

### Batch Processing

When matching statements with topics, the system processes statements in batches of 30 to optimize performance and prevent timeouts. This approach:

1. Splits large sets of statements into manageable batches
2. Processes each batch independently with the LLM
3. Combines the results from all batches into a single response
4. Provides detailed logging at each step of the process

Benefits of the batch processing approach:
- Avoids timeouts when processing large datasets
- Reduces memory usage
- Improves error handling (failures in one batch don't affect others)
- Provides more granular progress tracking

### Timeouts and Error Handling

The system implements:
- Configurable timeouts for API calls to prevent indefinite waiting
- Robust error handling with fallback mechanisms
- Detailed logging at each processing step

## Monitoring

### LangSmith Integration

The project integrates with LangSmith for monitoring LLM calls. This provides:
- Tracing of LLM requests and responses
- Performance metrics
- Error identification
- Visualization of processing flow

Enable LangSmith tracing by setting `LANGSMITH_TRACING=true` in your `.env` file.

## API Endpoints

### Run the API Server

```bash
python app.py
```

This will start the FastAPI server on http://localhost:8000. You can access the automatic API documentation at http://localhost:8000/docs.

### Ingestion Endpoint

#### POST /ingestion/v1

Endpoint for ingesting transcription data.

**Request Body:**

```json
{
  "text": "Full transcription text",
  "utterances": [
    {
      "speaker": "Speaker1",
      "text": "Hello, this is a test.",
      "start": 0,
      "end": 5000,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "transcription_id": 12345,
    "audio_file_id": 67890,
    "language": "en",
    "service": "test_service",
    "speakers_count": 1
  }
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Data ingested successfully",
  "data": {
    "topic_id": "59a7411102884724a5384ef31f9",
    "topic_label": "Transcription-12345",
    "statements_count": 1,
    "statement_ids": ["0b10b6af82744912a1a513f6c3be0b91"]
  }
}
```

### Testing

To test the API endpoints:

```bash
python test_api.py
