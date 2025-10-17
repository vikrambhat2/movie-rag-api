# Movie RAG API

Natural language movie query system combining structured database retrieval with LLM-powered response generation. Includes both traditional and agentic AI approaches.

## Overview

This API allows users to ask natural language questions about movies and receive conversational responses backed by real data from the TMDB dataset. It demonstrates two approaches to building conversational AI systems:

1. **Traditional RAG** - Controlled query processing with predictable SQL queries
2. **Agentic RAG** - Autonomous SQL generation via LangChain agents

**Example:**
```bash
User: "Recommend action movies from 2015"
System: "Based on 2015 action films, I'd recommend Mad Max: Fury Road - 
an intense post-apocalyptic thriller with stunning visuals and a rating 
of 7.6/10..."
```

---

## Quick Start

### Prerequisites

**1. Install Ollama**

macOS/Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Windows: Download from https://ollama.com/download

**2. Pull the Model**
```bash
ollama pull llama3.2
ollama serve  # Keep running in separate terminal
```

Verify:
```bash
ollama list  # Should show llama3.2
```

### Setup
```bash
# 1. Clone and setup environment
git clone <your-repo>
cd movie-rag-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Defaults work fine, edit if needed

# 3. Download TMDB dataset
# Get from: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
# Download both files:
# - tmdb_5000_movies.csv
# - tmdb_5000_credits.csv
# Place in: data/raw/

# 4. Load data into database
python data/load_data.py
# Should output: "Loaded ~4357 movies into data/movies.db"

# 5. Run the API
uvicorn app.main:app --reload

# API available at: http://localhost:8000
```

### Quick Test
```bash
# Traditional endpoint
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Recommend sci-fi movies from 2015"}'

# Agent endpoint (bonus feature)
curl -X POST "http://localhost:8000/query/agent" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many movies were released in 2015?"}'
```

---

## API Endpoints

### Traditional Approach

#### POST /query

Main endpoint for natural language movie queries using controlled query processing.

**Request:**
```json
{
  "question": "string"
}
```

**Response:**
```json
{
  "answer": "Natural language response from LLM",
  "movies": [
    {
      "id": 123,
      "title": "Movie Title",
      "year": 2015,
      "genres": ["Action", "Sci-Fi"],
      "overview": "Plot summary...",
      "vote_average": 7.5,
      "vote_count": 1234,
      "movie_cast": ["Actor 1", "Actor 2"],
      "director": "Director Name"
    }
  ],
  "query_info": {
    "intent": "recommend",
    "genre": "sci-fi",
    "year": 2015,
    "keywords": null
  }
}
```

**Supported Query Types:**
- Search by title: "Tell me about Inception"
- Recommend by genre: "Recommend action movies"
- Filter by year: "Show me movies from 2015"
- Combined filters: "Recommend comedy films from 2010"
- Top rated: "What are the best movies?"

**Performance:** ~1-2 seconds

---

### Agentic Approach (Bonus)

#### POST /query/agent

Alternative endpoint using LangChain SQL Agent for autonomous query generation.

**Request:**
```json
{
  "question": "string"
}
```

**Response:**
```json
{
  "answer": "Natural language response",
  "method": "sql_agent",
  "note": "Response generated via autonomous SQL agent",
  "approach": "autonomous_sql_agent"
}
```

**Best for Analytical Queries:**
- "How many movies were released in 2015?"
- "What is the average rating of action movies?"
- "Which genre has the highest average rating?"
- "How many movies have a rating above 8?"

**Performance:** ~3-5 seconds (includes agent reasoning)

---

### Other Endpoints

#### GET /movies/{id}
Get detailed information about a specific movie.

#### GET /health
Health check endpoint.

#### GET /agent/info
Get database schema information for agent capabilities.

---

## Architecture

### Two Approaches Compared

