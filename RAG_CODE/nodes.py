import sys
from pathlib import Path

# Add parent directory to path so we can import search.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from state import GraphState
from search import DocumentSearcher

# Connect strictly to your specified local llama.cpp endpoint
llm = ChatOpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="local", # Required by the SDK, ignored by the local server
    temperature=0,
)

# Initialize tools and searcher
web_search_tool = DuckDuckGoSearchResults()
local_searcher = DocumentSearcher()

def retrieve_local(state: GraphState):
    print("--> ROUTING TO LOCAL CHROMADB")
    results = local_searcher.search(state["question"])
    docs = [res["content"] for res in results]
    return {"documents": docs, "source": "local"}

def search_web(state: GraphState):
    print("--> ROUTING TO WEB SEARCH")
    docs = web_search_tool.invoke(state["question"])
    return {"documents": [docs], "source": "web"}

def generate(state: GraphState):
    print("--> GENERATING FINAL ANSWER")
    prompt = f"""Use the following context to answer the question.
    Question: {state["question"]}
    Context: {state["documents"]}
    Answer:"""
    
    response = llm.invoke(prompt)
    return {"generation": response.content}

def route_query(state: GraphState):
    prompt = PromptTemplate(
        template="""You are a routing agent. 
        If the query is about specific internal documents, architecture, or uploaded data, output 'local'. 
        If the query is about general knowledge, current events, or internet facts, output 'web'.
        
        Question: {question}
        Respond with ONLY JSON containing a 'route' key (e.g., {{"route": "local"}}).""",
        input_variables=["question"],
    )
    
    router = prompt | llm | JsonOutputParser()
    result = router.invoke({"question": state["question"]})
    return result["route"]