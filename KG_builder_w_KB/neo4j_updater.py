import os
import dotenv
import json
import re
import uuid  # To generate unique IDs
from neo4j import GraphDatabase

# Load environment variables
dotenv.load_dotenv('NEO4J_KEY.env')

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

    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.driver.session() as session:
                session.run(query)
                print("✅ Database cleared successfully")
        except Exception as e:
            print(f"Error clearing database: {str(e)}")

    def add_entity(self, entity_id, entity_name):
        """Create or update an entity in Neo4j."""
        query = """
        MERGE (n:Entity {id: $id})
        SET n.name = $name
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "id": entity_id,
                    "name": entity_name
                })
                print(f"✅ Added/Updated entity: {entity_name} (ID: {entity_id})")
        except Exception as e:
            print(f"❌ Error adding entity {entity_name}: {str(e)}")

    def add_relationship(self, subject_id, subject_name, relationship, object_id, object_name, evidence, metadata):
        """Create a relationship between entities in Neo4j."""
        sanitized_rel = re.sub(r"\s+", "_", relationship)  # Format relationship type
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
                print(f"✅ Added relationship: {subject_name} -[{relationship}]-> {object_name}")
        except Exception as e:
            print(f"❌ Error adding relationship: {str(e)}")

def load_relationships_to_neo4j(file_path, neo4j_handler):
    """Load relationships from JSONL file into Neo4j while ensuring unique entity IDs."""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    entity_mapping = {}  # Dictionary to store entity name → unique ID mapping
    relationship_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    text = entry.get("text", "")
                    spans = entry.get("spans", [])
                    meta = entry.get("meta", {})

                    # Extract subject and object entities
                    subject_text = extract_span_text(text, spans, "SUBJECT")
                    object_text = extract_span_text(text, spans, "OBJECT")

                    # Relationship type
                    relationship_type = meta.get("relationship")
                    if not relationship_type:
                        print(f"⚠️ Line {line_num}: Missing relationship type, skipping.")
                        continue

                    # Generate or reuse unique IDs
                    if subject_text not in entity_mapping:
                        entity_mapping[subject_text] = str(uuid.uuid4())  # Generate unique ID
                    subject_id = entity_mapping[subject_text]

                    if object_text not in entity_mapping:
                        entity_mapping[object_text] = str(uuid.uuid4())  # Generate unique ID
                    object_id = entity_mapping[object_text]

                    print(f"Processing Relationship: {subject_text} -[{relationship_type}]-> {object_text}")

                    # Add entities to Neo4j
                    neo4j_handler.add_entity(subject_id, subject_text)
                    neo4j_handler.add_entity(object_id, object_text)

                    # Add relationship
                    neo4j_handler.add_relationship(
                        subject_id, subject_text,
                        relationship_type,
                        object_id, object_text,
                        text,  # Evidence
                        {
                            "article_id": meta.get("article_id"),
                            "headline": meta.get("headline"),
                            "date": meta.get("date")
                        }
                    )

                    relationship_count += 1
                    if relationship_count % 10 == 0:
                        print(f"Processed {relationship_count} relationships so far...")

                except json.JSONDecodeError:
                    print(f"❌ Line {line_num}: Invalid JSON format")
                except Exception as e:
                    print(f"❌ Line {line_num}: Error processing entry: {str(e)}")

        print(f"\n✅ Processing completed: {relationship_count} relationships loaded into Neo4j.")

    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")

def extract_span_text(text, spans, label):
    """Extract text from a given span label."""
    for span in spans:
        if span.get("label") == label:
            start, end = span.get("start"), span.get("end")
            if start is not None and end is not None and 0 <= start < len(text) and end <= len(text):
                return text[start:end].strip()
    return None

if __name__ == "__main__":
    try:
        # Load Neo4j credentials
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Missing Neo4j credentials in environment variables")

        # Initialize Neo4j handler
        handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)

        # Load relationships from JSONL
        file_path = "relationships.jsonl"
        print(f"\n📂 Processing file: {file_path}")
        load_relationships_to_neo4j(file_path, handler)

        # Display Neo4j query for visualization
        print("\n🔍 To visualize relationships in Neo4j, run this query:")
        print("""
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n.name as Subject, 
               type(r) as Relationship, 
               m.name as Object,
               r.evidence as Evidence
        LIMIT 25;
        """)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'handler' in locals():
            handler.close()