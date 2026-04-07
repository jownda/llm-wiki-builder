#!/usr/bin/env python3
"""
Parse 本草纲目 raw text and generate wiki pages.
Works without LLM — just structured extraction.
"""

import re
from pathlib import Path
from datetime import datetime

SPLIT_DIR = Path(__file__).parent.parent / "raw" / "documents" / "split"
WIKI_DIR = Path(__file__).parent.parent / "wiki" / "bcgj" / "pages"
LOG_FILE = Path(__file__).parent.parent / "wiki" / "bcgj" / "log.md"

# Skip patterns: these are NOT herb names
SKIP_PATTERNS = [
    "时珍曰", "弘景曰", "宗曰", "颂曰", "藏器曰", "保升曰", "禹锡曰",
    "雷曰", "杲曰", "好古曰", "之才曰", "普曰", "元素曰", "志禹",
    "别录曰", "恭曰", "韩保升曰", "震亨曰", "孟诜曰",
    "^草之[一二三四五六七八九十]+$", "^木之[一二三四五六七八九十]+$",
    "^谷之[一二三四五六七八九十]+$", "^果之[一二三四五六七八九十]+$",
    "^菜之[一二三四五六七八九十]+$", "^虫之[一二三四五六七八九十]+$",
    "^禽之[一二三四五六七八九十]+$", "^兽之[一二三四五六七八九十]+$",
    "^鳞之[一二三四五六七八九十]+$", "^介之[一二三四五六七八九十]+$",
    "^水之[一二三四五六七八九十]+$", "^火之[一二三四五六七八九十]+$",
    "^土之[一二三四五六七八九十]+$", "^金之[一二三四五六七八九十]+$",
    "^人部第[一二三四五六七八九十]+$", "^人之一", "^序例[上下]$",
    "^序例[一二三四五六]$", "^本草经序例", "^序例目录",
    "^凡例", "^目录", "^释例", "附录", "校注说明",
    "^主治$", "^气味$", "^修治$", "^集解$", "^释名$", "^发明$", "^附方$",
    "^附方$", "^附录$",
]

# Patterns to detect section changes in text
SECTION_PATTERNS = [
    (r"水部", "水部"),
    (r"火部", "火部"),
    (r"土部", "土部"),
    (r"金石部", "金石部"),
    (r"草部", "草部"),
    (r"谷部", "谷部"),
    (r"菜部", "菜部"),
    (r"果部", "果部"),
    (r"木部", "木部"),
    (r"服器部", "服器部"),
    (r"虫部", "虫部"),
    (r"鳞部", "鳞部"),
    (r"介部", "介部"),
    (r"禽部", "禽部"),
    (r"兽部", "兽部"),
    (r"人部", "人部"),
]


def detect_section(text: str) -> str:
    """Detect which 部 a chunk of text belongs to by counting occurrences."""
    counts = {}
    for pattern, section in SECTION_PATTERNS:
        # Count all occurrences including "XX部第X卷" patterns
        c = len(re.findall(pattern, text))
        if c > 0:
            counts[section] = c
    
    if counts:
        most_common = max(counts, key=counts.get)
        return most_common
    
    # Check if this is in the front-matter / preface area
    if "神农" in text[:500] or "序例" in text[:500]:
        return "序例"
    
    return "未知"  # Unknown, not preface default


def is_valid_herb_name(name: str) -> bool:
    """Filter out noise lines that look like herb names but aren't."""
    # Must contain at least one Chinese character
    if not re.search(r'[\u4e00-\u9fff]', name):
        return False
    # Too short or too long
    if len(name) < 1 or len(name) > 15:
        return False
    # Check against skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, name):
            return False
    # Skip names that start with commentary patterns
    if re.match(r'^(时珍|弘景|宗曰|颂曰|藏器|保升|禹锡|之才|普曰|元素|好古|震亨|孟诜|雷公|恭曰)', name):
        return False
    # Skip lines that are just section markers
    if re.match(r'^[一二三四五六七八九十百]+卷', name):
        return False
    if re.match(r'^[草木谷果菜虫禽兽鳞介水火土金人]之[一二三四五六七八九十]+', name):
        return False
    return True


