import ollama
from typing import List, Dict
from app.config import OLLAMA_MODEL
import logging

logger = logging.getLogger(__name__)

def generate_response(question: str, movies: List[Dict], intent: str = 'search') -> str:
    """
    Generate natural language response using Ollama
    """
    if not movies:
        return "I couldn't find any movies matching your query. Try being more specific or adjusting your criteria."
    
    # Format movie data
    movie_context = []
    for m in movies[:5]:
        genres_str = ', '.join(m.get('genres', [])) if m.get('genres') else 'N/A'
        cast_str = ', '.join(m.get('movie_cast', [])[:3]) if m.get('movie_cast') else 'N/A'
        
        movie_context.append(
            f"- {m['title']} ({m.get('year', 'N/A')})\n"
            f"  Genres: {genres_str}\n"
            f"  Rating: {m.get('vote_average', 'N/A')}/10\n"
            f"  Plot: {m.get('overview', 'No plot available')[:200]}...\n"
            f"  Cast: {cast_str}"
        )

    
    context = "\n\n".join(movie_context)
    
    # Adjust instruction based on intent
    if intent == 'describe':
        instruction = "Provide a concise description of the movie(s), highlighting key details."
    elif intent == 'recommend':
        instruction = "Recommend these movies naturally, explaining why they match the query."
    else:
        instruction = "Answer the question conversationally using the movie data."
    
    prompt = f"""You are a helpful movie assistant. {instruction}

Movie Data:
{context}

User Question: {question}

Provide a friendly, conversational response (2-3 sentences). Use only the information provided. Do not make up information."""
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={
                'temperature': 0.7,
                'num_predict': 150
            }
        )
        
        return response['message']['content'].strip()
        
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        # Fallback response
        top_movie = movies[0]
        return (
            f"I found {len(movies)} movie(s) matching your query. "
            f"The top result is '{top_movie['title']}' ({top_movie.get('year', 'N/A')}) "
            f"with a rating of {top_movie.get('vote_average', 'N/A')}/10."
        )