import os
import dotenv
import pdfplumber
import spacy
import torch
from neo4j import GraphDatabase
from collections import defaultdict
from langchain_openai import ChatOpenAI  # ✅ Updated LangChain Import
from sentence_transformers import SentenceTransformer, util
import textwrap

# ✅ Fix Hugging Face tokenizers parallelism issue
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ✅ Load environment variables
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("🚨 Missing OpenAI API Key! Set it in .env or environment variables.")

os.environ["OPENAI_API_KEY"] = api_key
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, api_key=api_key)

# ✅ Load NLP Model (Use Prodigy-trained model if available)
PRODIGY_MODEL_PATH = "./ner_model"
if os.path.exists(PRODIGY_MODEL_PATH):
    print("✅ Loading Prodigy-trained NER model...")
    nlp = spacy.load(PRODIGY_MODEL_PATH)
else:
    print("⚠️ Prodigy model not found. Using default spaCy model...")
    nlp = spacy.load("en_core_web_sm")

# ✅ Load Sentence Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Neo4j Connection
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

# ✅ Entity & Relationship Definitions
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
    "AFFILIATED_WITH": ["start_date", "end_date"]
}

# ✅ 1️⃣ Extract Text & Chunk PDFs
def extract_text_from_pdf(pdf_path, chunk_size=1000):
    """Extract text from PDFs and chunk it to fit LLM context windows."""
    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    return textwrap.wrap(text, chunk_size)

# ✅ 2️⃣ Extract Entities Using NLP or Prodigy Model
def extract_entities(text):
    """Extracts named entities from text using NLP."""
    doc = nlp(text)
    entities = defaultdict(set)

    for ent in doc.ents:
        entity_type = ent.label_
        if entity_type in NODE_TYPES:
            entities[entity_type].add(ent.text.strip())

    return entities

# ✅ 3️⃣ Extract Relationships Using Embeddings/NLP
def extract_relationships_using_embeddings(text, entities):
    """Extracts relationships between entities using sentence embeddings and NLP."""
    sentences = text.split(". ")
    sentence_embeddings = embedding_model.encode(sentences, convert_to_tensor=True)

    entity_list = [e for entity_type in entities for e in entities[entity_type]]
    entity_embeddings = embedding_model.encode(entity_list, convert_to_tensor=True)

    relationships = []
    
    similarity_matrix = util.pytorch_cos_sim(entity_embeddings, sentence_embeddings)

    for i, entity in enumerate(entity_list):
        for j, sentence in enumerate(sentences):
            if similarity_matrix[i][j] > 0.7:
                relationships.append((entity, "RELATED_TO", sentence))

    return relationships

# ✅ 4️⃣ Optional LLM Enhancement
def extract_relationships_with_llm(entities, text):
    """Extracts relationships using GPT-4 (Optional)."""
    entity_list = ", ".join([f"{name} ({etype})" for etype, names in entities.items() for name in names])

    prompt = f"""
    Given the named entities:
    {entity_list}

    And the article text:
    {text}

    Identify structured relationships in this format:
    (Entity1 [Type1]) -[RELATIONSHIP_HERE]-> (Entity2 [Type2])
    """
    
    try:
        response = llm.invoke(prompt)
        return parse_llm_relationships(response.content.strip())
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return []

# ✅ 5️⃣ Parse LLM Relationships
def parse_llm_relationships(response_text):
    """Parses LLM output to extract structured relationships."""
    relationships = []
    pattern = r"\((.*?)\) -\[(.*?)\]-> \((.*?)\)"

    for line in response_text.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            entity1, relationship, entity2 = match.groups()
            relationships.append((entity1, relationship, entity2))

    return relationships

# ✅ 6️⃣ Fix Neo4j Insertion - Add Nodes
def add_nodes_to_graph(graph, entities):
    """Inserts extracted entities into Neo4j."""
    for entity_type, entity_values in entities.items():
        for entity in entity_values:
            query = f"""
            MERGE (n:{entity_type} {{name: $name}})
            ON CREATE SET n.source = 'extracted'
            """
            try:
                graph.run_query(query, {"name": entity})
            except Exception as e:
                print(f"❌ Failed to insert node {entity}: {str(e)}")

# ✅ 7️⃣ Fix Neo4j Insertion - Add Relationships
def add_relationships_to_graph(graph, relationships):
    """Inserts extracted relationships into Neo4j."""
    for entity1, relation, entity2 in relationships:
        query = f"""
        MATCH (a {{name: $entity1}}), (b {{name: $entity2}})
        MERGE (a)-[:`{relation}`]->(b)
        """
        try:
            graph.run_query(query, {"entity1": entity1, "entity2": entity2})
        except Exception as e:
            print(f"❌ Failed to insert relationship: {entity1} -[{relation}]-> {entity2}: {str(e)}")

# ✅ 8️⃣ Process Each PDF
def process_pdf(pdf_path, graph):
    print(f"📄 Processing {pdf_path}...")

    text_chunks = extract_text_from_pdf(pdf_path)
    all_entities = defaultdict(set)
    all_relationships = []

    for chunk in text_chunks:
        entities = extract_entities(chunk)
        relationships = extract_relationships_using_embeddings(chunk, entities)
        llm_relationships = extract_relationships_with_llm(entities, chunk)

        for key, value in entities.items():
            all_entities[key].update(value)
        
        all_relationships.extend(relationships)
        all_relationships.extend(llm_relationships)

    add_nodes_to_graph(graph, all_entities)  # ✅ Function restored
    add_relationships_to_graph(graph, all_relationships)

    print(f"✅ Finished processing {pdf_path}.")

# ✅ 9️⃣ Run on Multiple PDFs
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
graph = GraphDB(URI, USER, PASSWORD)

pdf_dir = "Frey_pdfs"
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        process_pdf(os.path.join(pdf_dir, filename), graph)

graph.close()
