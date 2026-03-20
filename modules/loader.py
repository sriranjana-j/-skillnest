import json, os

def load_questions(domain):
    path = os.path.join("data", f"{domain}.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except UnicodeDecodeError:
        # Fallback for files saved with BOM or alternate editors.
        with open(path, "r", encoding="utf-8-sig") as file:
            return json.load(file)
