from typing import Any, Dict, Optional

from chunking import VectorDatabase


class DocumentSearcher:

    def __init__(self, n_results: int = 3):
        self.vector_db = VectorDatabase()
        self.n_results = n_results

    @staticmethod
    def _matches_where_filter(result_metadata: Dict[str, Any], where_filter: Dict[str, Any]) -> bool:
        if not where_filter:
            return True

        for field_name, condition in where_filter.items():
            if not isinstance(condition, dict):
                continue

            value = str(result_metadata.get(field_name, "")).lower()

            for operator, expected in condition.items():
                expected = str(expected).lower()

                if operator == "$contains":
                    if expected not in value:
                        return False
                elif operator == "$eq":
                    if value != expected:
                        return False
                else:
                    return False

        return True

    def search(
        self,
        query: str,
        where_filter: Optional[Dict[str, Any]] = None,
    ):
        results = self.vector_db.search(
            query=query,
            n_results=self.n_results,
            where_filter=None,
        )

        if where_filter:
            results = [
                result
                for result in results
                if self._matches_where_filter(result.get("metadata", {}), where_filter)
            ]

        return results