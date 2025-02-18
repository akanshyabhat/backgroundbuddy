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
import json
from typing import Dict, Any, List
import spacy
from spacy.tokens import Span
from sentence_transformers import SentenceTransformer # for embedding entities (consolidation)
import uuid # for unique ids in KB
import numpy as np # for cosine similarity of embeddings

import prodigy
from prodigy.components.loaders import JSONL
from relationship_extractor import extract_relationships_block_by_block

# For sentence segmentation:
nlp = spacy.load("en_core_web_sm")
# For embeddings:
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

dotenv.load_dotenv("API.env")

'''
BACKGROUND - SETTING UP PRODIGY TO WORK WITH RELATIONSHIPS
'''

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
4. CONSOLIDATE OR CREATE NEW ENTITIES WITH KB
------------------------------------------------------------
'''

# knowledge base (in memory)
KB = {}

# similarity threshold for deciding "same entity"
SIMILARITY_THRESHOLD = 0.80  # MUST TUNE

def cosine_similarity(vec1, vec2):
    """
    Compute the cosine similarity between two embedding vectors.
    vec1, vec2 are Python lists or numpy arrays of floats.
    """
    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def match_or_create_kb_id(entity_text: str, embedding: List[float], kb: Dict[str, Any]) -> str:
    """
    1) loop over all existing entries in the KB
    2) For each entry, compare 'embedding' (entry lol) to KB embeddings 
       in that entry. We track the BEST similarity found.
    3) If the best similarity >= SIMILARITY_THRESHOLD, we unify with that entry:
       - Add this entity_text to 'aliases' if it's new (add name to alias list)
       - Append the embedding to 'embeddings' (COULD TRY AVERAGING THEM FOR SPEED)
       - Return the kb_id
    4) If no match is above threshold, create new KB entry with a new uuid
       - canonical_name = entity_text (WE NEED TO DECIDE HOW TO PICK CANONICAL NAME... can we do it automatically?)
       - aliases = [entity_text]
       - embeddings = [embedding]
       - Return the new kb_id
    """

    best_kb_id = None
    best_score = -1.0

    # 1) Compare with existing KB entries
    for kb_id, info in kb.items():
        # Each 'info' might contain multiple embeddings, so find the best similarity 
        # for the entire list of embeddings.
        existing_embeddings = info["embeddings"]
        for emb in existing_embeddings:
            sim = cosine_similarity(embedding, emb)
            if sim > best_score:
                best_score = sim
                best_kb_id = kb_id

    # 2) Decide if we unify or create new
    if best_score >= SIMILARITY_THRESHOLD:
        # unify w/ existing
        kb_entry = kb[best_kb_id]

        # if this mention isn't already an alias, add it
        if entity_text not in kb_entry["aliases"]:
            kb_entry["aliases"].append(entity_text)

        # append the new embedding
        kb_entry["embeddings"].append(embedding)

        return best_kb_id
    else:
        # create a new entry
        new_id = str(uuid.uuid4())
        kb[new_id] = {
            "canonical_name": entity_text,
            "aliases": [entity_text],
            "embeddings": [embedding]
        }
        return new_id
    
def consolidate_entities_with_kb(
    final_data: List[Dict[str, Any]], 
    kb: Dict[str, Any] = KB
) -> List[Dict[str, Any]]:
    """
    Goes through the final_data (the list of extracted entity records),
    attempts to unify each entity with the KB. 

    Steps:
      - For each entity:
        1) call match_or_create_kb_id(entity_text, embedding, kb)
        2) get the returned kb_id
        3) in final_data, add canonical_name = kb[kb_id]["canonical_name"]
        4) store final_data["kb_id"] = that kb_id

    Returns the updated final_data list.
    """

    updated_data = []
    for record in final_data:
        entity_text = record["entity_text"]
        embedding = record["embedding"]

        # 1) match or create
        kb_id = match_or_create_kb_id(entity_text, embedding, kb)

        # 2) unify name in final record
        canonical_name = kb[kb_id]["canonical_name"]
        record["canonical_name"] = canonical_name
        record["kb_id"] = kb_id

        updated_data.append(record)
    
    return updated_data


''' 
------------------------------------------------------------
5. EXTRACT RELATIONSHIPS FROM TEXT
note: right now this is being done content block by content block
------------------------------------------------------------
'''

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
                "relationship": rel["relationship"]
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



'''
# COMMENTED OUT BECAUSE IT CAUSES RATE LIMITS W GPT

