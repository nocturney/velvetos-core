#!/usr/bin/env python3
"""
vf_semantic_search.py — Local TF-IDF semantic search over VelvetOS Markdown.
No network calls, no paid API, no MCP server. Builds an index over every
.md file in packages/ + constitution/ + docs/, and answers free-text
Hebrew/English queries by cosine similarity.

Usage:
    python3 vf_semantic_search.py --build
    python3 vf_semantic_search.py "who sends instagram posts"
"""
import argparse, pickle, re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[3]
SCAN_DIRS = ["packages", "constitution", "docs"]
INDEX_PATH = ROOT / "packages" / "vfmem" / "semantic_index.pkl"

def collect_chunks():
    chunks = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            sections = re.split(r"\n(?=#{1,3}\s)", text)
            for sec in sections:
                sec = sec.strip()
                if len(sec) < 40:
                    continue
                chunks.append({"path": str(path.relative_to(ROOT)), "text": sec[:800]})
    return chunks

def build_index():
    chunks = collect_chunks()
    corpus = [c["text"] for c in chunks]
    vec = TfidfVectorizer(max_features=20000, ngram_range=(1, 2))
    matrix = vec.fit_transform(corpus)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"vectorizer": vec, "matrix": matrix, "chunks": chunks}, f)
    print(f"indexed {len(chunks)} chunks -> {INDEX_PATH}")

def query(text, top_k=5):
    if not INDEX_PATH.exists():
        print("no index found — run with --build first")
        return []
    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)
    vec, matrix, chunks = data["vectorizer"], data["matrix"], data["chunks"]
    q = vec.transform([text])
    sims = cosine_similarity(q, matrix)[0]
    ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]
    results = []
    for i in ranked:
        if sims[i] <= 0:
            continue
        results.append({"score": round(float(sims[i]), 4), "path": chunks[i]["path"],
                         "snippet": chunks[i]["text"][:220].replace("\n", " ")})
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default=None)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    if args.build or not INDEX_PATH.exists():
        build_index()
        if not args.query:
            return
    if args.query:
        results = query(args.query, args.top)
        if not results:
            print("no matches above zero similarity")
        for r in results:
            print(f"[{r['score']}] {r['path']}")
            print(f"    {r['snippet']}")

if __name__ == "__main__":
    main()
