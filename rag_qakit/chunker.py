"""文本切分器：把文档切成适合检索的 Chunk。

提供两种策略：
- fixed：按字符长度切分，支持重叠（overlap）
- recursive：优先按段落/句子边界切分，尽量不截断语义
"""
from __future__ import annotations

from typing import List

from .models import Chunk, Document


def _fixed_windows(text: str, chunk_size: int, overlap: int) -> List[str]:
    """按固定字符长度滑动切分。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正整数")
    step = max(1, chunk_size - overlap)
    pieces = []
    start = 0
    while start < len(text):
        window = text[start:start + chunk_size].strip()
        if window:
            pieces.append(window)
        start += step
    return pieces


def _recursive_split(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    """递归切分：优先用更粗的分隔符，超长再用更细的。"""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if len(separators) == 1:
        return _fixed_windows(text, chunk_size, 0)

    sep = separators[0]
    pieces = text.split(sep) if sep else list(text)
    results: List[str] = []
    buffer = ""
    for piece in pieces:
        piece = piece + sep
        if len(buffer) + len(piece) <= chunk_size:
            buffer += piece
        else:
            if buffer.strip():
                results.extend(_recursive_split(buffer.strip(), chunk_size, separators[1:]))
            buffer = piece
    if buffer.strip():
        results.extend(_recursive_split(buffer.strip(), chunk_size, separators[1:]))
    return results


def split_document(
    doc: Document,
    chunk_size: int = 500,
    overlap: int = 80,
    strategy: str = "recursive",
) -> List[Chunk]:
    """把文档切成 Chunk 列表。"""
    text = doc.content.strip()
    if strategy == "fixed":
        pieces = _fixed_windows(text, chunk_size, overlap)
    elif strategy == "recursive":
        separators = ["\n\n", "\n", "。", "！", "？", ". ", " ", ""]
        pieces = _recursive_split(text, chunk_size, separators)
    else:
        raise ValueError(f"未知切分策略：{strategy}")

    return [
        Chunk(
            id=f"{doc.id}-{i}",
            doc_id=doc.id,
            content=content.strip(),
            index=i,
            metadata={"char_len": len(content.strip())},
        )
        for i, content in enumerate(pieces)
    ]
