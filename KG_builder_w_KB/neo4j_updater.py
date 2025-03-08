import os
import dotenv
import json
import re
import uuid  # To generate unique IDs
from neo4j import GraphDatabase
from typing import Dict
# Try to load environment variables from multiple possible locations
if os.path.exists('NEO4J_KEY.env'):
    dotenv.load_dotenv('NEO4J_KEY.env')
elif os.path.exists('KG_v2/neo4jKey.env'):
    dotenv.load_dotenv('KG_v2/neo4jKey.env')
elif os.path.exists('.env'):
    dotenv.load_dotenv('.env')

''' 
------------------------------------------------------------
7. PASS VERIFIED RELATIONSHIPS TO NEO4J TO UPDATE KNOWLEDGE GRAPH
(INCLUDE EVIDENCE AND CITATION)
------------------------------------------------------------
'''

class Neo4jHandler:
    def __init__(self, uri, user, password):
        try:
            # Use basic auth explicitly
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Neo4j Connection Failed: {e}")
            raise

    def test_connection(self):
        """Test the connection to Neo4j."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful' as message")
                message = result.single()["message"]
                print(f"✅ {message}")
                return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

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
        if not entity_name:
            print(f"⚠️ Skipping entity with empty name (ID: {entity_id})")
            return
            
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
        if not relationship:
            print(f"⚠️ Skipping relationship with empty type between {subject_name} and {object_name}")
            return
            
        # Format relationship type - must be alphanumeric with underscores
        sanitized_rel = re.sub(r"\s+", "_", relationship.upper())  # Format relationship type
        sanitized_rel = re.sub(r"[^a-zA-Z0-9_]", "", sanitized_rel)
        
        if not sanitized_rel:
            sanitized_rel = "RELATED_TO"  # Default relationship type

        query = f"""
        MATCH (a:Entity {{id: $subject_id}})
        MATCH (b:Entity {{id: $object_id}})
        MERGE (a)-[r:{sanitized_rel}]->(b)
        SET r.evidence = $evidence,
            r.article_id = $article_id,
            r.headline = $headline,
            r.date = $date,
            r.confidence = $confidence
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "evidence": evidence,
                    "article_id": metadata.get("article_id"),
                    "headline": metadata.get("headline"),
                    "date": metadata.get("date"),
                    "confidence": metadata.get("confidence", 0.0)
                })
                print(f"✅ Added relationship: {subject_name} -[{relationship}]-> {object_name}")
        except Exception as e:
            print(f"❌ Error adding relationship: {str(e)}")

def extract_span_text(text, spans, label):
    """Extract text from a given span label."""
    for span in spans:
        if span.get("label") == label:
            start, end = span.get("start"), span.get("end")
            if start is not None and end is not None and 0 <= start < len(text) and end <= len(text):
                return text[start:end].strip()
    return None

def load_kb() -> Dict:
    """Load the knowledge base from KB.json"""
    try:
        with open("KB.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: KB.json not found")
        return {}

def get_entity_name_from_kb(kb_id: str, KB: Dict) -> str:
    """Get entity's canonical name from KB using its ID"""
    if kb_id and kb_id in KB:
        return KB[kb_id].get('canonical_name', '')
    print(f"❌ Entity not found in KB: {kb_id}")
    return ''

def load_relationships_to_neo4j(file_path, neo4j_handler):
    """Load relationships from JSONL file into Neo4j."""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    # Test connection before proceeding
    if not neo4j_handler.test_connection():
        print("❌ Cannot proceed with loading relationships due to connection issues.")
        return

    relationship_count = 0
    entity_mapping = {}  # To track entities we've already added

    # Load the knowledge base
    KB = load_kb()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Parse the JSON line
                    entry = json.loads(line)
                    
                    # Extract data
                    text = entry.get("text", "")
                    spans = entry.get("spans", [])
                    meta = entry.get("meta", {})
                    
                    # Extract subject and object from spans
                    subject_text = extract_span_text(text, spans, "SUBJECT")
                    object_text = extract_span_text(text, spans, "OBJECT")
                    
                    # Get the object text from KB if not directly available
                    if object_text is None:
                        object_kb_id = meta.get("object_kb_id")
                        object_text = get_entity_name_from_kb(object_kb_id, KB)
                    
                    # Get the subject text from KB if not directly available
                    if subject_text is None:
                        subject_kb_id = meta.get("subject_kb_id")
                        subject_text = get_entity_name_from_kb(subject_kb_id, KB)
                    
                    # Get relationship type from meta
                    relationship_type = meta.get("relationship")
                    
                    # Get KB IDs from meta if available, otherwise use the entity text as ID
                    subject_id = meta.get("subject_kb_id")
                    if not subject_id:
                        subject_id = entity_mapping.get(subject_text)
                        if not subject_id:
                            subject_id = str(uuid.uuid4())
                            entity_mapping[subject_text] = subject_id
                    
                    object_id = meta.get("object_kb_id")
                    if not object_id:
                        object_id = entity_mapping.get(object_text)
                        if not object_id:
                            object_id = str(uuid.uuid4())
                            entity_mapping[object_text] = object_id
                    
                    # Skip if missing critical data
                    if not subject_text or not object_text or not relationship_type:
                        print(f"⚠️ Line {line_num}: Missing critical data, skipping.")
                        print(f"   Subject: {subject_text}, Object: {object_text}, Relationship: {relationship_type}")
                        continue
                    
                    print(f"Processing: {subject_text} -[{relationship_type}]-> {object_text}")
                    
                    # Add entities to Neo4j
                    neo4j_handler.add_entity(subject_id, subject_text)
                    neo4j_handler.add_entity(object_id, object_text)
                    
                    # Add relationship
                    neo4j_handler.add_relationship(
                        subject_id, subject_text,
                        relationship_type,
                        object_id, object_text,
                        text,  # Full text as evidence
                        meta   # All metadata
                    )
                    
                    relationship_count += 1
                    
                except json.JSONDecodeError:
                    print(f"❌ Line {line_num}: Invalid JSON format")
                except Exception as e:
                    print(f"❌ Line {line_num}: Error processing entry: {str(e)}")
        
        print(f"\n✅ Processing completed: {relationship_count} relationships loaded into Neo4j.")
        
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")

if __name__ == "__main__":
    try:
        # Load Neo4j credentials
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Missing Neo4j credentials in environment variables")

        print(f"URI: {neo4j_uri}")
        print(f"Username: {neo4j_user}")
        print(f"Password: {'*' * len(neo4j_password) if neo4j_password else 'None'}")

        # Initialize Neo4j handler
        handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)
        
        # Test connection
        if not handler.test_connection():
            raise ValueError("Failed to connect to Neo4j database")

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