| Aspect | Traditional `/query` | Agent `/query/agent` |
|--------|---------------------|---------------------|
| **Query Processing** | Pattern matching | LLM-based analysis |
| **SQL Generation** | Predefined queries | Autonomous generation |
| **Latency** | 1-2s | 3-5s |
| **Reliability** | High (controlled) | Variable (LLM-generated) |
| **Flexibility** | Limited patterns | Any SQL-able question |
| **Safety** | Built-in constraints | Requires guardrails |
| **Best For** | Common queries | Analytical questions |
| **Production Ready** | Yes | Experimental |

### Traditional Approach Flow
```
User Query
    ↓
Query Processor (pattern matching)
    ↓
Database Search (predefined SQL)
    ↓
LLM Response Generation (Ollama)
    ↓
JSON Response
```

**Example:**
```
Query: "Recommend action movies from 2015"
  → Pattern match: intent=recommend, genre=action, year=2015
  → SQL: SELECT * FROM movies WHERE genres LIKE '%Action%' AND year=2015
  → LLM formats: "Based on 2015 action films, I'd recommend..."
```

### Agent Approach Flow
```
User Query
    ↓
SQL Agent (LangChain)
    ↓
- Analyzes question
- Generates SQL query
- Executes query
- Interprets results
    ↓
Natural Language Response
```

**Example:**
```
Query: "What's the average rating of action movies from the 2000s?"
  → Agent analyzes schema
  → Agent generates: SELECT AVG(vote_average) FROM movies 
                     WHERE genres LIKE '%Action%' 
                     AND year >= 2000 AND year < 2010
  → Agent executes query
  → Returns: "The average rating of action movies from the 2000s is 6.7/10"
```

---

## Design Decisions

### Why Two Approaches?

**Demonstrates:**
- Understanding of trade-offs
- When to use controlled vs autonomous systems
- Practical application of agentic AI
- Production thinking (stable + experimental)

**Production Strategy:**
- Use traditional for common queries (fast, reliable, 90% of traffic)
- Use agent for complex analytical questions (flexible, 10% of traffic)
- Monitor agent performance, promote successful patterns to traditional

---

### RAG Architecture: Database + LLM

**Traditional Approach:**
- Database provides factual, structured movie data
- LLM generates natural, conversational responses
- Clear separation of concerns

**Flow:**
```python
# 1. User query
"Recommend action movies from 2015"

# 2. Parse query (pattern matching)
{intent: "recommend", genre: "action", year: 2015}

# 3. SQL retrieval (controlled)
SELECT * FROM movies WHERE genres LIKE '%action%' AND year = 2015
ORDER BY vote_average DESC LIMIT 5

# 4. Format for LLM
context = format_movies_for_prompt(movies)

# 5. LLM generation
answer = ollama.generate(context + question)

# 6. Return combined result
{answer: LLM_text, movies: SQL_data}
```

---

### Query Processing: Pattern Matching

**Approach:** Simple keyword and regex-based parsing

**Trade-off:**
- ✅ Fast to implement (~30 min)
- ✅ Works for common query patterns
- ✅ No external NLP dependencies
- ✅ Predictable behavior
- ❌ Limited to predefined patterns
- ❌ Doesn't handle complex phrasing

**Production alternative:** Intent classification using proper NLP (Rasa, spaCy) or LLM-based classification

**Code example:**
```python
def parse_query(query: str) -> Dict:
    # Detect intent
    if 'recommend' in query: intent = 'recommend'
    elif 'about' in query: intent = 'describe'
    
    # Extract entities
    genre = match_genre(query)
    year = extract_year(query)
    
    return {intent, genre, year, keywords}
```

---

### LLM: Ollama vs OpenAI

**Chose Ollama because:**
- Runs locally (data privacy)
- No API costs
- Good quality with llama3.2
- Production-viable for enterprises
- No external dependencies

**Trade-off:**
- Response quality slightly below GPT-4
- Requires local compute resources
- First query has ~2-3s initialization
- Depends on hardware (GPU recommended)


---

### Database: Denormalized Schema

**Schema:**
```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    year INTEGER,
    genres TEXT, 
    overview TEXT,
    vote_average REAL,
    vote_count INTEGER,
    movie_cast TEXT,  
    director TEXT
)
```

