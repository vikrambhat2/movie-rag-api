from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

from app.database import MovieDB
from app.query_processor import parse_query
from app.llm_service import generate_response
from app.agent_service import query_with_agent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Movie RAG API",
    description="Natural language movie queries combining structured data with LLM",
    version="1.0.0"
)

db = MovieDB()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    movies: List[Dict]
    query_info: Dict


@app.get("/")
async def root():
    return {
        "message": "Movie RAG API",
        "endpoints": {
            "query": "POST /query",
            "movie": "GET /movies/{id}",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    try:
        # Quick DB check
        db.search(limit=1)
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/query", response_model=QueryResponse)
async def query_movies(request: QueryRequest):
    """
    Process natural language movie queries
    
    Examples:
    - "Recommend action movies from 2015"
    - "Tell me about Inception"
    - "What are the best comedy movies?"
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Query: {question}")
        
        # Parse query
        query_info = parse_query(question)
        logger.info(f"Parsed: {query_info}")
        
        # Search database based on intent
        if query_info['intent'] == 'top_rated':
            movies = db.get_top_rated(limit=5)
        else:
            movies = db.search(
                title=query_info.get('keywords'),
                genre=query_info.get('genre'),
                year=query_info.get('year'),
                limit=5
            )
        
        logger.info(f"Found {len(movies)} movies")
        
        # Generate response
        answer = generate_response(
            question, 
            movies, 
            intent=query_info['intent']
        )
        
        return QueryResponse(
            answer=answer,
            movies=movies,
            query_info=query_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    """Get detailed information about a specific movie"""
    movie = db.get_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.post("/query/agent")
async def query_movies_agent(request: QueryRequest):
    """
    Agent-based approach: LLM autonomously generates and executes SQL
    
    Differences from /query:
    - More flexible (handles any SQL-able question)
    - Higher latency (~3-5s due to agent reasoning)
    - Less predictable results
    - Demonstrates agentic AI capabilities
    
    Examples:
    - "What's the average rating of action movies?"
    - "How many movies were released in 2015?"
    - "Which director has the most highly-rated films?"
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Agent query: {question}")
        
        # Import here to avoid loading if not needed
        from app.agent_service import query_with_agent
        
        result = query_with_agent(question)
        
        return {
            "answer": result["answer"],
            "method": result["method"],
            "note": result.get("note", ""),
            "approach": "autonomous_sql_agent"
        }
    
    except ImportError:
        raise HTTPException(
            status_code=501, 
            detail="Agent service not available. Install langchain dependencies."
        )
    except Exception as e:
        logger.error(f"Agent endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Agent processing failed")


@app.get("/agent/info")
async def get_agent_info():
    """Get information about agent capabilities and database schema"""
    try:
        from app.agent_service import get_agent_info
        return get_agent_info()
    except ImportError:
        return {"error": "Agent service not available"}