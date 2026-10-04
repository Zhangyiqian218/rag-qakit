"""核心数据模型：Document（原始文档）与 Chunk（切分后的片段）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Document:
    """一份加载后的原始文档。"""

    id: str
    content: str
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """文档切分后的片段，是 RAG 检索的最小单元。"""

    id: str
    doc_id: str
    content: str
    index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
