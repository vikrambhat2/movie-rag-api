from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "endpoints" in response.json()


def test_query_endpoint_basic():
    response = client.post(
        "/query",
        json={"question": "Tell me about Inception"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "movies" in data
    assert "query_info" in data
    assert isinstance(data["movies"], list)


def test_query_with_genre_filter():
    response = client.post(
        "/query",
        json={"question": "Recommend action movies"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_info"]["genre"] == "action"
    assert data["query_info"]["intent"] == "recommend"


def test_query_with_year():
    response = client.post(
        "/query",
        json={"question": "Show me movies from 2015"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_info"]["year"] == 2015


def test_empty_query():
    response = client.post(
        "/query",
        json={"question": ""}
    )
    assert response.status_code == 400


def test_movie_by_id():
    # Assuming movie with id 1 exists
    response = client.get("/movies/1")
    if response.status_code == 200:
        data = response.json()
        assert "title" in data
        assert "year" in data


def test_movie_not_found():
    response = client.get("/movies/999999")
    assert response.status_code == 404

# ========== Agent Endpoint Tests (Bonus Feature) ==========

def test_agent_endpoint_basic():
    """Test agent endpoint works with simple query"""
    response = client.post(
        "/query/agent",
        json={"question": "How many movies were released in 2015?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["method"] == "sql_agent"
    # Should contain a number in the answer
    assert any(char.isdigit() for char in data["answer"])


def test_agent_vs_traditional():
    """Verify both endpoints work independently"""
    # Traditional
    trad = client.post("/query", json={"question": "Recommend action movies"})
    assert trad.status_code == 200
    assert "movies" in trad.json()
    
    # Agent
    agent = client.post("/query/agent", json={"question": "How many action movies are there?"})
    assert agent.status_code == 200
    assert "answer" in agent.json()


def test_agent_info():
    """Test agent info endpoint"""
    response = client.get("/agent/info")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data or "error" in data