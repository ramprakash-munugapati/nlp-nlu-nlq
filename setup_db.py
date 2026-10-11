import sqlite3

conn = sqlite3.connect("movies.db")
c = conn.cursor()

c.executescript("""
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS directors;
DROP TABLE IF EXISTS directed;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS actors;
DROP TABLE IF EXISTS roles;

CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    year INTEGER,
    genre TEXT
);

CREATE TABLE directors (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE directed (
    movie_id INTEGER,
    director_id INTEGER
);

CREATE TABLE ratings (
    movie_id INTEGER,
    rating REAL
);

CREATE TABLE actors (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE roles (
    movie_id INTEGER,
    actor_id INTEGER,
    role_name TEXT
);

INSERT INTO movies VALUES
(1, 'Inception', 2010, 'Sci-Fi'),
(2, 'Interstellar', 2014, 'Sci-Fi'),
(3, 'Dunkirk', 2017, 'War'),
(4, 'Tenet', 2020, 'Sci-Fi'),
(5, 'The Dark Knight', 2008, 'Action'),
(6, 'Pulp Fiction', 1994, 'Crime');

INSERT INTO directors VALUES
(1, 'Christopher Nolan'),
(2, 'Quentin Tarantino');

INSERT INTO directed VALUES
(1,1),(2,1),(3,1),(4,1),(5,1),(6,2);

INSERT INTO ratings VALUES
(1,8.8),(2,8.6),(3,7.8),(4,7.3),(5,9.0),(6,8.9);

INSERT INTO actors VALUES
(1, 'Leonardo DiCaprio'),
(2, 'Joseph Gordon-Levitt'),
(3, 'Matthew McConaughey'),
(4, 'John Travolta');

INSERT INTO roles VALUES
(1,1,'Cobb'),(1,2,'Arthur'),(2,3,'Cooper'),(6,4,'Vincent');
""")

conn.commit()
conn.close()
print("Database ready.")