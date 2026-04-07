#!/usr/bin/env python3
"""
Improved LLM Wiki Pipeline
Features:
- Windows path compatibility
- Multi-format support (PDF, DOCX, Markdown, TXT)
- OCR Warning (if text extraction fails for PDF)
- Better error handling & robust CLI
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============== Configuration ==============
SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent.resolve()

# Defaults (can be overridden by CLI)
RAW_DIR = BASE_DIR / "raw"
WIKI_DIR = BASE_DIR / "wiki"
PROMPT_PATH = BASE_DIR / "prompts" / "wiki_builder.md"
STATE_FILE = SCRIPT_DIR / ".pipeline_state.json"

# LLM Settings
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SUPPORTED_EXTENSIONS = {".md", ".txt", ".py", ".json", ".csv", ".tsv", ".pdf", ".docx"}

# ============== File Readers ==============
def extract_text(file_path: Path) -> Tuple[str, bool]:
    """
    Extract text from file. Returns (text, is_success).
    Handles PDF, DOCX, and text files.
    """
    suffix = file_path.suffix.lower()
    
    if suffix in [".md", ".txt"]:
        try:
            return file_path.read_text(encoding="utf-8"), True
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding="gbk"), True
            except Exception:
                print(f"    [WARN] Failed to decode {file_path.name}, skipping.")
                return "", False

    elif suffix == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            text = text.strip()
            if not text:
                print(f"    [WARN] No text extracted from PDF (may be scanned/image-only). Skipping auto-ingest.")
                return "", False
            return text, True
        except ImportError:
            print(f"    [WARN] Missing 'pdfplumber'. Install it to process PDFs.")
            return "", False

    elif suffix == ".docx":
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            if not text:
                print(f"    [WARN] Empty DOCX content: {file_path.name}")
                return "", False
            return text, True
        except ImportError:
            print(f"    [WARN] Missing 'python-docx'. Install it to process DOCX files.")
            return "", False
        except Exception as e:
            print(f"    [ERROR] Failed to parse DOCX: {e}")
            return "", False

    else:
        # Fallback for other text files
        try:
            return file_path.read_text(encoding="utf-8"), True
        except Exception:
            return "", False

# ============== LLM Integration ==============
def call_llm(prompt: str) -> Optional[str]:
    """Call LLM based on configured backend."""
    if LLM_BACKEND == "openai":
        if not OPENAI_API_KEY:
            print("    [ERROR] OPENAI_API_KEY not set.")
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"    [ERROR] OpenAI call failed: {e}")
            return None

    elif LLM_BACKEND == "anthropic":
        if not ANTHROPIC_API_KEY:
            print("    [ERROR] ANTHROPIC_API_KEY not set.")
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"    [ERROR] Anthropic call failed: {e}")
            return None

    elif LLM_BACKEND == "ollama":
        try:
            import ollama
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            print(f"    [ERROR] Ollama call failed (is Ollama running?): {e}")
            return None
    
    else:
        print(f"    [ERROR] Unknown backend: {LLM_BACKEND}")
        return None

# ============== Pipeline Core ==============
def build_ingest_prompt(text: str, prompt_template: Path) -> Optional[str]:
    """Construct the ingestion prompt."""
    if not prompt_template.exists():
        print(f"    [WARN] Prompt template not found at {prompt_template}. Using basic prompt.")
        return f"Analyze this document and output a YAML front matter and summary:\n\n{text}"
    
    template = prompt_template.read_text(encoding="utf-8")
    return template.replace("{{NEW_DOCUMENT}}", text).replace("{{EXISTING_CONCEPTS}}", "None yet (fresh wiki)")

def process_single_file(file_path: Path, wiki_dir: Path, dry_run=False):
    """Process a single file and generate wiki pages."""
    print(f"\n{'─'*40}")
    print(f"[->] {file_path.relative_to(BASE_DIR)}")
    
    # 1. Extract text
    text, success = extract_text(file_path)
    if not success:
        print(f"    [SKIP] Could not extract text or file empty.")
        return False

    # 2. Build Prompt
    prompt = build_ingest_prompt(text, PROMPT_PATH)
    if dry_run:
        print(f"    [DRY] Would generate prompt with {len(text)} chars.")
        return True

    # 3. Call LLM
    print(f"    [*] Calling {LLM_BACKEND}...")
    result = call_llm(prompt)
    if not result:
        print(f"    [FAIL] LLM returned empty/error.")
        return False

    # 4. Parse Response & Save (Simplified: just saves output to a file for now)
    # A full implementation would parse the Markdown output and create files.
    # Here we save the LLM output to the wiki pages directory for review.
    target_dir = wiki_dir / "pages" / "raw_ingest"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = target_dir / f"{file_path.stem}_output.md"
    out_file.write_text(result, encoding="utf-8")
    print(f"    [OK] Saved LLM output to {out_file.relative_to(BASE_DIR)}")
    return True

def run_pipeline(wiki_subdir: str, wiki_dir: Path, raw_dir: Path, dry_run=False):
    """Main pipeline loop."""
    # Find files in raw/
    files_to_process = []
    if raw_dir.exists():
        for ext in SUPPORTED_EXTENSIONS:
            files_to_process.extend(list(raw_dir.rglob(f"*{ext}")))
    
    if not files_to_process:
        print("[*] No files found in raw/ directory.")
        return

    print(f"[*] Found {len(files_to_process)} file(s) to process.")
    
    for f in files_to_process:
        process_single_file(f, wiki_dir, dry_run)

def init_wiki(wiki_dir: Path, wiki_subdir: str):
    """Initialize wiki structure."""
    target = wiki_dir / wiki_subdir
    if target.exists():
        print(f"[!] Wiki '{wiki_subdir}' already exists at {target}")
        return
    print(f"[*] Initializing wiki '{wiki_subdir}'...")
    
    # Create directories
    for d in ["pages/entities", "pages/concepts", "pages/references", "categories", "_maintenance", "_search_index"]:
        (target / d).mkdir(parents=True, exist_ok=True)
    
    # Create initial files
    (target / "log.md").write_text("# Change Log\n\n> Append-only.\n\n", encoding="utf-8")
    
    idx_content = f"# {wiki_subdir} Knowledge Base\n\n> Auto-generated.\n\n## Statistics\n- Last updated: {datetime.now().strftime('%Y-%m-%d')}\n"
    (target / "index.md").write_text(idx_content, encoding="utf-8")
    print("[OK] Wiki initialized.")

# ============== CLI ==============
def main():
    parser = argparse.ArgumentParser(description="LLM Wiki Pipeline")
    parser.add_argument("--wiki-dir", type=str, default=None, help="Path to wiki directory (default: ../wiki)")
    parser.add_argument("--raw-dir", type=str, default=None, help="Path to raw directory (default: ../raw)")
    parser.add_argument("--wiki-subdir", type=str, default="my-wiki", help="Subdirectory for the wiki topic")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--init", action="store_true", help="Initialize wiki structure")
    # LLM args
    parser.add_argument("--backend", type=str, choices=["ollama", "openai", "anthropic"], default=None)
    parser.add_argument("--prompt", type=str, default=None, help="Path to prompt file")

    args = parser.parse_args()

    # Update globals
    global WIKI_DIR, RAW_DIR, PROMPT_PATH
    WIKI_DIR = Path(args.wiki_dir).resolve() if args.wiki_dir else BASE_DIR / "wiki"
    RAW_DIR = Path(args.raw_dir).resolve() if args.raw_dir else BASE_DIR / "raw"
    if args.prompt:
        PROMPT_PATH = Path(args.prompt)
    if args.backend:
        global LLM_BACKEND
        LLM_BACKEND = args.backend

    # Target wiki
    target_wiki = WIKI_DIR / args.wiki_subdir
    target_wiki.mkdir(exist_ok=True, parents=True)

    if args.init:
        init_wiki(WIKI_DIR, args.wiki_subdir)
    else:
        run_pipeline(args.wiki_subdir, target_wiki, RAW_DIR, args.dry_run)

if __name__ == "__main__":
    main()
