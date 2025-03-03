import os
import dotenv
import spacy
import textacy
import textacy.extract
import json
import prodigy
from prodigy.components.preprocess import add_tokens
from prodigy.components.loaders import JSONL
from neo4j import GraphDatabase
from collections import defaultdict
from langchain_openai import ChatOpenAI
import pdfplumber
from difflib import SequenceMatcher
import prodigy.components.db
from extract_text import extract_text_from_pdfs

from neo4j import GraphDatabase
import os
import dotenv
import json
import re  # Import regex for sanitization

# Load environment variables
dotenv.load_dotenv('neo4jKey.env')  # Load Neo4j credentials

# Load Neo4j credentials
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_uri = os.getenv("NEO4J_URI")

if not neo4j_username or not neo4j_password or not neo4j_uri:
    raise ValueError("One or more Neo4j credentials are missing in the environment variables.")

class Neo4jHandler:
    """Handles Neo4j connections and database operations"""

    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Neo4j Connection Failed: {e}")
            raise

    def close(self):
        self.driver.close()

    def add_entity(self, entity_name, entity_type="Entity"):
        """Ensure an entity exists in the graph."""
        query = f"""
        MERGE (n:{entity_type} {{name: $name}})
        """
        with self.driver.session() as session:
            session.run(query, {"name": entity_name})
            print(f"✅ Added entity: {entity_name} [{entity_type}]")

    def add_relationship(self, subject, predicate, object_, confidence, evidence):
        """Ensure a relationship exists between entities."""
        sanitized_predicate = re.sub(r"\s+", "_", predicate)  # Replace spaces with underscores
        sanitized_predicate = re.sub(r"[^a-zA-Z0-9_]", "", sanitized_predicate)  # Remove invalid characters

        query = f"""
        MATCH (a:Entity {{name: $subject}})
        MATCH (b:Entity {{name: $object_}})
        MERGE (a)-[r:{sanitized_predicate}]->(b)
        SET r.confidence = $confidence, r.evidence = $evidence
        """

        with self.driver.session() as session:
            session.run(query, {
                "subject": subject,
                "object_": object_,
                "confidence": confidence,
                "evidence": evidence
            })
            print(f"✅ Added relationship: {subject} -[{sanitized_predicate}]-> {object_}")

def add_to_neo4j(graph, file):
    """Reads relationships from annotations.jsonl and adds them to Neo4j."""
    if not os.path.exists(file):
        print("❌ No annotations.jsonl file found!")
        return

    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            subject = entry["meta"]["subject"]
            predicate = entry["meta"]["predicate"]
            object_ = entry["meta"]["object"]
            confidence = entry["meta"]["confidence"]
            evidence = entry["text"]

            # Ensure both entities exist
            graph.add_entity(subject, "Entity")
            graph.add_entity(object_, "Entity")

            # Add the relationship
            graph.add_relationship(subject, predicate, object_, confidence, evidence)
    

# Load environment variables
dotenv.load_dotenv('neo4jKey.env')  # Load Neo4j credentials
dotenv.load_dotenv('openAI.env')      # Load OpenAI credentials

# Load API keys
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

# Load Neo4j credentials
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_uri = os.getenv("NEO4J_URI")
if neo4j_password is None or neo4j_uri is None:
    raise ValueError("NEO4J_PASSWORD or NEO4J_URI is not set in the environment variables.")

# Set environment variables
os.environ["OPENAI_API_KEY"] = api_key
os.environ["NEO4J_PASSWORD"] = neo4j_password
os.environ["NEO4J_URI"] = neo4j_uri

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError as e:
    print(f"❌ Error loading spaCy model: {e}")
    print("Please ensure the model is installed by running 'python -m spacy download en_core_web_sm'")
    raise

# Initialize GPT-4 model
llm = ChatOpenAI(model_name="o3-mini")


# --- Entity & Relationship Extraction ---
# REstricting entity types and their properties
#HAVEN'T RESTRICTED THIS YET
NODE_TYPES = {
    "PERSON": ["name", "birth_date", "role"],
    "ORG": ["name", "founded", "type"],
    "EVENT": ["name", "date", "location"],
    "GPE": ["name", "region", "country"],  # geopolitical
    "LAW": ["name", "date", "type"],
    "MONEY": ["name", "amount", "currency"],
    "TIME": ["date", "time", "duration"],
    "PRODUCT": ["name", "type", "manufacturer"],
    "LANGUAGE": ["name", "type", "dialect"],
    "NORP": ["name", "type", "region"],

}

