#!/usr/bin/env python3
"""Clean up noise herb pages from the bcgj wiki."""

import re
from pathlib import Path

HERBS_DIR = Path(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\skills\llm-wiki-builder\wiki\bcgj\pages\herbs')

# Noise patterns in filenames
NOISE_PATTERNS = [
    # Commentary attributions
    r'^时珍曰', r'^弘景曰', r'^宗曰', r'^颂曰', r'^藏器曰', r'^保升曰', r'^禹锡曰',
    r'^雷曰', r'^杲曰', r'^好古曰', r'^之才曰', r'^普曰', r'^元素曰', r'^震亨曰',
    r'^孟诜曰', r'^别录曰', r'^恭曰', r'^韩保升曰', r'^按吴普', r'^苏颂曰',
    r'^寇氏', r'^沈括', r'^郭璞', r'^王好古', r'^甄权曰', r'^大明曰', r'^王冰曰',
    r'^岐伯曰', r'^徐之才曰', r'^苏恭曰', r'^东垣', r'^丹溪', r'^李当之',
    # Explanatory phrases that leaked as names
    r'^今并', r'^今俗', r'^今人', r'^故曰', r'^故名', r'^皆以', r'^并以',
    r'^象其', r'^其种', r'^其性', r'^其根', r'^其砂', r'^其功', r'^其花',
    r'^其种', r'^其叶', r'^其味', r'^其气', r'^其形', r'^其状',
    r'^南人谓', r'^状如', r'^丈人', r'^与杜', r'^以能', r'^驼象', r'^鲻色',
    r'^黑色', r'^龙脑', r'^陶以柳', r'^子颇', r'^即木', r'^即其', r'^此草',
    r'^北人曰', r'^南人亦', r'^后人讹', r'^楚辞云', r'^梵书谓', r'^言其',
    r'^世谓', r'^则鼠', r'^每三五', r'^物也今', r'^河南北',
    r'^梵书谓', r'^言其', r'^旧附', r'^志曰',
    r'^肉多', r'^曰文', r'^曰是', r'^或作', r'^雷以', r'^诸朽', r'^诸蛇',
    r'^诸血', r'^诸铁', r'^火炭母', r'^火病', r'^下痔', r'^二物', r'^茎叶',
    r'^及松', r'^张宛', r'^葛洪', r'^机曰', r'^曰是众珀', r'^饭而', r'^香馥',
    r'^今并', r'^即此', r'^旧附桐下', r'^可碾为珠',
    r'^肠风', r'^风毒', r'^痈肿', r'^下瘀', r'^名金铃',
    r'^按', r'^又按', r'^谨按', r'^臣按', r'^又云', r'^又方', r'^又治',
    r'^及己', r'^本草',
    # Section headers like "草部第十二卷"
    r'^[草木谷果菜虫禽兽鳞介水火土金人服器]部第.+卷',
    # Very short non-Chinese
]

# Exact noise matches
EXACT_NOISE = {
    '东', '中', '西', '南', '北', '上', '下', '左', '右', '前', '后',
    '大', '小', '多', '少', '有', '无', '又', '也', '者', '而', '以', '之',
    '故', '可', '能', '为', '是', '在', '于', '与', '同', '并', '及',
    '或', '其', '此', '彼', '所', '从', '由', '因', '当', '若', '如',
    '则', '乃', '即', '亦', '已', '未', '非', '不', '无', '莫', '勿',
    '每', '凡', '皆', '俱', '咸', '悉', '尽', '都', '总', '共',
    '今', '古', '旧', '新', '旧附', '又出',
    '圣惠方', '外台秘要', '圣济总录', '千金方', '全幼心鉴',
    '直指方', '经验方', '广利方', '梅师方', '证治要诀',
    '外科精要方', '痈疽方', '保命集', '幼幼新书', '得效方', '奇方',
    '瑞香', '风尾草', '及己', '詹糖香',
}


def should_remove(filepath: Path) -> tuple:
    """Returns (should_remove: bool, reason: str)"""
    name = filepath.stem
    
    # 1. Exact noise
    if name in EXACT_NOISE:
        return True, f'exact noise: {name}'
    
    # 2. Pattern match
    for pat in NOISE_PATTERNS:
        if re.match(pat, name):
            return True, f'pattern {pat}: {name}'
    
    # 3. Check file content quality
    try:
        content = filepath.read_text(encoding='utf-8')
        # Must have at least some standard sections
        has_section = any(
            section in content
            for section in ['# 气味', '# 主治', '# 集解', '# 释名', '# 发明', '# 附方']
        )
        if not has_section and len(content.strip()) < 300:
            return True, f'short and no sections: {name}'
        
        # If the "name" doesn't appear as the title in the page, it's noise
        if f'# {name}' not in content and f'title:' in content:
            # Extract actual title from front matter
            m = re.search(r'title:\s*"\[.*?\](.*?)"', content)
            if m:
                actual_title = m.group(1)
                if len(actual_title) > 50:
                    return True, f'title mismatch: {name} -> {actual_title[:30]}'
    except Exception as e:
        return True, f'read error: {e}'
    
    return False, ''


def main():
    removed = 0
    kept = 0
    
    for f in sorted(HERBS_DIR.glob('*.md')):
        remove, reason = should_remove(f)
        if remove:
            f.unlink()
            removed += 1
        else:
            kept += 1
    
    print(f'Done. Kept: {kept}, Removed: {removed}')


if __name__ == '__main__':
    main()
