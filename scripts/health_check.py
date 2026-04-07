#!/usr/bin/env python3
"""
Generic wiki health checker for the LLM Wiki three-layer architecture.

Checks:
1. Page counts by type/category
2. Broken internal links [[...]] and [text](path.md)
3. Missing or incomplete front matter
4. Empty required fields (supports per-type rules)
5. Orphan pages (zero incoming links)
6. Pipeline processing state
7. Auto-generate index.md

Usage:
    python health_check.py                                  # run all checks
    python health_check.py --quick                          # quick check (links only)
    python health_check.py --wiki-dir path                  # specify wiki directory
    python health_check.py --wiki-subdir my-topic           # specify wiki subdirectory
    python health_check.py --required-fields title,summary  # global required fields
    python health_check.py --required-by-type emperor:title,dynasty battle:title,date,location
    python health_check.py --update-index                   # auto-generate/update index.md
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ============== Configuration ==============
SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent  # kb/

WIKI_DIR = BASE_DIR / "wiki"
WIKI_SUBDIR = "my-wiki"  # Override via --wiki-subdir or WIKI_SUBDIR env var

# Front matter fields that must be present and non-empty (global, applies to ALL pages)
REQUIRED_FM_FIELDS = ["title", "type"]
# Fields that must merely exist (can be empty)
REQUIRED_FM_EXISTS = ["status"]

# Per-type required fields: {page_type: [field1, field2, ...]}
# Override via --required-by-type
REQUIRED_BY_TYPE = {}

STATE_FILE = SCRIPT_DIR / ".pipeline_state.json"

# Patterns for discovering wiki pages
PAGE_PATTERNS = ["**/*.md"]

# Directories to skip during checks
SKIP_DIRS = {"_search_index", "_maintenance", ".git", "__pycache__", "node_modules"}

LINK_PATTERN_WIKI = re.compile(r'\[\[([^\]]+?)\]\]')
LINK_PATTERN_MD = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')


def append_log(operation, description, details=""):
    """Append an entry to log.md (append-only timeline)."""
    log_path = WIKI_DIR / WIKI_SUBDIR / "log.md"
    if not log_path.exists():
        return
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = "\n## [%s] %s | %s\n" % (date_str, operation, description)
    if details:
        entry += "- %s\n" % details
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def collect_pages(wiki_root):
    """Collect all .md files, skipping specified directories."""
    pages = []
    for pattern in PAGE_PATTERNS:
        for md in wiki_root.glob(pattern):
            parts = md.relative_to(wiki_root).parts
            if any(skip in parts for skip in SKIP_DIRS):
                continue
            if md.parent == wiki_root and md.stem in ("log", "CLAUDE", "index"):
                continue
            if "template" in md.stem.lower() or "backup" in md.stem.lower():
                continue
            pages.append(md)
    return sorted(pages)


def parse_front_matter(md_path):
    """Parse YAML front matter from a markdown file."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip("\"'").strip()
        fm[key] = value
    return fm


def build_name_index(wiki_root, pages):
    """
    Build a mapping from page titles/stems to file paths.
    Supports: exact stem, title from front matter, stem with [prefix] stripped,
    partial substring match.
    """
    index = defaultdict(list)
    for p in pages:
        stem = p.stem
        index[stem].append(p)
        # Strip [prefix] like "[027]" -> "[027]奥古斯都" -> "奥古斯都"
        stripped = re.sub(r'^\[[^\]]*\]', '', stem)
        if stripped and stripped != stem:
            index[stripped].append(p)
        # Index by front matter title
        fm = parse_front_matter(p)
        title = fm.get("title", "")
        if title:
            index[title].append(p)
            title_main = re.split(r'\s*[\(\uFF08]', title)[0].strip()
            if title_main and title_main != title:
                index[title_main].append(p)
    return dict(index)


def resolve_wikilink(target, name_index):
    """Try to resolve a wikilink target to an actual file path."""
    target = target.strip()
    # 1. Exact match
    if target in name_index:
        return name_index[target][0]
    # 2. Strip prefix from target
    stripped = re.sub(r'^\[[^\]]*\]', '', target)
    if stripped and stripped != target and stripped in name_index:
        return name_index[stripped][0]
    # 3. Suffix/prefix match
    for name, paths in name_index.items():
        if name.endswith(target) or target.endswith(name):
            if len(target) >= 2:
                return paths[0]
    # 4. Substring match
    for name, paths in name_index.items():
        if target in name and len(target) >= 2:
            return paths[0]
    return None


