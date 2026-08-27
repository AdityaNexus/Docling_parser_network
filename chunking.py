import hashlib
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.huggingface import (
    HuggingFaceTokenizer,
)

from transformers import AutoTokenizer


EMBED_MODEL_ID = "BAAI/bge-small-en-v1.5"
MAX_TOKENS = 500


class VectorDatabase:
    """Persistent ChromaDB manager for Docling chunks."""

    def __init__(
        self,
        db_path: str = "./vector_db",
        collection_name: str = "docling_paper",
        embedding_model_id: str = EMBED_MODEL_ID,
    ):
        self.client = chromadb.PersistentClient(path=db_path)

        self.embedding_fn = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model_id
            )
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _sanitize_metadata(chunk: Any) -> Dict[str, Any]:
        """Convert Docling metadata into Chroma-compatible values."""

        page_numbers = []

        doc_items = getattr(chunk.meta, "doc_items", [])

        for item in doc_items:
            provenance = getattr(item, "prov", [])

            for prov in provenance:
                page_no = getattr(prov, "page_no", None)

                if page_no is not None:
                    page_numbers.append(page_no)

        page_numbers = sorted(set(page_numbers))

        headings = getattr(chunk.meta, "headings", [])
        title = headings[0] if headings else "Untitled"

        origin = getattr(chunk.meta, "origin", None)
        filename = (
            getattr(origin, "filename", "unknown")
            if origin
            else "unknown"
        )

        return {
            "filename": filename,
            "title": title,
            "page_numbers": ", ".join(map(str, page_numbers)),
            "start_page": page_numbers[0] if page_numbers else -1,
            "end_page": page_numbers[-1] if page_numbers else -1,
        }

    @staticmethod
    def _generate_chunk_id(
        source_name: str,
        text: str,
    ) -> str:
        """Create deterministic ID from source and chunk content."""

        content = f"{source_name}:{text}"

        digest = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        return f"chk_{digest[:16]}"

    def add_docling_chunks(
        self,
        chunks: List[Any],
        source_name: str,
        batch_size: int = 100,
    ) -> None:

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:

            text = chunk.text.strip()

            # Ignore empty chunks
            if not text:
                continue

            chunk_id = self._generate_chunk_id(
                source_name,
                text,
            )

            metadata = self._sanitize_metadata(chunk)

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(metadata)

        total_chunks = len(ids)

        for start in range(0, total_chunks, batch_size):

            end = start + batch_size

            self.collection.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        print(
            f"Successfully upserted "
            f"{total_chunks} chunks into ChromaDB."
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        output = []

        if not results["ids"]:
            return output

        for i, chunk_id in enumerate(results["ids"][0]):

            distance = results["distances"][0][i]

            output.append(
                {
                    "id": chunk_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance,
                    "similarity": 1 - distance,
                }
            )

        return output


# ============================================================
# DOCUMENT INGESTION
# ============================================================
def ingest_document(doc_url: str) -> None:
# 1. Create tokenizer used by Docling's chunker

    hf_tokenizer = AutoTokenizer.from_pretrained(
        EMBED_MODEL_ID
    )

    docling_tokenizer = HuggingFaceTokenizer(
        tokenizer=hf_tokenizer,
        max_tokens=MAX_TOKENS,
    )

# 2. Create HybridChunker

    chunker = HybridChunker(
        tokenizer=docling_tokenizer,
        merge_peers=True,
    )

# 3. Convert document

    converter = DocumentConverter()

    result = converter.convert(doc_url)

    # 4. Create Docling chunks

    chunks = list(
        chunker.chunk(result.document)
    )

    print(f"Created {len(chunks)} chunks.")


    # ============================================================
    # VECTOR DATABASE
    # ============================================================

    db = VectorDatabase(
        db_path="./vector_db",
        collection_name="docling_paper",
        embedding_model_id=EMBED_MODEL_ID,
    )

    # 5. Store chunks

    db.add_docling_chunks(
        chunks,
        source_name="arxiv_2408.09869",
    )



