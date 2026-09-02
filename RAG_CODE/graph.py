from langgraph.graph import START, END, StateGraph
from state import GraphState
from nodes import retrieve_local, search_web, generate, route_query

def build_adaptive_rag():
    workflow = StateGraph(GraphState)

    # Add the action nodes
    workflow.add_node("local_search", retrieve_local)
    workflow.add_node("web_search", search_web)
    workflow.add_node("generate", generate)

    # Add the conditional router
    workflow.add_conditional_edges(
        START,
        route_query,
        {
            "local": "local_search",
            "web": "web_search",
        }
    )

    # Map the search nodes directly to the generator
    workflow.add_edge("local_search", "generate")
    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()

if __name__ == "__main__":
    app = build_adaptive_rag()
    
    while True:
        query = input("\nEnter query (or 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            break
        if not query:
            continue
            
        result = app.invoke({"question": query})
        print(f"\n[Source: {result['source'].upper()}]")
        print(f"Answer: {result['generation']}")