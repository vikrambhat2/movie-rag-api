"""
LangChain SQL Agent for autonomous query generation
"""

import logging
from typing import Dict
from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from app.config import DATABASE_PATH, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# Database and LLM setup
db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_PATH}")
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
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
    """Run the SQL agent on a natural language question."""
    try:
        logger.info(f"Agent processing: {question}")
        updated_question = (
            "Answer concisely (1-2 sentences). "
            "Do not include SQL or reasoning steps.\n\n"
            f"Question: {question}"
        )
        result = agent.invoke({"input": updated_question})
        return {
            "answer": result.get('output', 'No response generated'),
            "method": "sql_agent",
            "note": "Autonomous SQL agent response"
        }
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "answer": "Agent encountered an error. Try rephrasing your question.",
            "method": "agent_error",
            "error": str(e)
        }

def get_agent_info() -> Dict:
    """Return database tables and schema."""
    try:
        return {
            "tables": db.get_usable_table_names(),
            "schema": db.get_table_info()
        }
    except Exception as e:
        return {"error": str(e)}
