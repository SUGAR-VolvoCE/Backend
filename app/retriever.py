import faiss
import pickle
import numpy as np
import openai
from app.config import settings

openai.api_key = settings.API_KEY

# Load FAISS index and text mapping
index = faiss.read_index(settings.FAISS_INDEX_PATH)
with open(settings.TEXT_MAPPING_PATH, "rb") as f:
    id_to_text = pickle.load(f)

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> list:
    response = openai.Embedding.create(
        input=[text],
        model=model
    )
    return response["data"][0]["embedding"]

def retrieve_context(query, k=5):
    embedding = get_embedding(query)
    D, I = index.search(np.array([embedding]).astype("float32"), k)
    return "\n\n".join(id_to_text[i] for i in I[0])
