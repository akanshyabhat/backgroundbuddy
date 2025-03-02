import json
import re

# Keywords related to local politics (you can expand this list)
local_political_keywords = [
    "mayor", "city council", "politics", "public policy",
    "elections", "governance", "city budget", "campaign", "town hall", "legislation", "vote"
]

# Keywords related to crime (to exclude from politics)
crime_keywords = [
    "murder trial", "criminal charges", "defendant", "trial", "guilty", "criminal justice", "arrest", "sentencing",
    "restraining order", "charges", "shooter", "killed", "charged"
]

# Read the JSON file
json_file_path = 'BackgroundBuddy.json'
filtered_docs = []

def is_relevant_local_article(article):
    """
    Filters articles to check if they are related to Minneapolis politics using a broader set of keywords.
    """
    # Check the headline for local Minneapolis politics keywords
    headline = article.get('headline', '').lower()

    # Check the body content for local Minneapolis politics keywords
    body_content = ''
    for entry in article.get('jsonBody', []):
        content = entry.get('content', '')
        
        # Debugging to check if the content is a list or a string
        if isinstance(content, str):  # If the content is a string, process it normally
            body_content += content.lower() + ' '
        elif isinstance(content, list):  # If the content is a list, print debugging information
            body_content += ' '.join(str(item) for item in content).lower() + ' '
        else:
            print(f"Unexpected type for 'content' in article with headline: {article.get('headline', 'No headline')}")
            print(f"Content: {content}")
    

    # Check if "minneapolis" is mentioned at least once
    if 'minneapolis' not in body_content or 'minneapolis' not in headline:
        return False  # Exclude articles that do not mention Minneapolis
    
    # Debugging: Check crime keyword matching
    for keyword in crime_keywords:
        # Test for exact phrase match of crime-related keywords
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, body_content):
            print(f"Crime keyword '{keyword}' found in article: {article.get('headline')}")
            return False  # Exclude crime-related articles
        
# If any local-related keyword appears in the headline, it's considered relevant
    if any(keyword.lower() in body_content or keyword.lower() in headline for keyword in local_political_keywords):
        return True
    
    """
    # Count how many political keywords are found in the content
    political_keyword_count = sum(1 for keyword in local_political_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', body_content))
    
    # Only include articles with at least 2 political keywords
    if political_keyword_count >= 2:
        return True  # Include articles with at least two local political keywords
    """

    return False

# Read the file and filter the articles
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)  # Load the JSON data

    # Iterate through each article and filter based on relevance
    for article in data:
        if is_relevant_local_article(article):
            filtered_docs.append(article)

# Save the filtered articles to a new JSON file (keeping the same structure)
filtered_json_path = 'filtered_articles.json'

with open(filtered_json_path, 'w', encoding='utf-8') as f:
    json.dump(filtered_docs, f, ensure_ascii=False, indent=4)

print(f"Filtered articles saved to {filtered_json_path}")
