import os
import pickle
from pathlib import Path
from langchain_core.documents import Document 
import backoff
import openai
import numpy as np
from langchain_openai import OpenAIEmbeddings
import faiss

from .config import settings
from .logger import logger

api_key = settings.API_KEY
if not api_key:
    raise ValueError("OpenAI API key is not set.")

@backoff.on_exception(backoff.expo, openai.RateLimitError)
def compute_with_backoff(thunk):
    return thunk()

class Vectorstore:
    def __init__(self):
        self.embeddings_provider = OpenAIEmbeddings(api_key=api_key)
        self.index_cache = {}  # Cache of machine_name → (index, id_to_text)

    def load_machine_index(self, machine_name):
        """Load FAISS index and text mapping for a given machine."""
        if machine_name in self.index_cache:
            return self.index_cache[machine_name]

        # Folder structure: /FAISS_DIR/ec220d/index.faiss and index.pkl
        machine_dir = Path(settings.FAISS_INDEX_ROOT) / machine_name
        index_path = machine_dir / "index.faiss"
        mapping_path = machine_dir / "index.pkl"

        if not index_path.exists() or not mapping_path.exists():
            raise FileNotFoundError(f"FAISS index or mapping for machine '{machine_name}' not found.")

        logger.info(f"Loading FAISS index for machine {machine_name}...")

        index = faiss.read_index(str(index_path))
        with open(mapping_path, "rb") as f:
            id_to_text = pickle.load(f)

        self.index_cache[machine_name] = (index, id_to_text)
        return index, id_to_text

    def similarity_search(self, query, machine_name, k=5):
        print(query)
        index, id_to_text = self.load_machine_index(machine_name)
        embedding = self.embeddings_provider.embed_query(query)
        D, I = index.search(np.array([embedding]).astype("float32"), k)
        return [Document(page_content=id_to_text[i]) for i in I[0]]  # ✅ return Document objects

