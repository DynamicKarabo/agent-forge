import json
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import chromadb
from chromadb.utils import embedding_functions

# Initialize Vector DB (Ephemeral for demo)
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="knowledge_base")

# Simple embedding function usage (using default if sentence-transformers not explicitly loaded here to save startup time, 
# or letting chroma handle it. Chroma default is ONNX MiniLM, which is fine)

def web_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo.
    """
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        return json.dumps(results)
    except Exception as e:
        return f"Search error: {str(e)}"

def local_rag(query: str, content: str = None) -> str:
    """
    If 'content' is provided, adds it to the knowledge base.
    If only 'query' is provided, searches the knowledge base.
    """
    try:
        if content:
            # Add to KB
            doc_id = str(hash(content))
            collection.add(
                documents=[content],
                metadatas=[{"source": "user_input"}],
                ids=[doc_id]
            )
            return "Content added to knowledge base."
        else:
            # Query KB
            results = collection.query(
                query_texts=[query],
                n_results=2
            )
            return json.dumps(results['documents'])
    except Exception as e:
        return f"RAG error: {str(e)}"

# Tool Definitions / Schemas for Groq
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "local_rag",
            "description": "Store or retrieve information from the local knowledge base. Provide 'content' to store, or just 'query' to retrieve.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to store in the knowledge base (optional)."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

AVAILABLE_TOOLS = {
    "web_search": web_search,
    "local_rag": local_rag
}
