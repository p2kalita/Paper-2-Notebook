"""
Notebook Builder — Assembles extracted sections into a Jupyter .ipynb file.

This builder is purely mechanical: it takes extracted text and reformats
it into notebook cells. There is NO intelligence here — no code generation,
no LaTeX extraction, no understanding of the paper's content.

Compare this to the LLM-powered version which actually generates
implementations of the paper's algorithms.
"""

import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from pdf_processor.extractor import extract_code_blocks


# Hardcoded setup cell — we guess common dependencies
SETUP_CODE = """# Setup — install common dependencies
# NOTE: We're guessing which packages are needed. This often includes
# packages the notebook doesn't actually use, and misses ones it does.
!pip install torch torchvision numpy matplotlib scipy pandas -q
"""


def _make_title_cell(title: str) -> nbformat.NotebookNode:
    """Create the title cell for the notebook."""
    return new_markdown_cell(
        f"# {title}\n\n"
        f"*Auto-generated notebook from research paper.*\n\n"
        f"---"
    )


def _make_section_cell(section: dict) -> nbformat.NotebookNode:
    """Convert a section to a markdown cell."""
    title = section["title"]
    content = section["content"].strip()

    # Clean up the content a bit
    # Remove excessive blank lines
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")

    return new_markdown_cell(f"## {title}\n\n{content}")


def _make_code_cell(code: str) -> nbformat.NotebookNode:
    """Create a code cell from extracted code."""
    # Strip leading whitespace uniformly
    lines = code.split("\n")
    if lines:
        # Find minimum indentation
        indents = [
            len(line) - len(line.lstrip())
            for line in lines
            if line.strip()
        ]
        min_indent = min(indents) if indents else 0
        lines = [line[min_indent:] for line in lines]

    return new_code_cell("\n".join(lines))


def build_notebook(paper_data: dict) -> nbformat.NotebookNode:
    """Build a Jupyter notebook from extracted paper data.

    Args:
        paper_data: Dictionary from extract_text() containing:
            - title: Paper title
            - sections: List of {title, content} dicts
            - page_count: Number of pages

    Returns:
        A nbformat NotebookNode that can be written to a .ipynb file.
    """
    nb = new_notebook()
    cells = []

    # Title cell
    cells.append(_make_title_cell(paper_data["title"]))

    # Setup cell with hardcoded dependencies
    cells.append(new_code_cell(SETUP_CODE))

    # Add each section
    for section in paper_data["sections"]:
        # Add section as markdown
        cells.append(_make_section_cell(section))

        # Try to find code blocks in this section
        code_blocks = extract_code_blocks(section["content"])
        for code in code_blocks:
            cells.append(_make_code_cell(code))

    # Add a placeholder conclusion cell
    cells.append(
        new_markdown_cell(
            "---\n\n"
            "## Notes\n\n"
            "This notebook was auto-generated from a PDF. "
            "The code blocks above were extracted from the paper using "
            "heuristic detection and may not be accurate or runnable.\n\n"
            "**Manual review is required before running any code cells.**"
        )
    )

    nb.cells = cells

    # Set kernel metadata
    nb.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }

    return nb
