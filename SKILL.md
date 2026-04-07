---
name: llm-wiki-builder
description: "Build and maintain a personal LLM Wiki knowledge base using the Karpathy three-layer architecture. Use this skill when the user wants to create, organize, or maintain a structured wiki knowledge base — including ingesting source materials, generating wiki pages, setting up health checks, and managing cross-references. Triggers: 'build a knowledge base', 'create a wiki', 'organize my notes into a wiki', 'set up knowledge management', 'ingest documents into wiki'."
---

# LLM Wiki Builder

Build a personal knowledge base where LLM is the programmer, Markdown is the code, and the wiki is the codebase.

Based on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), refined through production use on a 600+ page knowledge base.

## Core Philosophy

1. **Raw sources are immutable** — LLM reads but never writes to raw/
2. **Wiki is the single source of truth** — all knowledge lives as .md pages
3. **Schema evolves collaboratively** — CLAUDE.md defines conventions, you and the user improve it together
4. **Operations leave traces** — every ingest/query/lint is logged in log.md

## Quick Start

```
kb/
├── raw/              ← Drop source files here (PDFs, docs, notes)
├── wiki/
│   └── <topic>/
│       ├── CLAUDE.md ← Schema: conventions, formats, link rules
│       ├── log.md    ← Append-only timeline
│       ├── index.md  ← Content index (what's in this wiki)
│       └── pages/    ← Wiki pages (LLM-maintained)
├── scripts/          ← Pipeline + health check tools
└── prompts/
    └── wiki_builder.md  ← LLM prompt template for ingestion
```

## Workflow Decision Tree

1. **Starting fresh?** → Follow "Setup" below
2. **Ingesting new materials?** → Follow "Ingest" workflow
3. **Querying the wiki?** → Follow "Query" workflow
4. **Maintaining health?** → Follow "Lint" workflow
5. **Customizing for a domain?** → Adapt CLAUDE.md

## Setup

### 1. Create Directory Structure

```
kb/
├── raw/
│   ├── documents/    ← Source PDFs, docs, papers
│   ├── notes/        ← Text notes, markdown files
│   └── data/         ← CSVs, JSONs, structured data
├── wiki/
│   └── <topic>/
├── scripts/          ← Copy from this skill's scripts/
└── prompts/
    └── wiki_builder.md  ← Copy from this skill's references/
```

### 2. Create CLAUDE.md (Schema)

Copy `references/CLAUDE_template.md` to `wiki/<topic>/CLAUDE.md` and customize:
- Replace `<topic>` with the knowledge domain name
- Define page types (entity, concept, document, etc.)
- Define front matter fields per page type
- Define link conventions
- Define naming conventions

### 3. Create log.md

Initialize with a header:

```markdown
# Change Log

> Append-only. Never edit or delete existing entries.

## [YYYY-MM-DD] init | Knowledge base created
- Structure: three-layer (raw → wiki → schema)
- Topic: <your topic>
```

### 4. Create index.md

Build a content index listing all top-level categories and entity counts.

### 5. Customize the Pipeline

Edit `scripts/pipeline.py` — update these constants:
- `WIKI_SUBDIR` — target wiki subdirectory under wiki/
- `FRONT_MATTER_FIELDS` — required YAML front matter fields
- `PROMPT_PATH` — path to your wiki_builder.md prompt

Edit `scripts/health_check.py` — update these constants:
- `WIKI_SUBDIR` — same wiki subdirectory
- `REQUIRED_FM_FIELDS` — fields to check in front matter
- `PAGE_PATTERNS` — glob patterns for page discovery

## Ingest Workflow

### Using the Pipeline Script

```bash
# Process all pending files in raw/
python scripts/pipeline.py

# Watch mode: auto-process new files
python scripts/pipeline.py --watch

# Preview without processing
python scripts/pipeline.py --dry-run

# Process only a specific category
python scripts/pipeline.py --category documents

# Check status
python scripts/pipeline.py --status
```

### Manual Ingest (LLM-Assisted)

When the pipeline isn't suitable (e.g., structured data, images):

1. Read the source file from `raw/`
2. Parse key information (entities, relationships, metadata)
3. Create wiki pages following the CLAUDE.md format
4. Add cross-references (links between related pages)
5. Update `index.md`
6. Append to `log.md`:

