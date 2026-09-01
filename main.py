from ingestion import add_document
from search import DocumentSearcher

def main():
    source = input("Enter Document URL or Local File Path: ").strip()

    if not source:
        raise SystemExit("A valid document URL or file path is required.")

    # Ingest document if new
    add_document(source)

    # Create searcher once
    searcher = DocumentSearcher()

    while True:
        print("\n" + "="*40)
        # 1. Ask for the target document first
        target_doc = input(
            "Enter filename to search in (or press Enter to search all): "
        ).strip()
        
        # 2. Ask for the query
        query = input(
            "Enter your query (or type 'exit' to quit): "
        ).strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        # 3. Construct the filename filter in a case-insensitive way.
        where_filter = None
        if target_doc:
            normalized_target = target_doc.strip().strip('"').strip("'").lower()
            where_filter = {"filename": {"$contains": normalized_target}}

        # 4. Pass the filter to your searcher
        results = searcher.search(query, where_filter=where_filter)

        if not results:
            print("No results found.")
            continue

        for i, result in enumerate(results, start=1):
            print(f"\n--- Result {i} ---")
            print(f"Similarity: {result['similarity']:.4f}")
            print(f"File:       {result['metadata'].get('filename', 'Unknown')}")
            print(f"Content:\n{result['content']}")

if __name__ == "__main__":
    main()