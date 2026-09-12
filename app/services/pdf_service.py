from pypdf import PdfReader
from docx import Document as DocxDocument


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append({"page": i + 1, "text": text})
    return pages


def extract_pages_from_docx(file_path: str) -> list[dict]:
    doc = DocxDocument(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return [{"page": None, "text": text}]


def extract_pages_from_txt(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page": None, "text": text}]


def extract_pages(file_path: str) -> list[dict]:
    if file_path.lower().endswith(".pdf"):
        return extract_pages_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return extract_pages_from_docx(file_path)
    elif file_path.lower().endswith(".txt"):
        return extract_pages_from_txt(file_path)
    else:
        raise ValueError("Unsupported file type for text extraction")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += chunk_size - overlap
    return chunks


def chunk_pages(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    all_chunks = []
    for page in pages:
        for c in chunk_text(page["text"], chunk_size, overlap):
            all_chunks.append({"page": page["page"], "text": c})
    return all_chunks