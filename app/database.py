import sqlite3
import json
from typing import List, Dict, Optional
from app.config import DATABASE_PATH


class MovieDB:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def search(
        self,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        min_rating: float = 0.0,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search movies with optional filters
        """
        conn = self._get_connection()
        
        query = """
            SELECT id, title, year, genres, overview, 
                vote_average, vote_count, movie_cast, director
            FROM movies 
            WHERE vote_average >= ?
        """
        params = [min_rating]
        
        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        
        if genre:
            query += " AND genres LIKE ?"
            params.append(f"%{genre}%")
        
        if year:
            query += " AND year = ?"
            params.append(year)
        
        query += " ORDER BY vote_average DESC, vote_count DESC LIMIT ?"
        params.append(limit)
        
        # DEBUG: Print query
        print("DEBUG Query:", query)
        print("DEBUG Params:", params)
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse JSON fields
        for movie in results:
            for field in ['genres', 'movie_cast']:
                if movie.get(field):
                    try:
                        movie[field] = json.loads(movie[field])
                    except:
                        movie[field] = []
        
        return results
    
    def get_by_id(self, movie_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.execute(
            'SELECT id, title, year, genres, overview, vote_average, vote_count, movie_cast, director FROM movies WHERE id = ?',
            (movie_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        movie = dict(row)
        for field in ['genres', 'movie_cast']:
            if movie.get(field):
                try:
                    movie[field] = json.loads(movie[field])
                except:
                    movie[field] = []
        
        return movie
        
    def get_top_rated(self, limit: int = 10, min_votes: int = 100) -> List[Dict]:
        """Get top rated movies with minimum vote threshold"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT id, title, year, genres, overview, vote_average, vote_count, movie_cast, director
            FROM movies
            WHERE vote_count >= ?
            ORDER BY vote_average DESC, vote_count DESC
            LIMIT ?
        """, (min_votes, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        for movie in results:
            for field in ['genres', 'movie_cast']:
                if movie.get(field):
                    try:
                        movie[field] = json.loads(movie[field])
                    except:
                        movie[field] = []
        
        return results