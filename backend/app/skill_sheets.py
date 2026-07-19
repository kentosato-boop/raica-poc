from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SKILL_ALIASES = {
    "python": ("python", "django", "fastapi"),
    "backend": ("backend", "バックエンド", "server-side"),
    "qc": ("quality control", "品質管理", " qc "),
    "kaizen": ("kaizen", "改善活動"),
    "cnc": ("cnc", "旋盤"),
    "line_management": ("line leader", "ライン管理", "班長"),
    "5s": ("5s", "整理整頓"),
    "interpretation": ("通訳", "interpreter", "interpretation"),
    "administration": ("総務", "administration"),
    "accounting": ("accounting", "会計", "経理"),
    "frontend": ("frontend", "フロントエンド"),
    "react": ("react",),
    "typescript": ("typescript",),
    "sql": (" sql ", "postgresql", "mysql"),
    "azure": ("azure", "data factory"),
    "data_engineering": ("data engineer", "data engineering", "データ基盤"),
    "production_planning": ("production planning", "生産計画"),
    "inventory": ("inventory", "在庫管理"),
    "sap": (" sap ",),
}


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("PDFの内容を確認できません。正しいPDFを選択してください")
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
        if not text.strip():
            raise ValueError("画像PDFは未対応です。OCR済みPDFまたはDOCXを登録してください")
        return text
    if suffix == ".docx":
        if not content.startswith(b"PK"):
            raise ValueError("DOCXの内容を確認できません。正しいDOCXを選択してください")
        document = Document(io.BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        if not text.strip():
            raise ValueError("本文が空のDOCXは登録できません")
        return text
    if suffix in {".txt", ".md", ".csv"}:
        text = content.decode("utf-8", errors="replace")
        if not text.strip():
            raise ValueError("本文が空のファイルは登録できません")
        return text
    raise ValueError("PDF、DOCX、TXT、MD、CSVに対応しています")


def analyze_skill_sheet(text: str) -> dict:
    normalized = f" {text.lower()} "
    skills = sorted({skill for skill, aliases in SKILL_ALIASES.items() if any(alias in normalized for alias in aliases)})
    years = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*(?:年|years?)", normalized)]
    specialization = skills[0] if skills else None
    return {
        "skills": skills,
        "specialization": specialization,
        "specialization_years": max(years, default=0),
        "text_preview": text.strip()[:500],
    }
