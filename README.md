# llm-wiki-builder

> 为大型知识库而生：基于 Karpathy 三层架构的个人 LLM Wiki 构建工具

---

## 🌟 项目简介

llm-wiki-builder 是一个**结构化 Wiki 知识库管理工具**，专为需要系统化整理大量资料的个人或小团队设计。

它遵循“三层架构”：
1. **Raw** — 原始资料（PDF、笔记、数据），只读 immutable
2. **Wiki** — 结构化 Markdown 页面（单一可信源）
3. **Schema** — CLAUDE.md 定义约定（类型、Front Matter、链接规则）

通过 Pipeline + Health Check + Index Generator 组合，让 600+ 页的知识库也能井井有条。

---

## ✨ 核心特性

- ✅ **自动化流水线** — 一次配置，持续 ingest 新资料
- ✅ **健康检查** — 自动发现断链、孤儿页、必填字段缺失
- ✅ **全局索引生成** — 一键生成带统计、分类、检索表的 `index.md`
- ✅ **多领域适配** — 中医、学术研究、个人笔记、技术文档皆可
- ✅ **Obsidian 友好** — 原生支持 `[[wikilink]]` 格式

---

## 🚀 快速开始

```bash
# 1. 克隆或复制此 skill 到你的项目
cp -r skills/llm-wiki-builder <你的项目>/skills/

# 2. 按需修改 scripts/pipeline.py 中的 WIKI_SUBDIR 等配置
# 3. 运行健康检查
python <你的项目>/skills/llm-wiki-builder/scripts/health_check.py

# 4. （可选）生成全局索引
python <你的项目>/skills/llm-wiki-builder/scripts/generate_global_index.py
```

详细配置步骤见 [SKILL.md](skills/llm-wiki-builder/SKILL.md)。

---

## 📦 新功能：全局索引生成器

### 问题
资料多了以后，没有一个“总目录”能快速浏览和检索所有页面。

### 方案
`scripts/generate_global_index.py` 会：
- 递归扫描 `wiki/<topic>/` 下所有 `.md`
- 解析 YAML Front Matter（title, type, source, chapter, status…）
- 生成 `wiki/<topic>/index.md`，包含：
  - 📊 概览统计（总页数、类型分布、经典分类）
  - 🔍 快速检索表（按名称排序，含链接）
  - 🆕 最近更新（最近修改的 20 条）

### 效果示例
以 2,644 页的中医知识库为例，生成的 index 提供了：
- 本草纲目（1,462 页） / 金匮要略（451 页） / 倪海厦经典配方（277 页）
- 按 A-Z 快速定位药材或方剂
- 一键跳转，无需逐层点开目录

> 详见：[wiki/中医/index.md](skills/llm-wiki-builder/wiki/中医/index.md)

---

## 🗂️ 目录结构

```
llm-wiki-builder/
├── raw/                    # 原始资料（PDF、txt、notes）
│   ├── documents/
│   ├── notes/
│   └── data/
├── wiki/
│   └── 中医/              # 你的主题（示例）
│       ├── CLAUDE.md      # 本主题的 Schema
│       ├── index.md       # 全局索引（自动生成）
│       ├── log.md         # 变更日志（只追加）
│       ├── _maintenance/  # 健康报告、pipeline 状态
│       ├── 神农百草经/
│       │   └── 中药名/
│       ├── 金匮要略/
│       │   └── 配方/
│       ├── 本草纲目/
│       └── 倪海厦经典配方/
├── scripts/
│   ├── pipeline.py        #  ingestion 流水线
│   ├── health_check.py    #  健康检查
│   └── generate_global_index.py  # ✨ 新增
└── prompts/
    └── wiki_builder.md    #  LLM  ingestion 提示模板
```

---

## 🛠️ 脚本说明

| 脚本 | 用途 |
|------|------|
| `pipeline.py` | 处理 raw/ 中的新文件，生成 wiki 页面 |
| `health_check.py` | 检查断链、孤儿页、必填字段等 |
| `generate_global_index.py` | 生成全局 `index.md`（检索入口） |

---

## 📖 使用文档

完整使用指南请阅读：[SKILL.md](skills/llm-wiki-builder/SKILL.md)

内容包括：
- 环境准备与配置
- Ingest 工作流（手动 / 自动）
- Query 工作流
- Lint 工作流
- CLAUDE.md 约定规范
- 领域定制示例

---

## 🤝 贡献与反馈

欢迎提 Issue 和 Pull Request。

如果你在构建自己的知识库时遇到问题，可以在 [Discussions](https://github.com/jownda/llm-wiki-builder/discussions) 中提问。

---

## 📄 许可证

MIT License。详见 [LICENSE](LICENSE) 文件。

---

**让知识从“散落”到“聚合”，一张表管全部。**