```markdown
## [YYYY-MM-DD] ingest | <description>
- Source: raw/<path>
- Generated: wiki/<topic>/pages/<file>.md
- Entities extracted: N
- Links created: N
```

## Query Workflow

1. **Locate**: Read `index.md` or `_maintenance/summary_index.json` to find relevant pages
2. **Read**: Load the relevant wiki pages
3. **Synthesize**: Combine information from multiple pages into an answer
4. **Capture**: If the answer represents new knowledge, create a new wiki page
5. **Log**: Append to `log.md`:

```markdown
## [YYYY-MM-DD] query | <topic searched>
- Pages consulted: page1.md, page2.md
- New page created: wiki/<topic>/pages/<new_page>.md (if applicable)
```

## Lint Workflow

### Using the Health Check Script

```bash
# Full check
python scripts/health_check.py

# Quick check (links only)
python scripts/health_check.py --quick
```

### Checks Performed

| Check | What it catches |
|-------|----------------|
| Broken links | `[[target]]` where target.md doesn't exist |
| Missing front matter | Pages without YAML `---` block |
| Empty required fields | Pages with blank/placeholder required fields |
| Orphan pages | Pages with zero incoming links |
| Duplicate entries | Pages with similar names or titles |
| Pipeline state | Files in raw/ not yet processed |

### Manual Lint

When you spot issues during normal work:

1. Fix the issue directly in the wiki page
2. Update any affected index pages
3. Append to `log.md`:

```markdown
## [YYYY-MM-DD] lint | <description>
- Issue: <what was wrong>
- Fix: <what was changed>
- Pages affected: N
```

## CLAUDE.md Conventions

The Schema file should define:

### Page Types
Each wiki should have clear page types with consistent formats. See `references/CLAUDE_template.md` for a starter template.

### Front Matter
Every page must have YAML front matter:

```yaml
---
title: "Page Title"
type: entity|concept|document|category
tags: ["tag1", "tag2"]
date_created: YYYY-MM-DD
status: complete|draft|needs-review
---
```

### Link Format
- Internal links: `[[Page Name]]` or `[Display Text](relative/path.md)`
- Cross-directory: `[Text](../../other-section/page.md)`
- External: `[Text](https://example.com)`

### Naming Conventions
- Files: `[identifier]title.md` (e.g., `[001]Entity Name.md`)
- Directories: descriptive names, no spaces preferred
- Index files: always `index.md` in each directory

## Resources

### scripts/
- `pipeline.py` — Raw → Wiki ingestion pipeline (watch, status, dry-run)
- `health_check.py` — Wiki health checker (links, front matter, orphans)

### references/
- `CLAUDE_template.md` — Starter Schema file to customize
- `wiki_builder_prompt.md` — LLM prompt template for ingestion
- `architecture.md` — Detailed three-layer architecture explanation
- `page_templates.md` — Template examples for different page types

## Domain Customization Examples

### Academic Research
```
pages/
├── papers/          → type: paper (title, authors, year, abstract, key findings)
├── concepts/        → type: concept (definition, related work, applications)
├── authors/         → type: author (name, affiliation, papers, h-index)
└── methods/         → type: method (name, description, use cases, limitations)
```

### Personal Knowledge
```
pages/
├── notes/           → type: note (title, date, tags, summary)
├── people/          → type: person (name, context, relationship, notes)
├── projects/        → type: project (name, status, tasks, links)
└── references/      → type: reference (source, author, key points, quotes)
```

### Technical Documentation
```
pages/
├── apis/            → type: api (endpoint, method, params, response, examples)
├── components/      → type: component (name, props, usage, examples)
├── decisions/       → type: decision (context, options, outcome, date)
└── guides/          → type: guide (title, audience, steps, prerequisites)
```

## Important Notes

- **log.md is append-only** — never modify or delete existing entries
- **raw/ is immutable** — never modify source files
- **Windows users**: set `PYTHONUTF8=1` before running Python scripts
- **Pipeline state** is tracked in `scripts/.pipeline_state.json`
- **Health reports** are saved to `wiki/<topic>/_maintenance/health_report.json`
