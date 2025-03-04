'''
Entity extraction TRAINING using prodigy
'''
import prodigy
import signal
import os
from prodigy.components.loaders import JSONL
from config import ENTITY_TYPES #, RELATIONSHIP_TYPES
from typing import Dict, Any, List
import json
import random
import spacy
import subprocess

TRAINING_EPOCHS = 20 # number of epochs to train the model

def train_model(dataset: str, base_model: str, output_dir: str):
    """
    Train a new model using Prodigy with the specified dataset and base model.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # full TEST command prodigy train-curve ./trained_models --ner my_dataset --show-plot
    # train command prodigy train ./trained_models --ner my_dataset --training.max_epochs=20
        
    command = [
        "prodigy", "train", output_dir, "--ner",dataset, "--training.max_epochs=" + str(TRAINING_EPOCHS)
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Model successfully trained and saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error training model: {e}")
        raise

def load_trained_model(model_path: str):
    """
    Load the trained Prodigy model from the specified path.
    """
    try:
        # Look for the model in the output directory
        model_files = os.listdir(model_path)
        model_dir = next((f for f in model_files if f.startswith("model")), None)
        if model_dir:
            full_path = os.path.join(model_path, model_dir)
            return spacy.load(full_path)
        else:
            raise FileNotFoundError(f"No model found in {model_path}")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise



if __name__ == "__main__":
    dataset = "my_dataset"
    base_model = "en_core_web_sm"
    output_dir = "./trained-models"
    
    print("\nTraining model...")
    train_model(dataset, base_model, output_dir)
    
    print("\nLoading trained model... from trained-models/model-last")
    nlp_model = load_trained_model(output_dir)
    print("\nModel trained and loaded. Now extracting entities from the entire archive...")
    # And now extract entities from the entire archive (haven't implemented this yet)