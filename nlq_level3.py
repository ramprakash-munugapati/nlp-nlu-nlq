import os
import re
import requests
import sqlite3
from pathlib import Path

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1").rstrip("/")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "liquid/lfm2.5-1.2b")
DATABASE_PATH = Path(__file__).resolve().with_name("movies.db")

SCHEMA = """
Tables:
- movies(id, title, year, genre)
- directors(id, name)
- directed(movie_id, director_id)
- ratings(movie_id, rating)
- actors(id, name)
- roles(movie_id, actor_id, role_name)
"""

def generate_sql(question):
    system_prompt = f"""You are a SQLite query generator. Use only this schema:

{SCHEMA}

Rules:
- Only use tables and columns from the schema above.
- Return exactly one read-only SELECT query, no explanation or Markdown.
- Use proper JOINs.
- When the question gives a partial person name or surname, match with LIKE, such as directors.name LIKE '%Nolan%'.
- For ratings, join ratings.movie_id to movies.id; do not invent columns.
- If a person directs a movie, join movies -> directed -> directors and filter directors.name.
- If a person acts in a movie, join movies -> roles -> actors and filter actors.name.
- A person's name is never a movie genre; only filter genre when the question names a genre.
- directed has exactly movie_id and director_id; it has no id column.
- Join directors with directed.director_id = directors.id; movies has no director_id column.

Example:
Question: Which movies did Nolan direct after 2010?
SQL: SELECT movies.title FROM movies JOIN directed ON movies.id = directed.movie_id
JOIN directors ON directed.director_id = directors.id
WHERE directors.name LIKE '%Nolan%' AND movies.year > 2010;

Question: What's the highest rated Nolan movie?
SQL: SELECT movies.title, ratings.rating FROM movies
JOIN directed ON movies.id = directed.movie_id
JOIN directors ON directed.director_id = directors.id
JOIN ratings ON ratings.movie_id = movies.id
WHERE directors.name LIKE '%Nolan%'
ORDER BY ratings.rating DESC LIMIT 1;
"""
    try:
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            json={
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "temperature": 0,
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except requests.HTTPError as exc:
        response = exc.response
        if response is None:
            raise RuntimeError(f"LM Studio returned an HTTP error: {exc}") from exc

        detail = response.text.strip()[:500]
        if response.status_code == 400 and '"terminated"' in detail:
            raise RuntimeError(
                f"LM Studio terminated model '{LM_STUDIO_MODEL}' while generating a response. "
                "Check the LM Studio logs for the model failure."
            ) from exc
        raise RuntimeError(
            f"LM Studio returned HTTP {response.status_code} for model "
            f"'{LM_STUDIO_MODEL}': {detail or response.reason}"
        ) from exc
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise RuntimeError(
            f"Could not connect to LM Studio at {LM_STUDIO_BASE_URL}. "
            "Start the LM Studio server and load the configured model."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"LM Studio request failed: {exc}") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LM Studio returned an invalid chat-completions response.") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LM Studio returned an empty SQL response.")

    sql = content.strip()
    fenced_sql = re.fullmatch(r"```(?:sql)?\s*(.*?)\s*```", sql, re.IGNORECASE | re.DOTALL)
    if fenced_sql:
        sql = fenced_sql.group(1).strip()

    return sql


def _validate_read_only_sql(sql):
    statement = re.sub(r"/\*.*?\*/|--[^\r\n]*", "", sql, flags=re.DOTALL).lstrip()
    if not re.match(r"(SELECT|WITH)\b", statement, re.IGNORECASE):
        raise ValueError("The model must return a read-only SELECT query.")

def run(question):
    sql = generate_sql(question)
    database_uri = f"{DATABASE_PATH.as_uri()}?mode=ro"
    conn = sqlite3.connect(database_uri, uri=True)
    try:
        for attempt in range(3):
            _validate_read_only_sql(sql)
            try:
                c = conn.cursor()
                c.execute(sql)
                result = c.fetchall()
                break
            except sqlite3.Error as exc:
                if attempt == 2:
                    raise RuntimeError(
                        f"Generated SQL failed after correction attempts: {exc}\nSQL: {sql}"
                    ) from exc
                sql = generate_sql(
                    f"""Fix this failed SQL for the original question: {question}
SQLite error: {exc}
Failed SQL: {sql}
Use exactly these relationships: directed.movie_id = movies.id and
directed.director_id = directors.id. The directed table has no id column;
movies has no director_id column. Match partial names with LIKE.
Return one corrected SELECT query only.
"""
                )
    finally:
        conn.close()
    return {"sql": sql, "result": result}

if __name__ == "__main__":
    try:
        print(run("Which movies did Nolan direct after 2010?"))
        print(run("What's the highest rated Nolan movie?"))
    except (RuntimeError, sqlite3.Error, ValueError) as exc:
        raise SystemExit(str(exc)) from exc