# Restricting relationship types and their properties
RELATIONSHIP_TYPES = {
    "WORKS_FOR": ["since"],
    "MENTIONS": ["frequency"],
    "LOCATED_IN": ["since"],
    "AFFILIATED_WITH": ["start_date", "end_date"],
    "VETOED": ["date"],
    "PROPOSED": ["date"],
    "SUPPORTED": ["date"],
    "OPPOSED": ["date"],
    "MENTIONS": ["frequency"],
    "MENTIONED_IN": ["frequency"],
    "HAS_PARTICIPANT": ["role"],
    "HAS_LOCATION": ["region", "country"],
    "HAS_DATE": ["date"],
    "HAS_TYPE": ["type"]
}
# Define political domain-specific entity types with granularity rules
POLITICAL_ENTITIES = {
    "POLITICIAN": {
        "terms": ["mayor", "senator", "council member", "representative"],
        "rules": {
            "title_person": [{"LOWER": {"IN": ["mayor", "senator"]}}, {"ENT_TYPE": "PERSON"}],
            "full_name": [{"ENT_TYPE": "PERSON"}, {"ENT_TYPE": "PERSON"}]
        }
    },
    "GOVERNMENT_ORG": {
        "terms": ["city council", "department", "committee", "agency"],
        "rules": {
            "org_full": [{"LOWER": "department"}, {"LOWER": "of"}, {"IS_TITLE": True}]
        }
    },
    "POLICY": {
        "terms": ["bill", "ordinance", "regulation", "resolution"],
        "rules": {
            "policy_name": [{"LOWER": {"IN": ["bill", "ordinance"]}}, {"IS_TITLE": True, "OP": "+"}]
        }
    }
}

def setup_annotation_patterns():
    """Create comprehensive patterns for entity recognition"""
    patterns = []
    
    # Basic term patterns
    for entity_type, config in POLITICAL_ENTITIES.items():
        for term in config["terms"]:
            patterns.append({
                "label": entity_type,
                "pattern": term,
                "id": f"{entity_type}_{term}"
            })
        
        # Complex rule patterns
        for rule_name, rule_pattern in config.get("rules", {}).items():
            patterns.append({
                "label": entity_type,
                "pattern": rule_pattern,
                "id": f"{entity_type}_{rule_name}"
            })
    
    return patterns

def get_annotations():
    """Retrieve annotations from Prodigy"""
    try:
        # Get entity annotations with accepted spans only
        entity_examples = prodigy.get_dataset("political_ner")
        accepted_entities = []
        for example in entity_examples:
            if example.get("answer") == "accept":
                for span in example.get("spans", []):
                    accepted_entities.append({
                        "text": span["text"],
                        "label": span["label"],
                        "context": example["text"]
                    })
        print(f"Retrieved {len(accepted_entities)} accepted entity annotations")
        return accepted_entities
    except Exception as e:
        print(f"Error retrieving annotations: {e}")
        return []

def process_entities_for_relationships(entities):
    """Group entities by their context and prepare for relationship extraction"""
    context_entities = defaultdict(list)
    for entity in entities:
        context_entities[entity["context"]].append({
            "text": entity["text"],
            "label": entity["label"]
        })
    return context_entities

def extract_entities(text):
    """Extract named entities using spaCy"""
    doc = nlp(text)
    entities = defaultdict(set)
    
    for ent in doc.ents:
        entities[ent.label_].add(ent.text.strip())
    
    # Debug: Print extracted entities
    print(f"Extracted entities from text: {text[:50]}...")  # Print the first 50 characters of the text for context
    print(f"Entities: {dict(entities)}")  # Print the entities dictionary
    
    return entities

