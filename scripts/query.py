#!/usr/bin/env python3
"""
LLM Wiki Query Tool

Usage:
    python query.py "What is the relationship between cunkou and pulse diagnosis?"
    python query.py --wiki-subdir my-wiki "Your question here"
    python query.py --auto-create "What are the five acupoint types?"
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent

WIKI_DIR = BASE_DIR / "wiki"
WIKI_SUBDIR = "my-wiki"

# LLM Settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

def load_index(wiki_root: Path):
    """Load index.md and return page list."""
    idx_file = wiki_root / "index.md"
    if not idx_file.exists():
        return []
    
    pages = []
    content = idx_file.read_text(encoding="utf-8")
    # Extract markdown table lines with .md links
    for line in content.splitlines():
        match = re.search(r'[|`\s]*([^\s|`]+\.md)', line)
        if match:
            pages.append(match.group(1))
    return pages

def find_relevant_pages(query: str, wiki_root: Path):
    """Simple keyword matching to find relevant pages."""
    all_pages = []
    for md_file in wiki_root.rglob("*.md"):
        # Skip structural files
        if md_file.name in ("index.md", "log.md", "CLAUDE.md"):
            continue
        if md_file.parent.name in ("_search_index", "_maintenance"):
            continue
        
        # Read content
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        
        # Simple keyword overlap score
        query_terms = set(re.findall(r'[\u4e00-\u9fff\w]+', query.lower()))
        content_terms = set(re.findall(r'[\u4e00-\u9fff\w]+', content.lower()))
        
        score = len(query_terms & content_terms)
        if score > 0:
            all_pages.append((score, md_file))
    
    # Sort by relevance
    all_pages.sort(key=lambda x: x[0], reverse=True)
    return all_pages[:5]  # Top 5

def format_context(pages):
    """Format pages into context for LLM."""
    context = []
    for score, page_path in pages:
        try:
            content = page_path.read_text(encoding="utf-8")
            context.append(f"## {page_path.name}\n{content[:2000]}  # truncated")
        except Exception:
            pass
    return "\n\n---\n\n".join(context)

def call_ollama(prompt: str):
    """Call Ollama API."""
    try:
        import ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"[Error] Ollama call failed: {e}"

def query_wiki(query: str, wiki_subdir: str, auto_create: bool = False):
    """Main query workflow."""
    wiki_root = WIKI_DIR / wiki_subdir
    
    if not wiki_root.exists():
        print(f"Error: Wiki '{wiki_subdir}' not found at {wiki_root}")
        return
    
    print(f"[*] Searching for: '{query}'")
    
    # Step 1: Find relevant pages
    relevant = find_relevant_pages(query, wiki_root)
    if not relevant:
        print("[!] No relevant pages found.")
        return
    
    print(f"[*] Found {len(relevant)} relevant page(s):")
    for score, page_path in relevant:
        print(f"    • {page_path.relative_to(wiki_root)} (score: {score})")
    
    # Step 2: Format context
    context = format_context(relevant)
    
    # Step 3: Build prompt
    prompt = f"""You are a query engine for a wiki knowledge base.
Using ONLY the context provided below, answer the user's question.

If the context doesn't contain enough information to answer, say so clearly.
If you generate new knowledge that should be saved to the wiki, output it as a markdown page.

<context>
{context}
</context>

Question: {query}"""

    # Step 4: Call LLM (Ollama by default)
    print("\n[*] Generating answer...")
    response = call_ollama(prompt)
    
    print("\n" + "=" * 60)
    print(response)
    print("=" * 60)
    
    # Step 5: Log
    log_path = wiki_root / "log.md"
    if log_path.exists():
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## [{datetime.now().strftime('%Y-%m-%d')}] query | {query}\n")
            f.write(f"- Pages consulted: {', '.join([p[1].name for p in relevant])}\n")

def main():
    parser = argparse.ArgumentParser(description="LLM Wiki Query Tool")
    parser.add_argument("query", type=str, nargs="?", help="Question to ask")
    parser.add_argument("--wiki-subdir", type=str, default=os.getenv("WIKI_SUBDIR", "my-wiki"))
    parser.add_argument("--auto-create", action="store_true", help="Auto-create new wiki page from answer")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("Wiki Query Interactive Mode (Ctrl+D to exit)")
        print(f"Target wiki: {WIKI_DIR / args.wiki_subdir}")
        while True:
            try:
                q = input("\n> ")
                if q.strip():
                    query_wiki(q, args.wiki_subdir, args.auto_create)
            except (EOFError, KeyboardInterrupt):
                break
    elif args.query:
        query_wiki(args.query, args.wiki_subdir, args.auto_create)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
