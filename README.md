# LLM Wiki Builder

> Build and maintain a personal LLM Wiki knowledge base using the Karpathy three-layer architecture.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this?

An operational toolkit for building a **persistent, compounding knowledge base** using LLMs. Unlike traditional RAG (which re-reads raw documents on every query), this system has the LLM incrementally build and maintain a structured wiki that gets smarter with every source you add.

**Inspired by [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** and refined through production use.

## Architecture

```
Layer 3: Schema (CLAUDE.md)        ← Defines conventions, templates, rules
Layer 2: The Wiki (Markdown pages) ← LLM-maintained, cross-linked knowledge
Layer 1: Raw Sources (raw/)        ← Immutable original files (PDFs, docs, notes)
```

## Quick Start

### 1. Setup

```bash
# Initialize a new wiki
python scripts/pipeline.py --init --wiki-subdir my-topic

# Configure LLM backend
cp .env.example .env
# Edit .env with your API keys or set LLM_BACKEND=ollama
```

### 2. Ingest

```bash
# Drop files into raw/ and run the pipeline
python scripts/pipeline.py

# Or with specific options
python scripts/pipeline.py --backend openai --wiki-subdir my-topic --dry-run
```

### 3. Query

```bash
# Ask questions about your wiki
python scripts/query.py "What is X?" --wiki-subdir my-wiki

# Interactive mode
python scripts/query.py --interactive
```

### 4. Health Check

```bash
# Check wiki integrity
python scripts/health_check.py --wiki-subdir my-topic --update-index

# Quick check (links only)
python scripts/health_check.py --quick
```

## Supported Formats

| Format | Extension | Method |
|--------|-----------|--------|
| Markdown | `.md` | Direct read |
| Plain Text | `.txt` | Direct read |
| PDF (text) | `.pdf` | `pdfplumber` |
| PDF (scanned) | `.pdf` | ⚠️ Needs OCR (see below) |
| Word | `.docx` | `python-docx` |

## Dependencies

```bash
pip install pdfplumber python-docx python-dotenv ollama openai anthropic
```

## Scanned PDF Support

If your PDFs are image-only scans, install OCR:

```bash
pip install paddleocr pdf2image
```

The pipeline will fall back to OCR automatically (if configured).

## Directory Structure

```
llm-wiki-builder/
├── SKILL.md              ← Agent instructions
├── .env.example          ← Configuration template
├── scripts/
│   ├── pipeline.py       ← Ingestion pipeline (watch, status, dry-run)
│   ├── health_check.py   ← Wiki health checker (links, front matter, orphans)
│   ├── query.py          ← NEW: Query your wiki with LLM
│   └── ocr_fallback.py   ← NEW: OCR for scanned PDFs
├── references/
│   ├── CLAUDE_template.md
│   ├── architecture.md
│   ├── page_templates.md
│   └── wiki_builder_prompt.md
├── raw/
│   ├── documents/        ← Source files
│   ├── notes/            ← Markdown/TXT notes
│   └── data/             ← Structured data
└── wiki/
    └── <topic>/          ← Your knowledge base
```

## Contributing

Issues and PRs welcome. This is an evolving toolkit.

## Credits

- Core concept: Karpathy's LLM Wiki pattern
- Implementation: Community contributions
- Inspiration: Obsidian Zettelkasten, Roam Research, Notion AI
