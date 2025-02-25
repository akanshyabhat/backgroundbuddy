import os
import dotenv
import json
import re
from neo4j import GraphDatabase

# Load environment variables
dotenv.load_dotenv('neo4jKey.env')

''' 
------------------------------------------------------------
7. PASS VERIFIED RELATIONSHIPS TO NEO4J TO UPDATE KNOWLEDGE GRAPH
(INCLUDE EVIDENCE AND CITATION)
------------------------------------------------------------
'''

class Neo4jHandler:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Neo4j Connection Failed: {e}")
            raise

    def close(self):
        self.driver.close()

    def add_entity(self, entity_id, entity_text):
        """
        Create or update an entity with display name.
        """
        query = """
        MERGE (n:Entity {id: $id})
        SET n.name = $name,
            n.displayName = $name
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "id": entity_id,
                    "name": entity_text
                })
                print(f"✅ Added entity: {entity_text}")
        except Exception as e:
            print(f"❌ Error adding entity {entity_text}: {str(e)}")

    def add_relationship(self, subject_id, relationship, object_id, evidence, metadata):
        """
        Create a relationship between entities with evidence and citation.
        """
        # Sanitize relationship type for Neo4j
        sanitized_rel = re.sub(r"\s+", "_", relationship)
        sanitized_rel = re.sub(r"[^a-zA-Z0-9_]", "", sanitized_rel)

        query = f"""
        MATCH (a:Entity {{id: $subject_id}})
        MATCH (b:Entity {{id: $object_id}})
        MERGE (a)-[r:{sanitized_rel}]->(b)
        SET r.evidence = $evidence,
            r.article_id = $article_id,
            r.headline = $headline,
            r.date = $date
        """

        try:
            with self.driver.session() as session:
                session.run(query, {
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "evidence": evidence,
                    "article_id": metadata.get("article_id"),
                    "headline": metadata.get("headline"),
                    "date": metadata.get("date")
                })
                print(f"✅ Added relationship: {subject_id} -[{relationship}]-> {object_id}")
        except Exception as e:
            print(f"❌ Error adding relationship: {str(e)}")

    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        try:
            with self.driver.session() as session:
                session.run(query)
                print("✅ Database cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing database: {str(e)}")

def load_relationships_to_neo4j(file_path, neo4j_handler):
    """Load relationships from JSONL file into Neo4j."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    meta = entry.get("meta", {})
                    spans = entry.get("spans", [])

                    # Extract entity texts from spans
                    subject_text = None
                    object_text = None
                    for span in spans:
                        if span["label"] == "SUBJECT":
                            subject_text = entry["text"][span["start"]:span["end"]]
                        elif span["label"] == "OBJECT":
                            object_text = entry["text"][span["start"]:span["end"]]

                    # Get IDs and relationship info
                    subject_id = meta.get("subject_kb_id")
                    object_id = meta.get("object_kb_id")
                    relationship = meta.get("relationship")

                    if not all([subject_id, object_id, relationship]):
                        print(f"⚠️ Skipping incomplete entry: {entry}")
                        continue

                    # Create entities with both ID and display text
                    if subject_text:
                        neo4j_handler.add_entity(subject_id, subject_text)
                    if object_text:
                        neo4j_handler.add_entity(object_id, object_text)

                    # Add relationship with metadata
                    metadata = {
                        "article_id": meta.get("article_id"),
                        "headline": meta.get("headline"),
                        "date": meta.get("date")
                    }

                    neo4j_handler.add_relationship(
                        subject_id,
                        relationship,
                        object_id,
                        entry.get("text", ""),
                        metadata
                    )

                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON in line: {line[:100]}...")
                except Exception as e:
                    print(f"❌ Error processing entry: {str(e)}")

        print("✅ Finished loading relationships")
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")

if __name__ == "__main__":
    try:
        # Get Neo4j credentials from environment
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Missing Neo4j credentials in environment variables")

        # Initialize handler
        handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)


        # Load relationships
        load_relationships_to_neo4j("relationships.jsonl", handler)

        print("\nTo visualize the graph with names, run this Cypher query:")
        print("""
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n.name as Subject, 
               type(r) as Relationship, 
               m.name as Object,
               r.evidence as Evidence,
               r.article_id as Article,
               r.date as Date
        LIMIT 25;
        """)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'handler' in locals():
            handler.close()