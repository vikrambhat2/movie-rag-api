# models.py
from sqlalchemy import (
    Column, Integer, String, Float, Table, ForeignKey, create_engine, Text
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

movie_genre = Table(
    'movie_genre', Base.metadata,
    Column('movie_id', ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', ForeignKey('genres.id'), primary_key=True)
)

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    year = Column(Integer, index=True)
    overview = Column(Text)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    director = Column(String, nullable=True)
    cast = Column(Text, nullable=True)  # comma-separated simple approach

    genres = relationship('Genre', secondary=movie_genre, back_populates='movies')

class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)

    movies = relationship('Movie', secondary=movie_genre, back_populates='genres')

def create_db(db_url="sqlite:///./movies.db"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine

# Session factory
def get_session_factory(db_url="sqlite:///./movies.db"):
    engine = create_db(db_url)
    return sessionmaker(bind=engine)
