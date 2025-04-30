import os
import faiss
import pickle
import numpy as np
import openai
from app.config import settings

openai.api_key = settings.API_KEY

# === Load FAISS and text map for a machine ===
def load_machine_index(machine_name):
    index_path = os.path.join(settings.FAISS_INDEX_ROOT, machine_name, "index.faiss")
    text_map_path = os.path.join(settings.FAISS_INDEX_ROOT, machine_name, "index.pkl")

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found for machine {machine_name} at {index_path}")
    if not os.path.exists(text_map_path):
        raise FileNotFoundError(f"Text mapping not found for machine {machine_name} at {text_map_path}")

    index = faiss.read_index(index_path)
    with open(text_map_path, "rb") as f:
        id_to_text = pickle.load(f)

    return index, id_to_text

# === Get OpenAI embedding ===
def get_embedding(text: str, model: str = "text-embedding-ada-002") -> list:
    response = openai.Embedding.create(
        input=[text],
        model=model
    )
    return response["data"][0]["embedding"]

# === Retrieve context from a machine ===
def retrieve_context(query, machine_name, k=5):
    index, id_to_text = load_machine_index(machine_name)

    embedding = get_embedding(query)
    D, I = index.search(np.array([embedding]).astype("float32"), k)
    return "\n\n".join(id_to_text[i] for i in I[0])
