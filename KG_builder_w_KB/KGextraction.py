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

import os
import dotenv
import json
from typing import Dict, Any, List, Optional, Set
import spacy
from spacy.tokens import Span
from sentence_transformers import SentenceTransformer # for embedding entities (consolidation)
import uuid # for unique ids in KB
import numpy as np # for cosine similarity of embeddings
from langchain_openai import ChatOpenAI
from collections import defaultdict
from consolidate_entities import consolidate_entities_with_kb


import prodigy
from prodigy.components.loaders import JSONL
from entity_matcher import unify_mention_to_kb_id  # Import the function

# For sentence segmentation:
nlp = spacy.load("en_core_web_sm")
# For embeddings:
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

dotenv.load_dotenv("API.env")

'''
BACKGROUND - SETTING UP PRODIGY TO WORK WITH RELATIONSHIPS
'''
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
    "HAS_TYPE": ["type"],
    "IS_ACCUSED_OF": ["charge"],
    "IS_CHARGED_WITH": ["charge"],
    "IS_PAROLE_ELIGIBLE": ["date"],
    "IS_PAROLE_GRANTED": ["date"],
}

def add_tokens(task):
    """
    Use spaCy to compute tokens for the task text and update spans with token indices.
    """
    doc = nlp(task["text"])
    # Create a list of tokens with an id and their character offsets.
    tokens = [
        {"id": i, "text": token.text, "start": token.idx, "end": token.idx + len(token.text)}
        for i, token in enumerate(doc)
    ]
    task["tokens"] = tokens

    # Update each span with token_start and token_end computed from tokens.
    for span in task.get("spans", []):
        token_start = None
        token_end = None
        # Find the token index where the span starts.
        for i, token in enumerate(tokens):
            if token["start"] <= span["start"] < token["end"]:
                token_start = i
            if token["start"] < span["end"] <= token["end"]:
                token_end = i + 1  # token_end is exclusive
        span["token_start"] = token_start
        span["token_end"] = token_end
    return task