def extract_herbs(content: str) -> list:
    """Extract herb entries from a chunk of text."""
    herbs = []
    lines = content.split("\n")
    current_entry = None
    
    for i, line in enumerate(lines):
        clean = line.strip()
        if not clean:
            continue
        
        # Check if this line might be a herb name (short, no 【)
        if len(clean) <= 20 and "【" not in clean and "】" not in clean:
            # Look ahead: does 【释名】or【集解】appear in the next 300 chars?
            lookahead = "".join(lines[i:i+10])[:500]
            if "【释名】" in lookahead or "【集解】" in lookahead:
                # Validate the name
                candidate_name = clean.split("（")[0].split("(")[0].strip()
                # Remove leading full-width spaces and other whitespace
                candidate_name = candidate_name.strip()
                
                if is_valid_herb_name(candidate_name):
                    # This looks like a real herb entry
                    if current_entry and len(current_entry["content"]) > 100:
                        herbs.append(current_entry)
                    current_entry = {
                        "name": candidate_name,
                        "content": clean,
                        "section": "",
                    }
                # Invalid name → this is commentary, skip
                continue
        
        if current_entry:
            current_entry["content"] += "\n" + line
    
    if current_entry and len(current_entry["content"]) > 100:
        herbs.append(current_entry)
    
    return herbs


def generate_herb_page(herb: dict, index: int) -> str:
    """Generate a wiki page for a herb entry."""
    name = herb["name"]
    # Sanitize filename
    safe_name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_\-]', '', name)
    if not safe_name:
        safe_name = f"herb_{index:04d}"
    
    # Extract sections from content
    sections = {}
    for marker in ["释名", "集解", "辨疑", "正误", "修治", "气味", "主治", "发明", "附方"]:
        pattern = rf"【{marker}】(.+?)(?=【|$)"
        match = re.search(pattern, herb["content"], re.DOTALL)
        if match:
            sections[marker] = match.group(1).strip()
    
    # Build aliases from 释名
    aliases = []
    if "释名" in sections:
        alias_section = sections["释名"]
        # Extract items in （《...》）or separated by、
        alias_matches = re.findall(r'（[^）]*）', alias_section[:300])
        # Also look for  named items
        alias_matches += re.findall(r'[^（【]+?（', alias_section[:300])
        aliases = [a.strip("（）") for a in alias_matches if len(a.strip("（）")) > 1][:5]
    
    page = f"""---
title: "[{index:03d}]{name}"
type: herb
category: "{herb.get('section', '未知')}"
tags: ["herb", "{herb.get('section', 'unknown')}"]
date_created: {datetime.now().strftime('%Y-%m-%d')}
status: draft
---

# {name}

## 释名
{sections.get('释名', '（待补充）')}

## 集解
{sections.get('集解', '（待补充）')}

## 辨疑/正误
{sections.get('辨疑', sections.get('正误', '（未见）'))}

## 修治
{sections.get('修治', '（未见）')}

## 气味
{sections.get('气味', '（待补充）')}

## 主治
{sections.get('主治', '（待补充）')}

## 发明
{sections.get('发明', '（未见）')}

## 附方
{sections.get('附方', '（待补充）')}

---
*Source: raw/documents/本草纲目.txt (chunk split)*
*Extracted by pipeline.py on {datetime.now().strftime('%Y-%m-%d')}*
"""
    return safe_name, page


