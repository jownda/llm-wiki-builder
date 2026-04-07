# 本草纲目知识库 Schema

> Define conventions, templates, and link rules for the 本草纲目 (Compendium of Materia Medica) wiki.

## Topic

本草纲目（Compendium of Materia Medica / Bencao Gangmu）—明代李时珍编纂的药物学巨著。

## Page Types

### 1. Category (部类)
Each of the 16 major categories (部) of the compendium.

```yaml
---
title: "部名"
type: category
tags: ["category", "部"]
volume_range: "卷X–卷Y"
date_created: YYYY-MM-DD
status: complete|draft
---
```

**Content:** 部类概述 → 包含哪些卷/药物 → 分类逻辑说明

### 2. Herb (药物条目)
Individual herb/mineral/animal entry.

```yaml
---
title: "[编号]药物正名"
type: herb
category: "所属部"
volume: "卷X"
synonyms: ["别名1", "别名2"]
date_created: YYYY-MM-DD
status: complete|draft
---
```

**Content structure:**
- **正名** （纲）
- **释名** （目：别名溯源）
- **集解** （产地、形态、采集）
- **辨疑/正误** （考证纠错）
- **修治** （炮制方法）
- **气味** （性味归经）
- **主治** （功效）
- **发明** （时珍按语）
- **附方** （相关方剂）

### 3. Concept (概念)
TCM concepts, theories, methodology referenced in the text.

```yaml
---
title: "概念名"
type: concept
tags: ["theory", "TCM"]
date_created: YYYY-MM-DD
status: complete|draft
---
```

### 4. Reference (文献)
Historical sources, editions, commentaries.

```yaml
---
title: "文献名"
type: reference
tags: ["source", "edition"]
date_created: YYYY-MM-DD
status: complete|draft
---
```

## Page Types

| 类型 | 用途 | 路径 |
|------|------|------|
| category | 16 大部概述 | pages/categories/ |
| herb | 具体药物条目 | pages/herbs/ |
| concept | 中医理论概念 | pages/concepts/ |
| reference | 参考文献/版本 | pages/references/ |

## Front Matter Fields

Every page must have YAML front matter with:
- `title`: Display title
- `type`: category | herb | concept | reference
- `tags`: array of tags
- `date_created`: YYYY-MM-DD
- `status`: complete | draft | needs-review

Optional (by type):
- `herb`: category, volume, synonyms
- `category`: volume_range
- `concept`: related_category

## Link Conventions

- Internal: `[[Page Name]]` for wiki-style, `[Text](relative/path.md)` for markdown links
- Cross-reference herbs to their category
- Reference classical sources using `[[Source Name]]`
- External: `[Text](https://...)`

## Naming Conventions

- Herb files: `[NNN]药物名.md` (e.g., `[001]人参.md`)
- Category files: `category-部名.md` (e.g., `category-草部.md`)
- Concept files: `concept-概念名.md`
- Reference files: `ref-文献名.md`
- No spaces in filenames; use hyphens or no separator for Chinese
- Index files: always `index.md`
