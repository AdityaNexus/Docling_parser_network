from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse

import requests
from docling.chunking import HybridChunker
from docling.datamodel.base_models import DocumentStream
from chunking import VectorDatabase
from docling.document_converter import DocumentConverter


def add_document(url: str) -> bool:

    url = url.strip()
    if not url:
        raise ValueError("Document URL cannot be empty.")

    # ------------------------------------------------
    # 1. Download
    # ------------------------------------------------

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    pdf_bytes = response.content
    source_name = (
        PurePosixPath(urlparse(url).path).name
        or "document.pdf"
    )

    # ------------------------------------------------
    # 2. Identify document
    # ------------------------------------------------

    vector_db = VectorDatabase()

    document_hash = (
        vector_db.calculate_hash(pdf_bytes)
    )

    # ------------------------------------------------
    # 3. Check whether already ingested
    # ------------------------------------------------

    if vector_db.document_exists(
        document_hash
    ):

        print("Document already exists. Skipping ingestion.")

        return False

    # ------------------------------------------------
    # 4. New document → Docling
    # ------------------------------------------------

    print("New document detected. Starting ingestion...")

    converter = DocumentConverter()
    source = DocumentStream(
        name=source_name,
        stream=BytesIO(pdf_bytes),
    )
    conversion_result = converter.convert(source)

    chunker = HybridChunker()
    chunks = chunker.chunk(dl_doc=conversion_result.document)
    vector_db.add_docling_chunks(
        chunks=chunks,
        source_name=source_name,
        document_hash=document_hash,
    )

    return True