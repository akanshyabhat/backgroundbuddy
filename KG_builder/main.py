import os
import dotenv
import pdfplumber
import spacy
from neo4j import GraphDatabase
from collections import defaultdict
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

'''
Currently:
1. Use spacy to extract entities from the text
2. Pass these entities and the text to chatGPT to extract relationships
3. Parse relationships
4. Add entities and relationships to neo4j

To do:
- Chunk pdfs in case context window misses things
- Add citations for each piece of knowledge
- Can we extract relationships without LLMs?
- How can we perform entity consolidation? (have tried fuzzywuzzy)

'''

# Spacy NLP
nlp = spacy.load("en_core_web_sm")

# API key for extracting relationships (trying to find non LLM way to do tgis)
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key
llm = ChatOpenAI(model_name="gpt-4", temperature=0)


# Neo4j connection
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

# REstricting entity types and their properties
NODE_TYPES = {
    "PERSON": ["name", "birth_date", "role"],
    "ORG": ["name", "founded", "type"],
    "EVENT": ["name", "date", "location"],
    "GPE": ["name", "region", "country"],  # geopolitical
}

# Restricting relationship types and their properties
RELATIONSHIP_TYPES = {
    "WORKS_FOR": ["since"],
    "MENTIONS": ["frequency"],
    "LOCATED_IN": ["since"],
    "AFFILIATED_WITH": ["start_date", "end_date"]
}

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def extract_entities(text):
    doc = nlp(text)
    entities = defaultdict(set)
    for ent in doc.ents:
        entity_type = ent.label_  # Uses spacy's entity labels
        if entity_type in NODE_TYPES:  # Only keeps relevant entities
            entities[entity_type].add(ent.text.strip())
    return entities

# extracts relationships using structured LLM prompt (TODO - can we do this with NLP?)
def extract_relationships(entities, text):
    entity_list = ", ".join([f"{name} ({etype})" for etype, names in entities.items() for name in names])

    prompt = PromptTemplate.from_template("""
    You are building a knowledge graph for journalists.
    Given the following named entities extracted from a document:
    {entities}

    And the following text:
    {text}

    Identify and extract meaningful relationships between them.
    Return relationships in the format (relationships should be all caps with underscores):

    (Entity1 [Type1]) -[RELATIONSHIP_HERE]-> (Entity2 [Type2])

    Do not add any other text, just structured relationships.
    """)

    formatted_prompt = prompt.format(entities=entity_list, text=text)

    try:
        response = llm.invoke(formatted_prompt)
        response_text = response.content.strip()
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return []

    # Initialize relationships list
    relationships = []

    for line in response_text.split("\n"):
        line = line.strip()
        if line.startswith("(") and "->" in line:
            try:
                # Ensure proper format before splitting
                parts = line.split(" -[")
                if len(parts) != 2:
                    raise ValueError("Malformed relationship format")

                entity1_part, rel_part = parts
                relationship, entity2_part = rel_part.split("]-> ")

                # Properly extract entity names and types
                entity1_raw, entity1_type_raw = entity1_part.strip("()").rsplit(" [", 1)
                entity2_raw, entity2_type_raw = entity2_part.strip("()").rsplit(" [", 1)

                entity1 = entity1_raw.strip()
                entity2 = entity2_raw.strip()
                entity1_type = entity1_type_raw.strip("] ")  # ✅ Properly clean up extra brackets
                entity2_type = entity2_type_raw.strip("] ")  # ✅ Properly clean up extra brackets
                relationship = relationship.strip()

                # Validate entity types
                if entity1_type not in NODE_TYPES or entity2_type not in NODE_TYPES:
                    print(f"Skipping invalid entity type: {entity1_type} or {entity2_type}")
                    continue

                relationships.append((entity1_type, entity1, relationship, entity2_type, entity2))

            except Exception as e:
                print(f"Skipping malformed line: {line} - Error: {str(e)}")

    if not relationships:
        print("No relationships extracted.")
    print("Relationships: ", relationships)
    return relationships

# adds nodes to neo4j via cypher query
def add_nodes_to_graph(graph, entities):
    for entity_type, entity_values in entities.items():
        for entity in entity_values:
            '''
            props = {prop: None for prop in NODE_TYPES[entity_type]}
            query = f"MERGE (n:{entity_type} {{name: $name}}) SET n += $props"
            graph.run_query(query, {"name": entity, "props": props})
            '''

            props = {prop: None for prop in NODE_TYPES[entity_type]}
            props["name"] = entity
            query = f"""
            MERGE (n:{entity_type} {{name: $name}})
            ON CREATE SET n += $props
            ON MATCH SET n += $props
            """
            graph.run_query(query, {"name": entity, "props": props})

# adds relationships to neo4j via cypher query
def add_relationships_to_graph(graph, relationships):
    for entity1_type, entity1, rel_type, entity2_type, entity2 in relationships:
        # make sure entity types are valid
        if entity1_type not in NODE_TYPES or entity2_type not in NODE_TYPES:
            print(f"Skipping invalid entity type: {entity1_type} or {entity2_type}")
            continue

        query = f"""
        MATCH (a:{entity1_type} {{name: $entity1}}), (b:{entity2_type} {{name: $entity2}})
        MERGE (a)-[r:{rel_type}]->(b)
        """

        print(f"🔗 Adding relationship: ({entity1} [{entity1_type}]) -[{rel_type}]-> ({entity2} [{entity2_type}])")

        try:
            graph.run_query(query, {"entity1": entity1, "entity2": entity2})
        except Exception as e:
            print(f"❌ Failed to add relationship {entity1} -[{rel_type}]-> {entity2}: {str(e)}")

# full process for a single pdf (extract entities, relationships, make graph)
def process_pdf(pdf_path, graph):
    print(f"Processing {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    entities = extract_entities(text)
    relationships = extract_relationships(entities, text)

    add_nodes_to_graph(graph, entities)
    add_relationships_to_graph(graph, relationships)

# Neo4j connection
URI = os.getenv("URI")
AUTH = os.getenv("AUTH")
graph = GraphDB(URI, AUTH[0], AUTH[1])

# Process PDFs in directory
pdf_dir = "/Users/averylouis/Documents/Stanford/CS206/code/KG_builder/Frey_pdfs"
for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        process_pdf(os.path.join(pdf_dir, filename), graph)

graph.close()