**Why denormalized:**
- Simpler queries (no JOINs needed)
- Faster to implement
- Sufficient for POC scale (~5K movies)
- Single table easier for SQL agent

**Production:** Would normalize (separate tables for genres, cast) for:
- Data integrity
- Update efficiency
- Reduced redundancy
- Better scaling

**Note:** Renamed `cast` to `movie_cast` to avoid SQL reserved keyword conflict

---

### Agent Safety Mechanisms

**Implemented guardrails:**
```python
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    max_iterations=3,        
    max_execution_time=10,   
    handle_parsing_errors=True
)
```

**Additional safety:**
- Read-only database access (SQLite connection doesn't allow writes)
- Prompt engineering to focus output on final answer
- Error handling and fallbacks
- Logging for monitoring

**Production considerations:**
- Query complexity limits
- Rate limiting per user
- Query cost tracking
- Monitoring and alerting

---

### Single-Turn vs Multi-Turn

**Current:** Stateless, single-turn queries

**Why:**
- ✅ Simpler architecture (no session management)
- ✅ RESTful design
- ✅ Core requirement is DB+LLM combination, not conversation state
- ✅ Easier to scale horizontally

**Next Steps:** Add conversation memory:
```python
# Multi-turn example:
User: "Recommend action movies"
Bot: "Here are great action films..."
User: "What about from 2015?"  # Needs context from previous turn
```

**Implementation:**
- Session IDs for tracking conversations
- Store last 5-10 turns in Redis/memory
- Include relevant context in LLM prompts
- Token limit management for growing context

---

## Improve in next version

**Priority 1: Better Query Understanding**
- Use proper NLP for intent classification (Rasa, spaCy)
- Handle typos and variations (fuzzy matching)
- Entity extraction using NER
- Support complex queries: "action movies like Inception but from 2010s"
- Query understanding feedback loop

**Priority 2: Conversation Memory**
- Session management with unique IDs
- Store conversation history (last 5-10 turns)
- Include relevant context in LLM prompts
- Support follow-up queries
- Context summarization for long conversations

**Priority 3: Caching & Performance**
- Cache frequent queries (Redis)
- Cache LLM responses for identical questions
- Pre-compute popular recommendations
- Reduce latency to <500ms for cached queries
- Monitor cache hit rates

**Priority 4: Query Refinement Loop**
- If no results, automatically relax constraints
- Suggest alternative queries
- "Did you mean..." functionality
- Feedback-driven query improvement
- A/B test query strategies

**Priority 5: Enhanced Agent Capabilities**
- Multi-step reasoning for complex questions
- Tool use (external APIs for trailers, reviews, ratings)
- Query cost optimization
- Result caching for agent queries
- Hybrid: use traditional first, agent as fallback

**Priority 6: Enhanced Responses**
- Streaming responses (SSE) for better UX
- Include movie posters/images (TMDb API)
- Provide similar movie recommendations
- Add user ratings/reviews integration
- Explain why movies were recommended

**Priority 7: Testing & Monitoring**
- Comprehensive test coverage (>80%)
- Integration tests for full pipeline
- Performance benchmarks
- Query analytics and logging
- User feedback collection
- A/B testing framework

**Priority 8: Production Readiness**
- Rate limiting per user/IP
- Authentication/authorization
- Database connection pooling
- Async processing for concurrent requests
- Proper error handling and retries
- Containerization (Docker)
- CI/CD pipeline
- Deployment configuration (K8s)
- Monitoring and alerting (Prometheus, Grafana)

---

## Problems Encountered & Solutions

**Problem 1: TMDB Dataset Column Mismatch**
- Credits CSV uses `movie_id` instead of `id`
- **Solution:** Renamed column during merge: `credits.rename(columns={'movie_id': 'id'})`

**Problem 2: SQL Reserved Keyword**
- `cast` is a reserved SQL keyword, causing syntax errors
- **Solution:** Renamed column to `movie_cast` in database schema

**Problem 3: Genre Matching**
- Users say "sci-fi" but database has "Science Fiction"
- **Solution:** Added mapping in query processor

**Problem 4: LLM Token Limits**
- Full movie data for 5 movies exceeds comfortable context
- **Solution:** Truncate overviews to 200 chars, limit cast to 3 actors

**Problem 5: Query Keyword Extraction**
- Pattern matching extracted irrelevant words ("tell me about inception" → extracted "tell me inception")
- **Solution:** Improved stop word filtering and regex cleaning

**Problem 6: Agent Verbose Output**
- Agent included reasoning steps and SQL queries in responses
- **Solution:** Prompt engineering: "Answer briefly, do not include tool calling information or SQL queries"

**Problem 7: Empty Query Results**
- Strict filters (e.g., "horror movies from 1950") return nothing
- **Solution:** LLM generates helpful "no results" message, suggests broadening search
- **Better solution:** Automatic query relaxation (would add with more time)

---

## Testing

Run tests:
```bash
pytest tests/ -v
```

**Current coverage:**
- ✅ API endpoints (health, query, movie by ID)
- ✅ Traditional query processing
- ✅ Agent endpoint basics
- ✅ Error handling (empty queries, invalid IDs)
- ✅ Both approaches working independently

**Test results:**
```
11 passed in ~25s
- 8 traditional endpoint tests
- 3 agent endpoint tests
```

**Not covered (POC scope):**
- Database edge cases
- Concurrent request handling
- Performance under load
- Agent failure modes

---

## Performance Notes

**Typical latency:**

Traditional endpoint:
- First request: 2-3s (Ollama model initialization)
- Subsequent requests: 1-2s
- Database queries: <50ms

Agent endpoint:
- First request: 4-6s (model + agent initialization)
- Subsequent requests: 3-5s (agent reasoning overhead)
- Database queries: <50ms

**Bottlenecks:**
- Traditional: LLM inference time (~1s)
- Agent: Agent reasoning + LLM inference (~3s)

**Scaling considerations:**
- Database: Add read replicas, caching, indexes
- LLM: GPU acceleration, model warm pools, request batching
- Agent: Query result caching, pattern promotion to traditional
- API: Horizontal scaling (stateless design enables this)

---

## Dataset

**TMDB 5000 Movie Dataset**
- Source: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
- Size: ~5000 movies (filtered to ~4357 with sufficient data)
- Fields: title, year, genres, plot, ratings, cast, director
- License: CC0 Public Domain

**Data Quality:**
- Filtered out movies with <10 votes
- Removed entries with missing titles or overviews
- Merged movies and credits datasets

---

## Tech Stack

- **API:** FastAPI 0.104.1
- **LLM:** Ollama (llama3.2)
- **Agent:** LangChain 0.1.0 with SQL Agent
- **Database:** SQLite3
- **Data Processing:** Pandas 2.1.3
- **Testing:** pytest 7.4.3
- **Python:** 3.11+

---

## Project Structure
```
movie-rag-api/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database queries
│   ├── query_processor.py   # Intent extraction
│   ├── llm_service.py       # Ollama integration
│   ├── agent_service.py     # LangChain SQL Agent (bonus)
│   └── config.py            # Configuration
├── data/
│   ├── load_data.py         # Dataset loader
│   ├── movies.db            # SQLite database
│   └── raw/                 # Raw CSV files
├── tests/
│   └── test_api.py          # API tests
└── examples/
    └── sample_requests.json # Example queries
```

---

## Assumptions

- Single-turn queries (no conversation history)
- English language only
- Local Ollama deployment
- SQLite sufficient for scale (would use PostgreSQL in production)
- Movie data is relatively static (no real-time updates needed)
- Users have basic understanding of movie queries
- Read-only database access (no writes needed)

---

## Acknowledgments

- TMDB for the movie dataset
- Ollama team for local LLM infrastructure
- LangChain for agent frameworks
- FastAPI for excellent API framework

---

## License

MIT

---

## Contact

For questions about this implementation, please see the GitHub repository.