"""文本清洗器：规范化空白、按行去重，为切分做准备。"""
from __future__ import annotations

import re

from .models import Document

_INLINE_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """规范化空白：去除行尾多余空格、合并连续空行。"""
    lines = [_INLINE_SPACE.sub(" ", line).rstrip() for line in text.splitlines()]
    text = "\n".join(lines)
    return _MULTI_NEWLINE.sub("\n\n", text).strip()


def clean_document(doc: Document, dedup_lines: bool = True) -> Document:
    """清洗单个文档；可选地按行去重。"""
    text = normalize_text(doc.content)
    if dedup_lines:
        seen = set()
        kept = []
        for line in text.splitlines():
            key = line.strip()
            if key and key in seen:
                continue
            seen.add(key)
            kept.append(line)
        text = "\n".join(kept)
    doc.content = text
    doc.metadata["cleaned"] = True
    return doc
