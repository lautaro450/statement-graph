"""
Test script to identify which module import is causing issues
"""
import sys
import time

def test_import(module_name):
    print(f"Trying to import {module_name}...", end="", flush=True)
    try:
        start_time = time.time()
        __import__(module_name)
        end_time = time.time()
        print(f" SUCCESS ({end_time - start_time:.2f}s)")
        return True
    except Exception as e:
        print(f" FAILED: {str(e)}")
        return False

# Base modules
print("\n--- Testing base modules ---")
modules_to_test = [
    "core",
    "core.schemas",
    "core.services",
    "helpers",
    "helpers.db_connect"
]

for module in modules_to_test:
    test_import(module)

# Test modules
print("\n--- Testing test modules one by one ---")
test_modules = [
    "tests.test_schema",
    "tests.test_api",
    "tests.test_db_connect",
    "tests.test_langsmith",
    "tests.test_semantic_ingestion",
    "tests.test_topic",
    "tests.test_batch_processing"
]

for module in test_modules:
    test_import(module)

print("\nImport testing complete")
