"""
SQL Agent implementation using LangChain
Alternative approach demonstrating autonomous query generation
"""

from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Dict
import logging

from app.config import DATABASE_PATH, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# Initialize database connection
db_uri = f"sqlite:///{DATABASE_PATH}"
db = SQLDatabase.from_uri(db_uri)

# Initialize LLM
llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=0 
)

# Create toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create agent with safety constraints
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=False,
    agent_type="tool-calling",
    handle_parsing_errors=True,
    max_iterations=3,  
    max_execution_time=10  
)


def query_with_agent(question: str) -> Dict:
    """
    Use SQL Agent for autonomous query generation
    
    Agent can generate and execute SQL queries based on natural language.
    More flexible but less predictable than traditional approach.
    """
    try:
        logger.info(f"Agent processing: {question}")
        
        updated_question = (
            "Answer this question concisely in 1-2 sentences. "
            "Do not include SQL queries, tool calls, or reasoning steps in your answer. "
            "Only provide the final answer.\n\n"
            f"Question: {question}"
        )
        # Run agent
        result = agent.invoke({"input": updated_question})
        
        # Extract answer
        answer = result.get('output', 'No response generated')
        
        return {
            "answer": answer,
            "method": "sql_agent",
            "note": "Response generated via autonomous SQL agent"
        }
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "answer": f"Agent encountered an error. Please try rephrasing your question.",
            "method": "agent_error",
            "error": str(e)
        }


def get_agent_info() -> Dict:
    """Get information about available database tables and schema"""
    try:
        table_info = db.get_table_info()
        return {
            "tables": db.get_usable_table_names(),
            "schema": table_info
        }
    except Exception as e:
        return {"error": str(e)}