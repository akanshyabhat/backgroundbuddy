import os
import dotenv
import pdfplumber
import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import re
from transformers import pipeline, AutoTokenizer
import torch
from fuzzywuzzy import fuzz
import transformers

# Ensure all operations run on CPU (MPS can be unstable on macOS)
torch.set_default_device("cpu")

# Load environment variables
dotenv.load_dotenv()

# Load NLP & embedding model
nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load relation extraction model (use `text2text-generation` for Babelscape/rebel-large)
relation_extraction = pipeline("text2text-generation", model="Babelscape/rebel-large", device=-1)  # -1 forces CPU
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
max_length = 1024

# Set logging to error only
transformers.logging.set_verbosity_error()

# Neo4j Entity Type Definitions
NODE_TYPES = {
    "PERSON": ["name", "birth_date", "role"],
    "ORG": ["name", "founded", "type"],
    "EVENT": ["name", "date", "location"],
    "GPE": ["name", "region", "country"],  # Geopolitical entities
}

def normalize_entity(entity):
    return entity.strip().lower()

class GraphDB:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            print("✅ Connected to Neo4j successfully")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {str(e)}")

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            session.run(query, parameters or {})

    def insert_entity(self, entity, entity_type):
        entity = normalize_entity(entity)

        # Ensure entity type is valid
        if entity_type not in NODE_TYPES:
            print(f"⚠️ Skipping unrecognized entity type: {entity_type}")
            return

        # Insert entity into Neo4j
        query = f"""
        MERGE (e:{entity_type} {{name: $name}})
        """
        self.run_query(query, {"name": entity})

    def insert_relationship(self, entity1, entity2):
        entity1 = normalize_entity(entity1)
        entity2 = normalize_entity(entity2)

        # Check if the relationship already exists
        query = """
        MATCH (a {name: $name1})-[r:RELATED_TO]->(b {name: $name2})
        RETURN COUNT(r) AS count
        """
        with self.driver.session() as session:
            count = session.run(query, {"name1": entity1, "name2": entity2}).single()["count"]

        if count == 0:  # Only insert if it doesn't exist
            query = """
            MATCH (a {name: $name1}), (b {name: $name2})
            MERGE (a)-[:RELATED_TO]->(b)
            """
            self.run_query(query, {"name1": entity1, "name2": entity2})
        else:
            print(f"⚠️ Duplicate relationship skipped: ({entity1}) -[:RELATED_TO]-> ({entity2})")

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text.strip()

def extract_entities(text):
    doc = nlp(text)
    entities = defaultdict(set)
    for ent in doc.ents:
        entity_type = ent.label_
        entities[entity_type].add(ent.text.strip().lower())  # Normalize case
    return entities

def find_similar_entity(existing_entities, new_entity, threshold=90):
    """Finds if new_entity is a close match to an existing entity."""
    for existing in existing_entities:
        if fuzz.ratio(existing, new_entity) > threshold:  # Similar enough
            return existing  # Return the best match
    return None  # No match found

def pretrained_relation_extraction(text):
    """Extract relations using the Babelscape/rebel-large model, ensuring text truncation."""
    truncated_text = tokenizer.decode(
        tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)["input_ids"][0],
        skip_special_tokens=True
    )

    # Remove `device=0` when calling the pipeline
    output = relation_extraction(truncated_text, max_length=512, truncation=True)

    # Ensure response format is valid
    return output[0]['generated_text'] if output else ""


def extract_relation_triplets(text):
    """Extract structured (entity1, relation, entity2) triplets from model output."""
    pattern = r"\((.*?)\) -- \[(.*?)\] --> \((.*?)\)"
    return re.findall(pattern, text)

def extract_relationships_with_cosine_similarity(entities, threshold=0.7):
    """Find relationships between entities using cosine similarity."""
    entity_list = [e for values in entities.values() for e in values]
    embeddings = embedding_model.encode(entity_list)
    similarity_matrix = cosine_similarity(embeddings)

    relationships = []
    for i in range(len(entity_list)):
        for j in range(i + 1, len(entity_list)):
            if similarity_matrix[i][j] > threshold:
                relationships.append((entity_list[i], entity_list[j]))

    return relationships

def process_pdf(pdf_path, graph):
    print(f"📄 Processing {pdf_path}...")

    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("❌ No text extracted.")
        return

    # Truncate text to model's max token length
    truncated_text = tokenizer.decode(
        tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)["input_ids"][0],
        skip_special_tokens=True
    )

    # Extract entities and relationships
    entities = extract_entities(truncated_text)
    relationships = extract_relationships_with_cosine_similarity(entities)
    extracted_relations = pretrained_relation_extraction(truncated_text)

    # Debug: Check extracted text-based relations
    print(f"🔍 Raw extracted relations: {extracted_relations}")

    # Convert relations to structured triplets
    valid_relations = extract_relation_triplets(extracted_relations)

    # Store in Neo4j
    for entity_type, entity_set in entities.items():
        for entity in entity_set:
            graph.insert_entity(entity, entity_type)

    for entity1, entity2 in relationships:
        graph.insert_relationship(entity1, entity2)

    for entity1, relation, entity2 in valid_relations:
        graph.insert_relationship(entity1, entity2)

    print(f"✅ Finished processing {pdf_path}.")

# Initialize Neo4j connection
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise ValueError(f"🚨 Missing Neo4j credentials!")

print(f"✅ Using Neo4j URI: {URI}")
graph = GraphDB(URI, USER, PASSWORD)

# Process PDFs
pdf_dir = "Frey_pdfs"
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        process_pdf(os.path.join(pdf_dir, filename), graph)

graph.close()
