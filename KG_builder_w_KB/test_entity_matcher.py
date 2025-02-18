import unittest
import pytest
from entity_matcher import EntityMatcher

# Sample entity records
SAMPLE_RECORDS = [
    {
        "name": "Donald Trump",
        "aliases": ["President Trump", "Trump", "Donald J. Trump"],
        "kb_id": "Q22686",
        "description": "45th President of the United States, businessman, and media personality."
    },
    {
        "name": "Ivanka Trump",
        "aliases": ["Ivanka"],
        "kb_id": "Q47562",
        "description": "Daughter of Donald Trump, businesswoman, and former White House advisor."
    },
    {
        "name": "Democratic Party",
        "aliases": ["Democrats", "Democrat"],
        "kb_id": "Q196",
        "description": "A major political party in the United States."
    },
]

@pytest.fixture
def matcher():
    return EntityMatcher(SAMPLE_RECORDS)  # Use the sample records we defined above

def test_exact_match(matcher):
    assert matcher.match_entity("Donald Trump", "Donald Trump was in the news") == "Q22686"

def test_alias_match(matcher):
    assert matcher.match_entity("President Trump", "President Trump held a press conference") == "Q22686"

def test_fuzzy_match(matcher):
    assert matcher.match_entity("Donal Tramp", "Donal Tramp was on TV") == "Q22686"

def test_context_disambiguation_politics(matcher):
    assert matcher.match_entity("Trump", "Trump signed a new law") == "Q22686"

def test_context_disambiguation_business(matcher):
    result = matcher.match_entity("Trump", "Ivanka Trump launched a new fashion line")
    assert result == "Q47562"

def test_context_disambiguation_politics(matcher):
    result = matcher.match_entity("Democrats", "The Democratic Party is a major political party in the United States.")
    assert result == "Q196"

if __name__ == "__main__":
    unittest.main()
