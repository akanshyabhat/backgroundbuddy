import json
import spacy
import prodigy
from prodigy.components.preprocess import add_tokens
from prodigy.components.loaders import JSONL
from neo4j import GraphDatabase
from collections import defaultdict
import os
import re
from langchain.chat_models import ChatOpenAI
import dotenv




# Load environment variables
dotenv.load_dotenv('neo4jKey.env')

# Initialize LLM for enhanced relationship extraction
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

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

def prepare_annotation_tasks():
    """Prepare both entity and relationship annotation tasks"""
    print("\n=== Annotation Pipeline ===")
    
    # 1. Entity Annotation
    print("\n1. Entity Annotation Commands:")
    print("Run these commands in order:")
    print("a) Create entity dataset:")
    print("prodigy dataset political_ner \"Political entity annotations\"")
    
    print("\nb) Annotate entities with patterns:")
    print("prodigy ner.make-gold political_ner en_core_web_trf ../Frey_pdfs -p patterns.jsonl")
    
    # 2. Relationship Annotation
    print("\n2. Relationship Annotation Commands:")
    print("a) Create relationship dataset:")
    print("prodigy dataset political_rels \"Political relationship annotations\"")
    
    print("\nb) Annotate relationships:")
    print("prodigy rel.manual political_rels ./data.jsonl --label VETOED,PROPOSED,SUPPORTED,OPPOSED --span-label POLITICIAN,GOVERNMENT_ORG,POLICY")
    
    input("\nPress Enter after completing both entity and relationship annotations...")

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

def extract_relationships_with_llm(text, entities):
    """Extract relationships using GPT-4 with confidence scores"""
    prompt = f"""
    Analyze this political text and extract relationships between entities.
    Focus on political actions like 'VETOED', 'PROPOSED', 'SUPPORTED', 'OPPOSED'.
    
    Text: "{text}"
    Entities: {entities}
    
    For each relationship, provide:
    1. The initiating entity (subject)
    2. The action taken (predicate)
    3. The target entity (object)
    4. Confidence score (0.0-1.0)
    5. Supporting evidence (quote from text)
    
    Return as JSON array of relationships.
    Example:
    [
        {{
            "subject": "Mayor Jacob Frey",
            "predicate": "VETOED",
            "object": "carbon emissions fee",
            "confidence": 0.95,
            "evidence": "Mayor Jacob Frey vetoed the carbon emissions fee"
        }}
    ]
    """
    
    try:
        response = llm.predict(prompt)
        relationships = json.loads(response)
        return relationships
    except Exception as e:
        print(f"Error in LLM relationship extraction: {e}")
        return []

def validate_relationships_with_prodigy(relationships, dataset_name):
    """Human validation of extracted relationships using Prodigy"""
    validation_examples = []
    
    for rel in relationships:
        # Format relationship for human review
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
        validation_examples.append(example)
    
    # Save examples for Prodigy
    with open("relationships_to_validate.jsonl", "w") as f:
        for example in validation_examples:
            f.write(json.dumps(example) + "\n")
    
    print("\n=== Relationship Validation Phase ===")
    print("Review and validate extracted relationships:")
    print(f"prodigy review {dataset_name}_rels ./relationships_to_validate.jsonl")
    
    input("\nPress Enter after completing relationship validation...")
    return validation_examples

class Neo4jGraphBuilder:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def create_entity(self, entity_type, name, properties=None):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (e:`{entity_type}` {name: $name})
                SET e += $properties
                """,
                name=name,
                properties=properties or {}
            )

    def create_relationship(self, subject, predicate, object, confidence, evidence):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a {name: $subject}), (b {name: $object})
                MERGE (a)-[r:`{predicate}` {
                    confidence: $confidence,
                    evidence: $evidence
                }]->(b)
                """,
                subject=subject,
                object=object,
                confidence=confidence,
                evidence=evidence
            )

def main():
    try:
        # 1. Set up and run entity annotation
        patterns = setup_annotation_patterns()
        with open("patterns.jsonl", "w") as f:
            for pattern in patterns:
                f.write(json.dumps(pattern) + "\n")
        
        print("\n=== Entity Annotation Phase ===")
        print("Run: prodigy ner.make-gold political_ner en_core_web_trf ../Frey_pdfs -p patterns.jsonl")
        input("\nPress Enter after completing entity annotation...")

        # 2. Get accepted entities and process for relationships
        entities = get_annotations()
        context_entities = process_entities_for_relationships(entities)
        
        # 3. Extract and validate relationships
        all_relationships = []
        for context, entities_in_context in context_entities.items():
            # Extract relationships using LLM
            relationships = extract_relationships_with_llm(context, entities_in_context)
            if relationships:
                all_relationships.extend(relationships)
        
        # 4. Human validation of relationships
        validated_relationships = validate_relationships_with_prodigy(all_relationships, "political")
        
        # 5. Build Knowledge Graph
        print("\n=== Building Knowledge Graph ===")
        graph = Neo4jGraphBuilder()
        
        # Add entities first
        unique_entities = set()
        for rel in validated_relationships:
            if rel.get("answer") == "accept":
                unique_entities.add((rel["meta"]["subject"], "ENTITY"))
                unique_entities.add((rel["meta"]["object"], "ENTITY"))
        
        for entity, entity_type in unique_entities:
            graph.create_entity(entity_type, entity)
            print(f"✅ Added entity: {entity}")
        
        # Add validated relationships
        for rel in validated_relationships:
            if rel.get("answer") == "accept":
                graph.create_relationship(
                    rel["meta"]["subject"],
                    rel["meta"]["predicate"],
                    rel["meta"]["object"],
                    rel["meta"]["confidence"],
                    rel["text"]
                )
                print(f"✅ Added relationship: {rel['meta']['subject']} -[{rel['meta']['predicate']}]-> {rel['meta']['object']}")
        
        print("\n✅ Knowledge graph built successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'graph' in locals():
            graph.close()

if __name__ == "__main__":
    main()
