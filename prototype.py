import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from tqdm import tqdm
import time
import os

# Load the data
def load_data(file_path):
    print("📂 Loading data file...")
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    print(f"✓ Loaded {len(data)} articles")
    return data

# Compute top-k most relevant articles
def find_top_k_articles(query_embedding, article_embeddings, k=3):
    k = min(k, len(article_embeddings))  # Ensure k doesn't exceed available articles
    similarities = cosine_similarity([query_embedding], article_embeddings)[0]
    top_k_indices = np.argsort(similarities)[-k:][::-1]
    return top_k_indices, similarities

def format_article_response(article_data, idx, similarity):
    try:
        key = list(article_data.keys())[idx]
        meta = article_data[key]["meta"]
        date = meta.get('date', 'Date not available')
        return f"""
📰 Article {idx + 1}
Headline: {meta['headline']}
Date: {date}
Summary: {meta['dek']}
Relevance: {similarity:.2f}
"""
    except Exception as e:
        return f"Error formatting article {idx}: {str(e)}"

def save_embeddings(embeddings, file_path='article_embeddings.pickle'):
    print("💾 Saving embeddings for future use...")
    with open(file_path, 'wb') as f:
        pickle.dump(embeddings, f)
    print("✓ Embeddings saved")

def load_or_compute_embeddings(article_data, model):
    embedding_file = 'article_embeddings.pickle'
    
    if os.path.exists(embedding_file):
        print("📂 Loading pre-computed embeddings...")
        with open(embedding_file, 'rb') as f:
            return pickle.load(f)
    
    print("📚 Computing embeddings for the first time...")
    article_embeddings = []
    articles_list = list(article_data.values())
    for article in tqdm(articles_list, desc="Processing"):
        embedding = model.encode(article["meta"]["headline"])
        article_embeddings.append(embedding)
    embeddings = np.array(article_embeddings)
    
    # Save for future use
    save_embeddings(embeddings)
    return embeddings

def filter_by_date(article_data, start_date=None, end_date=None):
    """Filter articles by date range"""
    if not start_date and not end_date:
        return article_data
    
    filtered_data = {}
    for key, article in article_data.items():
        article_date = article["meta"].get('date')
        if not article_date:
            continue
            
        if start_date and end_date:
            if start_date <= article_date <= end_date:
                filtered_data[key] = article
        elif start_date and article_date >= start_date:
            filtered_data[key] = article
        elif end_date and article_date <= end_date:
            filtered_data[key] = article
    
    return filtered_data

def parse_date(date_str):
    """Parse date string in format YYYY-MM-DD"""
    try:
        from datetime import datetime
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

def chatbot():
    print("\n🤖 Welcome to the Article Search Chatbot!")
    print("Loading resources...")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    article_data = load_data("embeds_with_headline.pickle")
    
    # Load or compute embeddings
    article_embeddings = load_or_compute_embeddings(article_data, model)
    print("✓ Ready to chat!")
    print("\n💡 Tips:")
    print("- Specify number of articles: 'n:query' (e.g., '5:technology news')")
    print("- Filter by date: 'date:YYYY-MM-DD:query' for single date")
    print("- Filter by range: 'date:YYYY-MM-DD,YYYY-MM-DD:query'")
    
    while True:
        query = input("\n🔍 What would you like to know about? (type 'exit' to quit)\n> ")
        
        if query.lower() in ['exit', 'quit', 'bye']:
            print("👋 Thanks for chatting! Goodbye!")
            break
        
        # Default values
        k = 3
        start_date = None
        end_date = None
        
        # Parse date filter if present
        if query.startswith('date:'):
            try:
                date_part, query = query.split(':', 2)[1:]
                if ',' in date_part:
                    start_str, end_str = date_part.split(',')
                    start_date = parse_date(start_str)
                    end_date = parse_date(end_str)
                else:
                    start_date = end_date = parse_date(date_part)
                
                if not start_date and not end_date:
                    print("⚠️ Invalid date format. Use YYYY-MM-DD")
            except:
                print("⚠️ Invalid date format, ignoring date filter")
        
        # Parse k value if present
        if ':' in query:
            try:
                k_str, query = query.split(':', 1)
                k = int(k_str)
                if k < 1:
                    print("⚠️ Number of articles must be positive, using default (3)")
                    k = 3
            except ValueError:
                pass
            
        start_time = time.time()
        print(f"\n🤔 Searching for {k} relevant articles...")
        
        # Filter articles by date if specified
        filtered_data = filter_by_date(article_data, start_date, end_date)
        if not filtered_data:
            print("❌ No articles found in the specified date range")
            continue
            
        # Get embeddings for filtered articles
        filtered_embeddings = []
        filtered_indices = []
        for i, (key, article) in enumerate(article_data.items()):
            if key in filtered_data:
                filtered_embeddings.append(article_embeddings[i])
                filtered_indices.append(i)
        filtered_embeddings = np.array(filtered_embeddings)
        
        # Encode query and find matches
        query_embedding = model.encode(query)
        top_k_indices, similarities = find_top_k_articles(query_embedding, filtered_embeddings, k)
        
        # Map back to original indices
        original_indices = [filtered_indices[idx] for idx in top_k_indices]
        
        # Format response
        print(f"\n📚 Here are the {len(original_indices)} most relevant articles:")
        for i, (idx, sim) in enumerate(zip(original_indices, similarities[top_k_indices])):
            response = format_article_response(article_data, int(idx), sim)
            print(response)
            
        print(f"\n⏱️ Found in {time.time() - start_time:.2f} seconds")
        if start_date or end_date:
            date_range = f"Date range: {start_date or 'any'} to {end_date or 'any'}"
            print(f"📅 {date_range}")
        print("\nAsk another question or type 'exit' to quit.")

if __name__ == "__main__":
    try:
        chatbot()
    except KeyboardInterrupt:
        print("\n\n👋 Chat ended by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