def check_page_counts(wiki_root):
    print("\n--- Page Counts ---")
    pages = collect_pages(wiki_root)
    if not pages:
        print("  No wiki pages found")
        return {"total": 0, "by_dir": {}, "by_type": {}}
    by_dir = defaultdict(int)
    for p in pages:
        rel = p.relative_to(wiki_root)
        dir_name = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        by_dir[dir_name] += 1
    for d, count in sorted(by_dir.items()):
        print("  %s: %d" % (d, count))
    by_type = defaultdict(int)
    for p in pages:
        fm = parse_front_matter(p)
        t = fm.get("type", "unknown")
        by_type[t] += 1
    if by_type:
        print()
        for t, count in sorted(by_type.items()):
            print("  type=%s: %d" % (t, count))
    print("\n  Total wiki pages: %d" % len(pages))
    return {"total": len(pages), "by_dir": dict(by_dir), "by_type": dict(by_type)}


def check_broken_links(wiki_root, name_index=None):
    print("\n--- Broken Links ---")
    pages = collect_pages(wiki_root)
    if name_index is None:
        name_index = build_name_index(wiki_root, pages)
    all_stems = set()
    all_rel_paths = set()
    for p in pages:
        all_stems.add(p.stem)
        all_rel_paths.add(str(p.relative_to(wiki_root)))
    broken = defaultdict(list)
    resolved_count = 0
    for md in pages:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel_src = str(md.relative_to(wiki_root))
        for match in LINK_PATTERN_WIKI.findall(text):
            target = match.split("|")[0].split("#")[0].strip()
            if not target:
                continue
            resolved = resolve_wikilink(target, name_index)
            if resolved:
                resolved_count += 1
            else:
                broken[rel_src].append("[[%s]]" % target)
        for text_part, path_part in LINK_PATTERN_MD.findall(text):
            target = path_part.split("#")[0].strip()
            current_dir = str(md.parent.relative_to(wiki_root))
            if target.startswith("./"):
                resolved = "%s/%s" % (current_dir, target[2:])
            elif target.startswith("../"):
                resolved = _resolve_relative(current_dir, target)
            else:
                resolved = target
            target_stem = Path(target).stem
            if target_stem not in all_stems and resolved not in all_rel_paths:
                broken[rel_src].append("[%s]" % path_part)
    if resolved_count:
        print("  Wiki-style links resolved: %d" % resolved_count)
    if broken:
        total_broken = sum(len(v) for v in broken.values())
        print("  [!] %d file(s) with %d broken link(s)" % (len(broken), total_broken))
        for src, targets in sorted(broken.items())[:10]:
            print("    %s: %s" % (src, targets[:3]))
        if len(broken) > 10:
            print("    ... %d more file(s)" % (len(broken) - 10))
    else:
        print("  [OK] No broken links")
    return total_broken if broken else 0


def _resolve_relative(current_dir, path):
    parts = list(Path(current_dir).parts)
    while path.startswith("../"):
        if parts:
            parts.pop()
        path = path[3:]
    resolved = "/".join(parts) + "/" + path if parts else path
    return resolved


def check_front_matter(wiki_root):
    print("\n--- Front Matter ---")
    pages = collect_pages(wiki_root)
    missing_fm = 0
    missing_fields = defaultdict(list)
    empty_fields = defaultdict(list)
    for p in pages:
        fm = parse_front_matter(p)
        rel = p.relative_to(wiki_root)
        if not fm:
            missing_fm += 1
            continue
        page_type = fm.get("type", "")
        if REQUIRED_BY_TYPE and page_type in REQUIRED_BY_TYPE:
            type_fields = REQUIRED_BY_TYPE[page_type]
        else:
            type_fields = REQUIRED_FM_FIELDS
        for field in type_fields:
            if field not in fm:
                missing_fields[field].append("%s [%s]" % (str(rel), page_type))
            elif not fm[field] or fm[field] in ("", '""', "''", "null", "*to-be-filled*"):
                empty_fields[field].append("%s [%s]" % (str(rel), page_type))
        for field in REQUIRED_FM_EXISTS:
            if field not in fm:
                missing_fields[field].append(str(rel))
    print("  Missing front matter entirely: %d" % missing_fm)
    if REQUIRED_BY_TYPE:
        print("  Per-type required fields: %s" % dict(REQUIRED_BY_TYPE))
    if missing_fields:
        print("  Missing required fields:")
        for field, files in sorted(missing_fields.items()):
            print("    %s: %d page(s)" % (field, len(files)))
            for f in files[:3]:
                print("      - %s" % f)
            if len(files) > 3:
                print("      ... +%d more" % (len(files) - 3))
    if empty_fields:
        print("  Empty required fields:")
        for field, files in sorted(empty_fields.items()):
            print("    %s: %d page(s)" % (field, len(files)))
            for f in files[:3]:
                print("      - %s" % f)
            if len(files) > 3:
                print("      ... +%d more" % (len(files) - 3))
    issues = missing_fm + sum(len(v) for v in missing_fields.values())
    return issues


