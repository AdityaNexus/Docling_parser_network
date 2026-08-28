# Docling Extractor

A local document ingestion and semantic search tool for PDF documents. It uses [Docling](https://github.com/docling-project/docling) to understand document structure, `HybridChunker` to create searchable passages, and ChromaDB to store embeddings locally.

## Features

- Downloads a document from a URL.
- Converts the document with Docling.
- Splits the converted document into structure-aware chunks.
- Embeds and stores chunks in a local ChromaDB database.
- Skips documents that have already been ingested by comparing their SHA-256 hash.
- Searches stored passages using the `BAAI/bge-small-en-v1.5` embedding model.
- Displays similarity, source metadata, and retrieved content.

## Requirements

- Python 3.11 or newer
- Internet access on the first run to download Python packages and model files
- Enough disk space for Docling and embedding model caches

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
```

On PowerShell, if script execution is restricted, enable it for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## Usage

Run the application:

```powershell
python main.py
```

Enter a publicly accessible document URL when prompted. After ingestion finishes, enter search queries. Type `exit` to close the application.

Example:

```text
Enter document URL: https://arxiv.org/pdf/2206.01062
Enter your query (or type 'exit' to quit): What is Docling?
```

The application accepts any URL that Docling can convert, although the current workflow is intended primarily for PDFs.

## How It Works

1. `ingestion.py` downloads the document with a 60-second timeout.
2. The document bytes are hashed with SHA-256.
3. Existing documents are skipped when the hash is already present in ChromaDB.
4. New documents are converted to a Docling document.
5. `HybridChunker` creates structure-aware chunks.
6. `chunking.py` stores the chunks and metadata in ChromaDB in batches of 100.
7. `main.py` creates a searcher and provides an interactive query loop.

## Project Structure

```text
.
├── chunking.py       # ChromaDB storage, metadata, and similarity search
├── ingestion.py      # Download, conversion, deduplication, and chunking
├── main.py           # Interactive command-line application
├── search.py         # Searcher wrapper around VectorDatabase
├── extraction.py     # Standalone Docling conversion example
├── pyproject.toml    # Project metadata and dependencies
└── vector_db/        # Local persistent ChromaDB data
```

## Data and Configuration

By default, ChromaDB stores data in `./vector_db` and uses the collection `docling_paper`. The embedding model is downloaded and cached by `sentence-transformers` on first use. These defaults can be changed by passing different values to `VectorDatabase` in `chunking.py`.

The local `vector_db/` directory contains generated database data. Back it up before deleting it, and do not commit it if the database is not intended to be shared.

## Troubleshooting

- **Ingestion is very fast:** check whether the output says `Document already exists. Skipping ingestion.` The document was deduplicated by content hash.
- **The first run is slow:** Docling and the embedding model may download and initialize model assets.
- **No results are returned:** confirm that ingestion reported a positive chunk count and that the query is not empty.
- **The URL fails:** confirm that it is publicly reachable and that the server returns a supported document.

## Development Check

Compile the main modules without running model inference:

```powershell
.\.venv\Scripts\python.exe -m compileall -q ingestion.py main.py chunking.py search.py
```