@prodigy.recipe("test-jsonl")
def my_rel_manual(dataset, source, label: str = ""):
    """
    Custom recipe for testing relation tasks from a JSONL file.
    It adds token information to each task so the relations view can render properly.
    Run it with:
        prodigy -F KG_extraction.py test-jsonl my_test_dataset relationships.jsonl
    """
    stream = JSONL(source)
    
    # if no label string is provided, use the keys of RELATIONSHIP_TYPES
    if not label:
        labels = list(RELATIONSHIP_TYPES.keys())
    else:
        labels = [l.strip() for l in label.split(",")]

    config = {
        "wrap_relations": True,
        "relations_span_labels": ["SUBJECT", "OBJECT"],
        "labels": labels
    }

    # add tokens and token indices to each task.
    transformed_stream = (add_tokens(task) for task in stream)

    return {
        "dataset": dataset,
        "view_id": "relations",  # built-in relations view.
        "stream": transformed_stream,
        "config": config
    }


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
            entity_label = span["label"]

            # find the sentence in which this entity occurs
            evidence_sentence = get_sentence_for_span(block_text, start, end)

            # compute embedding
            embedding_vec = embed_sentence(evidence_sentence)

            record = {
                "article_id": article_id,
                "headline": headline,
                "date": date_str,
                "entity_label": entity_label,
                "entity_text": entity_text,
                "evidence": evidence_sentence,
                "embedding": embedding_vec,
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


def extract_relationships_for_block(block_text, block_entities, headline, date, model_name):
    """
    Extract relationships from each block of text using OpenAI's API via LangChain.
    """
    relationships = []
    
    llm = ChatOpenAI(model_name=model_name, temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

    
    prompt = f"""
    Given the following block of text, identify relationships between the named entities.

    ---

    Headline: "{headline}"
    Date: "{date}"
    Text Block: "{block_text}"

    Named Entities (from the text): {block_entities}

    ---

    Possible relationships: 
    {RELATIONSHIP_TYPES}

    Return structured JSON in this exact format:

    [
        {{
            "subject_text": "<subject entity>",
            "relationship": "<relationship>",
            "object_text": "<object entity>",
            "confidence": <confidence score (0.0-1.0)>,
            "evidence": "<sentence containing the relationship>"
        }},
        ...
    ]
    """

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        print("[DEBUG] LLM Response:\n", content)

        if content.startswith("```"):
            # Remove the first line (e.g., "```json") and the last line ("```")
            content = "\n".join(content.splitlines()[1:-1]).strip()

        rel = json.loads(content)  # Convert JSON string to Python list
        relationships.extend(rel)

    except json.JSONDecodeError:
        print("[ERROR] LLM returned invalid JSON:", content)
    except Exception as e:
        print(f"[ERROR] OpenAI API Error: {e}")

    print(f"[INFO] Extracted {len(relationships)} relationships.")
    return relationships

### THIS PART IS SHIT RIGHT NOW>>> SO OVERCOMPLICATED NEED TO SIMPLIFY
def extract_relationships_block_by_block(
    consolidated_data: List[Dict[str, Any]],
    model_name
) -> List[Dict[str, Any]]:
    from collections import defaultdict

    # Group the consolidated data by block_text
    block_map = defaultdict(list)
    for rec in consolidated_data:
        block_map[rec["block_text"]].append(rec)

    all_relationships = []

    # For each block
    for block_text, entity_records in block_map.items():
        if not entity_records:
            continue

        article_id = entity_records[0]["article_id"]
        headline = entity_records[0]["headline"]
        date_str = entity_records[0]["date"]

        # 1) Let the LLM detect relationships from the entire block
        block_relationships = extract_relationships_for_block(
            block_text=block_text,
            block_entities=entity_records,
            headline=headline,
            date=date_str,
            model_name=model_name
        )

        if not block_relationships:
            continue

        # 2) Unify LLM mentions with known kb_ids using mention_text + evidence
        for rel in block_relationships:
            sub_text = rel.get("subject_text", "").strip()
            obj_text = rel.get("object_text", "").strip()
            rel_evidence = rel.get("evidence", "").strip()  # from LLM

            # Use the unify_mention_to_kb_id function
            subject_kb_id = unify_mention_to_kb_id(sub_text, rel_evidence, entity_records)
            object_kb_id = unify_mention_to_kb_id(obj_text, rel_evidence, entity_records)

            # Build final record
            rel_record = {
                "article_id": article_id,
                "headline": headline,
                "date": date_str,
                "block_text": block_text,
                "subject_text": sub_text,
                "subject_kb_id": subject_kb_id,
                "object_text": obj_text,
                "object_kb_id": object_kb_id,
                "relationship": rel.get("relationship", ""),
                "confidence": rel.get("confidence", 0.0),
                "evidence": rel_evidence
            }
            all_relationships.append(rel_record)
            print(f"[INFO] Extracted {len(all_relationships)} relationships.")

    return all_relationships

def save_relationships_for_prodigy(relationships: List[Dict[str, Any]], output_file="relationships.jsonl"):
    """
    Create a Prodigy JSONL to verify these relationships. 
    Each record has text = the 'evidence' (or block_text) plus meta fields for subject/object.
    """
    data = []
    for rel in relationships:
        # We'll pick the 'evidence' if not empty, else the block_text
        text = rel["evidence"] if rel["evidence"] else rel["block_text"]
        # Try to highlight subject/object if they appear in text:
        spans = []
        sub_idx = text.lower().find(rel["subject_text"].lower())
        if sub_idx >= 0:
            spans.append({
                "start": sub_idx,
                "end": sub_idx + len(rel["subject_text"]),
                "label": "SUBJECT"
            })
        obj_idx = text.lower().find(rel["object_text"].lower())
        if obj_idx >= 0:
            spans.append({
                "start": obj_idx,
                "end": obj_idx + len(rel["object_text"]),
                "label": "OBJECT"
            })
        
        record = {
            "text": text,
            "spans": spans,
            "meta": {
                "article_id": rel["article_id"],
                "headline": rel["headline"],
                "date": rel["date"],
                "subject_kb_id": rel["subject_kb_id"],
                "object_kb_id": rel["object_kb_id"],
                "relationship": rel["relationship"],
                "confidence": rel["confidence"]
            }
        }
        data.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        for d in data:
            f.write(json.dumps(d) + "\n")

    print(f"Saved {len(data)} relationships to {output_file}.")
    print("You can verify them in Prodigy, e.g.:")
    print(f"prodigy rel.manual my_relationships {output_file}")

def main_relationship_extraction_pipeline(final_data, model_name):
    """
    final_data: the list of consolidated entity records from step 4 (with kb_id, canonical_name, etc.)
    """
    # 1) Extract relationships block by block
    relationships = extract_relationships_block_by_block(final_data, model_name)

    # 2) Save them for Prodigy verification
    save_relationships_for_prodigy(relationships, output_file="relationships.jsonl")

    print("Now run your Prodigy recipe to validate these relationships:")
    print("prodigy rel.manual my_relationships relationships.jsonl")

    return relationships

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
        doc = nlp(block_text)
        spans = []
        for ent in doc.ents:
            spans.append({
                "start": ent.start_char,
                "end": ent.end_char,
                "text": ent.text,
                "label": ent.label_
            })
        if spans:  # Only keep blocks with found entities
            accepted_records.append({
                "text": block_text,
                "meta": {
                    "article_id": article["id"],
                    "headline": article["headline"],
                    "date": article["date"],
                    "block_index": block_index
                },
                "spans": spans
            })
    
    if not accepted_records:
        print(f"[INFO] No entities found for article {article['id']}.")
        return article_relationships

    # Create final records with evidence and embeddings for each entity mention
    final_data = piecewise_extraction_to_records(accepted_records)
    # Consolidate entities with the KB (updates KB in place)
    updated_data = consolidate_entities_with_kb(final_data, KB)

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
    sample_path = "BackgroundBuddy.json" 
    articles = parse_archive(sample_path)
    articles = articles[:1]  # limited to 1 article for testing

    all_relationships = []
    model_name = "gpt-4o" 

    # process each article individually
    for article in articles:
        print(f"[INFO] Processing article: {article['id']}")
        article_rels = process_article(article, model_name=model_name)
        all_relationships.extend(article_rels)

    # save the relationships to a JSONL file for verification in prodigy
    save_relationships_for_prodigy(all_relationships, output_file="relationships.jsonl")
    print("\n[INFO] All articles processed. Next step: verify relationships in 'relationships.jsonl' with Prodigy.")
    print("\n[INFO] Run this command to verify relationships:")
    print("prodigy -F KGextraction.py test-jsonl my_test_dataset relationships.jsonl")
