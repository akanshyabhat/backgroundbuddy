import spacy
import json

# Load the same spaCy model used in Prodigy
nlp = spacy.load("en_core_web_sm")

# Load your annotations
with open("annotations.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

# Check each annotation
for entry in data:
    text = entry["text"]
    doc = nlp(text)
    
    print(f"\nText: {text}")
    print("Tokens:")
    for token in doc:
        print(f"  {token.text} ({token.idx}-{token.idx + len(token.text)})")
    
    # Check spans
    for span in entry["spans"]:
        start, end = span["start"], span["end"]
        span_text = text[start:end]
        print(f"  → Annotated Span: {span_text} ({start}-{end})")

