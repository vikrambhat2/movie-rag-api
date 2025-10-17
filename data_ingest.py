# data_ingest.py
import csv
from models import Movie, Genre, get_session_factory
from sqlalchemy.exc import IntegrityError
import argparse
import os

Session = get_session_factory()

def ingest_movielens(movies_csv_path, ratings_csv_path):
    session = Session()
    # Load genres map
    genre_objs = {}
    with open(movies_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # movies.csv columns: movieId,title,genres
        for row in reader:
            title_raw = row['title']
            # MovieLens title often contains year in parentheses, extract
            year = None
            title = title_raw
            if title_raw.endswith(')'):
                try:
                    idx = title_raw.rfind('(')
                    year = int(title_raw[idx+1:-1])
                    title = title_raw[:idx].strip()
                except:
                    pass
            genres = row['genres'].split('|') if row['genres'] else []
            m = Movie(title=title, year=year, overview=None)
            # attach genre objects
            for g in genres:
                if g == '(no genres listed)':
                    continue
                if g not in genre_objs:
                    genre_obj = Genre(name=g)
                    session.add(genre_obj)
                    genre_objs[g] = genre_obj
                m.genres.append(genre_objs[g])
            session.add(m)
    session.commit()

    # Ratings aggregation
    # ratings.csv: userId,movieId,rating,timestamp
    from collections import defaultdict
    sums = defaultdict(float)
    counts = defaultdict(int)
    # Need movieId->Movie.id mapping: but MovieLens movieId ordering is not necessarily same as autoincrement
    # For simplicity, create a map from title to Movie objects earlier — safer to update by reading movies again
    # We'll build a mapping from MovieLens movieId to SQL title using movies.csv again
    movieid_to_title = {}
    with open(movies_csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            movieid_to_title[row['movieId']] = row['title']

    with open(ratings_csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            mid = row['movieId']
            rating = float(row['rating'])
            sums[mid] += rating
            counts[mid] += 1

    # Apply to DB
    # naive match by title (lost year may cause duplicates but acceptable for POC)
    for mid, total in sums.items():
        cnt = counts[mid]
        raw_title = movieid_to_title.get(mid)
        if not raw_title:
            continue
        # extract title text
        title = raw_title
        if raw_title.endswith(')'):
            try:
                idx = raw_title.rfind('(')
                title = raw_title[:idx].strip()
            except:
                pass
        avg = total / cnt
        # find first matching movie record
        db_movie = session.query(Movie).filter(Movie.title == title).first()
        if db_movie:
            db_movie.avg_rating = avg
            db_movie.rating_count = cnt
    session.commit()
    session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True, help="path to movies.csv")
    parser.add_argument("--ratings", required=True, help="path to ratings.csv")
    args = parser.parse_args()
    ingest_movielens(args.movies, args.ratings)
    print("Ingest complete.")
