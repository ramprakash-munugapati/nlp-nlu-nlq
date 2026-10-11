import spacy
import sqlite3

try:
    nlp = spacy.load("en_core_web_sm")
except OSError as exc:
    raise SystemExit(
        "spaCy's English model is missing. Install it with: "
        "python -m spacy download en_core_web_sm"
    ) from exc

def parse(question):
    doc = nlp(question)

    # NER: find people, dates
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # POS-based relation detection: find the main verb
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

    # Numeric years
    years = [int(t.text) for t in doc if t.text.isdigit() and len(t.text) == 4]

    return {
        "persons": persons,
        "dates": dates,
        "verbs": verbs,
        "years": years,
        "doc": doc,
    }

if __name__ == "__main__":
    q = "Which movies did Christopher Nolan direct after 2010?"
    result = parse(q)
    print("Persons:", result["persons"])
    print("Verbs:", result["verbs"])
    print("Years:", result["years"])

    # Show dependency tree
    for token in result["doc"]:
        print(f"{token.text:15} {token.pos_:8} {token.dep_:10} -> {token.head.text}")