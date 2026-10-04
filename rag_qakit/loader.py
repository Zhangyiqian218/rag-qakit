"""文档加载器：把本地文件统一加载成 Document 对象。

支持纯文本类格式：.txt / .md / .markdown / .json / .jsonl。
PDF / Word 等二进制格式建议先转成 Markdown，或后续接入可选依赖。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Union

from .models import Document

PathLike = Union[str, os.PathLike]
SUPPORTED_EXTS = (".txt", ".md", ".markdown", ".jsonl", ".json")


def load_file(path: PathLike, doc_id: str | None = None) -> Document:
    """加载单个文件为 Document。"""
    path = Path(path)
    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    if suffix == ".jsonl":
        # 常见问答数据：每行一个对象，尝试拼出可读的 Q/A 文本
        lines = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                lines.append(line)
                continue
            q = obj.get("question") or obj.get("prompt") or obj.get("input")
            a = obj.get("answer") or obj.get("completion") or obj.get("output")
            parts = [f"Q: {q}" if q else None, f"A: {a}" if a else None]
            lines.append("\n".join(p for p in parts if p) or json.dumps(obj, ensure_ascii=False))
        content = "\n\n".join(lines)
    elif suffix == ".json":
        obj = json.loads(content)
        if isinstance(obj, (list, dict)):
            content = json.dumps(obj, ensure_ascii=False, indent=2)

    return Document(
        id=doc_id or path.stem,
        content=content,
        source=str(path),
        metadata={"suffix": suffix},
    )


def load_directory(path: PathLike, exts: tuple = SUPPORTED_EXTS) -> List[Document]:
    """加载目录下所有支持的文本文件。"""
    root = Path(path)
    docs = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            docs.append(load_file(p))
    return docs
