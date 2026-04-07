# Three-Layer Architecture

## Overview

The LLM Wiki follows a strict three-layer architecture, inspired by software engineering's separation of concerns:

```
┌─────────────────────────────────────────────┐
│  Layer 3: Schema (CLAUDE.md)               │
│  Defines conventions, formats, and rules    │
│  Evolved collaboratively by human + LLM     │
├─────────────────────────────────────────────┤
│  Layer 2: The Wiki (Markdown pages)         │
│  LLM-maintained knowledge base              │
│  Create, update, cross-reference            │
├─────────────────────────────────────────────┤
│  Layer 1: Raw Sources (original files)      │
│  Immutable — read-only for the LLM         │
│  PDFs, docs, notes, data files             │
└─────────────────────────────────────────────┘
```

## Why Three Layers?

### Layer 1: Raw Sources
- **Purpose**: Preserve original materials in their exact form
- **Rule**: Never modify raw files — they are the ground truth
- **Format**: Any readable format (PDF, DOCX, TXT, MD, CSV, JSON)
- **Organization**: Grouped by source type (documents, notes, data)

### Layer 2: The Wiki
- **Purpose**: LLM-curated, structured knowledge
- **Rule**: LLM has full read/write authority
- **Format**: Markdown with YAML front matter
- **Key feature**: Cross-references between pages (links)

### Layer 3: Schema
- **Purpose**: Define how the wiki should be structured and maintained
- **Rule**: Both human and LLM can propose changes; human approves
- **Format**: CLAUDE.md (Markdown)
- **Key feature**: Page templates, naming conventions, link rules

## The Three Operations

### Ingest (Raw → Wiki)
Transform source materials into structured wiki pages.

```
raw/document.pdf → [pipeline/LLM analysis] → wiki/pages/[001]Topic.md
```

Key behaviors:
- Track processing state (which files are done, which failed)
- Detect changes (re-process only modified raw files)
- Support watch mode (auto-process new files)

### Query (Read Wiki)
Answer questions by reading and synthesizing wiki pages.

```
User question → [index lookup] → [page reading] → synthesized answer
                                    ↓
                            [new page?] → save to wiki
```

Key behaviors:
- Use indices to locate relevant pages efficiently
- Synthesize across multiple pages
- Capture valuable new knowledge back into the wiki

### Lint (Health Check)
Verify wiki integrity and quality.

```
wiki/ → [broken links?] → [missing fields?] → [orphans?] → report
```

Key behaviors:
- Automated (can run on schedule)
- Append results to log.md
- Fix issues when found

## Navigation Files

Two files provide complementary navigation:

### index.md (Content-Oriented)
- **Purpose**: "What's in this wiki?"
- **Structure**: Hierarchical listing of all categories and pages
- **Updated**: After every ingest operation

### log.md (Time-Oriented)
- **Purpose**: "What happened to this wiki?"
- **Structure**: Append-only chronological record
- **Format**:
  ```markdown
  ## [YYYY-MM-DD] operation | description
  - detail 1
  - detail 2
  ```
- **Rule**: NEVER edit or delete existing entries

## Data Flow

```
                    ┌──────────┐
                    │  raw/    │ (immutable)
                    └────┬─────┘
                         │ Ingest
                         ▼
                    ┌──────────┐
           ┌──────▶│  wiki/   │◀──────┐
           │       └────┬─────┘       │
           │            │             │
     [new page]    Query          Lint
           │            │             │
           └────────────┘─────────────┘
                         │
                         ▼
                    ┌──────────┐
                    │  log.md  │ (append-only)
                    └──────────┘
```

## Scaling Considerations

- **Under 100 pages**: Direct file reading is fast enough
- **100-1000 pages**: Use `_search_index/` for efficient lookup
- **1000+ pages**: Consider `summary_index.json` for LLM quick-reference
- **10,000+ pages**: May need a search engine (Meilisearch, Typesense)

The architecture scales because the LLM always operates on a small subset of pages at a time, using indices to navigate.