def check_orphans(wiki_root, name_index=None):
    print("\n--- Orphan Pages ---")
    pages = collect_pages(wiki_root)
    if name_index is None:
        name_index = build_name_index(wiki_root, pages)
    all_stems = {p.stem for p in pages}
    incoming = defaultdict(int)
    for md in pages:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for match in LINK_PATTERN_WIKI.findall(text):
            target = match.split("|")[0].split("#")[0].strip()
            if not target:
                continue
            resolved = resolve_wikilink(target, name_index)
            if resolved:
                incoming[resolved.stem] += 1
            elif target in all_stems:
                incoming[target] += 1
        for _, path_part in LINK_PATTERN_MD.findall(text):
            target_stem = Path(path_part).stem
            if target_stem in all_stems:
                incoming[target_stem] += 1
    orphans = [p for p in pages if incoming.get(p.stem, 0) == 0]
    real_orphans = [p for p in orphans if p.stem not in ("index", "CLAUDE")]
    if real_orphans:
        print("  [!] %d orphan page(s) (no incoming links)" % len(real_orphans))
        for p in sorted(real_orphans)[:10]:
            print("    %s" % p.relative_to(wiki_root))
        if len(real_orphans) > 10:
            print("    ... %d more" % (len(real_orphans) - 10))
    else:
        print("  [OK] No orphan pages")
    return len(real_orphans)


def check_duplicates(wiki_root):
    print("\n--- Duplicate Detection ---")
    pages = collect_pages(wiki_root)
    title_map = defaultdict(list)
    for p in pages:
        fm = parse_front_matter(p)
        title = fm.get("title", p.stem).lower()
        title_map[title].append(str(p.relative_to(wiki_root)))
    dupes = {k: v for k, v in title_map.items() if len(v) > 1}
    if dupes:
        print("  [!] %d potential duplicate(s):" % len(dupes))
        for title, files in sorted(dupes.items())[:10]:
            print('    "%s": %s' % (title, files))
        if len(dupes) > 10:
            print("    ... %d more" % (len(dupes) - 10))
    else:
        print("  [OK] No duplicates found")
    return len(dupes)


def check_pipeline_state(wiki_root):
    print("\n--- Pipeline State ---")
    if not STATE_FILE.exists():
        print("  [INFO] No pipeline state found (pipeline not yet run)")
        return
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        print("  [ERR] Cannot read pipeline state")
        return
    total = len(data)
    compiled = sum(1 for v in data.values() if v.get("status") == "compiled")
    failed = sum(1 for v in data.values() if v.get("status") == "failed")
    print("  Total tracked: %d" % total)
    print("  Compiled: %d" % compiled)
    print("  Failed: %d" % failed)
    if failed:
        print("  Failed files:")
        for k, v in data.items():
            if v.get("status") == "failed":
                print("    - %s: %s" % (k, v.get('error', '?')[:50]))


