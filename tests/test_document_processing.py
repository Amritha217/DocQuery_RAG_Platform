from docx import Document
from reportlab.pdfgen import canvas

from app.services.document_processing import (
    chunk_text,
    extract_pages_from_docx,
    extract_pages_from_pdf,
    extract_pages_from_txt,
)


def test_chunk_text_returns_text_chunks():
    text = " ".join(f"word{i}" for i in range(20))

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) == 3
    assert len(chunks[0].split()) == 10
    assert len(chunks[1].split()) == 10
    assert len(chunks[2].split()) == 4


def test_chunk_text_handles_short_text():
    text = "This is a short document."

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_handles_empty_text():
    chunks = chunk_text("", chunk_size=10, overlap=2)

    assert chunks == []


def test_extract_pages_from_txt(tmp_path):
    # Create a temporary text file for testing.
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "This is a test document.",
        encoding="utf-8",
    )

    pages = extract_pages_from_txt(str(file_path))

    assert len(pages) == 1
    assert pages[0]["page"] is None
    assert pages[0]["text"] == "This is a test document."



def test_extract_pages_from_pdf(tmp_path):
    file_path = tmp_path / "sample.pdf"

    # Create a small PDF for testing.
    pdf = canvas.Canvas(str(file_path))
    pdf.drawString(100, 750, "This is a PDF test.")
    pdf.save()

    pages = extract_pages_from_pdf(str(file_path))

    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "This is a PDF test." in pages[0]["text"]


def test_extract_pages_from_docx(tmp_path):
    file_path = tmp_path / "sample.docx"

    # Create a temporary Word document.
    doc = Document()
    doc.add_paragraph("This is a DOCX test.")
    doc.save(str(file_path))

    pages = extract_pages_from_docx(str(file_path))

    assert len(pages) == 1
    assert pages[0]["page"] is None
    assert "This is a DOCX test." in pages[0]["text"]