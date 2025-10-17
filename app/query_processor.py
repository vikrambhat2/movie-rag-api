import re
from typing import Dict, Optional

# Common genres in TMDB
GENRES = [
    'action', 'adventure', 'animation', 'comedy', 'crime', 
    'documentary', 'drama', 'family', 'fantasy', 'history',
    'horror', 'music', 'mystery', 'romance', 'science fiction',
    'sci-fi', 'thriller', 'war', 'western'
]

# Words to remove when extracting title keywords
STOP_WORDS = [
    'recommend', 'about', 'find', 'show', 'me', 'tell', 'what', 'is',
    'best', 'top', 'movies', 'films', 'movie', 'film', 'the', 'a', 'an',
    'from', 'in', 'of', 'and', 'or'
]


def parse_query(query: str) -> Dict:
    """
    Simple pattern-based query parsing
    
    For POC - production would use proper NLP/intent classification
    """
    q = query.lower().strip()
    
    # Determine intent based on keywords
    intent = 'search'
    if any(kw in q for kw in ['recommend', 'suggest', 'what should i watch']):
        intent = 'recommend'
    elif any(kw in q for kw in ['about', 'plot', 'synopsis', 'tell me about']):
        intent = 'describe'
    elif any(kw in q for kw in ['best', 'top', 'highest rated']):
        intent = 'top_rated'
    
    # Extract genre
    genre = None
    for g in GENRES:
        if g in q:
            genre = g
            if g == 'sci-fi':
                genre = 'science fiction'  # Match DB format
            break
    
    # Extract year
    year = None
    year_match = re.search(r'\b(19|20)\d{2}\b', q)
    if year_match:
        year = int(year_match.group())
    
    # Extract title keywords - improved cleaning
    title_keywords = q
    
    # Remove common query words
    for word in STOP_WORDS:
        title_keywords = re.sub(r'\b' + word + r'\b', '', title_keywords)
    
    # Remove genre from keywords
    if genre:
        title_keywords = title_keywords.replace(genre, '')
        title_keywords = title_keywords.replace('sci-fi', '')  # Also remove sci-fi variant
    
    # Remove year from keywords
    if year:
        title_keywords = title_keywords.replace(str(year), '')
    
    # Clean up: remove extra spaces, strip
    title_keywords = re.sub(r'\s+', ' ', title_keywords).strip()
    
    # Only use keywords if they're meaningful (not just punctuation/spaces)
    if title_keywords and len(title_keywords) > 2:
        title_keywords = title_keywords
    else:
        title_keywords = None
    
    return {
        'intent': intent,
        'genre': genre,
        'year': year,
        'keywords': title_keywords
    }