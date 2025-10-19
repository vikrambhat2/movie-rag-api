import ollama
from typing import List, Dict
from app.config import OLLAMA_MODEL
import logging

logger = logging.getLogger(__name__)

def generate_response(question: str, movies: List[Dict], intent: str = 'search') -> str:
    if not movies:
        return "I couldn't find any movies matching your query. Try being more specific."

    # Prepare context for up to 5 movies
    context_lines = []
    for m in movies[:5]:
        genres = ', '.join(m.get('genres', [])) or 'N/A'
        cast = ', '.join(m.get('movie_cast', [])[:3]) or 'N/A'
        context_lines.append(
            f"- {m['title']} ({m.get('year', 'N/A')}) | Rating: {m.get('vote_average', 'N/A')}/10\n"
            f"  Genres: {genres} | Plot: {m.get('overview', 'No plot')[:200]}...\n"
            f"  Cast: {cast}"
        )

    context = "\n\n".join(context_lines)

    # Instruction based on intent
    instructions = {
        'describe': "Give a concise description highlighting key details.",
        'recommend': "Recommend these movies naturally, explaining why they fit the query.",
        'search': "Answer conversationally using the movie data."
    }
    instruction = instructions.get(intent, instructions['search'])

    prompt = f"""You are a helpful movie assistant. {instruction}

Movie Data:
{context}

User Question: {question}

Provide a friendly 2-3 sentence response using only the info above."""

    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.7, 'num_predict': 150}
        )
        return resp['message']['content'].strip()
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        top = movies[0]
        return f"I found {len(movies)} movie(s). Top result: '{top['title']}' ({top.get('year','N/A')}) with rating {top.get('vote_average','N/A')}/10."
