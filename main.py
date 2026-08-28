from ingestion import add_document
from search import DocumentSearcher


def main(url: str):

    # Add only if this is a new document
    add_document(url)

    # Create searcher once
    searcher = DocumentSearcher()

    while True:

        query = input(
            "\nEnter your query "
            "(or type 'exit' to quit): "
        ).strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        results = searcher.search(query)

        if not results:
            print("No results found.")
            continue

        for i, result in enumerate(
            results,
            start=1,
        ):

            print(f"\n--- Result {i} ---")

            print(
                f"Similarity: "
                f"{result['similarity']:.4f}"
            )

            print(
                f"Metadata: "
                f"{result['metadata']}"
            )

            print(
                f"Content:\n"
                f"{result['content']}"
            )


if __name__ == "__main__":

    url = input("Enter document URL: ").strip()

    if not url:
        raise SystemExit("A document URL is required.")

    main(url)