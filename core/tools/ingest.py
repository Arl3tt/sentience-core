# ingestion helpers (text and PDF)

from pypdf import PdfReader
from core.memory import ingest_document


def ingest_text_file(path, doc_id=None):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    doc_id = doc_id or path
    return ingest_document(doc_id, text, {"source": "file", "path": path})


def ingest_pdf(path, doc_id=None):
    reader = PdfReader(path)
    text = "\n\n".join([p.extract_text() or "" for p in reader.pages])
    doc_id = doc_id or path
    return ingest_document(doc_id, text, {"source": "pdf", "path": path})
