'''
Entity extraction ANNOTATION using prodigy
1. Extract entities from 10 random text blocks
2. Send extracted entities to prodigy for validation & retraining

pip install prodigy
'''

import prodigy
from signal import SIGKILL
import os
from prodigy.components.loaders import JSONL
from config import ENTITY_TYPES, RELATIONSHIP_TYPES
from typing import Dict, Any, List
import json
import random
import spacy
import subprocess
import freeport

TRAINING_SIZE = 10 # number of article paragraphs to use for training
TRAINING_EPOCHS = 20 # number of epochs to train the model
def parse_single_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given one article dict (with keys _id, headline, jsonBody, displayDate),
    return a structured dictionary with:
      - id
      - date
      - headline
      - contentBlocks (list of strings)
    """
    # extract basic fields
    article_id = article.get("_id", None)
    headline = article.get("headline", "")
    
    display_date = article.get("displayDate") or {}  
    date_obj = display_date.get("$date", None)
    
    # Extract each block of text
    json_body = article.get("jsonBody", [])
    content_blocks = []
    for block in json_body:
        text = block.get("content", "")
        if text:  # only append if there is actually some text
            content_blocks.append(text)
    

    return {
        "id": article_id,
        "date": date_obj,
        "headline": headline,
        "contentBlocks": content_blocks
    }

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
  

def extract_for_annotation(articles: List[Dict[str, Any]], output_file: str = "initial_entity_validation_group.jsonl"):
    """
    Extract entities from a # of random text blocks in the archive and save them to a JSONL file.
    """
    tasks = []

    # Randomly select a number fo articles for training purposes
    num_articles = min(TRAINING_SIZE, len(articles))
    selected_articles = random.sample(articles, num_articles)
    
    for article in selected_articles:
        article_id = article["id"]
        headline = article["headline"]
        date_str = article["date"]
        block = article["contentBlocks"][0] if article["contentBlocks"] else ""

        # store metadata so can link it back later
        task = {
            "text": block,
            "meta": {
                "article_id": article_id,
                "headline": headline,
                "date": date_str,
            }           
        }
        tasks.append(task)

    # Write to JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")
    
    labels = ",".join(ENTITY_TYPES)

    print(f"Created {len(tasks)} Prodigy tasks in {output_file}.\n")
    print("Press ^C to continue once you're done annotating...\n")
    
    command = [
        "prodigy", "ner.correct", "my_dataset", "en_core_web_sm", output_file,
        "--label", labels
    ]
    subprocess.run(command, check=True)

def main():
    sample_path = "BackgroundBuddy.json"
    articles = parse_archive(sample_path)
    
    print("Starting the annotation process via Prodigy ...")
    extract_for_annotation(articles)

if __name__ == "__main__":
    main()
