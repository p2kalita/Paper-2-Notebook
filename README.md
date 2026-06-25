# Paper to Notebook — Traditional Version

> The "old way" of converting research papers to Jupyter notebooks.
> No AI, no LLMs — just PDF extraction and heuristic-based formatting.


## What it does

1. Accepts a research paper PDF upload
2. Extracts text using PyMuPDF (`page.get_text()`)
3. Identifies sections using regex heuristics
4. Assembles a Jupyter notebook using nbformat
5. Returns the `.ipynb` file

## What it DOESN'T do (and why this matters)

- No code generation (can't implement the paper's algorithms)
- No LaTeX extraction (equations are lost)
- No arXiv URL support
- No frontend
- Breaks on two-column layouts
- Section detection is fragile


## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Visit `http://localhost:8000/docs` for the Swagger UI.

## Tests

```bash
pytest tests/ -v
```

## Project Structure

```
├── pdf_processor/          # PDF text extraction
│   └── extractor.py        # PyMuPDF + regex heuristics
├── notebook_builder/       # Notebook assembly
│   └── builder.py          # nbformat-based builder
├── api/                    # FastAPI server
│   └── main.py             # /convert endpoint
├── tests/                  # Unit tests
│   └── test_extractor.py   # Tests (some intentionally xfail)
├── .github/workflows/      # CI/CD
│   └── ci.yml              # Lint + test + deploy
├── requirements.txt
├── run.py                  # Entry point
└── README.md
```

