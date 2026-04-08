# llm-wiki-builder

> A personal LLM Wiki builder built for large knowledge bases, following the Karpathy three-layer architecture

[简体中文](./README.md)

---

## About

llm-wiki-builder is a **structured Wiki knowledge base management tool** designed for individuals or small teams who need to systematically organize large amounts of material.

It follows a **three-layer architecture**:
1. **Raw** — source materials (PDFs, notes, data), read-only and immutable
2. **Wiki** — structured Markdown pages (single source of truth)
3. **Schema** — CLAUDE.md defines conventions (types, front matter, link rules)

With Pipeline + Health Check + Index Generator, even a 600+ page knowledge base stays organized.

---

## Features

- ✅ **Automated pipeline** — one-time setup, continuous ingestion
- ✅ **Health checks** — detects broken links, orphan pages, missing fields
- ✅ **Global index generation** — one-click `index.md` with stats, categories, lookup table
- ✅ **Multi-domain ready** — TCM, academic research, personal notes, technical docs
- ✅ **Obsidian-friendly** — native `[[wikilink]]` support

---

## Quick Start

```bash
# 1. Copy this skill into your project
cp -r skills/llm-wiki-builder <your-project>/skills/

# 2. Edit scripts/pipeline.py to set WIKI_SUBDIR, etc.
# 3. Run health check
python <your-project>/skills/llm-wiki-builder/scripts/health_check.py

# 4. (Optional) Generate global index
python <your-project>/skills/llm-wiki-builder/scripts/generate_global_index.py
```

See [SKILL.md](skills/llm-wiki-builder/SKILL.md) for full documentation.

---

## New: Global Index Generator

### Problem
When your knowledge base grows, there's no single "table of contents" to quickly browse and find pages.

### Solution
`scripts/generate_global_index.py` will:
- Recursively scan `wiki/<topic>/` for `.md` files
- Parse YAML front matter (title, type, source, chapter, status…)
- Generate `wiki/<topic>/index.md` containing:
  - 📊 Overview stats (total pages, type/source distribution, categories)
  - 🔍 Quick lookup table (sorted by title, with links)
  - 🆕 Recent updates (top 20 modified pages)

### Example
For a 2,644-page TCM knowledge base, the generated index shows:
- Bencao Gangmu (1,462 pages) / Jinkui Yaolue (451 pages) / Ni Haixia Formulas (277 pages)
- A-Z quick navigation for herbs and formulas
- One-click jumping without manual directory drilling

> See: [wiki/中医/index.md](skills/llm-wiki-builder/wiki/中医/index.md)

---

## Directory Structure

```
llm-wiki-builder/
├── raw/                    # Source materials (PDFs, txt, notes)
│   ├── documents/
│   ├── notes/
│   └── data/
├── wiki/
│   └── 中医/              # Your topic (example)
│       ├── CLAUDE.md      # Schema for this topic
│       ├── index.md       # Global index (auto-generated)
│       ├── log.md         # Append-only changelog
│       ├── _maintenance/  # Health reports, pipeline state
│       ├── 神农百草经/
│       │   └── 中药名/
│       ├── 金匮要略/
│       │   └── 配方/
│       ├── 本草纲目/
│       └── 倪海厦经典配方/
├── scripts/
│   ├── pipeline.py        # Ingestion pipeline
│   ├── health_check.py    # Health checks
│   └── generate_global_index.py  # ✨ New
└── prompts/
    └── wiki_builder.md    # LLM ingestion prompt template
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `pipeline.py` | Process new files in raw/ into wiki pages |
| `health_check.py` | Check for broken links, orphan pages, missing fields |
| `generate_global_index.py` | Generate global `index.md` (lookup entry) |

---

## Documentation

Full guide: [SKILL.md](skills/llm-wiki-builder/SKILL.md)

Covers:
- Setup & configuration
- Ingest workflows (manual / automatic)
- Query workflows
- Lint workflows
- CLAUDE.md conventions
- Domain customization examples

---

## Contributing

Issues and Pull Requests are welcome.

For questions about building your own knowledge base, start a [Discussion](https://github.com/jownda/llm-wiki-builder/discussions).

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Turn scattered notes into an organized knowledge hub — with a single index page.**
