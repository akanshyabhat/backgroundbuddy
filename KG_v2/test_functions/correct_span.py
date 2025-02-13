import json
import spacy

# Load a minimal spaCy model
nlp = spacy.blank("en")

# Load the annotations file
file_path = "annotations.jsonl"  # Update with your file path
fixed_annotations_path = "fixed_annotations.jsonl"

# Read the JSONL file
with open(file_path, "r", encoding="utf-8") as f:
    annotations = [json.loads(line) for line in f]

# Function to correct span offsets
def fix_spans(text, spans):
    """Corrects span offsets to align with spaCy tokenization."""
    doc = nlp(text)
    corrected_spans = []

    for span in spans:
        if span["start"] < 0:
            continue  # Ignore invalid spans

        # Find token boundaries
        corrected_start = None
        corrected_end = None

        for token in doc:
            if token.idx <= span["start"] < token.idx + len(token.text):
                corrected_start = token.idx
            if token.idx < span["end"] <= token.idx + len(token.text):
                corrected_end = token.idx + len(token.text)

        if corrected_start is not None and corrected_end is not None:
            corrected_spans.append({
                "start": corrected_start,
                "end": corrected_end,
                "label": span["label"]
            })

    return corrected_spans

# Fix all annotations
for entry in annotations:
    entry["spans"] = fix_spans(entry["text"], entry["spans"])

# Save the corrected annotations
with open(fixed_annotations_path, "w", encoding="utf-8") as f:
    for entry in annotations:
        f.write(json.dumps(entry) + "\n")

print(f"Corrected annotations saved to {fixed_annotations_path}")
