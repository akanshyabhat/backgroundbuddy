'''
CONFIGURATION FILE INCLUDING:
- Entity types
- Relationship types
- KB file path (not yet)
'''

# Entity types
ENTITY_TYPES = ["EVENT", "FAC","GPE", "LANGUAGE", "LAW", "LOC", "NORP", "ORG", "PERSON", "PRODUCT"]

# Relationship types and their properties
RELATIONSHIP_TYPES = {
    "WORKS_FOR": ["since"],
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
    "IS_ACCUSED_OF": ["charge"],
    "IS_CHARGED_WITH": ["charge"],
}

