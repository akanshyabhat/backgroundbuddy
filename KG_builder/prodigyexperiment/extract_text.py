import os
import json
import pdfplumber
import re

input_dir = "./articles"  # Path to PDF directory
output_file = "data.jsonl"

def clean_text(text):
    """Extracts only the article content, author, and date/time while removing footers and other irrelevant data."""
    lines = text.split("\n")
    cleaned_lines = []
    capturing = False
    metadata = {"author": None, "date": None}
    
    for line in lines:
        line = line.strip()
        
        # Extract author
        if re.search(r'By [A-Z][a-z]+ [A-Z][a-z]+', line):
            metadata["author"] = line
        
        # Extract date/time
        if re.search(r'\b(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER) \d{1,2}, \d{4}\b', line):
            metadata["date"] = line
        
        # Start capturing article content after metadata
        if "NEWS" in line or "POLITICS" in line or "OPINION" in line:
            capturing = True
            continue
        
        # Stop capturing when encountering footer-like content
        if re.search(r'Page \d+ of \d+|All rights reserved|©|Subscribe|Contact us|ADVERTISEMENT|Subscribe Today', line, re.IGNORECASE):
            capturing = False
        
        if capturing and line:
            cleaned_lines.append(line)
    
    return metadata, " ".join(cleaned_lines)

def extract_text_from_pdfs(input_dir, output_file):
    data = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            with pdfplumber.open(pdf_path) as pdf:
                metadata, text = clean_text(" ".join([page.extract_text() for page in pdf.pages if page.extract_text()]))
                data.append({"author": metadata["author"], "date": metadata["date"], "text": text})

    with open(output_file, "w") as f:
        for entry in data:
            json.dump(entry, f)
            f.write("\n")

    print(f"✅ Extracted and cleaned article content, author, and date/time from PDFs, saved to {output_file}")

extract_text_from_pdfs(input_dir, output_file)