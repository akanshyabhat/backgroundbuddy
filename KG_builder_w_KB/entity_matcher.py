from typing import List, Dict, Any, Optional
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import numpy as np

# EntityMatcher class
# This class is used to match mentions to knowledge base entities
# It uses three methods to match mentions:
# 1. Exact matching
# 2. Fuzzy matching (Levenshtein similarity)
# 3. Context-based disambiguation (TF-IDF & Sentence Similarity)

''' 
------------------------------------------------------------
UNIFY MENTION TO KB ID   
------------------------------------------------------------
'''

class EntityMatcher:
    def __init__(self, entity_records: List[Dict[str, Any]]):
        """
        Initialize with a list of entity records from the knowledge base.
        
        Each entity record should contain:
        - `name`: The canonical name
        - `aliases`: List of alternative names
        - `kb_id`: The unique identifier
        - `description`: Optional text description for context matching
        """
        self.entity_records = entity_records
        self.names_to_kb = {entity["name"]: entity["kb_id"] for entity in entity_records}
        self.alias_to_kb = {alias: entity["kb_id"] for entity in entity_records for alias in entity.get("aliases", [])}
        self.kb_id_to_desc = {entity["kb_id"]: entity.get("description", "") for entity in entity_records}

        # Prepare TF-IDF model for context matching
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.kb_id_to_desc.values())
        self.kb_id_list = list(self.kb_id_to_desc.keys())

        # Pre-trained sentence embedding model for deeper context similarity
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.entity_embeddings = self.embed_model.encode(list(self.kb_id_to_desc.values()), convert_to_tensor=True)

    def match_entity(self, mention_text: str, mention_evidence: str) -> Optional[str]:
        """
        Match a mention to a knowledge base entity using:
        1. Exact matching
        2. Fuzzy matching (Levenshtein similarity)
        3. Context-based disambiguation (TF-IDF & Sentence Similarity)
        """
        # Step 1: Exact Matching
        if mention_text in self.names_to_kb:
            return self.names_to_kb[mention_text]
        if mention_text in self.alias_to_kb:
            return self.alias_to_kb[mention_text]

        # Step 2: Fuzzy Matching
        potential_matches = list(self.names_to_kb.keys()) + list(self.alias_to_kb.keys())
        best_match, best_score = process.extractOne(mention_text, potential_matches)
        if best_score > 85:  # Threshold for fuzzy match
            return self.names_to_kb.get(best_match, self.alias_to_kb.get(best_match))

        # Step 3: Context-Based Disambiguation
        return self.resolve_with_context(mention_text, mention_evidence)


    def resolve_with_context(self, mention_text: str, mention_evidence: str) -> Optional[str]:
        """
        Uses TF-IDF and Sentence Similarity to resolve ambiguous mentions.
        """
        mention_vector = self.tfidf_vectorizer.transform([mention_evidence])
        similarity_scores = (mention_vector * self.tfidf_matrix.T).toarray().flatten()
        top_tfidf_match = self.kb_id_list[np.argmax(similarity_scores)]

        # Deep Context Similarity (Sentence Embeddings)
        mention_embedding = self.embed_model.encode([mention_evidence], convert_to_tensor=True).to("cpu")  # Move to CPU
        cosine_scores = np.dot(self.entity_embeddings.cpu(), mention_embedding.cpu().T).flatten()  # Ensure both are on CPU
        top_embedding_match = self.kb_id_list[np.argmax(cosine_scores)]

        # Final Decision (Hybrid Approach)
        if similarity_scores[np.argmax(similarity_scores)] > 0.3:
            return top_tfidf_match  # TF-IDF similarity threshold
        if cosine_scores[np.argmax(cosine_scores)] > 0.7:
            return top_embedding_match  # Embedding similarity threshold

        return None  # No confident match found


# Wrapper function
def unify_mention_to_kb_id(
    mention_text: str,
    mention_evidence: str,
    entity_records: List[Dict[str, Any]],
) -> Optional[str]:
    matcher = EntityMatcher(entity_records)
    return matcher.match_entity(mention_text, mention_evidence)
