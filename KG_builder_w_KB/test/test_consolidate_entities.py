import pytest
import numpy as np
from sentence_transformers import SentenceTransformer
from consolidate_entities import (
    consolidate_entities_with_kb,
    create_new_kb_entry,
    clean_canonical_name,
    cosine_similarity,
    KB
)

# Load embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text):
    """Generate sentence embedding using a transformer model."""
    return embedding_model.encode(text).tolist()

@pytest.fixture
def empty_kb():
    """Fixture for an empty knowledge base."""
    return {}

@pytest.fixture
def populated_kb():
    """Fixture for a populated knowledge base."""
    kb = {}
    create_new_kb_entry("Jacob Frey", generate_embedding("Jacob Frey"), kb)
    create_new_kb_entry("Democratic Party", generate_embedding("Democratic Party"), kb)
    return kb

def test_clean_canonical_name():
    """Test canonical name cleaning for different cases."""
    assert clean_canonical_name("Dr. John Doe") == "john doe"
    assert clean_canonical_name("Mayor Jacob Frey") == "jacob frey"
    assert clean_canonical_name("Ms. Jane Smith Jr.") == "jane smith jr."
    assert clean_canonical_name("Professor Anne Marie") == "anne marie"

def test_consolidate_entities_with_kb_new_entry(empty_kb):
    """Test adding a new entity to an empty knowledge base."""
    final_data = [{"entity_text": "John Doe", "embedding": generate_embedding("John Doe")}]
    updated_data = consolidate_entities_with_kb(final_data, empty_kb)
    
    assert len(empty_kb) == 1
    assert updated_data[0]["canonical_name"] == "john doe"
    assert "kb_id" in updated_data[0]

def test_consolidate_entities_with_kb_merge(populated_kb):
    """Test merging similar entities into the knowledge base."""
    final_data = [
        {"entity_text": "Jacob Lawrence Frey", "embedding": generate_embedding("Jacob Lawrence Frey")}
    ]
    
    updated_data = consolidate_entities_with_kb(final_data, populated_kb)
    
    assert len(populated_kb) == 2  # Should not create a new entry
    assert updated_data[0]["kb_id"] in populated_kb
    assert updated_data[0]["canonical_name"] == "jacob frey"  # Merges into existing

def test_consolidate_entities_with_kb_distinct_entry(populated_kb):
    """Test that distinct names are not merged incorrectly."""
    final_data = [
        {"entity_text": "Jane Doe", "embedding": generate_embedding("Jane Doe")}
    ]
    
    updated_data = consolidate_entities_with_kb(final_data, populated_kb)
    
    assert len(populated_kb) == 3  # Should create a new KB entry
    assert updated_data[0]["canonical_name"] == "jane doe"
    assert "kb_id" in updated_data[0]

def test_cosine_similarity():
    """Test that cosine similarity behaves correctly."""
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0, 0])
    assert np.isclose(cosine_similarity(vec1, vec2), 1.0)

    vec1 = np.array([1, 0, 0])
    vec2 = np.array([0, 1, 0])
    assert np.isclose(cosine_similarity(vec1, vec2), 0.0)

def test_consolidate_entities_with_alias(populated_kb):
    """Test that an alias is correctly added."""
    final_data = [
        {"entity_text": "Democrats", "embedding": generate_embedding("Democrats")}
    ]
    
    updated_data = consolidate_entities_with_kb(final_data, populated_kb)
    
    assert len(populated_kb) == 2  # Should merge into "Democratic Party"
    kb_id = updated_data[0]["kb_id"]
    assert "democrats" in populated_kb[kb_id]["aliases"]

def test_consolidate_jacob_frey_variations(empty_kb):
    """Test that all variations of Jacob Frey correctly merge into one entry."""
    final_data = [
        {"entity_text": "Jacob Frey", "embedding": generate_embedding("Jacob Frey")},
        {"entity_text": "Mayor Frey", "embedding": generate_embedding("Mayor Frey")},
        {"entity_text": "Jacob Lawrence Frey", "embedding": generate_embedding("Jacob Lawrence Frey")},
    ]
    
    updated_data = consolidate_entities_with_kb(final_data, empty_kb)
    
    assert len(empty_kb) == 1  # All should merge into a single entry
    kb_id = updated_data[0]["kb_id"]
    
    assert "jacob frey" == empty_kb[kb_id]["canonical_name"]
    assert "mayor frey" in empty_kb[kb_id]["aliases"]
    assert "jacob lawrence frey" in empty_kb[kb_id]["aliases"]

def test_consolidate_political_parties(populated_kb):
    """Test that variations of a political party merge correctly."""
    final_data = [
        {"entity_text": "Democrats", "embedding": generate_embedding("Democrats")},
        {"entity_text": "Democratic National Committee", "embedding": generate_embedding("Democratic National Committee")},
    ]
    
    updated_data = consolidate_entities_with_kb(final_data, populated_kb)
    
    assert len(populated_kb) == 2  # Should not create a new entry
    kb_id = updated_data[0]["kb_id"]
    
    assert "democratic party" == populated_kb[kb_id]["canonical_name"]
    assert "democrats" in populated_kb[kb_id]["aliases"]
    assert "democratic national committee" in populated_kb[kb_id]["aliases"]

if __name__ == "__main__":
    pytest.main()