def check_search_indices(wiki_root):
    print("\n--- Search Indices ---")
    for idx_name in ["_search_index", "_maintenance"]:
        idx_dir = wiki_root / idx_name
        if idx_dir.exists():
            files = list(idx_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print("  %s/: %d file(s) (%d bytes)" % (idx_name, len(files), total_size))
        else:
            print("  %s/: NOT FOUND (optional)" % idx_name)


def generate_index(wiki_root):
    print("\n--- Generating index.md ---")
    pages = collect_pages(wiki_root)
    if not pages:
        print("  No pages found, skipping index generation")
        return
    by_type = defaultdict(list)
    for p in pages:
        fm = parse_front_matter(p)
        by_type[fm.get("type", "unknown")].append(p)
    lines = []
    lines.append("# Content Index\n")
    lines.append("> Auto-generated by health_check.py on %s" % datetime.now().strftime('%Y-%m-%d %H:%M'))
    lines.append("> Total: %d pages\n" % len(pages))
    lines.append("## Overview\n")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for t, ps in sorted(by_type.items(), key=lambda x: -len(x[1])):
        lines.append("| %s | %d |" % (t, len(ps)))
    lines.append("")
    for t in sorted(by_type.keys()):
        dir_pages = by_type[t]
        lines.append("## %s\n" % t.replace("_", " ").replace("-", " ").title())
        lines.append("| File | Title |")
        lines.append("|------|-------|")
        for p in sorted(dir_pages, key=lambda x: x.stem):
            fm = parse_front_matter(p)
            title = fm.get("title", p.stem)
            lines.append("| `%s` | %s |" % (p.name, title))
        lines.append("")
    content = "\n".join(lines)
    index_path = wiki_root / "index.md"
    custom_header = ""
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        marker = "> Auto-generated"
        if marker in existing:
            custom_header = existing.split(marker)[0]
            if not custom_header.endswith("\n\n"):
                custom_header += "\n"
    index_path.write_text(custom_header + content, encoding="utf-8")
    print("  [OK] Generated index.md with %d pages" % len(pages))


def main():
    global WIKI_DIR, WIKI_SUBDIR, REQUIRED_FM_FIELDS, REQUIRED_FM_EXISTS
    global REQUIRED_BY_TYPE, STATE_FILE

    parser = argparse.ArgumentParser(description="Wiki health checker (LLM Wiki architecture)")
    parser.add_argument("--quick", action="store_true", help="Quick check (links only)")
    parser.add_argument("--wiki-dir", type=str, help="Override wiki directory")
    parser.add_argument("--wiki-subdir", type=str, help="Wiki subdirectory")
    parser.add_argument("--required-fields", type=str, help="Comma-separated required FM fields (global)")
    parser.add_argument("--required-by-type", type=str, action="append",
                        help="Per-type required fields. Format: type:field1,field2")
    parser.add_argument("--update-index", action="store_true", help="Auto-generate/update index.md")
    args = parser.parse_args()

    if args.wiki_dir:
        WIKI_DIR = Path(args.wiki_dir)
    subdir = args.wiki_subdir or os.environ.get("WIKI_SUBDIR", WIKI_SUBDIR)
    WIKI_SUBDIR = subdir

    wiki_root = WIKI_DIR / WIKI_SUBDIR

    if args.required_fields:
        REQUIRED_FM_FIELDS = [f.strip() for f in args.required_fields.split(",")]

    if args.required_by_type:
        for spec in args.required_by_type:
            if ":" not in spec:
                print("[WARN] Invalid --required-by-type format: %s" % spec)
                continue
            page_type, fields_str = spec.split(":", 1)
            REQUIRED_BY_TYPE[page_type.strip()] = [f.strip() for f in fields_str.split(",")]

    STATE_FILE = SCRIPT_DIR / f".pipeline_state_{WIKI_SUBDIR.replace('/', '_')}.json"

    if not wiki_root.exists():
        print("[ERR] Wiki directory not found: %s" % wiki_root)
        sys.exit(1)

    print("=== Wiki Health Check -- %s ===" % datetime.now().strftime('%Y-%m-%d %H:%M'))
    print("    Wiki root: %s" % wiki_root)

    pages = collect_pages(wiki_root)
    name_index = build_name_index(wiki_root, pages)

    if args.update_index:
        generate_index(wiki_root)
        append_log("lint", "Auto-generated index.md", "pages: %d" % len(pages))
        sys.exit(0)

    issues = 0

    if args.quick:
        issues += check_broken_links(wiki_root, name_index)
    else:
        counts = check_page_counts(wiki_root)
        broken = check_broken_links(wiki_root, name_index)
        issues += broken
        issues += check_front_matter(wiki_root)
        orphans = check_orphans(wiki_root, name_index)
        dupes = check_duplicates(wiki_root)
        check_pipeline_state(wiki_root)
        check_search_indices(wiki_root)
        total_pages = counts.get("total", 0)
        append_log("lint", "Health check (issues: %d)" % issues,
                   "pages: %d | broken links: %d | orphans: %d | duplicates: %d" % (total_pages, broken, orphans, dupes))

    print("\n=== Result: %d issue(s) found ===" % issues)
    sys.exit(min(issues, 1))


if __name__ == "__main__":
    main()
