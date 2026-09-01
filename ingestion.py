from io import BytesIO
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
import requests

from docling.chunking import HybridChunker
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter
from chunking import VectorDatabase


def resolve_document_input(source: str) -> tuple[bytes, str]:
    """
    Resolves the input source (URL or local file path) and returns 
    the raw binary content along with the source filename.
    """
    source_str = source.strip().strip('"').strip("'")

    # Check if input is a Web URL
    if source_str.startswith(("http://", "https://")):
        response = requests.get(source_str, timeout=60)
        response.raise_for_status()
        content = response.content

        # Infer filename from URL path or fallback
        parsed_path = urlparse(source_str).path
        filename = PurePosixPath(parsed_path).name or "downloaded_document"
        return content, filename

    # Check if input is a Local File Path
    file_path = Path(source_str)
    if file_path.is_file():
        content = file_path.read_bytes()
        return content, file_path.name

    raise ValueError(
        f"Invalid document source: '{source}'. "
        "Must be a valid web URL or existing local file path."
    )


def add_document(source: str) -> bool:
    source = source.strip().strip('"').strip("'")
    if not source:
        raise ValueError("Document source cannot be empty.")

    # 1. Obtain bytes and filename (Handles URLs, PDF, DOCX, Images, etc.)
    file_bytes, source_name = resolve_document_input(source)

    # 2. Hash Calculation & Deduplication Check
    vector_db = VectorDatabase()
    document_hash = vector_db.calculate_hash(file_bytes)

    if vector_db.document_exists(document_hash):
        print(f"Document '{source_name}' already ingested. Skipping.")
        return False

    # 3. Docling Conversion Pipeline
    print(f"Processing new document ('{source_name}')...")

    # DocumentConverter auto-detects file types (PDF, DOCX, PPTX, Images, HTML, etc.)
    converter = DocumentConverter()

    doc_stream = DocumentStream(
        name=source_name,
        stream=BytesIO(file_bytes),
    )

    conversion_result = converter.convert(doc_stream)

    # 4. Chunking
    chunker = HybridChunker()
    chunks = list(chunker.chunk(dl_doc=conversion_result.document))

    # 5. Ingest Chunks into Vector DB
    vector_db.add_docling_chunks(
        chunks=chunks,
        source_name=source_name,
        document_hash=document_hash,
    )

    print(f"Successfully processed and stored '{source_name}'.")
    return True