def extract_relationships_llm(entities, text):
    """Extract relationships using GPT-4 with confidence scores"""
    entity_str = "\n".join([f"{etype}: {list(ents)}" for etype, ents in entities.items()])
    
    prompt = f"""
    Extract political relationships from this text. Focus on actions like VETOED, PROPOSED, SUPPORTED, OPPOSED.

    Text: {text}

    Identified Entities:
    {entity_str}

    Return a JSON array of relationships. Each relationship must follow this EXACT format:
    [
        {{
            "subject": "<entity that performed the action>",
            "predicate": "<VETOED|PROPOSED|SUPPORTED|OPPOSED>",
            "object": "<entity that received the action>",
            "confidence": <number between 0.0 and 1.0>,
            "evidence": "<exact quote from text showing this relationship>"
        }}
    ]

    If no clear relationships are found, return an empty array: []
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Debug: Print raw response
        print("\nRaw LLM Response:")
        print(content)
        
        if content:
            relationships = json.loads(content)
            if isinstance(relationships, list):
                print(f"\nExtracted {len(relationships)} relationships")
                return relationships
            else:
                print("Response was not a JSON array")
                return []
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON response: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return []

# --- Saving for Human Validation with Prodigy ---

def save_relationships(entities, relationships, output_file="annotations.jsonl"):
    """ Save extracted entities and relationships for human validation """
    data = []
    for rel in relationships:
        example = {
            "text": rel["evidence"],
            "meta": {
                "subject": rel["subject"],
                "predicate": rel["predicate"],
                "object": rel["object"],
                "confidence": rel["confidence"]
            },
            "spans": [
                {"start": rel["evidence"].find(rel["subject"]), 
                 "end": rel["evidence"].find(rel["subject"]) + len(rel["subject"]),
                 "label": "SUBJECT"},
                {"start": rel["evidence"].find(rel["object"]),
                 "end": rel["evidence"].find(rel["object"]) + len(rel["object"]),
                 "label": "OBJECT"}
            ]
        }
        data.append(example)

    with open(output_file, "w") as f:
        for example in data:
            f.write(json.dumps(example) + "\n")

    print(f"✅ Saved {len(data)} relationships for Prodigy validation")

def validate_relationships():
    """Human-in-the-loop validation and save approved relationships."""
    if not os.path.exists("annotations.jsonl"):
        print("❌ No annotations.jsonl file found!")
        return []

    approved_relationships = []
    rejected_count = 0
    more_info_count = 0

    with open("annotations.jsonl", "r", encoding="utf-8") as f:
        relationships = [json.loads(line) for line in f]

    print("\n🔍 Starting Human Validation Process...\n")

    for i, entry in enumerate(relationships):
        subject = entry["meta"]["subject"]
        predicate = entry["meta"]["predicate"]
        object_ = entry["meta"]["object"]
        confidence = entry["meta"]["confidence"]
        evidence = entry["text"]

        print(f"\n📝 Relationship {i+1}/{len(relationships)}")
        print("───────────────────────────────────────────")
        print(f"🔹 **Subject:** {subject}")
        print(f"🔹 **Predicate:** {predicate}")
        print(f"🔹 **Object:** {object_}")
        print(f"🔹 **Confidence Score:** {confidence:.2f}")
        print(f"📜 **Evidence:** {evidence}")
        print("───────────────────────────────────────────")

        while True:
            user_input = input("✅ Approve? (y/n/more): ").strip().lower()
            if user_input in ["y", "n", "more"]:
                break
            print("Invalid input. Please enter 'y' for yes or 'n' for no or 'more' for would need more information.")

        if user_input == "y":
            approved_relationships.append(entry)
            print("✅ Relationship Approved.")
        elif user_input == "more":
            print("More information requested.")
            more_info_count += 1
        else:
            rejected_count += 1
            print("❌ Relationship Rejected.")

    # Save approved relationships to a file
    with open("validated_relationships.jsonl", "w", encoding="utf-8") as f:
        for rel in approved_relationships:
            f.write(json.dumps(rel) + "\n")

    print("\n🎯 Validation Complete!")
    print(f"✅ **Approved Relationships:** {len(approved_relationships)} (Saved to `validated_relationships.jsonl`)")
    print(f"❌ **Rejected Relationships:** {rejected_count}")
    print(f"❌ **More Information Requested:** {more_info_count}")

    return approved_relationships

# --- Full Pipeline ---

def process_pdfs_and_store(graph):
    """Process articles from data.jsonl and store relationships in Neo4j"""
    all_relationships = []
    
    # Read from data.jsonl
    if not os.path.exists("annotations.jsonl"):
        print("Generating annotations.jsonl...")
        with open("data.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                text = entry["text"]
                author = entry.get("author", "Unknown Author")  # Default to "Unknown Author" if not present
                date = entry.get("date", "Unknown Date")  # Default to "Unknown Date" if not present
                
                print(f"📄 Processing text from {author} on {date}...")
                
                # Extract entities & relationships
                entities = extract_entities(text)
                relationships = extract_relationships_llm(entities, text)
                all_relationships.extend(relationships)
    
        # Save for Prodigy validation 
        save_relationships(entities, all_relationships)

    # --- Human Validation ---
    print("Waiting for human validation...")

    # Get validated relationships
    validated_relationships = validate_relationships()
    # Store in Neo4j
    add_to_neo4j(graph, "validated_relationships.jsonl")

# --- Execution ---

if __name__ == "__main__":

    try:
        # Initialize Neo4j connection
        graph = Neo4jHandler(neo4j_uri, neo4j_username, neo4j_password)
        
        # Process articles and build knowledge graph
        process_pdfs_and_store(graph)
        
        # Show Prodigy setup instructions
        
    finally:
        if 'graph' in locals():
            graph.close()
