"""
PDF Text Extractor — Traditional approach using PyMuPDF + regex.

This is the "old way" of extracting structured content from research papers.
It works okay for well-formatted papers, but breaks on:
  - Two-column layouts
  - Non-standard section headings
  - Papers with unusual fonts or formatting
  - Scanned PDFs (no OCR support)
"""

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


# Common section headings in research papers
SECTION_PATTERNS = [
    r"^(abstract)$",
    r"^(\d+\.?\s+introduction)$",
    r"^(\d+\.?\s+related\s+work)$",
    r"^(\d+\.?\s+method(?:ology)?)$",
    r"^(\d+\.?\s+approach)$",
    r"^(\d+\.?\s+experiments?)$",
    r"^(\d+\.?\s+results?)$",
    r"^(\d+\.?\s+(?:results?\s+and\s+)?discussion)$",
    r"^(\d+\.?\s+conclusion)$",
    r"^(\d+\.?\s+references?)$",
    r"^(appendix.*)$",
]


def _is_section_heading(line: str) -> bool:
    """Check if a line looks like a section heading.

    Uses heuristics:
      1. Line is ALL CAPS and short (< 6 words)
      2. Line matches a known section pattern (case-insensitive)
      3. Line starts with a number followed by a period

    This is fragile. Different papers use different conventions.
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Heuristic 1: ALL CAPS, short line
    if stripped.isupper() and len(stripped.split()) < 6 and len(stripped) > 3:
        return True

    # Heuristic 2: Matches known patterns
    for pattern in SECTION_PATTERNS:
        if re.match(pattern, stripped.lower()):
            return True

    # Heuristic 3: Numbered heading like "1. Introduction" or "3.2 Methods"
    if re.match(r"^\d+\.?\d*\s+[A-Z]", stripped) and len(stripped.split()) < 8:
        return True

    return False


def extract_text(pdf_path: str) -> dict:
    """Extract text from a PDF and split into sections.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dictionary with:
          - title: Detected paper title (first line of first page)
          - sections: List of {title, content} dicts
          - page_count: Number of pages
    """
    doc = fitz.open(pdf_path)

    sections = []
    current_section = {"title": "Preamble", "content": ""}
    title = ""

    for page_num, page in enumerate(doc):
        # Simple text extraction — NO layout awareness
        # This is the main weakness: get_text() doesn't handle columns
        text = page.get_text()
        lines = text.split("\n")

        for i, line in enumerate(lines):
            # Grab the title from the first page (crude heuristic)
            if page_num == 0 and i == 0 and not title:
                title = line.strip()
                continue

            if _is_section_heading(line):
                # Save the previous section
                if current_section["content"].strip():
                    sections.append(current_section)
                current_section = {
                    "title": line.strip(),
                    "content": "",
                }
            else:
                current_section["content"] += line + "\n"

    # Don't forget the last section
    if current_section["content"].strip():
        sections.append(current_section)

    page_count = len(doc)
    doc.close()

    return {
        "title": title or "Untitled Paper",
        "sections": sections,
        "page_count": page_count,
    }


def extract_code_blocks(text: str) -> list[str]:
    """Attempt to find code blocks in extracted text.

    Uses indentation as a heuristic: if 3+ consecutive lines start with
    spaces/tabs and look like code, we treat it as a code block.

    This is extremely brittle and misidentifies:
      - Pseudocode
      - Indented quotations
      - Formatted tables
      - Algorithm environments
    """
    lines = text.split("\n")
    code_blocks = []
    current_block = []
    in_code = False

    for line in lines:
        # Lines that start with 4+ spaces or a tab might be code
        looks_like_code = (
            line.startswith("    ") or line.startswith("\t")
        ) and len(line.strip()) > 0

        # Also check for code-like patterns
        has_code_patterns = any(
            keyword in line
            for keyword in [
                "def ", "class ", "import ", "return ", "for ",
                "while ", "if ", "print(", "self.", "= ", "==",
                "torch.", "np.", "tf.",
            ]
        )

        if looks_like_code or (in_code and has_code_patterns):
            current_block.append(line)
            in_code = True
        else:
            if len(current_block) >= 3:
                code_blocks.append("\n".join(current_block))
            current_block = []
            in_code = False

    # Catch trailing block
    if len(current_block) >= 3:
        code_blocks.append("\n".join(current_block))

    return code_blocks
