from neo4j_updater import Neo4jHandler, load_relationships_to_neo4j
import os
import dotenv

# Try to load environment variables from multiple possible locations
dotenv.load_dotenv('.env')

# Get credentials
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

print(f"URI: {neo4j_uri}")
print(f"Username: {neo4j_user}")
print(f"Password: {'*' * len(neo4j_password) if neo4j_password else 'None'}")

try:
    # Initialize Neo4j handler
    handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)
    
    # Test connection
    if handler.test_connection():
        # Load relationships from JSONL
        file_path = "relationships.jsonl"
        print(f"\n📂 Processing file: {file_path}")
        load_relationships_to_neo4j(file_path, handler)
        print("✅ Relationships loaded successfully.")
        print("running locally at http://localhost:7474/browser/")
    else:
        print("❌ Cannot proceed due to connection issues.")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
finally:
    if 'handler' in locals():
        handler.close() 