"""
Test script to debug Neo4j database connection issues step by step.
This script isolates the database connection logic for troubleshooting.
"""
import sys
import os
import time
import socket
import traceback
from dotenv import load_dotenv

# Set timeout for all socket operations
socket.setdefaulttimeout(10)

print("=" * 80)
print("DATABASE CONNECTION TEST SCRIPT")
print("=" * 80)

def log_step(step_name):
    """Log a step with timestamps"""
    print(f"\n[{time.time()}] STEP: {step_name}")

# STEP 1: Environment Setup
log_step("Loading environment variables")
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
print(f"Looking for .env file at: {env_path}")

try:
    load_dotenv(env_path, override=True)
    print("Loaded .env file successfully")
except Exception as e:
    print(f"Error loading .env file: {e}")
    traceback.print_exc()
    sys.exit(1)

# STEP 2: Verify environment variables
log_step("Checking environment variables")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

print(f"NEO4J_URI: {NEO4J_URI}")
print(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
if NEO4J_PASSWORD:
    masked_password = "*" * len(NEO4J_PASSWORD)
    print(f"NEO4J_PASSWORD present with length: {len(NEO4J_PASSWORD)}")
else:
    print("WARNING: NEO4J_PASSWORD not set")

if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
    print("ERROR: Missing required Neo4j environment variables")
    sys.exit(1)
else:
    print("All required Neo4j environment variables are set")

# STEP 3: Test basic network connectivity
log_step("Testing network connectivity")

try:
    # Extract hostname and port from URI
    if NEO4J_URI.startswith("neo4j+s://"):
        host_port = NEO4J_URI.replace("neo4j+s://", "")
    elif NEO4J_URI.startswith("neo4j://"):
        host_port = NEO4J_URI.replace("neo4j://", "")
    else:
        host_port = NEO4J_URI.split("://")[-1] if "://" in NEO4J_URI else NEO4J_URI
    
    # Split host and port (default to 7687 if no port specified)
    if ":" in host_port:
        host, port_str = host_port.split(":")
        port = int(port_str.split("/")[0])  # Remove any path component
    else:
        host = host_port
        port = 7687  # Default Neo4j bolt port
    
    print(f"Attempting to connect to host: {host} on port: {port}")
    start_time = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = s.connect_ex((host, port))
        if result == 0:
            print(f"Socket connection to {host}:{port} succeeded in {time.time() - start_time:.2f}s")
        else:
            print(f"Socket connection to {host}:{port} failed with error code: {result}")
            print("This indicates the host is unreachable or the port is closed")
    finally:
        s.close()
except Exception as e:
    print(f"Network connectivity test failed: {e}")
    traceback.print_exc()

# STEP 4: Test with neomodel
log_step("Testing connection with neomodel")
try:
    print("Importing neomodel...")
    from neomodel import config, db
    print("Successfully imported neomodel")
    
    # Format the connection URL
    host_port = NEO4J_URI.replace("neo4j+s://", "")
    connection_url = f"bolt+s://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{host_port}"
    masked_url = connection_url.replace(NEO4J_PASSWORD, "********") if NEO4J_PASSWORD else connection_url
    print(f"Setting database URL: {masked_url}")
    
    config.DATABASE_URL = connection_url
    config.AUTO_INSTALL_LABELS = True
    config.ENCRYPTED = True
    
    print("Attempting cypher query...")
    start_time = time.time()
    try:
        results, meta = db.cypher_query("MATCH (n) RETURN count(n) AS count LIMIT 1", timeout=10)
        count = results[0][0]
        print(f"Query successful! Database contains {count} nodes.")
        print(f"Query completed in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"Cypher query failed after {time.time() - start_time:.2f}s: {e}")
        traceback.print_exc()
        print("\nDETAILED ERROR ANALYSIS:")
        if "Unauthorized" in str(e):
            print("Authentication failed. Please check your Neo4j username and password.")
        elif "Connection refused" in str(e):
            print("Connection refused. Please check that Neo4j is running and the URI is correct.")
        elif "Name or service not known" in str(e) or "nodename nor servname provided" in str(e):
            print("Could not resolve hostname. Please check the Neo4j URI.")
        elif "timed out" in str(e):
            print("Connection timed out. The server might be down or blocked by a firewall.")
except Exception as e:
    print(f"Neomodel test failed: {e}")
    traceback.print_exc()

# STEP 5: Test directly with neo4j driver
log_step("Testing with direct neo4j driver")
try:
    print("Importing neo4j driver...")
    from neo4j import GraphDatabase
    print("Successfully imported neo4j driver")
    
    print("Creating driver instance...")
    # Format URI for direct driver connection
    driver_uri = NEO4J_URI
    if driver_uri.startswith("neo4j+s://"):
        driver_uri = "neo4j+s://" + driver_uri.replace("neo4j+s://", "")
    
    print(f"Using URI: {driver_uri}")
    driver = GraphDatabase.driver(
        driver_uri, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    print("Testing connection with driver...")
    start_time = time.time()
    try:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count LIMIT 1")
            record = result.single()
            count = record["count"]
            print(f"Driver connection successful! Database contains {count} nodes.")
            print(f"Query completed in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"Driver connection failed after {time.time() - start_time:.2f}s: {e}")
        traceback.print_exc()
    finally:
        driver.close()
except Exception as e:
    print(f"Neo4j driver test failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("CONNECTION TEST COMPLETE")
print("=" * 80)
