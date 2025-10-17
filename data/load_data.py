"""
Load TMDB 5000 dataset into SQLite
Download from: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
"""

import pandas as pd
import sqlite3
import json
from pathlib import Path

DB_PATH = "data/movies.db"
RAW_DATA_PATH = "data/raw/tmdb_5000_movies.csv"
CREDITS_PATH = "data/raw/tmdb_5000_credits.csv"


def extract_names(json_str, key='name', limit=5):
    """Extract names from JSON string"""
    if pd.isna(json_str):
        return None
    try:
        items = json.loads(json_str)
        names = [item.get(key, '') for item in items[:limit]]
        return json.dumps(names) if names else None
    except:
        return None


def extract_director(crew_json):
    """Get director from crew JSON"""
    if pd.isna(crew_json):
        return None
    try:
        crew = json.loads(crew_json)
        directors = [person['name'] for person in crew if person.get('job') == 'Director']
        return directors[0] if directors else None
    except:
        return None


def load_tmdb_data():
    print(f"Loading data from {RAW_DATA_PATH}")
    
    movies = pd.read_csv(RAW_DATA_PATH)
    credits = pd.read_csv(CREDITS_PATH)
    credits_upd = credits.rename(columns={'movie_id': 'id'})

    df = movies.merge(credits_upd[['id', 'cast', 'crew']], on='id', how='left')

    
    
    # Clean and transform
    df['genres'] = df['genres'].apply(lambda x: extract_names(x, 'name'))
    df['movie_cast'] = df['cast'].apply(lambda x: extract_names(x, 'name', limit=5))
    df['director'] = df['crew'].apply(extract_director)
    df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    
    # Select relevant columns
    df = df[[
        'id', 'title', 'year', 'genres', 'overview', 
        'vote_average', 'vote_count', 'movie_cast', 'director'
    ]]
    
    # Filter out movies with missing critical data
    df = df.dropna(subset=['title', 'overview'])
    df = df[df['vote_count'] > 10]  # Filter low-quality entries
    
    print(f"Processed {len(df)} movies")
    return df


def create_database(df):
    Path("data").mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER,
            genres TEXT,
            overview TEXT,
            vote_average REAL,
            vote_count INTEGER,
            movie_cast TEXT,
            director TEXT
        )
    """)
    
    # Create indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON movies(title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON movies(year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON movies(vote_average DESC)")
    
    # Load data
    df.to_sql('movies', conn, if_exists='replace', index=False)
    
    count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    print(f"Loaded {count} movies into {DB_PATH}")
    
    conn.close()


if __name__ == "__main__":
    if not Path(RAW_DATA_PATH).exists():
        print(f"Error: {RAW_DATA_PATH} not found")
        print("Download TMDB 5000 dataset from Kaggle and place in data/raw/")
        exit(1)
    
    df = load_tmdb_data()
    create_database(df)
    print("Done!")