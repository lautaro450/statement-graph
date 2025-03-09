"""
Debug script to verify imports and basic functionality
"""
import logging
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    from helpers.db_connect import verify_connection
    print("Successfully imported verify_connection")
except Exception as e:
    print(f"Error importing verify_connection: {e}")

try:
    from core.services.services import IngestionService
    print("Successfully imported IngestionService")
except Exception as e:
    print(f"Error importing IngestionService: {e}")

try:
    from core.services.llm_service import LLMService
    print("Successfully imported LLMService")
except Exception as e:
    print(f"Error importing LLMService: {e}")

print("Debug script completed")
