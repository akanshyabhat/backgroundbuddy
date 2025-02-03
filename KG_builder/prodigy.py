import os
import dotenv
import pdfplumber
import spacy
import re
import torch
from collections import defaultdict
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

#First approach (Prodigy + LLMs): Best for high-accuracy entity extraction, but requires manual annotation.
# need OPENAI_API_KEY
# need pretrained prodigy model

# Load environment variables
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

# Initialize LLM (Optional, used for complex relationship extraction)
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# Load NLP Model (Use Prodigy-trained model if available)
NER_MODEL_PATH = "./ner_model"
nlp = spacy.load(NER_MODEL_PATH) if os.path.exists(NER_MODEL_PATH) else spacy.load("en_core_web_trf")

# Sentence Transformer for entity consolidation
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Neo4j Connection
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

# Define Node & Relationship Types
NODE_TYPES = {
    "PERSON": ["name", "birth_date", "role"],
    "ORG": ["name", "founded", "type"],
    "EVENT": ["name", "date", "location"],
    "GPE": ["name", "region", "country"],
    "POLICY": ["name", "category", "status"],
    "LEGAL_CASE": ["name", "status"],
    "COMPANY": ["name", "industry", "carbon_emissions"],
}

RELATIONSHIP_TYPES = {
    "WORKS_FOR": ["since"],
    "MENTIONS": ["frequency"],
    "LOCATED_IN": ["since"],
    "AFFILIATED_WITH": ["start_date", "end_date"],
    "CHALLENGES": [],
    "VETOES": ["date"],
    "PROPOSES": ["date"],
    "INVESTIGATED_FOR": ["reason"]
}

# 📌 Extracts text from PDFs (chunks large PDFs)
def extract_text_from_pdf(pdf_path, chunk_size=1000):
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# 📌 Extracts named entities
def extract_entities(text):
    doc = nlp(text)
    entities = defaultdict(set)
    for ent in doc.ents:
        if ent.label_ in NODE_TYPES:
            entities[ent.label_].add(ent.text.strip())
    return entities

# 📌 Finds similar entities using embeddings (better than fuzzy matching)
def consolidate_entities(existing_entities, new_entity, threshold=0.85):
    entity_list = list(existing_entities)
    if not entity_list:
        return new_entity

    embeddings = embedding_model.encode(entity_list + [new_entity])
    scores = torch.cosine_similarity(
        torch.tensor([embeddings[-1]]), torch.tensor(embeddings[:-1])
    ).tolist()

    best_match = max(zip(entity_list, scores), key=lambda x: x[1])
    return best_match[0] if best_match[1] > threshold else new_entity

# 📌 Extracts relationships using dependency parsing + regex
def extract_relationships(text, entities):
    relationships = []
    
    # Rule-based Patterns for Politics
    patterns = [
        (r"(\b{}\b).*?\bchallenges\b.*?(\b{}\b)", "CHALLENGES"),
        (r"(\b{}\b).*?\bproposes\b.*?(\b{}\b)", "PROPOSES"),
        (r"(\b{}\b).*?\bvetoes\b.*?(\b{}\b)", "VETOES"),
        (r"(\b{}\b).*?\binvestigated for\b.*?(\b{}\b)", "INVESTIGATED_FOR"),
    ]

    detected_entities = [e for values in entities.values() for e in values]

    for entity1 in detected_entities:
        for entity2 in detected_entities:
            if entity1 != entity2:
                for pattern, relation in patterns:
                    regex = pattern.format(re.escape(entity1), re.escape(entity2))
                    match = re.search(regex, text, re.IGNORECASE)
                    if match:
                        relationships.append((entity1, relation, entity2))

    return relationships

# 📌 Adds nodes to Neo4j
def add_nodes_to_graph(graph, entities):
    for entity_type, entity_values in entities.items():
        for entity in entity_values:
            props = {prop: None for prop in NODE_TYPES[entity_type]}
            props["name"] = entity
            query = f"""
            MERGE (n:{entity_type} {{name: $name}})
            ON CREATE SET n += $props
            """
            graph.run_query(query, {"name": entity, "props": props})

# 📌 Adds relationships to Neo4j
def add_relationships_to_graph(graph, relationships):
    for entity1, rel_type, entity2 in relationships:
        query = f"""
        MATCH (a {{name: $entity1}}), (b {{name: $entity2}})
        MERGE (a)-[r:{rel_type}]->(b)
        """
        print(f"🔗 Adding relationship: ({entity1}) -[{rel_type}]-> ({entity2})")
        graph.run_query(query, {"entity1": entity1, "entity2": entity2})

# 📌 Full pipeline to process PDFs
def process_pdf(pdf_path, graph):
    print(f"📄 Processing {pdf_path}...")

    text_chunks = extract_text_from_pdf(pdf_path)
    all_entities, all_relationships = defaultdict(set), []

    for text in text_chunks:
        entities = extract_entities(text)
        relationships = extract_relationships(text, entities)

        # Consolidate entities before adding to the graph
        for entity_type, entity_set in entities.items():
            all_entities[entity_type].update(
                consolidate_entities(all_entities[entity_type], e) for e in entity_set
            )
        all_relationships.extend(relationships)

    add_nodes_to_graph(graph, all_entities)
    add_relationships_to_graph(graph, all_relationships)
    print(f"✅ Finished processing {pdf_path}.")

# Initialize Neo4j connection
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise ValueError("🚨 Missing Neo4j credentials!")

graph = GraphDB(URI, USER, PASSWORD)

# Process PDFs in directory
pdf_dir = "Frey_pdfs"
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        process_pdf(os.path.join(pdf_dir, filename), graph)

graph.close()
