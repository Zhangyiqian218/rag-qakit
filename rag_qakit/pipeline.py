"""高层一站式 API：加载 -> 清洗 -> 切分 -> 质量评估。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from .chunker import split_document
from .cleaner import clean_document
from .loader import load_file
from .models import Chunk
from .quality import QualityReport, assess_chunks


def process_file(
    path: str,
    chunk_size: int = 500,
    overlap: int = 80,
    strategy: str = "recursive",
) -> Tuple[List[Chunk], QualityReport]:
    """对单个文件跑完整处理流程，返回 chunks 和质量报告。"""
    doc = clean_document(load_file(path))
    chunks = split_document(doc, chunk_size=chunk_size, overlap=overlap, strategy=strategy)
    report = assess_chunks(chunks, max_len=chunk_size * 2)
    return chunks, report


def export_chunks(chunks: List[Chunk], out_path: str) -> None:
    """把 chunks 导出为 JSONL，可直接导入向量库或 Dify / Coze 等平台。"""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(
                json.dumps(
                    {
                        "id": c.id,
                        "doc_id": c.doc_id,
                        "content": c.content,
                        "metadata": c.metadata,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
