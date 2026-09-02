from typing import List, TypedDict

class GraphState(TypedDict):
    "Represents the state of our graph"
    question: str
    documents: List[str]
    generation: str
    source: str 
