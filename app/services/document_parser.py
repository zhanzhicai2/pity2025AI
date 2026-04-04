"""
文档解析服务：PDF / DOCX / Markdown / TXT
"""
import hashlib
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import Config


class DocumentParser:
    """文档解析服务"""

    SUPPORTED_TYPES = [".pdf", ".docx", ".md", ".txt"]

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

    def parse(self, file_path: str) -> str:
        """解析文档，返回纯文本"""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return self._parse_pdf(file_path)
        elif suffix == ".docx":
            return self._parse_docx(file_path)
        elif suffix == ".md":
            return self._parse_markdown(file_path)
        elif suffix == ".txt":
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {suffix}")

    def _parse_pdf(self, file_path: str) -> str:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def _parse_docx(self, file_path: str) -> str:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    def _parse_markdown(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def split_text(self, text: str) -> list[str]:
        """切分文本为 chunks"""
        return self.text_splitter.split_text(text)

    @staticmethod
    def compute_hash(content: str) -> str:
        """计算内容 MD5 哈希"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()
