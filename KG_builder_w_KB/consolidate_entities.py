from typing import List, Dict, Any
import uuid
import numpy as np
import difflib

''' 
------------------------------------------------------------
4. CONSOLIDATE OR CREATE NEW ENTITIES WITH KB
------------------------------------------------------------
'''

# Similarity threshold for deciding "same entity"
SIMILARITY_THRESHOLD = 0.8  # Adjusted threshold for more precise matching

# Titles and suffixes to remove
TITLES_TO_REMOVE = ["mr.", "mrs.", "ms.", "dr.", "prof.", "hon.", "sir", "dame", "mx.", "mayor", "councilmember", "councilperson", "president", "governor", "senator", "representative", "judge", "attorney", "lawyer", "doctor", "professor", "prime minister"]
SUFFIXES_TO_REMOVE = ["jr.", "sr.", "ii", "iii", "iv", "v"]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def clean_canonical_name(name: str) -> str:
    """Cleans the canonical name by removing titles and converting to lowercase."""
    name_parts = name.strip().lower().split()
    filtered_parts = [part for part in name_parts if part not in TITLES_TO_REMOVE]
    
    if len(filtered_parts) >= 2:
        first_name, last_name = filtered_parts[0], filtered_parts[-1]
        if last_name in SUFFIXES_TO_REMOVE and len(filtered_parts) > 2:
            return f"{first_name} {filtered_parts[-2]} {last_name}"
        return f"{first_name} {last_name}"
    return " ".join(filtered_parts)

def create_new_kb_entry(entity_text: str, embedding: List[float], kb: Dict[str, Any]) -> str:
    """Helper function to create a new KB entry with a cleaned canonical name."""
    canonical_name = clean_canonical_name(entity_text)
    new_id = str(uuid.uuid4())
    kb[new_id] = {
        "canonical_name": canonical_name,
        "aliases": [canonical_name],  # Store in lowercase
        "embeddings": [embedding]
    }
    return new_id

def find_best_match(entity_text: str, embedding: List[float], kb: Dict[str, Any]) -> tuple[str or None, float]:
    entity_text_lower = entity_text.lower()  # Normalize to lowercase
    best_match_id = None
    best_score = -1.0

    for kb_id, info in kb.items():
        # Compare canonical names and aliases in lowercase
        existing_canonical_name = info["canonical_name"].lower()
        if entity_text_lower == existing_canonical_name or existing_canonical_name in entity_text_lower or entity_text_lower in existing_canonical_name:
            return kb_id, 1.0  # Direct match
        for alias in info["aliases"]:
            if entity_text_lower == alias or alias in entity_text_lower or entity_text_lower in alias:
                return kb_id, 1.0  # Direct match
        
        # Compare with all embeddings for this entity
        for existing_emb in info["embeddings"]:
            # sim = cosine_similarity(embedding, existing_emb)
            sim = difflib.SequenceMatcher(None, entity_text.lower(), existing_canonical_name.lower()).ratio()
            if sim > best_score:
                best_score = sim
                best_match_id = kb_id

    return best_match_id, best_score

def consolidate_entities_with_kb(final_data: List[Dict[str, Any]], kb: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Consolidate similar entities and update the knowledge base."""
    updated_data = []
    
    for record in final_data:
        entity_text = record["entity_text"].lower()  # Normalize to lowercase
        embedding = record["embedding"]
        # print("entity_text", entity_text)
        
        # Find best matching entity in KB
        best_match_id, similarity = find_best_match(entity_text, embedding, kb)
        # print("best_match_id, similarity", best_match_id, similarity)

        
        if similarity >= SIMILARITY_THRESHOLD and best_match_id is not None:
            # Merge with existing entity
            kb_entry = kb[best_match_id]
            if entity_text not in kb_entry["aliases"]:
                kb_entry["aliases"].append(entity_text)  # Store in lowercase
            kb_entry["embeddings"].append(embedding)
            
            # Update record with KB info
            record["kb_id"] = best_match_id
            record["canonical_name"] = kb_entry["canonical_name"]
        else:
            # Create new KB entry
            new_id = create_new_kb_entry(entity_text, embedding, kb)
            record["kb_id"] = new_id
            record["canonical_name"] = clean_canonical_name(entity_text)
            # print("new_id, new_name", record["kb_id"], record["canonical_name"])
            
        updated_data.append(record)
    
    return updated_data