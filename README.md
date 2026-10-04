# rag-qakit

> 面向 RAG 的数据处理与**多模型质量审计**工具包：既把原始文档变成干净、可检索的知识库片段，也用「多模型交叉评测 + 心理测量指标」，**从模型的回答行为反推数据本身的问题**。

大多数 RAG 工具只负责"把文档切开"。但在真实的大模型落地中，**喂进去的数据质量直接决定检索效果和回答质量**——重复内容、歧义题目、错误答案、过短片段都会造成召回噪声和幻觉。

`rag-qakit` 提供两层能力：

1. **数据处理流水线**：加载 → 清洗 → 切分 → 质检 → 导出，在切分的同时自动发现并报告问题；
2. **多模型行为审计（差异化核心）**：让一批大模型回答同一批问题，从回答行为反推数据问题——所有模型都答错（可能答案错）、强弱模型无差别（低区分度）、答案高度发散（表述歧义）。

核心模块**零第三方依赖**（仅用 Python 标准库），开箱即用、易于阅读和二次开发。

## 特性

- **多格式加载**：`.txt / .md / .jsonl / .json`，自动把常见问答数据（Q/A、prompt/completion）整理成可读文本。
- **清洗归一化**：规范化空白、合并空行、按行去重。
- **两种切分策略**：
  - `recursive`（默认）：优先按段落 / 句子边界切分，尽量不截断语义；
  - `fixed`：固定长度 + 重叠窗口（overlap）。
- **质量评估**：
  - 自动标记过短 / 过长片段；
  - **段落级重复检测**（归一化标点空白后比对，即使重复段落被切进不同 chunk 也能发现）；
  - 输出质量报告与通过率。
- **多模型行为审计（差异化核心，`audit.py`）**：
  - 输入一批模型的答题日志，计算**项目区分度**（强 30% 减弱 30% 通过率）、**题总相关**（该题对错与模型总分）、**答题发散率**等心理测量指标；
  - 负相关 → 疑似答案错误；区分度低 → 低质量题；高发散 → 表述歧义；
  - 指标可解释、可复现，配套 `examples/audit_dashboard.html` 可视化看板。
- **可选向量化**：内置 OpenAI 兼容 Embedding 接口调用（标准库实现）。
- **可导出**：一键导出 JSONL，可直接导入向量库或 Dify / Coze 等平台。
- **CLI + Python API**：既能命令行跑批，也能嵌入工程代码。

## 工作流

**数据处理流水线：**

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

**多模型行为审计：**

```
一批问题
  │  多个大模型分别作答
  ▼
分层判卷（结构 / 数字 / 字符串 / 符号 / LM 判官）
  │
  ▼
心理测量指标（区分度 / 题总相关 / 发散率）
  │
  ▼
反推问题数据：错误答案 / 低区分度 / 表述歧义
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

## 多模型审计示例

```python
from rag_qakit import audit_answer_log, ModelRecord

# 同一道题，收集多个模型的作答（is_correct 由判卷层给出）
data = {
    "q1": [
        ModelRecord("gpt-4", True, "1000Hz"),
        ModelRecord("deepseek", False, "1Hz"),
        # ... 其余模型
    ],
}
report = audit_answer_log(data)
print(report.summary())
```

命令行跑示例，或直接打开可视化看板：

```bash
py examples/audit_demo.py
# 浏览器打开 examples/audit_dashboard.html 查看可交互审计报告
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
│   ├── quality.py     # 片段质量评估（长度 / 重复）
│   ├── audit.py       # 多模型行为审计（差异化核心）
│   ├── embedder.py    # 可选：Embedding 接口
│   ├── pipeline.py    # 一站式 API
│   └── cli.py         # 命令行入口
├── examples/
│   ├── demo.py
│   ├── audit_demo.py
│   └── audit_dashboard.html   # 可交互审计看板
├── data/sample.md
├── pyproject.toml
└── LICENSE
```

## 设计理念

**先高召回、再精准确认**：先用可量化规则高召回地圈出疑似问题，再交人工或模型复核——既不漏掉问题，也不必对全部数据逐条排查。

**多模型行为比文本形态更有说服力**：文本 linter 能发现"长得像重复"的问题，却发现不了"答案错误、题目歧义、没有区分度"这类深层问题。让多个模型作答、从统计行为反推，正是经典心理测量学（区分度、项目分析）的思路，可解释、可复现。

## Roadmap

- [x] 多模型交叉评测 + 心理测量指标审计（`audit.py`）
- [x] 可视化审计看板（`audit_dashboard.html`）
- [ ] 语义切分（基于 embedding 的相邻句合并）
- [ ] 检索结果质量评估（召回命中率、上下文相关性）
- [ ] 语义级矛盾检测（多模型/LLM 判官）
- [ ] 支持 PDF / Word 直接解析（可选依赖）

## License

[MIT](LICENSE)
