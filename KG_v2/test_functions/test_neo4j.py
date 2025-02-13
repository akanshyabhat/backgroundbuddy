from neo4j import GraphDatabase
import os
import dotenv
import json

# Load environment variables
dotenv.load_dotenv('neo4jKey.env')  # Load Neo4j credentials

# Load Neo4j credentials
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_uri = os.getenv("NEO4J_URI")

if not neo4j_username or not neo4j_password or not neo4j_uri:
    raise ValueError("One or more Neo4j credentials are missing in the environment variables.")

def add_entity_to_graph(entity_name, entity_type):
    """Add an entity to the Neo4j graph."""
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        with driver.session() as session:
            print(f"🔗 Attempting to add entity: {entity_name} of type {entity_type}")
            query = f"""
            MERGE (n:{entity_type} {{name: $name}})
            """
            session.run(query, {"name": entity_name})
            print(f"✅ Added entity: {entity_name} of type {entity_type}")
        driver.close()
    except Exception as e:
        print(f"❌ Error adding entity to Neo4j: {e}")

def add_relationship_to_graph(subject, predicate, object_, confidence, evidence):
    """Add a relationship to the Neo4j graph."""
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        with driver.session() as session:
            print(f"🔗 Attempting to add relationship: {subject} -[{predicate}]-> {object_}")
            query = f"""
            MATCH (a {{name: $subject}}), (b {{name: $object_}})
            MERGE (a)-[r:{predicate} {{confidence: $confidence, evidence: $evidence}}]->(b)
            """
            session.run(query, {
                "subject": subject,
                "object_": object_,
                "confidence": confidence,
                "evidence": evidence
            })
            print(f"✅ Added relationship: {subject} -[{predicate}]-> {object_}")
        driver.close()
    except Exception as e:
        print(f"❌ Error adding relationship to Neo4j: {e}")

# Test adding an entity and a relationship
if __name__ == "__main__":
    # Test adding a sample entity
    add_entity_to_graph("Mayor Jacob Frey", "POLITICIAN")
    add_entity_to_graph("Minneapolis City Council", "GOVERNMENT_ORG")
    
    # Load relationships from annotations.jsonl
    with open("annotations.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            subject = entry["meta"]["subject"]
            predicate = entry["meta"]["predicate"]
            object_ = entry["meta"]["object"]
            confidence = entry["meta"]["confidence"]
            evidence = entry["text"]

            # Add relationship to the graph
            add_relationship_to_graph(subject, predicate, object_, confidence, evidence)
