import re
import sqlite3

def parse(question):
    q = question.lower()

    # --- Step 1: Intent ---
    if q.startswith("how many"):
        intent = "COUNT"
    elif q.startswith(("which", "what", "show me")):
        intent = "FIND"
    else:
        intent = "UNKNOWN"

    # --- Step 2: Entities ---
    year_match = re.search(r"\b(19|20)\d{2}\b", q)
    year = int(year_match.group()) if year_match else None

    person = None
    for name in ["nolan", "tarantino", "dicaprio", "mcconaughey"]:
        if name in q:
            person = name.capitalize()
            break

    # --- Step 3: Filter / operator ---
    operator = None
    if "after" in q or "since" in q:
        operator = ">"
    elif "before" in q:
        operator = "<"
    elif "from" in q:
        operator = "="

    # --- Step 4: Relation ---
    if "direct" in q:
        relation = "DIRECTED"
    elif "act" in q:
        relation = "ACTED_IN"
    else:
        relation = None

    return {
        "intent": intent,
        "year": year,
        "operator": operator,
        "person": person,
        "relation": relation,
    }

def to_sql(parsed):
    # Build SQL based on the parsed structure
    if parsed["intent"] == "UNKNOWN":
        return None

    select = "SELECT COUNT(*)" if parsed["intent"] == "COUNT" else "SELECT movies.title"
    from_clause = "FROM movies"
    joins = []
    wheres = []

    if parsed["relation"] == "DIRECTED" and parsed["person"]:
        joins.append("JOIN directed ON movies.id = directed.movie_id")
        joins.append("JOIN directors ON directors.id = directed.director_id")
        wheres.append(f"directors.name LIKE '%{parsed['person']}%'")

    if parsed["relation"] == "ACTED_IN" and parsed["person"]:
        joins.append("JOIN roles ON movies.id = roles.movie_id")
        joins.append("JOIN actors ON actors.id = roles.actor_id")
        wheres.append(f"actors.name LIKE '%{parsed['person']}%'")

    if parsed["year"] and parsed["operator"]:
        wheres.append(f"movies.year {parsed['operator']} {parsed['year']}")

    sql = " ".join([select, from_clause] + joins)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)

    return sql

def run(question):
    parsed = parse(question)
    sql = to_sql(parsed)

    if not sql:
        return "Sorry, I didn't understand that."

    conn = sqlite3.connect("movies.db")
    c = conn.cursor()
    try:
        c.execute(sql)
        result = c.fetchall()
    except Exception as e:
        return f"SQL error: {e}\nGenerated SQL: {sql}"
    finally:
        conn.close()

    return {"sql": sql, "result": result}

# --- Test ---
if __name__ == "__main__":
    tests = [
        "Which movies did Nolan direct after 2010?",
        "How many movies did Nolan direct?",
        "Which movies did DiCaprio act in?",
        "Show me movies from 2014",
    ]
    for t in tests:
        print(f"\nQ: {t}")
        print(run(t))