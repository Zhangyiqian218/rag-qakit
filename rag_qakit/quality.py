"""数据质量评估：对切分结果做质量打分并生成报告。

这是工具的差异化模块：不只是切分，还能自动发现：
- 过短（信息不足）或过长（检索不精准）的片段
- 段落级的高度重复/冗余内容（即使重复段落被切进不同 chunk）

设计思路与我此前的 LLM 数据质检工作一致：先按可量化规则高召回圈出问题，
再交人工或模型复核，兼顾召回率与效率。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from .models import Chunk

_PUNCT_SPACE = re.compile(r"[\s\u3000，。！？、；：,.!?;:（）()「」\"'#-]+")


@dataclass
class QualityIssue:
    chunk_id: str
    issue_type: str
    severity: str  # low / medium / high
    detail: str


@dataclass
class QualityReport:
    total_chunks: int
    issues: List[QualityIssue] = field(default_factory=list)
    stats: Dict[str, float] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """无 high 级别问题的片段占比。"""
        if self.total_chunks == 0:
            return 0.0
        flagged = {i.chunk_id for i in self.issues if i.severity == "high"}
        return 1 - len(flagged) / self.total_chunks

    def summary(self) -> str:
        high = sum(1 for i in self.issues if i.severity == "high")
        lines = [
            f"片段总数：{self.total_chunks}",
            f"高严重问题片段数：{high}",
            f"质量通过率（无高严重问题）：{self.pass_rate:.1%}",
        ]
        for k, v in self.stats.items():
            lines.append(f"{k}：{v:.2f}")
        return "\n".join(lines)


def _norm_for_compare(text: str) -> str:
    """归一化后再比较：去掉空白和标点，降低写法差异对查重的干扰。"""
    return _PUNCT_SPACE.sub("", text)


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_for_compare(a), _norm_for_compare(b)).ratio()


def _split_units(text: str, min_len: int = 15) -> List[str]:
    """把 chunk 拆成用于查重的段落单元，忽略标题等短行。"""
    return [p.strip() for p in re.split(r"\n+", text) if len(p.strip()) >= min_len]


def assess_chunks(
    chunks: List[Chunk],
    min_len: int = 20,
    max_len: int = 1000,
    duplicate_threshold: float = 0.88,
) -> QualityReport:
    """对一批 Chunk 做质量评估。"""
    issues: List[QualityIssue] = []
    lengths: List[int] = []

    # 1) 长度检查
    for c in chunks:
        n = len(c.content)
        lengths.append(n)
        if n < min_len:
            issues.append(QualityIssue(c.id, "too_short", "medium", f"长度 {n} < {min_len}，信息可能不足"))
        if n > max_len:
            issues.append(QualityIssue(c.id, "too_long", "medium", f"长度 {n} > {max_len}，检索可能不精准"))

    # 2) 段落级重复检测：收集所有 (chunk_id, 段落)，跨 chunk 两两比对
    units: List[Tuple[str, str]] = []
    for c in chunks:
        for u in _split_units(c.content):
            units.append((c.id, u))

    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            cid_i, u_i = units[i]
            cid_j, u_j = units[j]
            sim = _similarity(u_i, u_j)
            if sim >= duplicate_threshold:
                # 无论两个重复段落是否落在同一个 chunk，都应报告
                where = "同一片段内" if cid_i == cid_j else f"与 {cid_i} 中段落"
                issues.append(
                    QualityIssue(
                        cid_j,
                        "duplicate",
                        "high",
                        f"{where}相似度 {sim:.0%}，疑似重复内容",
                    )
                )

    avg_len = sum(lengths) / len(lengths) if lengths else 0.0
    return QualityReport(
        total_chunks=len(chunks),
        issues=issues,
        stats={"平均片段长度": float(avg_len)},
    )
