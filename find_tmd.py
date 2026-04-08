# -*- coding: utf-8 -*-
import re

with open(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\nihaixia_shennong.txt', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# 从天门冬章节开始（第981行）往后找，找到下一章节为止
found = False
section_lines = []
for i in range(980, min(1100, len(lines))):
    line = lines[i]
    # 检测是否是下一个章节标题（带编号的草药名）
    if found:
        if re.match(r'^\s*[三四五六七八九十百]+[、．.]', line) and line.strip() != '二十二、天门冬':
            break
    if '二十二、天门冬' in line:
        found = True
    if found:
        section_lines.append(line)

print('\n'.join(section_lines))
