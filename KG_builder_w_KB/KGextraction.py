'''
Knowledge Graph Extraction Script

1. Takes archive info and extracts text from them
----- FOR EACH ARTICLE CHUNK -----
2. Passes text to SpaCy to extract named entities
3. Computes embeddings for each mention of each entity
4. Compares embedding to KB to find matches and consolidate or create new entities (uuid)
5. Passes named entities (and uuid) and text to LLM to discover relationships
----- END OF ARTICLE CHUNK -----
6. Human-in-the-loop to verify relationships using prodigy
7. NOT DONE Passes verified relationships to Neo4j to update a knowledge graph (include evidence and citation)


pip install openai python-dotenv spacy sentence-transformers prodigy neo4j numpy langchain langchain-openai
'''

import dotenv
import os
import json
from typing import Dict, Any, List, Optional, Set
import spacy
from spacy.tokens import Span
from sentence_transformers import SentenceTransformer # for embedding entities (consolidation)
import numpy as np # for cosine similarity of embeddings
from langchain_openai import ChatOpenAI
from collections import defaultdict
from consolidate_entities import consolidate_entities_with_kb
from relationship_extractor import extract_relationships_block_by_block
from entity_training import extract_entities_from_archive
from entity_training import load_trained_model
import re
from bs4 import BeautifulSoup



from relationship_validator import save_relationships_for_prodigy

import os

# For sentence segmentation:
nlp = spacy.load("en_core_web_sm")
# For embeddings:
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

dotenv.load_dotenv("API.env")

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

openai_api_key = os.getenv("OPENAI_API_KEY")
VALID_ENTITY_TYPES = ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "LAW", "NORP", "FAC"]


def is_valid_entity(text: str) -> bool:
    """Check if an entity text is valid"""
    # Skip if text contains invalid characters or patterns
    invalid_patterns = [
        '/',  # URLs or file paths
        '>',  # HTML tags
        '<',  # HTML tags
        'css_',  # CSS classes
        'px',  # CSS units
        '.com',  # URLs
        'http',  # URLs
        '"',  # Quotes from HTML
        '-3rd-',  # Malformed text
        '="',  # HTML attributes
        '_',   # Underscores from markup
        ']',  # Markdown/markup
        '[',  # Markdown/markup
    ]
    
    # Check for invalid patterns
    if any(pattern in text for pattern in invalid_patterns):
        return False
        
    # Check if it's mostly alphanumeric (allow spaces and some punctuation)
    valid_chars = re.match(r'^[\w\s\'-,.]+$', text)
    if not valid_chars:
        return False
        
    # Ensure it's not just numbers or special characters
    if re.match(r'^[\d\W]+$', text):
        return False
    
    return True

