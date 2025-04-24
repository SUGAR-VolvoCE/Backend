import os
import pickle
from pathlib import Path

import backoff
import openai
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from .config import settings
from .logger import logger

api_key = settings.API_KEY
if not api_key:
    raise ValueError("OpenAI API key is not set.")

# Define file paths
faiss_index_path = Path(settings.FAISS_INDEX_PATH)  # Corrected FAISS index path
text_mapping_path = Path(settings.TEXT_MAPPING_PATH)   # Corrected pickle file path

import faiss

class Vectorstore:
    def __init__(self):
        self.embeddings_provider = OpenAIEmbeddings(api_key=api_key)
        self.index = None
        self.id_to_text = {}
        self.build_or_load_index()

    def build_or_load_index(self):
        """Load existing FAISS index and text mapping."""
        if faiss_index_path.exists() and text_mapping_path.exists():
            logger.info("Loading existing FAISS index and text mapping...")

            self.index = faiss.read_index(str(faiss_index_path))

            with open(text_mapping_path, "rb") as f:
                self.id_to_text = pickle.load(f)
        else:
            logger.error("FAISS index or text mapping not found. Please create them first.")
            raise FileNotFoundError("FAISS index or text mapping file is missing.")

    def similarity_search(self, query, k=5):
        """Perform a similarity search on the FAISS index."""
        embedding = self.embeddings_provider.embed_query(query)
        D, I = self.index.search(np.array([embedding]).astype("float32"), k)
        return [self.id_to_text[i] for i in I[0]]


@backoff.on_exception(backoff.expo, openai.RateLimitError)
def compute_with_backoff(thunk):
    """Handle retries for rate-limited API requests."""
    return thunk()
