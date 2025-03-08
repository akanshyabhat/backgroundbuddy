''' 
------------------------------------------------------------
5. EXTRACT RELATIONSHIPS FROM TEXT
note: right now this is being done content block by content block
------------------------------------------------------------
'''
import difflib
import json
import os
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List

# Restricting relationship types and their properties
"""RELATIONSHIP_TYPES = {
    "WORKS_FOR": ["since"],
    "LOCATED_IN": ["region", "country"],
    "AFFILIATED_WITH": ["start_date", "end_date"],
    "VETOED": ["date"],
    "PROPOSED": ["date"],
    "SUPPORTED": ["date"],
    "OPPOSED": ["date"],
    "HAS_PARTICIPANT": ["role"],
    "HAS_AFFILIATION_WITH": ["organization", "role"],
    "HAS_TYPE": ["type"],
    "IS_ACCUSED_OF": ["charge"],
    "IS_CHARGED_WITH": ["charge"],
    "IS_PAROLE_ELIGIBLE": ["date", "action"],
    "IS_PAROLE_GRANTED": ["date", "action"],
    "SENTENCED": ["charge"],
    "REFERENCED": ["person", "subject"],
    "INVOLVED_IN": ["crime", "incident"], 
    "ASSOCIATED_WITH": ["individual", "case", "incident"],
    "INFORMED": ["individual", "organization"],
}"""

RELATIONSHIP_TYPES = {
    "VETOED": ["bill", "ordinance", "policy", "resolution"],  
    "PROPOSED": ["bill", "policy", "initiative", "amendment"],  
    "SUPPORTED": ["candidate", "policy", "bill", "resolution", "initiative"],  
    "OPPOSED": ["candidate", "bill", "policy", "amendment", "initiative"]
}

def extract_relationships_for_block(block_text, block_entities, headline, date, model_name):
    """
    Extract relationships from each block of text using OpenAI's API via LangChain.
    """
    relationships = []

    # Filter the entities to exclude the 'embedding' field and keep all other fields
    filtered_entities = [
        {key: value for key, value in entity.items() if key != 'embedding'}
        for entity in block_entities
    ]
    
    llm = ChatOpenAI(model_name=model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    You are an expert in Minneapolis local political relationship extraction. Your task is to identify meaningful relationships about local politics in Minneapolis only between the provided named entities listed below.
    Given the following block of text, extract relationships only between the named entities provided.
    Both subject and object must be named entities (person, organization, location) from the provided list. Ignore non-entity terms (e.g., dates, numbers) unless tied to an action.
    Extract relationships that are meaningful and relevant to the context of the article.
    Ensure relationships are not repeated. If the same relationship exists for a subject-object pair, include it only once.
    Avoid using LOCATED_IN unless the location is significant or tied to an event. Do not use it for where a person is from.
    Use the exact entity names as listed in the provided named entities. Do not alter or shorten the entity name in any way.
    Do not extract relationships regarding author contributions (e.g., "Staff writer [name] contributed to this report").
    --- 

    Headline: "{headline}"
    Date: "{date}"
    Text Block: "{block_text}"

    Named Entities (from the text): {filtered_entities}

    The entity names can be accessed from the "canonical name" field. The entity type can be accessed from the "entity type" field.

    **Possible Relationships**: 
    {RELATIONSHIP_TYPES}


    Return the extracted relationships in this **exact format** without any additional information:

    [
        {{
            "subject_text": "<subject entity>",
            "relationship": "<relationship>",
            "object_text": "<object entity>",
            "subject_type": "<subject entity type>",
            "object_type": "<object entity type>",
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

def unify_mention_to_kb_id(
    mention_text: str,
    mention_evidence: str,
    entity_records: List[Dict[str, Any]],
    text_threshold: float = 0.8,
    evidence_threshold: float = 0.4
) -> str:
    """
    Attempt to match (mention_text, mention_evidence) from the LLM
    to a single entity in 'entity_records' by looking at:
      - The entity's 'entity_text'
      - The entity's 'evidence' snippet
    1) We compute string similarity between mention_text and entity_text
    2) We also compute an overlap/similarity measure between mention_evidence and the entity's evidence
    3) We combine or weigh these to pick the best match
    4) If best match is above some threshold, return that entity's kb_id
       Otherwise return None (or create a new entity if you want)
    """
    if not mention_text:
        return None
    # print("mention_text", mention_text)
    # print("mention_evidence", mention_evidence)
    best_kb_id = None
    best_score = 0.0
    for record in entity_records:
        # The text we got from the dataset
        ent_text = record["entity_text"]
        ent_evidence = record["evidence"]
        # print("ent_text", ent_text)
        # print("ent_evidence", ent_evidence)
        # print("ent_kb_id", record["kb_id"])

        # 1) Compare mention_text to ent_text
        text_sim = sequence_similarity(mention_text, ent_text)
        # print(mention_text, ent_text)
        # print("text_sim", text_sim)

        """# 2) Compare mention_evidence to ent_evidence
        # (We can do partial match or ratio – up to you.)
        # E.g. see how much of mention_evidence is found in ent_evidence
        overlap_ratio = overlap_coefficient(mention_evidence, ent_evidence)
        print("overlap_ratio", overlap_ratio)

        # Combine or weigh these
        # For example, we might do a simple average
        combined_score = (text_sim * 3 + overlap_ratio) / 4
        print("combined_score", combined_score)"""

        if text_sim > best_score:
            best_score = text_sim
            best_kb_id = record["kb_id"]

    # If we consider ~0.5 or 0.6 a good overall threshold, tune as needed:
    # WILL NEED IF WE OBSERVE LLM HALLUCINATING
    """if best_score >= 0.5:
        return best_kb_id
    else:
        print(best_score)
        return None"""
    return best_kb_id


def sequence_similarity(a: str, b: str) -> float:
    """
    Simple ratio from difflib. Values in [0..1].
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def overlap_coefficient(text_a: str, text_b: str) -> float:
    """
    A simple measure of overlap between two strings:
    length_of_intersection / min(len(a), len(b))
    We'll just do naive token sets.

    If there's no overlap, returns 0. 
    If one string is completely contained in the other, returns 1.
    """
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    overlap = len(intersection)
    denom = min(len(tokens_a), len(tokens_b))
    return overlap / denom if denom else 0.0


    
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
        for record in entity_records:
            print("--------------------------------")
            print("This is the entity records in extract_relationships_block_by_block:")
            print("entity_text", record["entity_text"])
            print("entity_type", record["entity_type"])
            print("kb_id", record["kb_id"])
            print("evidence", record["evidence"])
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
            sub_type = rel.get("subject_type", "").strip()
            obj_type = rel.get("object_type", "").strip()
            rel_evidence = rel.get("evidence", "").strip()  # from LLM

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
                #"properties": rel.get("properties", {}),
                "object_type": obj_type,
                "subject_type": sub_type,
                "evidence": rel_evidence
            }
            all_relationships.append(rel_record)
            print("--------------------------------")
            print(f"[INFO] Extracted {len(all_relationships)} relationships.")

    return all_relationships