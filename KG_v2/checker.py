from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv("neo4jKey.env")

print("URI:", os.getenv("NEO4J_URI"))
print("Username:", os.getenv("NEO4J_USERNAME"))
print("Password:", os.getenv("NEO4J_PASSWORD"))

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1")
        print("✅ Connected successfully! Result:", result.single()[0])
except Exception as e:
    print(f"❌ Connection failed: {e}")
finally:
    driver.close()
