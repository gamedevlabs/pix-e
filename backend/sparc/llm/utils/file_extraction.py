"""
Text extraction utilities for design documents.
Simple text-only extraction for MVP.
"""

import os
from typing import Optional


def extract_text_from_file(file_path: str) -> str:
    """
    Extract plain text from various file formats.

    Args:
        file_path: Path to the file

    Returns:
        Extracted text content

    Raises:
        ValueError: If file type is unsupported or extraction fails
    """
    file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")

    try:
        if file_ext == "pdf":
            return _extract_from_pdf(file_path)
        elif file_ext == "docx":
            return _extract_from_docx(file_path)
        elif file_ext in ["txt", "md"]:
            return _extract_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: .{file_ext}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from {file_path}: {str(e)}")


def _extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyPDF2."""
    import PyPDF2

    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        pages = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

        if not pages:
            raise ValueError("No text content found in PDF")

        return "\n\n".join(pages)


def _extract_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    if not paragraphs:
        raise ValueError("No text content found in DOCX")

    return "\n\n".join(paragraphs)


def _extract_from_text(file_path: str) -> str:
    """Extract text from plain text files."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("File is empty")

    return content


def validate_file_size(file_size: int, max_size_mb: int = 10) -> None:
    """
    Validate file size is within limits.

    Args:
        file_size: File size in bytes
        max_size_mb: Maximum allowed size in MB

    Raises:
        ValueError: If file is too large
    """
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(
            f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds "
            f"maximum allowed size ({max_size_mb}MB)"
        )


def validate_file_type(filename: str, allowed_types: Optional[list] = None) -> str:
    """
    Validate file type is supported.

    Args:
        filename: Name of the file
        allowed_types: List of allowed extensions (default: pdf, docx, txt, md)

    Returns:
        File extension (lowercase, without dot)

    Raises:
        ValueError: If file type is not supported
    """
    if allowed_types is None:
        allowed_types = ["pdf", "docx", "txt", "md"]

    file_ext = os.path.splitext(filename)[1].lower().lstrip(".")

    if not file_ext:
        raise ValueError("File has no extension")

    if file_ext not in allowed_types:
        raise ValueError(
            f"File type .{file_ext} not supported. "
            f"Allowed types: {', '.join(allowed_types)}"
        )

    return file_ext