def main():
    print("=" * 60)
    print("本草纲目 Wiki Generator — Structured Extraction")
    print("=" * 60)
    
    # Ensure output directories exist
    herbs_dir = WIKI_DIR / "herbs"
    categories_dir = WIKI_DIR / "categories"
    references_dir = WIKI_DIR / "references"
    herbs_dir.mkdir(parents=True, exist_ok=True)
    categories_dir.mkdir(parents=True, exist_ok=True)
    references_dir.mkdir(parents=True, exist_ok=True)
    
    # Process chunks
    chunks = sorted(SPLIT_DIR.glob("chunk_*.txt"))
    if not chunks:
        print("No chunks found! Run split_book.py first.")
        return
    
    print(f"\nProcessing {len(chunks)} chunks...")
    
    total_herbs = 0
    total_text = ""
    
    for chunk_file in chunks:
        content = chunk_file.read_text(encoding="utf-8")
        total_text += content
        
        section = detect_section(content)
        herbs = extract_herbs(content)
        
        for i, herb in enumerate(herbs):
            herb["section"] = section
            safe_name, page = generate_herb_page(herb, total_herbs + 1)
            out_path = herbs_dir / f"{safe_name}.md"
            
            # Avoid overwriting
            counter = 1
            while out_path.exists():
                out_path = herbs_dir / f"{safe_name}_{counter}.md"
                counter += 1
            
            out_path.write_text(page, encoding="utf-8")
            total_herbs += 1
        
        print(f"  {chunk_file.name}: section={section}, herbs={len(herbs)}")
    
    # Generate category overview pages
    print(f"\nGenerating category overview pages...")
    categories = {}
    
    # Scan all herb pages to count by category
    for herb_file in herbs_dir.glob("*.md"):
        content = herb_file.read_text(encoding="utf-8")
        # Extract category from front matter
        cat_match = re.search(r'category: "([^"]+)"', content)
        if cat_match:
            cat = cat_match.group(1)
            categories.setdefault(cat, []).append(herb_file.name)
    
    for cat, herbs_list in sorted(categories.items()):
        safe_cat = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_\-]', '', cat)
        cat_page = f"""---
title: "{cat}"
type: category
tags: ["category", "{safe_cat}"]
date_created: {datetime.now().strftime('%Y-%m-%d')}
status: draft
---

# {cat}

## 概述

{cat}是《本草纲目》十六部之一。

## 收录药物

共 **{len(herbs_list)}** 个条目。

"""
        for h in sorted(herbs_list)[:50]:  # Limit to first 50 for page
            herb_name = h.replace(".md", "").lstrip("0123456789[]_")
            cat_page += f"- [[{herb_name}]]\n"
        
        if len(herbs_list) > 50:
            cat_page += f"\n...以及更多（共 {len(herbs_list)} 个条目）"
        
        cat_path = categories_dir / f"category-{safe_cat}.md"
        cat_path.write_text(cat_page, encoding="utf-8")
        print(f"  {cat}: {len(herbs_list)} entries")
    
    # Update log
    log_entry = f"""

## [{datetime.now().strftime('%Y-%m-%d')}] ingest | 本草纲目 structured extraction
- Source: raw/documents/本草纲目.txt (39 chunks)
- Generated: {total_herbs} herb entries in wiki/bcgj/pages/herbs/
- Categories: {len(categories)} category overview pages
- Method: Rule-based extraction (no LLM), sections detected by keyword matching
- Status: Draft pages — content extracted but may need review/refinement
"""
    
    if LOG_FILE.exists():
        LOG_FILE.write_text(LOG_FILE.read_text(encoding="utf-8") + log_entry, encoding="utf-8")
    else:
        LOG_FILE.write_text(f"# Change Log\n> Append-only. Never edit or delete existing entries.\n{log_entry}", encoding="utf-8")
    
    # Update index
    index_path = WIKI_DIR.parent / "index.md"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        # Update statistics
        content = re.sub(r'\| 药物条目 \| \d+', f'| 药物条目 | {total_herbs}', content)
        content = re.sub(r'\| 页面总数 \| \d+', f'| 页面总数 | {total_herbs + len(categories)}', content)
        content = re.sub(r'目前尚未开始摄入.*$', f'已完成首批结构化摄入，共 {total_herbs} 个药物条目。', content, flags=re.MULTILINE)
        index_path.write_text(content, encoding="utf-8")
    
    print(f"\n{'=' * 60}")
    print(f"Done! Generated {total_herbs} herb pages, {len(categories)} category pages")
    print(f"Location: {WIKI_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
