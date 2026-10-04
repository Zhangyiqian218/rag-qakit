# rag-qakit

> 面向 RAG 的轻量数据处理与**质量评估**工具包：一行命令把原始文档变成干净、可检索、质量可控的知识库片段。

大多数 RAG 工具只负责"把文档切开"。但在真实的大模型落地中，**喂进去的数据质量直接决定检索效果和回答质量**——重复内容、过短片段、被截断的语义都会造成召回噪声和幻觉。`rag-qakit` 把「数据处理」与「数据质量」放在同一条流水线里，在切分的同时自动发现并报告问题。

核心模块**零第三方依赖**（仅用 Python 标准库），开箱即用、易于阅读和二次开发。

## 特性

- **多格式加载**：`.txt / .md / .jsonl / .json`，自动把常见问答数据（Q/A、prompt/completion）整理成可读文本。
- **清洗归一化**：规范化空白、合并空行、按行去重。
- **两种切分策略**：
  - `recursive`（默认）：优先按段落 / 句子边界切分，尽量不截断语义；
  - `fixed`：固定长度 + 重叠窗口（overlap）。
- **质量评估（核心亮点）**：
  - 自动标记过短 / 过长片段；
  - **段落级重复检测**（归一化标点空白后比对，即使重复段落被切进不同 chunk 也能发现）；
  - 输出质量报告与通过率。
- **可选向量化**：内置 OpenAI 兼容 Embedding 接口调用（标准库实现）。
- **可导出**：一键导出 JSONL，可直接导入向量库或 Dify / Coze 等平台。
- **CLI + Python API**：既能命令行跑批，也能嵌入工程代码。

## 工作流

```
原始文档
  │  加载（loader）
  ▼
清洗归一化（cleaner）
  │
  ▼
切分 chunk（chunker：recursive / fixed）
  │
  ├──► 质量评估（quality：长度 / 重复 / 通过率）
  │
  ▼
导出 JSONL ──► 向量库 / Dify / Coze
（可选：embedding 向量化）
```

## 安装

```bash
# 直接使用：核心功能零依赖，克隆后即可运行
git clone https://github.com/Zhangyiqian218/rag-qakit.git
cd rag-qakit
py examples/demo.py

# 或以可编辑模式安装，获得 rag-qakit 命令
py -m pip install -e .
```

## 快速开始

命令行：

```bash
# 处理文件并导出 JSONL
py -m rag_qakit process data/sample.md --out chunks.jsonl

# 只看质量报告
py -m rag_qakit quality data/sample.md
```

Python API：

```python
from rag_qakit import process_file, export_chunks

chunks, report = process_file("data/sample.md", chunk_size=400, overlap=60)

print(report.summary())
export_chunks(chunks, "chunks.jsonl")
```

## 质量报告示例

对一份含重复段落的文档，工具会自动圈出问题：

```
片段总数：3
高严重问题片段数：1
质量通过率（无高严重问题）：66.7%
平均片段长度：329.00
```

## 项目结构

```
rag-qakit/
├── rag_qakit/
│   ├── models.py      # Document / Chunk 数据模型
│   ├── loader.py      # 文档加载
│   ├── cleaner.py     # 清洗归一化
│   ├── chunker.py     # 切分（recursive / fixed）
│   ├── quality.py     # 质量评估（差异化核心）
│   ├── embedder.py    # 可选：Embedding 接口
│   ├── pipeline.py    # 一站式 API
│   └── cli.py         # 命令行入口
├── examples/demo.py
├── data/sample.md
├── pyproject.toml
└── LICENSE
```

## 设计理念

质检模块沿用了我在 LLM 数据工程实践中的方法：**先用可量化规则高召回地圈出疑似问题，再交人工或模型复核**——这样既不会漏掉问题，也不必对全部数据逐条人工排查。相比只做切分的工具，`rag-qakit` 更关注"进知识库之前，数据到底可不可靠"。

## Roadmap

- [ ] 语义切分（基于 embedding 的相邻句合并）
- [ ] 检索结果质量评估（召回命中率、上下文相关性）
- [ ] 多模型交叉验证，对问答类数据做一致性校验
- [ ] 支持 PDF / Word 直接解析（可选依赖）

## License

[MIT](LICENSE)
