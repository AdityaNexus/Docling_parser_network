import hashlib
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions


class VectorDatabase:

    def __init__(
        self,
        db_path: str = "./vector_db",
        collection_name: str = "docling_paper",
        embedding_model_id: str = "BAAI/bge-small-en-v1.5",
    ):
        self.client = chromadb.PersistentClient(
            path=db_path
        )

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

    def document_exists(
        self,
        document_hash: str,
    ) -> bool:

        results = self.collection.get(
            where={
                "document_hash": document_hash
            },
            limit=1,
        )

        return len(results["ids"]) > 0

    @staticmethod
    def calculate_hash(
        content: bytes,
    ) -> str:

        return hashlib.sha256(content).hexdigest()



    @staticmethod
    def _sanitize_metadata(
        chunk: Any,
        source_name: str,
        document_hash: str,
    ) -> Dict[str, Any]:

        page_numbers = []

        doc_items = getattr(
            chunk.meta,
            "doc_items",
            [],
        )

        for item in doc_items:

            provenance = getattr(
                item,
                "prov",
                [],
            )

            for prov in provenance:

                page_no = getattr(
                    prov,
                    "page_no",
                    None,
                )

                if page_no is not None:
                    page_numbers.append(page_no)

        page_numbers = sorted(
            set(page_numbers)
        )

        headings = getattr(
            chunk.meta,
            "headings",
            [],
        )

        title = (
            headings[0]
            if headings
            else "Untitled"
        )

        origin = getattr(
            chunk.meta,
            "origin",
            None,
        )

        filename = (
            getattr(
                origin,
                "filename",
                source_name,
            )
            if origin
            else source_name
        )

        return {
            "filename": filename,
            "title": title,
            "page_numbers": ", ".join(
                map(str, page_numbers)
            ),
            "start_page": (
                page_numbers[0]
                if page_numbers
                else -1
            ),
            "end_page": (
                page_numbers[-1]
                if page_numbers
                else -1
            ),

            # IMPORTANT
            "document_hash": document_hash,
        }

    @staticmethod
    def _generate_chunk_id(
        document_hash: str,
        text: str,
    ) -> str:

        content = (
            f"{document_hash}:{text}"
        )

        digest = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        return f"chk_{digest[:16]}"

    def add_docling_chunks(
        self,
        chunks: List[Any],
        source_name: str,
        document_hash: str,
        batch_size: int = 100,
    ) -> None:

        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:

            text = chunk.text.strip()

            if not text:
                continue

            chunk_id = self._generate_chunk_id(
                document_hash,
                text,
            )

            metadata = self._sanitize_metadata(
                chunk,
                source_name,
                document_hash,
            )

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append(metadata)

        for start in range(
            0,
            len(ids),
            batch_size,
        ):

            end = start + batch_size

            self.collection.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        print(
            f"Successfully upserted "
            f"{len(ids)} chunks."
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:

        # OPTIMIZATION: BGE models require this exact prefix for queries
        bge_prefix = "Represent this sentence for searching relevant passages: "
        formatted_query = f"{bge_prefix}{query}"

        results = self.collection.query(
            query_texts=[formatted_query], # Pass the formatted query
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        output = []

        if not results["ids"]:
            return output

        for i, chunk_id in enumerate(
            results["ids"][0]
        ):

            distance = (
                results["distances"][0][i]
            )

            output.append({
                "id": chunk_id,
                "content": (
                    results["documents"][0][i]
                ),
                "metadata": (
                    results["metadatas"][0][i]
                ),
                "distance": distance,
                "similarity": 1 - distance,
            })

        return output