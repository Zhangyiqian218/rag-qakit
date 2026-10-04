"""快速演示：对示例数据跑完整流程，打印质量报告并导出 JSONL。

直接运行：  py examples/demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许在未安装的情况下直接运行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_qakit import export_chunks, process_file

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sample.md"

chunks, report = process_file(str(DATA), chunk_size=400, overlap=60)

print("=== 质量报告 ===")
print(report.summary())

print("\n=== 切分片段 ===")
for c in chunks:
    preview = c.content.replace("\n", " ")
    print(f"[{c.id}] {preview[:50]}...")

out = ROOT / "data" / "sample_chunks.jsonl"
export_chunks(chunks, str(out))
print(f"\n已导出：{out}")
