"""命令行入口。

用法：
  py -m rag_qakit process <文件> --out chunks.jsonl
  py -m rag_qakit quality <文件>
"""
from __future__ import annotations

import argparse
import sys

from .pipeline import export_chunks, process_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="rag_qakit", description="RAG 数据处理与质量评估工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("process", help="处理文件并导出 JSONL")
    p.add_argument("path")
    p.add_argument("--out", default="chunks.jsonl")
    p.add_argument("--chunk-size", type=int, default=500)
    p.add_argument("--overlap", type=int, default=80)
    p.add_argument("--strategy", choices=["recursive", "fixed"], default="recursive")

    q = sub.add_parser("quality", help="仅输出质量报告")
    q.add_argument("path")
    q.add_argument("--chunk-size", type=int, default=500)

    args = parser.parse_args(argv)
    if args.command == "process":
        chunks, report = process_file(
            args.path, chunk_size=args.chunk_size, overlap=args.overlap, strategy=args.strategy
        )
        export_chunks(chunks, args.out)
        print(report.summary())
        print(f"已导出 {len(chunks)} 个片段到 {args.out}")
    elif args.command == "quality":
        _, report = process_file(args.path, chunk_size=args.chunk_size)
        print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
