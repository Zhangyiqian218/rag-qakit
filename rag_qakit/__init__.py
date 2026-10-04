"""rag_qakit：面向 RAG 的数据处理与质量评估工具包。"""
from .chunker import split_document
from .cleaner import clean_document, normalize_text
from .loader import load_directory, load_file
from .models import Chunk, Document
from .pipeline import export_chunks, process_file
from .quality import QualityReport, assess_chunks

__version__ = "0.1.0"

__all__ = [
    "Document",
    "Chunk",
    "load_file",
    "load_directory",
    "clean_document",
    "normalize_text",
    "split_document",
    "assess_chunks",
    "QualityReport",
    "process_file",
    "export_chunks",
]
