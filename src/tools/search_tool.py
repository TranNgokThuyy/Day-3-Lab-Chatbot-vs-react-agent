import os
import re
from typing import List

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def search_documents(query: str, top_k: int = 3) -> str:
    """
    Simple keyword-based search over text documents in `src/tools/docs/`.
    Returns a short ranked list of matching files with snippets.
    """
    query = query.lower().strip()
    if not os.path.exists(DOCS_DIR):
        return "No documents directory found. Add text files under src/tools/docs/."

    tokens = [token for token in re.findall(r"[a-z0-9ç]+", query) if len(token) > 2]
    if not tokens:
        return "Query is too short to search. Please provide a longer query."

    results = []
    for fname in os.listdir(DOCS_DIR):
        path = os.path.join(DOCS_DIR, fname)
        if not os.path.isfile(path):
            continue
        text = _read_file(path).lower()
        score = 0
        snippets = []

        for token in tokens:
            for match in re.finditer(re.escape(token), text):
                score += 1
                if len(snippets) < 2:
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    snippet = text[start:end].replace("\n", " ")
                    snippets.append(snippet)

        if score > 0:
            results.append((score, fname, snippets))

    if not results:
        return f"No documents matched the query '{query}'."

    results.sort(key=lambda x: x[0], reverse=True)
    out_lines: List[str] = []
    for score, fname, snippets in results[:top_k]:
        out_lines.append(f"File: {fname} (matches={score})")
        for s in snippets[:2]:
            out_lines.append(f"  - ...{s}...")

    return "\n".join(out_lines)
