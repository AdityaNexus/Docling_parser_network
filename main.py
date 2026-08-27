from chunking import ingest_document
from search import DocumentSearcher


def main(url: str):

    # Ingest document
    ingest_document(url)

    print("Document ingested successfully.")

    # Create searcher ONCE
    searcher = DocumentSearcher()

    # Keep searching using the same object
    while True:

        query = input(
            "\nEnter your query (or type 'exit' to quit): "
        ).strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        results = searcher.search(query)

        if results:

            for result in results:

                print(
                    f"\nSimilarity: "
                    f"{result['similarity']:.4f}"
                )

                print(
                    f"Metadata: "
                    f"{result['metadata']}"
                )

                print(
                    f"Content: "
                    f"{result['content']}"
                )

        else:
            print("No results found.")


if __name__ == "__main__":

    url = input("Enter document URL: ")

    main(url)