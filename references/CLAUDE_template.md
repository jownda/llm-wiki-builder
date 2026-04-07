# CLAUDE.md Template — Wiki Schema

> Copy this template to `wiki/<topic>/CLAUDE.md` and customize for your domain.
> This is the Schema layer — it defines how the LLM should read, write, and maintain the wiki.

---

# CLAUDE.md — <Topic> Knowledge Base

> **Role**: You are a disciplined wiki maintainer, not a general chatbot.
> **Philosophy**: Obsidian is the IDE, LLM is the programmer, Wiki is the codebase.

---

## Directory Structure

```
wiki/<topic>/
├── CLAUDE.md                    ← This file (Schema layer)
├── log.md                       ← Change timeline (append-only)
├── index.md                     ← Content index (what's in this wiki)
├── pages/                       ← Main wiki pages
│   ├── entities/                ← Entity pages (core objects)
│   ├── concepts/                ← Concept pages (ideas, theories)
│   └── references/              ← Reference pages (sources, citations)
├── categories/                  ← Category/taxonomy pages
├── _search_index/               ← Search indices (auto-generated)
│   └── full_index.json
└── _maintenance/                ← Maintenance tool output
    ├── summary_index.json       ← Summary index (for LLM quick lookup)
    └── health_report.json       ← Health check report
```

---

## Three-Layer Architecture

| Layer | Location | Principle |
|-------|----------|-----------|
| **Raw Sources** | `raw/` | Immutable — LLM reads only, never writes |
| **The Wiki** | `wiki/<topic>/` | LLM maintains fully: create, update, cross-reference |
| **The Schema** | `CLAUDE.md` (this file) | Defines conventions — evolves collaboratively |

---

## Page Format Standards

### Entity Pages (`pages/entities/`)

Filename: `[id]title.md` (e.g., `[001]Entity Name.md`)

```yaml
---
title: "Entity Name"
id: "001"
type: entity
tags:
  - "category1"
  - "category2"
summary: "One-line description"
status: complete|draft|needs-review
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

**Body sections**: Overview → Key Attributes → Relationships → Notes → References

### Concept Pages (`pages/concepts/`)

Filename: `concept_name.md`

```yaml
---
title: "Concept Name"
type: concept
tags:
  - "domain"
definition: "Clear definition"
related_entities: ["entity1", "entity2"]
status: complete|draft
---
```

**Body sections**: Definition → Explanation → Examples → Related Concepts → References

### Reference Pages (`pages/references/`)

Filename: `[author_year]short_title.md`

```yaml
---
title: "Full Reference Title"
type: reference
authors: ["Author 1", "Author 2"]
year: YYYY
source: "Journal/Publisher/URL"
tags: ["topic1", "topic2"]
summary: "Key findings or content summary"
---
```

**Body sections**: Bibliographic Info → Summary → Key Points → Related Entities → Quotes

---

## Link Conventions

### Within Same Directory
```markdown
[Display Text](./filename.md)
```

### Cross-Directory
```markdown
[Display Text](../other-section/filename.md)
```

### Two Levels Up
```markdown
[Display Text](../../other-topic/pages/filename.md)
```

### General Rules
- Use `[Display Text](relative/path.md)` format for file links
- Use `[[Page Name]]` for wiki-style links (resolved at query time)
- Every entity page should link to its category page
- Every category page should appear in `index.md`
- Keep link text descriptive — avoid bare URLs

---

## Operations (How the LLM Should Work)

### Ingest (Add New Material)

1. Read source from `raw/`
2. Extract entities, concepts, and relationships
3. Create wiki pages following format standards above
4. Add cross-references between related pages
5. Update relevant `index.md` and category pages
6. Append to `log.md`:
   ```
   ## [YYYY-MM-DD] ingest | <description>
   - Source: raw/<path>
   - Generated: wiki/<topic>/pages/<file>.md
   - Links created: N
   ```

### Query (Answer Questions)

1. Check `summary_index.json` or `index.md` to locate relevant pages
2. Read the relevant pages
3. Synthesize a comprehensive answer
4. **Important**: If the answer represents new, useful knowledge, save it as a new wiki page

### Lint (Health Check)

1. Run `health_check.py` or manually check:
   - Broken links (targets that don't exist)
   - Missing or incomplete front matter
   - Empty required fields
   - Orphan pages (no incoming links)
2. Fix issues found
3. Append to `log.md`:
   ```
   ## [YYYY-MM-DD] lint | Health check
   - Pages: N | Broken links: N | Empty fields: N
   ```

---

## Required Front Matter Fields

| Page Type | Required Fields |
|-----------|----------------|
| entity | title, id, type, summary, status |
| concept | title, type, definition |
| reference | title, type, authors, year, summary |
| category | title, type, description |

---

## Tool Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `pipeline.py` | scripts/ | raw→wiki compilation (watch/dry-run/status) |
| `health_check.py` | scripts/ | Health check (broken links/empty fields/missing) |

---

## Notes

- **Windows encoding**: Set `PYTHONUTF8=1` when running Python scripts
- **log.md is append-only**: Never edit or delete existing entries
- **raw/ is immutable**: Never modify source files
- **Maintenance mode**: Always update wiki content first, then update indices
