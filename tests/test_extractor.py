"""
Tests for the PDF extractor.

These tests illustrate the challenges of testing PDF extraction:
  - We need actual PDF files as fixtures
  - Results depend heavily on PDF formatting
  - Heuristic-based detection is inherently flaky
"""

import pytest
from pdf_processor.extractor import _is_section_heading, extract_code_blocks


class TestSectionHeadingDetection:
    """Test the heuristic section heading detector."""

    def test_all_caps_heading(self):
        assert _is_section_heading("INTRODUCTION") is True

    def test_all_caps_short(self):
        assert _is_section_heading("ABSTRACT") is True

    def test_numbered_heading(self):
        assert _is_section_heading("1. Introduction") is True

    def test_numbered_heading_no_period(self):
        assert _is_section_heading("2 Related Work") is True

    def test_subsection_heading(self):
        assert _is_section_heading("3.1 Data Collection") is True

    def test_regular_text_not_heading(self):
        assert _is_section_heading("This is a regular sentence.") is False

    def test_empty_line_not_heading(self):
        assert _is_section_heading("") is False
        assert _is_section_heading("   ") is False

    def test_short_caps_not_heading(self):
        # "AI" is too short (< 4 chars), should not be a heading
        assert _is_section_heading("AI") is False

    # ---- Known failures that illustrate the fragility ----

    @pytest.mark.xfail(reason="Bold headings without caps are not detected")
    def test_bold_heading(self):
        # Some papers use bold (not caps) for headings
        # We can't detect bold from plain text extraction
        assert _is_section_heading("Introduction") is True

    @pytest.mark.xfail(reason="Roman numeral headings not supported")
    def test_roman_numeral_heading(self):
        assert _is_section_heading("IV. EXPERIMENTS") is True


class TestCodeBlockExtraction:
    """Test heuristic code block detection."""

    def test_detects_indented_code(self):
        text = """Some text before.

    def hello():
        print("hello world")
        return True

More text after."""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "def hello" in blocks[0]

    def test_ignores_short_indentation(self):
        text = """
    line one
    line two
"""
        # Only 2 indented lines — below threshold of 3
        blocks = extract_code_blocks(text)
        assert len(blocks) == 0

    def test_detects_torch_code(self):
        text = """Regular paragraph text here.

    model = torch.nn.Linear(10, 5)
    optimizer = torch.optim.Adam(model.parameters())
    loss = torch.nn.functional.cross_entropy(output, target)

End of code."""
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert "torch" in blocks[0]

    @pytest.mark.xfail(reason="Pseudocode is often misidentified as code")
    def test_does_not_detect_pseudocode(self):
        text = """
    Algorithm 1: Training Loop
    Input: dataset D, learning rate α
    for each epoch e = 1 to E do
        for each batch b in D do
            compute loss L(b)
"""
        blocks = extract_code_blocks(text)
        # This SHOULD return 0 blocks (it's pseudocode, not Python)
        # but our heuristic will likely pick it up
        assert len(blocks) == 0
