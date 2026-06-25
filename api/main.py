"""
FastAPI Server — Traditional PDF-to-Notebook converter.

Single endpoint: upload a PDF, get back a .ipynb file.
No AI, no LLMs — just PDF extraction + mechanical notebook assembly.
"""

import io
import tempfile
from pathlib import Path

import nbformat
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pdf_processor.extractor import extract_text
from notebook_builder.builder import build_notebook

app = FastAPI(
    title="Paper to Notebook (Traditional)",
    description="Convert research paper PDFs to Jupyter notebooks — no AI involved.",
    version="0.1.0",
)

# CORS — allow everything for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "running",
        "version": "0.1.0 (traditional)",
        "note": "This is the non-AI version. It uses regex and heuristics.",
    }


@app.post("/convert")
async def convert_pdf_to_notebook(file: UploadFile = File(...)):
    """Upload a PDF, get back a .ipynb notebook.

    The conversion pipeline:
      1. Save uploaded PDF to a temp file
      2. Extract text using PyMuPDF (page.get_text())
      3. Split into sections using regex heuristics
      4. Assemble into a Jupyter notebook using nbformat
      5. Return the .ipynb as a download

    No AI is used anywhere in this pipeline.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Read the uploaded file
    content = await file.read()

    if len(content) > 30 * 1024 * 1024:  # 30 MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 30 MB.")

    # Save to temp file (PyMuPDF needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: Extract text from PDF
        paper_data = extract_text(tmp_path)

        if not paper_data["sections"]:
            raise HTTPException(
                status_code=422,
                detail="Could not extract any sections from the PDF. "
                       "The paper format may not be supported.",
            )

        # Step 2: Build the notebook
        notebook = build_notebook(paper_data)

        # Step 3: Serialize to .ipynb
        output = io.StringIO()
        nbformat.write(notebook, output)
        output.seek(0)

        # Generate filename from paper title
        safe_title = "".join(
            c if c.isalnum() or c in " -_" else ""
            for c in paper_data["title"]
        )[:50].strip()
        filename = f"{safe_title or 'notebook'}.ipynb"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="application/x-ipynb+json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}",
        )
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
