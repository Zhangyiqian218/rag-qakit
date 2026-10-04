"""可选模块：调用 OpenAI 兼容的 Embedding 接口，把文本向量化。

不引入第三方依赖，用标准库 urllib；通过环境变量 RAGQAKIT_EMBED_API_KEY 传密钥。
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import List


def embed_texts(
    texts: List[str],
    model: str = "text-embedding-3-small",
    base_url: str = "https://api.openai.com/v1",
) -> List[List[float]]:
    """把一组文本转成向量。"""
    api_key = os.environ.get("RAGQAKIT_EMBED_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 RAGQAKIT_EMBED_API_KEY")

    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/embeddings",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
