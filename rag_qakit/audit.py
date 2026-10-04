"""audit.py：基于多模型行为的数据可靠性审计（工具的差异化核心）。

思路：不是看文本"长什么样"，而是让一批大模型回答同一批问题，
再从模型的回答行为，反推出数据 / 题目本身的问题：

- 所有模型（含强模型）都答错        -> 疑似标准答案错误 / 超纲
- 强弱模型通过率没差别（区分度低）   -> 低质量题，没有区分能力
- 该题对错与模型总分负相关          -> 极强的"答案可能错"信号
- 各模型答案高度发散               -> 题目表述有歧义

其中区分度、题总相关等指标来自经典心理测量学（项目反应理论），
可解释、可复现，比"只看感觉"更可靠。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _pearson(x: List[float], y: List[float]) -> float:
    """两个向量的 Pearson 相关系数（标准库实现）。"""
    n = len(x)
    if n == 0:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return 0.0
    return num / (sx * sy)


@dataclass
class ModelRecord:
    """单个模型对单道题的作答记录。"""

    model: str
    is_correct: bool
    answer: str = ""


@dataclass
class ItemAudit:
    """单道题的审计结果。"""

    question_id: str
    pass_rate: float
    discrimination: float          # 项目区分度：强 30% - 弱 30% 通过率
    total_correlation: float       # 题总相关：该题对错与模型总分
    divergence: float              # 答题发散率：不同答案占比
    flags: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """整批数据的审计报告。"""

    total_items: int
    total_models: int
    items: List[ItemAudit] = field(default_factory=list)

    @property
    def flagged_items(self) -> List[ItemAudit]:
        return [it for it in self.items if it.flags]

    def reliability_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return 1 - len(self.flagged_items) / self.total_items

    def summary(self) -> str:
        kinds = ("疑似错误答案", "低区分度", "表述歧义", "全部答错")
        lines = [
            f"题目总数：{self.total_items}（参与模型 {self.total_models} 个）",
            f"疑似问题题数：{len(self.flagged_items)}",
            f"数据可靠率：{self.reliability_rate():.1%}",
        ]
        for k in kinds:
            c = sum(1 for it in self.items for f in it.flags if f == k)
            if c:
                lines.append(f"  - {k}：{c} 题")
        return "\n".join(lines)


def _fraction_unique_answers(records: List[ModelRecord]) -> float:
    answers = [r.answer.strip() for r in records if r.answer]
    if not answers:
        return 0.0
    return len(set(answers)) / len(answers)


def audit_answer_log(
    question_records: Dict[str, List[ModelRecord]],
    discrimination_floor: float = 0.15,
    divergence_floor: float = 0.7,
    all_wrong_floor: float = 0.1,
) -> AuditReport:
    """对一批「题目 -> 多个模型作答记录」做审计。

    题目记录示例：
        {
          "q1": [ModelRecord("gpt-4", True, "1000Hz"),
                 ModelRecord("deepseek", False, "1Hz")],
          ...
        }
    """
    qids = list(question_records.keys())
    models = sorted({r.model for recs in question_records.values() for r in recs})
    model_index = {m: i for i, m in enumerate(models)}

    # 每个模型的总分（答对题数），用于排序强弱与题总相关
    totals = [0.0] * len(models)
    correctness_matrix: Dict[str, List[float]] = {}
    for qid in qids:
        vec = [0.0] * len(models)
        for r in question_records[qid]:
            vec[model_index[r.model]] = 1.0 if r.is_correct else 0.0
            totals[model_index[r.model]] += 1 if r.is_correct else 0
        correctness_matrix[qid] = vec

    # 强 30% / 弱 30% 模型（按总分）
    order = sorted(range(len(models)), key=lambda i: totals[i])
    k = max(1, math.ceil(len(models) * 0.3))
    weak_idx = set(order[:k])
    strong_idx = set(order[-k:])

    items: List[ItemAudit] = []
    for qid in qids:
        recs = question_records[qid]
        vec = correctness_matrix[qid]
        n = len(recs)
        pass_rate = sum(vec) / len(vec) if vec else 0.0

        strong_p = sum(vec[i] for i in strong_idx) / len(strong_idx)
        weak_p = sum(vec[i] for i in weak_idx) / len(weak_idx)
        discrimination = strong_p - weak_p

        total_corr = _pearson(vec, totals)
        divergence = _fraction_unique_answers(recs)

        flags: List[str] = []
        if pass_rate <= all_wrong_floor:
            flags.append("全部答错")
        # 负相关：越强的模型越答错，几乎可以断定答案有问题
        if total_corr < 0:
            flags.append("疑似错误答案")
        if discrimination < discrimination_floor and "疑似错误答案" not in flags:
            flags.append("低区分度")
        if divergence >= divergence_floor:
            flags.append("表述歧义")

        items.append(
            ItemAudit(
                question_id=qid,
                pass_rate=pass_rate,
                discrimination=discrimination,
                total_correlation=total_corr,
                divergence=divergence,
                flags=flags,
            )
        )

    return AuditReport(
        total_items=len(qids),
        total_models=len(models),
        items=items,
    )
