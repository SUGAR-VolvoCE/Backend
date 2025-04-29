from app.retriever import retrieve_context
from app.vectorstore import Vectorstore

vectorstore = Vectorstore()

rag_tool = {
    "type": "function",
    "function": {
        "name": "search_manuals",
        "description": "Retrieve relevant documents using a semantic search from the knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for retrieving relevant documents."
                }
            },
            "required": ["query"]
        }
    }
}

def search_manuals(query: str, document: str = "default") -> dict:
    """Uses the vector store to retrieve similar chunks given a query."""
    print("Using search manual")
    try:
        docs = vectorstore.similarity_search(document=document, query=query)
        context = [doc.page_content for doc in docs]
        return {"documents": context}
    except Exception as e:
        return {"error": str(e)}
