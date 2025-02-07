import os
import subprocess
"""
To Annotate Entities:

Run Named Entity Recognition (NER) annotation:
    prodigy ner.manual political_ner en_core_web_trf data.jsonl
OR use model-assisted correction:
    prodigy ner.correct political_ner en_core_web_trf data.jsonl
If you have patterns.jsonl, you can bootstrap annotation with:
    prodigy ner.teach political_ner en_core_web_trf data.jsonl --patterns patterns.jsonl


Once entities are labeled, run relationship annotation:
    prodigy rel.manual political_rels data.jsonl --label VETOED,PROPOSED,SUPPORTED,OPP 

Review manually:
    prodigy review political_ner
    prodigy review political_rels

To export annotations:
prodigy db-out political_ner > entity_annotations.jsonl
prodigy db-out political_rels > relationship_annotations.jsonl

To extract relationships:
python extract_relationships.py

To review extracted relationships:
prodigy review ai_extracted_relationships.jsonl

To build Neo4j graph:
python build_neo4j_graph.py


"""

def run_command(command):
    """Runs a shell command and prints output."""
    print(f"\n🚀 Running: {command}")
    input("Press Enter to execute this command...")
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(process.stdout)
    if process.stderr:
        print(f"⚠️ Error: {process.stderr}")
    input("Press Enter to continue to next step...")

def convert_pdfs_to_jsonl():
    """Converts PDFs to JSONL for annotation."""
    print("\n=== Converting PDFs to JSONL ===")
    print("This step will convert your PDF documents into JSONL format for annotation.")
    run_command("python extract_text.py")

def annotate_entities():
    """Runs Prodigy entity annotation."""
    print("\n=== Annotating Entities ===")
    print("You will now annotate entities in the text. Use the following keys:")
    print("- [1-9]: Select entity type")
    print("- [Space]: Accept annotation")
    print("- [a/s]: Accept/reject example")
    print("\nIMPORTANT: Press [q] to save and exit the Prodigy session when done")
    run_command("prodigy ner.correct political_ner en_core_web_trf data.jsonl")

def annotate_relationships():
    """Runs Prodigy relationship annotation."""
    print("\n=== Annotating Relationships ===")
    print("Now you'll annotate relationships between entities.")
    print("1. Select the first entity (subject)")
    print("2. Select the second entity (object)")
    print("3. Choose the relationship type")
    print("\nIMPORTANT: Press [q] to save and exit the Prodigy session when done")
    run_command("prodigy rel.manual political_rels data.jsonl --label VETOED,PROPOSED,SUPPORTED,OPPOSED --span-label POLITICIAN,GOVERNMENT_ORG,POLICY")

def review_annotations():
    """Reviews Prodigy annotations before processing."""
    print("\n=== Reviewing Annotations ===")
    print("\nIMPORTANT: Press [q] to save and exit the Prodigy review session when done")
    run_command("prodigy review political_ner")
    run_command("prodigy review political_rels")

def extract_relationships_with_llm():
    """Runs GPT-4-based relationship extraction."""
    print("\n=== Extracting Relationships with LLM ===")
    run_command("python extract_relationships.py")

def validate_extracted_relationships():
    """Runs Prodigy review on extracted relationships."""
    print("\n=== Validating AI-Extracted Relationships ===")
    print("\nIMPORTANT: Press [q] to save and exit the Prodigy review session when done")
    run_command("prodigy review ai_extracted_relationships.jsonl")

def build_neo4j_graph():
    """Builds the knowledge graph in Neo4j."""
    print("\n=== Building Knowledge Graph in Neo4j ===")
    run_command("python build_neo4j_graph.py")

def run_full_pipeline():
    """Runs the entire Prodigy pipeline from PDF extraction to Neo4j storage."""
    print("\n=== Political Knowledge Graph Pipeline ===")
    print("This pipeline will guide you through the process of building a political knowledge graph.")
    print("You can press Enter to proceed through each step.")
    input("Press Enter to begin...")

    steps = [
        (convert_pdfs_to_jsonl, "Converting PDFs to JSONL"),
        (annotate_entities, "Annotating Entities"),
        (annotate_relationships, "Annotating Relationships"),
        (review_annotations, "Reviewing Annotations"),
        (extract_relationships_with_llm, "Extracting Relationships with LLM"),
        (validate_extracted_relationships, "Validating Extracted Relationships"),
        (build_neo4j_graph, "Building Knowledge Graph")
    ]

    for step_func, step_name in steps:
        print(f"\n{'='*50}")
        print(f"Step: {step_name}")
        print(f"{'='*50}")
        step_func()
        print(f"\n✅ Completed: {step_name}")
        input("Press Enter to continue to next step (or Ctrl+C to exit)...")

    print("\n✅ Pipeline completed successfully!")

if __name__ == "__main__":
    run_full_pipeline()