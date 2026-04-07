#!/usr/bin/env python3
"""Build a simple search index for the bcgj wiki."""

import re
import json
from pathlib import Path
from datetime import datetime

HERBS_DIR = Path(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\skills\llm-wiki-builder\wiki\bcgj\pages\herbs')
CATEGORIES_DIR = Path(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\skills\llm-wiki-builder\wiki\bcgj\pages\categories')
INDEX_DIR = Path(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\skills\llm-wiki-builder\wiki\bcgj\_search_index')
INDEX_DIR.mkdir(parents=True, exist_ok=True)


def build_index():
    entries = []
    
    for f in sorted(HERBS_DIR.glob('*.md')):
        content = f.read_text(encoding='utf-8')
        
        # Extract title from front matter
        m = re.search(r'title:\s*"\[.*?\](.*?)"', content)
        title = m.group(1) if m else f.stem
        
        # Extract category
        m_cat = re.search(r'category:\s*"([^"]+)"', content)
        category = m_cat.group(1) if m_cat else '未知'
        
        # Extract tags
        m_tags = re.search(r'tags:\s*\[([^\]]+)\]', content)
        tags = [t.strip().strip('"') for t in m_tags.group(1).split(',')] if m_tags else []
        
        # Extract key content for search
        # 气味, 主治 summary
        qiwei = ''
        qm = re.search(r'## 气味\n(.+?)(?=## |\Z)', content, re.DOTALL)
        if qm:
            qiwei = qm.group(1).strip()[:300]
        
        zhuzhi = ''
        zm = re.search(r'## 主治\n(.+?)(?=## |\Z)', content, re.DOTALL)
        if zm:
            zhuzhi = zm.group(1).strip()[:300]
        
        entries.append({
            'file': f.name.replace('.md', ''),
            'title': title,
            'category': category,
            'tags': tags,
            'qiwei': qiwei,
            'zhuzhi': zhuzhi,
            'path': f'pages/herbs/{f.name}',
        })
    
    # Also index categories
    for f in sorted(CATEGORIES_DIR.glob('*.md')):
        content = f.read_text(encoding='utf-8')
        m = re.search(r'title:\s*"(.*?)"', content)
        title = m.group(1) if m else f.stem
        
        entries.append({
            'file': f.stem,
            'title': title,
            'category': 'category',
            'tags': ['category'],
            'qiwei': '',
            'zhuzhi': '',
            'path': f'pages/categories/{f.name}',
        })
    
    # Write index
    index_path = INDEX_DIR / 'summary_index.json'
    index_path.write_text(
        json.dumps({'count': len(entries), 'updated': datetime.now().isoformat(), 'entries': entries},
                   ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    # Also write a simple text index
    text_index = '\n'.join(f"{e['title']}\t{e['category']}\t{e['file']}" for e in entries)
    (INDEX_DIR / 'summary_index.txt').write_text(text_index, encoding='utf-8')
    
    print(f'Indexed {len(entries)} entries ({sum(1 for e in entries if e["category"] != "category")} herbs, {sum(1 for e in entries if e["category"] == "category")} categories)')


def update_main_index():
    """Update wiki/bcgj/index.md with accurate stats."""
    INDEX_PATH = Path(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\skills\llm-wiki-builder\wiki\bcgj\index.md')
    if not INDEX_PATH.exists():
        return
    
    herb_count = len(list(HERBS_DIR.glob('*.md')))
    cat_count = len(list(CATEGORIES_DIR.glob('*.md')))
    
    content = INDEX_PATH.read_text(encoding='utf-8')
    content = re.sub(r'\| 药物条目 \| .+', f'| 药物条目 | {herb_count}', content)
    content = re.sub(r'\| 页面总数 \| .+', f'| 页面总数 | {herb_count + cat_count}', content)
    content = re.sub(r'已完成首批结构化摄入，共 \d+ 个药物条目',
                     f'已完成结构化摄入，共 {herb_count} 个药物条目', content)
    content = re.sub(r'\*最后更新：.*', f'*最后更新：{datetime.now().strftime("%Y-%m-%d")}*', content)
    
    INDEX_PATH.write_text(content, encoding='utf-8')
    print(f'Updated main index: {herb_count} herbs, {cat_count} categories')


if __name__ == '__main__':
    build_index()
    update_main_index()
    print('Done.')
