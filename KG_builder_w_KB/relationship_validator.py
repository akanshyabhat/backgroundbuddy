'''
Takes extracted relationships from the relationship_extractor.py file
and validates them using prodigy's interface.
1) Sets up prodigy to work with our relationships data
    -> Creates a custom recipe for validating relationships
    -> Adds tokens and token indices to each task
2) Creates a Prodigy JSONL to verify these relationships
    -> Each record has text = the 'evidence' (or block_text) plus meta fields for subject/object

'''

import prodigy
from typing import Dict, Any, List, Optional, Set
import json
from prodigy.components.loaders import JSONL
from config import RELATIONSHIP_TYPES
import spacy

nlp = spacy.load("en_core_web_sm")


''' 
------------------------------------------------------------
1. SET UP PRODIGY
------------------------------------------------------------
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

@prodigy.recipe("relationship-recipe")
def my_rel_manual(dataset, source, label: str = ""):
    """
    Custom recipe for testing relation tasks from a JSONL file.
    It adds token information to each task so the relations view can render properly.
    Run it with:
        prodigy -F relationship_validator.py relationship-recipe my_test_dataset relationships.jsonl
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
2. FORMAT RELATIONSHIPS FOR PRODIGY
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
    print("You can verify them in Prodigy, e.g.:\n")
    print(f"prodigy -F relationship_validator.py relationship-recipe validated_relationships {output_file}")
    print("You can access the validated relationships in the database:\n")
    print("prodigy db-out validated_relationships > validated_relationships.jsonl")