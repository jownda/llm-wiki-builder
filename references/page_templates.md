# Page Templates

Templates for common wiki page types. Customize these for your domain.

## Entity Page

Use for: core objects in your domain (people, places, products, drugs, etc.)

```markdown
---
title: "Entity Name"
id: "001"
type: entity
tags:
  - "category1"
summary: "One-line description of what this entity is and why it matters"
status: complete
created: YYYY-MM-DD
updated: YYYY-MM-DD
related:
  - "[Related Entity 1](../entities/[id]related1.md)"
  - "[Related Entity 2](../entities/[id]related2.md)"
---

# Entity Name

## Overview
A brief introduction to this entity — 2-3 paragraphs covering what it is,
its significance, and context within the domain.

## Key Attributes

| Attribute | Value |
|-----------|-------|
| Attribute 1 | Value 1 |
| Attribute 2 | Value 2 |
| Attribute 3 | Value 3 |

## Detailed Description

### Aspect 1
Detailed information about the first major aspect.

### Aspect 2
Detailed information about the second major aspect.

## Relationships

- **Related to**: [Entity A](./[id]entity_a.md) — nature of relationship
- **Contrasts with**: [Entity B](./[id]entity_b.md) — how they differ
- **Part of**: [Category](../../categories/category_name.md)

## Notes

Additional observations, caveats, or context that doesn't fit elsewhere.

## References

- Source 1
- Source 2
```

---

## Concept Page

Use for: abstract ideas, theories, frameworks, principles.

```markdown
---
title: "Concept Name"
type: concept
tags:
  - "domain"
  - "subdomain"
definition: "Clear, concise definition"
related_concepts:
  - "[Concept A](./concept_a.md)"
  - "[Concept B](./concept_b.md)"
status: complete
created: YYYY-MM-DD
---

# Concept Name

## Definition

A precise definition of this concept in 1-2 sentences.

## Explanation

Expanded explanation covering:
- What this concept means in practice
- Why it matters
- Common misconceptions

## Examples

### Example 1: Title
Description of a concrete example.

### Example 2: Title
Description of another example.

## Related Concepts

| Concept | Relationship |
|---------|-------------|
| [Concept A](./concept_a.md) | How they relate |
| [Concept B](./concept_b.md) | How they differ |

## Applications

Where and how this concept is applied in practice.

## References

- Source 1
- Source 2
```

---

## Category / Index Page

Use for: grouping entities, taxonomy pages, directory pages.

```markdown
---
title: "Category Name"
type: category
description: "What this category covers"
parent: "Parent Category (if nested)"
item_count: N
---

# Category Name

> description of what this category covers

## Items

| ID | Name | Summary |
|----|------|---------|
| 001 | [Item 1](../pages/entities/[001]item1.md) | One-line summary |
| 002 | [Item 2](../pages/entities/[002]item2.md) | One-line summary |
| 003 | [Item 3](../pages/entities/[003]item3.md) | One-line summary |

## Subcategories

- [Subcategory A](./subcategory_a.md)
- [Subcategory B](./subcategory_b.md)

## Notes

Any observations about this category as a whole.

---

[Back to Index](../index.md)
```

---

## Document / Reference Page

Use for: papers, books, articles, source documents.

```markdown
---
title: "Full Document Title"
type: reference
authors: ["Author 1", "Author 2"]
year: YYYY
source: "Publisher/Journal/URL"
tags: ["topic1", "topic2"]
summary: "Key findings or content summary"
related_entities: ["entity1", "entity2"]
status: complete
created: YYYY-MM-DD
---

# Full Document Title

## Bibliographic Info

| Field | Value |
|-------|-------|
| Authors | Author 1, Author 2 |
| Year | YYYY |
| Source | Publisher/Journal |
| URL | [link](https://...) |

## Summary

A 2-3 paragraph summary of the document's key content and findings.

## Key Points

1. **Point 1**: Description
2. **Point 2**: Description
3. **Point 3**: Description

## Related Entities

- [Entity A](../entities/[id]entity_a.md) — how this document relates
- [Entity B](../entities/[id]entity_b.md) — connection

## Notable Quotes

> "Quote from the document" — Author, Page X

## Notes

Personal observations, relevance to the knowledge base, caveats.

---

[Back to References](../index.md)
```

---

## index.md (Root Index)

The top-level content index for the entire wiki.

```markdown
# <Topic> Knowledge Base

> Brief description of what this knowledge base covers.

## Statistics

- Total pages: N
- Entities: N
- Concepts: N
- References: N
- Last updated: YYYY-MM-DD

## Quick Navigation

- [Entities](./pages/entities/) — Core objects (N items)
- [Concepts](./pages/concepts/) — Ideas and theories (N items)
- [References](./pages/references/) — Source documents (N items)
- [Categories](./categories/) — Topic groupings (N categories)

## Recent Changes

See [log.md](./log.md) for the complete change history.

## Entity Index

### Category A (N items)
| ID | Name | Summary |
|----|------|---------|
| ... | ... | ... |

### Category B (N items)
| ID | Name | Summary |
|----|------|---------|
| ... | ... | ... |
```
