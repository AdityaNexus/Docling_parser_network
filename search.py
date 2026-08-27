from chunking import VectorDatabase


class DocumentSearcher:

    def __init__(self, n_results: int = 3):
        self.vector_db = VectorDatabase()
        self.n_results = n_results

    def search(self, query: str):
        return self.vector_db.search(
            query=query,
            n_results=self.n_results,
        )