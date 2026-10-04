"""审计工具演示：构造 12 个强弱不同的模型与几道不同类型的题，
验证能否从模型行为反推出数据问题。

运行：  py examples/audit_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag_qakit.audit import ModelRecord, audit_answer_log

# 12 个模型，编号越靠后越强
MODELS = [f"model_{i:02d}" for i in range(1, 13)]


def records(correct_idx, answers=None):
    out = []
    for i, m in enumerate(MODELS):
        ok = i in correct_idx
        if answers and i in answers:
            ans = answers[i]
        else:
            ans = "1000Hz" if ok else "1Hz"
        out.append(ModelRecord(m, ok, ans))
    return out


all_idx = set(range(12))
data = {
    "q_normal_1": records({6, 7, 8, 9, 10, 11}),        # 强模型答对，正常
    "q_normal_2": records({8, 9, 10, 11}),               # 最强的 4 个答对，正常
    "q_wrong_answer": records({0, 1, 2, 3, 4, 5}),       # 弱答对、强答错，负相关
    "q_low_disc": records(all_idx),                      # 全答对，无区分度
    "q_ambiguous": records(
        {6, 7, 8, 9, 10, 11},
        answers={i: f"ans_{i}" for i in range(12)},      # 答案各不相同，高发散
    ),
}

report = audit_answer_log(data)
print("=== 审计报告 ===")
print(report.summary())

print("\n=== 逐题明细 ===")
for it in report.items:
    tag = "、".join(it.flags) if it.flags else "正常"
    print(
        f"{it.question_id}: 通过率{it.pass_rate:.0%} "
        f"区分度{it.discrimination:.2f} 题总相关{it.total_correlation:.2f} "
        f"发散{it.divergence:.2f} -> {tag}"
    )
