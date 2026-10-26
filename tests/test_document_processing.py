# Unit Test file to test the document_processing service. To  check if the functions properly work in that file

# Creates a Word document for testing
from docx import Document

# Creates a sample PDF file for testing
from reportlab.pdfgen import canvas

from app.services.document_processing import (
    chunk_text,
    extract_pages_from_docx,
    extract_pages_from_pdf,
    extract_pages_from_txt,
)

# 1. Checks whether long text is split into the expected number and size of chunks.

# This fn ensures long docs are divided into manageable pieces for retrieval and wns answering

# - Creates text containing 20 words
# - Calls chunk_text() with chunk_size=10 and overlap=2
# - Checks that three chunks are returned
# - Verifies that the first two chunks contain 10 words each and the final chunk contains 4 words


def test_chunk_text_returns_text_chunks():
    text = " ".join(f"word{i}" for i in range(20))

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) == 3
    assert len(chunks[0].split()) == 10
    assert len(chunks[1].split()) == 10
    assert len(chunks[2].split()) == 4


# 2. Checks how the chunking function handles text that is shorter than the configured chunk size

# This fn prevents unnecessary splitting of short documents

# - Creates a short sentence
# - Passes it to chunk_text()
# - Verifies that one chunk is returned and the original sentence remains unchanged
    

def test_chunk_text_handles_short_text():
    text = "This is a short document."

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) == 1
    assert chunks[0] == text

# 3. Checks how the chunking function behaves when no text is provided

# This fn prevents empty chunks from entering your document-processing and retrieval pipeline.

# - Passes an empty string to chunk_text()
# - Verifies that the result is an empty list

def test_chunk_text_handles_empty_text():
    chunks = chunk_text("", chunk_size=10, overlap=2)

    assert chunks == []


# 4. Checks whether text can be extracted correctly from a TXT file

# This fn confirms that plain-text documents can be processed correctly

# tmp_path - pytest fixture that provides a temporary directory for creating test files

# assert - checks whether the result matches what we expect. If a condition is false, test fails and pytest reports the failure.
    
    
# - Creates a temporary .txt file
# - Writes sample text into it
# - Calls extract_pages_from_txt()
# - Verifies that one page-like result is returned, its page number is None, and the extracted text matches the original text.


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



# 5. Checks whether text can be extracted from a PDF file
    
# This fn confirms that PDF text extraction works and that page numbering is preserved.
    
# - Creates a temporary PDF containing a sample sentence
# - Calls extract_pages_from_pdf()
# - Verifies that one page is returned, the page number is 1, and the extracted text contains the expected sentence

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


# 6. Checks whether text can be extracted from a Word document
    
#  This fn confirms that Word documents can be processed correctly
    
# - Creates a temporary DOCX file
# - Adds a paragraph containing sample text
# - Calls extract_pages_from_docx()
# - Verifies that one result is returned, its page number is None, and the extracted text contains the expected sentence

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