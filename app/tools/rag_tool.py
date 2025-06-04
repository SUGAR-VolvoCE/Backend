from app.vectorstore import Vectorstore

vectorstore = Vectorstore()

search_manuals_tool = {
    "type": "function",
    "function": {
        "name": "search_manuals",
        "description": "Retrieve relevant documents using a semantic search from the knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for retrieving relevant documents. It MUST be in ENGLISH."
                },
                "machine_name": {
                    "type": "string",
                    "description": "The name of the machine to retrieve the correct FAISS index for."
                }
            },
            "required": ["query", "machine_name"]
        }
    }
}

def search_manuals(query: str, machine_name: str) -> dict:
    """Uses the vector store to retrieve similar chunks given a query and machine name, ensuring the machine name is in uppercase."""
    machine_name_upper = "WLOL60H"  # Convert machine name to uppercase
    print(f"Using search for machine: {machine_name_upper}")    
    try:
        docs = vectorstore.similarity_search(query=query, machine_name=machine_name_upper)
        context = [doc.page_content for doc in docs]
        return {"documents": context}
    except Exception as e:
        return {"error": str(e)}