def parse_archive(archive_path: str) -> List[Dict[str, Any]]:
    """
    Given a path to a JSON file containing an array of articles,
    parse each article with parse_single_article and return
    a list of structured article dicts.
    """
    with open(archive_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # data is expected to be a list of article dicts
        parsed_articles = []
        for article_dict in data:
            parsed = parse_single_article(article_dict)
            parsed_articles.append(parsed)
        return parsed_articles


if __name__ == "__main__":
    # 1) Parse the archive & limit to 5 articles
    sample_path = "BackgroundBuddy.json"  # or your input file
    articles = parse_archive(sample_path)
    articles = articles[:2]  # limit to 5 for a test run
    ''
    # 2) Create Prodigy tasks for NER in "blocks.jsonl"
    create_prodigy_tasks(articles, output_file="blocks.jsonl")
    print("\n[INFO] Next step: run Prodigy to label entities in 'blocks.jsonl'. Example:\n")
    print("   prodigy ner.manual my_entities_dataset en_core_web_sm blocks.jsonl\n")
    print("After labeling, press ENTER to continue.")
    input("Press ENTER when you're done with entity annotation in Prodigy...")
    ''
    accepted_records = []
    for article in articles:
        for block_index, block_text in enumerate(article["contentBlocks"]):
            doc = nlp(block_text)
            spans = []

            for ent in doc.ents:  # Auto-detect entities using SpaCy
                spans.append({
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "text": ent.text,
                    "label": ent.label_
                })

            if spans:  # Only store if entities were found
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

    print(f"[INFO] Auto-labeled {len(accepted_records)} text blocks with named entities.")

    # 3) Load accepted entity spans from Prodigy
    entities_dataset_name = "my_entities_dataset"
    #accepted_records = get_accepted_entities_from_prodigy(entities_dataset_name)
    if not accepted_records:
        print("No accepted entity records found. Exiting.")
        exit(0)

    # 4) Convert accepted entity spans to final records with evidence & embeddings
    final_data = piecewise_extraction_to_records(accepted_records)

    # 5) Consolidate or create KB entries
    updated_data = consolidate_entities_with_kb(final_data, KB)
    print(f"[INFO] KB now has {len(KB)} entries.\n")
    print(f"KB{KB}")

    # 6) Extract relationships (block by block) using LLM
    relationships = extract_relationships_block_by_block(updated_data, model_name="gpt-4o")

    # 7) Save these relationships to a JSONL for Prodigy verification
    save_relationships_for_prodigy(relationships, output_file="relationships.jsonl")
    print("\n[INFO] Next step: run Prodigy to verify relationships in 'relationships.jsonl'. Example:\n")
    print("   prodigy rel.manual my_relationships relationships.jsonl\n")
    print("After labeling, you can db-out the final accepted data from Prodigy.\n")

    # Done! Next, you'd run something like:
    #   prodigy db-out my_relationships > verified_relationships.jsonl
    # Then load that verified file to push to Neo4j or further steps.

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

    # ✅ Print extracted entities - use to debug!
    print("\n✅ Final Named Entities Stored in KB:")
    for record in updated_data:
        print(f"  - {record['canonical_name']} ({record['entity_label']}) -> {record['kb_id']}")

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
    articles = articles[:2]  # limited to 1 article for testing

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
