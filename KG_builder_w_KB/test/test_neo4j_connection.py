import os
import dotenv
from neo4j import GraphDatabase


dotenv.load_dotenv('.env')

# Get credentials
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

print(f"URI: {neo4j_uri}")
print(f"Username: {neo4j_user}")
print(f"Password: {'*' * len(neo4j_password) if neo4j_password else 'None'}")

# Test connection
try:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    with driver.session() as session:
        result = session.run("RETURN 'Connection successful' as message")
        print(result.single()["message"])
    driver.close()
    print("Connection test passed!")
except Exception as e:
    print(f"Connection test failed: {e}") 