def clean_text(text: str) -> str:
    """Clean text by removing HTML tags, URLs, and other markup"""
    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove HTML/CSS artifacts
    text = re.sub(r'css_[a-zA-Z_]+="[^"]*"', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove file paths and similar patterns
    text = re.sub(r'\S+/\S+', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

''' 
------------------------------------------------------------
1. EXTRACT RELEVANT TEXT FROM ARTICLES
------------------------------------------------------------
'''

def parse_single_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given one article dict (with keys like _id, headline, jsonBody, displayDate),
    return a structured dictionary with:
      - id
      - date
      - headline
      - contentBlocks (list of strings)
    """
    # Extract basic fields
    article_id = article.get("_id", None)
    headline = article.get("headline", "")
    
    display_date = article.get("displayDate") or {}   # If None, default to {}
    date_obj = display_date.get("$date", None)
    
    # Extract each block of text from jsonBody
    json_body = article.get("jsonBody", [])
    content_blocks = []
    for block in json_body:
        text = block.get("content", "")
        if text:  # only append if there's actual text
            content_blocks.append(text)
    

    return {
        "id": article_id,
        "date": date_obj,
        "headline": headline,
        "contentBlocks": content_blocks
    }

''' 
------------------------------------------------------------
2. EXTRACT NAMED ENTITIES FROM TEXT
------------------------------------------------------------
'''

def create_prodigy_tasks(articles: List[Dict[str, Any]], output_file: str = "blocks.jsonl"):
    """
    for each content block in each article, create a prodigy task with:
      - text = that block
      - meta = {article_id, date, headline, block_index}
    tasks can then be labeled with Prodigy (ner.manual or ner.correct).
    """
    tasks = []
    for article in articles:
        article_id = article["id"]
        headline = article["headline"]
        date_str = article["date"]
        blocks = article["contentBlocks"]

        for i, block_text in enumerate(blocks):
            # store metadata so can link it back later
            task = {
                "text": block_text,
                "meta": {
                    "article_id": article_id,
                    "headline": headline,
                    "date": date_str,
                    "block_index": i
                }
            }
            tasks.append(task)

    # Write to JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")

    print(f"Created {len(tasks)} Prodigy tasks in {output_file}.\n")
    print("can now run:")
    print(f"  prodigy ner.manual my_dataset en_core_web_sm {output_file}")


# Now after labeling we can get the accepted entities only (human-in-the-loop)
from prodigy.components.db import connect

def get_accepted_entities_from_prodigy(dataset_name: str):
    """
    Load accepted entity spans from Prodigy's dataset.
    Returns a list of records, each including:
      - text (the block)
      - meta (article_id, date, etc.)
      - spans (the accepted entity annotations)
    """
    db = connect()  # Connect to the Prodigy database
    examples = db.get_dataset(dataset_name)  # Fetch dataset
    
    accepted_records = []
    for eg in examples:
        if eg.get("answer") == "accept":  # Only process accepted annotations
            spans = eg.get("spans", [])
            if spans:
                accepted_records.append({
                    "text": eg["text"],
                    "meta": eg["meta"],
                    "spans": spans
                })
    return accepted_records

''' 
------------------------------------------------------------
3. FIND EVIDENCE AND EMBED TEXT
------------------------------------------------------------
'''

def get_sentence_for_span(text: str, start: int, end: int) -> str:
    """
    Given a text block, plus the start/end char indices for an entity,
    find the sentence containing that span. Relies on spaCy's sentence segmentation.
    """
    doc = nlp(text)
    for sent in doc.sents:
        if sent.start_char <= start and sent.end_char >= end:
            return sent.text
    # fallback if we don't find a matching sentence
    return text  # or return ""

def embed_sentence(sentence: str) -> List[float]:
    return embedder.encode(sentence).tolist()

def piecewise_extraction_to_records(accepted_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each accepted record (block text + spans), produce this final structure for each entity:
      {
        "article_id": ...
        "headline": ...
        "date": ...
        "entity_label": ... # e.g. "PERSON"
        "entity_text": ... # e.g. "Bertrand Russell"
        "evidence": <the sentence containing that entity>,
        "embedding": [...float...]
        "block_text": ... # the original block text (just for context in relationship extraction)
      }
    """
    final_data = []
    for rec in accepted_records:
        block_text = rec["text"]
        meta = rec["meta"]  # has article_id, date, headline, block_index
        spans = rec["spans"]

        article_id = meta.get("article_id")
        headline = meta.get("headline", "")
        date_str = meta.get("date", "")

        for span in spans:
            start = span["start"]
            end = span["end"]
            entity_text = block_text[start:end]
            entity_type = span["entity_type"]
            # find the sentence in which this entity occurs
            evidence_sentence = get_sentence_for_span(block_text, start, end)

            # compute embedding
            embedding_vec = embed_sentence(evidence_sentence)

            record = {
                "article_id": article_id,
                "headline": headline,
                "date": date_str,
                "entity_type": entity_type,
                "entity_text": entity_text,
                "evidence": evidence_sentence,
                "embedding": embedding_vec, #embedding_vec
                "block_text": block_text
            }
            final_data.append(record)

    return final_data

''' 
------------------------------------------------------------
5. EXTRACT RELATIONSHIPS FROM TEXT
note: right now this is being done content block by content block
------------------------------------------------------------
'''

import time


def process_article(article: Dict[str, Any], model_name: str) -> List[Dict[str, Any]]:
    """
    Process a single article:
      1. Run entity extraction on each block.
      2. Compute evidence sentences and embeddings.
      3. Consolidate entities with KB.
      4. Extract relationships using the LLM.
         (Wait 10 seconds after each API call to avoid rate limits.)
    Returns the relationships extracted for this article.
    """
    article_relationships = []
    accepted_records = []
    
    # Process each text block in the article
    for block_index, block_text in enumerate(article["contentBlocks"]):
        # Clean the text before processing
        cleaned_text = clean_text(block_text)
        
        # use trained model to extract entities
        trained_model = "trained-models"
        use_trained_model = load_trained_model(trained_model)
        doc = use_trained_model(cleaned_text)
        spans = []
        
        # Only accept valid entities
        for ent in doc.ents:
            if (ent.label_ in VALID_ENTITY_TYPES and 
                is_valid_entity(ent.text)):
                
                spans.append({
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "text": ent.text,
                    "entity_type": ent.label_,
                })
                print(f"Accepted entity: {ent.text} ({ent.label_})")
            else:
                print(f"Rejected entity: {ent.text} ({ent.label_})")
        
        if spans:  # Only keep blocks with found entities
            accepted_records.append({
                "text": cleaned_text,
                "meta": {
                    "article_id": article["id"],
                    "headline": article["headline"],
                    "date": article["date"],
                    "block_index": block_index,
                                            
                },
                "spans": spans
            })

    if not accepted_records:
        print(f"[INFO] No entities found for article {article['id']}.")
        return article_relationships
    print("accepted_records", accepted_records)
    # Create final records with evidence and embeddings for each entity mention
    final_data = piecewise_extraction_to_records(accepted_records)
    print("After piecewise_extraction_to_records")
    for entity in KB:
        print("canonical_name", KB[entity]["canonical_name"])
        print("aliases", KB[entity]["aliases"])

    # Consolidate entities with the KB (updates KB in place)
    updated_data = consolidate_entities_with_kb(final_data, KB)
    print("After consolidate_entities_with_kb")
    for entity in KB:
        print("canonical_name", KB[entity]["canonical_name"])
        print("aliases", KB[entity]["aliases"])

    # Group records by block_text for relationship extraction
    # (Assuming extract_relationships_block_by_block groups internally)
    relationships = extract_relationships_block_by_block(updated_data, model_name=model_name)

    
    # Add article-level metadata if needed
    for rel in relationships:
        rel["article_id"] = article["id"]
        rel["headline"] = article["headline"]
        rel["date"] = article["date"]
    article_relationships.extend(relationships)
    
    # Wait 10 seconds after the API call (or after processing this article)
    print(f"[INFO] Finished processing article {article['id']}. Waiting 10 seconds before next article...")
    time.sleep(10)
    
    return article_relationships


def parse_archive(archive_path: str) -> List[Dict[str, Any]]:
    """
    Given a path to a JSON file containing an array of articles,
    parse each article with parse_single_article and return a list
    of structured article dicts.
    """
    with open(archive_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    parsed_articles = [parse_single_article(article) for article in data]
    return parsed_articles

if __name__ == "__main__":
    # parse the archive & optionally limit to a few articles for testing
    sample_path = "filtered_articles.json" 
    articles = parse_archive(sample_path)
    articles = articles[21:22]  # limited to 2 articles for testing

    all_relationships = []
    model_name = "o3-mini" 
    # knowledge base (in memory)
    KB = {}  # uuid -> {canonical_name, aliases, embeddings}

    # process each article individually
    for article in articles:
        print(f"[INFO] Processing article: {article['id']}")
        article_rels = process_article(article, model_name=model_name)
        print("AFTER")
        for entity_id, entity_data in KB.items():
            print(f"ID: {entity_id}")
            print(f"Canonical Name: {entity_data['canonical_name']}")
            print(f"Aliases: {entity_data['aliases']}")
            print("-" * 40)  # Separator for clarity
        all_relationships.extend(article_rels)
         #save the KB to a json file
        with open("KB.json", "w", encoding="utf-8") as f:
            json.dump(KB, f, indent=4)

    # save the relationships to a JSONL file for verification in prodigy
    save_relationships_for_prodigy(all_relationships, output_file="relationships.jsonl") # prints instructions for Prodigy

    
    