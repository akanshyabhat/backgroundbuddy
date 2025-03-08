import os
import dotenv
import json
import re
from neo4j import GraphDatabase
from typing import Dict


# Load environment variables from multiple possible locations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "neo4jKey.env")
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path, override=True)
elif os.path.exists('NEO4J_KEY.env'):
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
        """Close the Neo4j connection."""
        self.driver.close()

    def add_entity(self, entity_id, entity_name, entity_type="Unknown"):
        """Create or update an entity in Neo4j using its type as the label."""
        if not entity_name:
            print(f"⚠️ Skipping entity with empty name (ID: {entity_id})")
            return
            
        # Ensure entity_type is valid for Neo4j (no spaces, alphanumeric)
        label = entity_type.replace(" ", "_").upper() if entity_type else "UNKNOWN"
        
        query = """
        MERGE (n:`%s` {id: $id})
        SET n.name = $name
        """ % label
        
        try:
            with self.driver.session() as session:
                session.run(query, {"id": entity_id, "name": entity_name})
                print(f"✅ Added/Updated {label}: {entity_name} (ID: {entity_id})")
        except Exception as e:
            print(f"❌ Error adding entity {entity_name}: {str(e)}")

    def add_relationship(self, subject_id, subject_name, relationship, object_id, object_name, evidence, metadata):
        """Create a relationship between entities in Neo4j."""
        if not relationship:
            print(f"⚠️ Skipping relationship with empty type between {subject_name} and {object_name}")
            return
            
        # Format relationship type - must be alphanumeric with underscores
        sanitized_rel = re.sub(r"\s+", "_", relationship.upper())  
        sanitized_rel = re.sub(r"[^a-zA-Z0-9_]", "", sanitized_rel)
        
        if not sanitized_rel:
            sanitized_rel = "RELATED_TO"  

        # Get the entity types from metadata
        subject_type = metadata.get("subject_type", "UNKNOWN").replace(" ", "_").upper()
        object_type = metadata.get("object_type", "UNKNOWN").replace(" ", "_").upper()

        query = f"""
        MATCH (a:`{subject_type}` {{id: $subject_id}})
        MATCH (b:`{object_type}` {{id: $object_id}})
        MERGE (a)-[r:{sanitized_rel}]->(b)
        SET r.evidence = $evidence,
            r.article_id = $article_id,
            r.headline = $headline,
            r.date = $date,
            r.confidence = $confidence,
            r.subject_type = $subject_type,
            r.object_type = $object_type
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
                    "confidence": metadata.get("confidence", 0.0),
                    "subject_type": metadata.get("subject_type"),
                    "object_type": metadata.get("object_type")
                })
                print(f"✅ Added relationship: {subject_name} -[{relationship}]-> {object_name}")
        except Exception as e:
            print(f"❌ Error adding relationship: {str(e)}")

    def export_relationships_to_json(self, output_file="output.json"):
        """Pull relationships from Neo4j and save them as a JSON file."""
        query = """
        MATCH (a:Entity)-[r]->(b:Entity)
        RETURN 
            a.name AS subject_text, 
            a.type AS subject_type,
            type(r) AS relationship, 
            b.name AS object_text, 
            b.type AS object_type,
            r.evidence AS evidence
        """

        try:
            with self.driver.session() as session:
                results = session.run(query)
                data = [record.data() for record in results]

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
                print(f"✅ Relationships successfully exported to {output_file}")

        except Exception as e:
            print(f"❌ Error exporting relationships: {str(e)}")

    def import_relationships_from_jsonl(self, file_path="validated_relationships.jsonl"):
        """Read relationships from JSONL and store them in Neo4j with proper entity types."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    meta = data.get("meta", {})

                    subject_id = meta.get("subject_kb_id")
                    object_id = meta.get("object_kb_id")
                    relationship = meta.get("relationship")
                    article_id = meta.get("article_id")
                    headline = meta.get("headline")
                    date = meta.get("date")
                    subject_type = meta.get("subject_type")
                    object_type = meta.get("object_type")
                    
                    # Load KB
                    KB = load_kb()
                    
                    # Extract entity texts from spans
                    subject_text = None
                    object_text = None
                    for span in data.get("spans", []):
                        if span["label"] == "SUBJECT":
                            subject_text = data["text"][span["start"]:span["end"]]
                        elif span["label"] == "OBJECT":
                            object_text = data["text"][span["start"]:span["end"]]

                    # Fallback to KB if spans don't provide the text
                    if not subject_text:
                        subject_text = get_entity_name_from_kb(subject_id, KB)
                    if not object_text:
                        object_text = get_entity_name_from_kb(object_id, KB)

                    # Verify we have all required data
                    if not all([subject_id, object_id, relationship]):
                        print(f"Missing required fields in relationship", data)
                        continue

                    # Add entities and relationship to Neo4j
                    self.add_entity(subject_id, subject_text, subject_type)
                    self.add_entity(object_id, object_text, object_type)

                    metadata = {
                        "article_id": article_id,
                        "headline": headline,
                        "date": date,
                        "subject_type": subject_type,
                        "object_type": object_type
                    }
                    
                    self.add_relationship(
                        subject_id, 
                        subject_text, 
                        relationship, 
                        object_id, 
                        object_text, 
                        data["text"], 
                        metadata
                    )
                    
                    print(f"✅ Processed relationship: {subject_text} -[{relationship}]-> {object_text}")

        except Exception as e:
            print(f"❌ Error reading JSONL file {file_path}: {str(e)}")

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

if __name__ == "__main__":
    try:
        # Load Neo4j credentials
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Missing Neo4j credentials in environment variables")

        # Initialize Neo4j handler
        handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)

        # Test connection
        if not handler.test_connection():
            raise ValueError("Failed to connect to Neo4j database")

        # Import relationships from JSONL
        print("\n📥 Importing relationships from validated_relationships.jsonl...")
        handler.import_relationships_from_jsonl("validated_relationships.jsonl")

        # Export relationships to JSON file
        print("\n📤 Exporting relationships to output.json...")
        handler.export_relationships_to_json("output.json")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if "handler" in locals():
            handler.close()
