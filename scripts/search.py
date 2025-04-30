import faiss
import numpy as np
import pickle
import os
from langchain_openai import OpenAIEmbeddings

OPENAI_API_KEY="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"

# Set your OpenAI API Key (just like your config does)
api_key = OPENAI_API_KEY  # replace with settings.API_KEY if using settings
embeddings_provider = OpenAIEmbeddings(api_key=api_key)

# Paths
index_path = 'data/faiss_index/EC220D/index.faiss'
pkl_path = 'data/faiss_index/EC220D/index.pkl'

# Load FAISS index
def load_faiss_index(index_path):
    index = faiss.read_index(index_path)
    print(f"Loaded index with dimension: {index.d}")
    return index

# Load pickle metadata
def load_pkl_metadata(pkl_path):
    with open(pkl_path, 'rb') as f:
        metadata = pickle.load(f)
    print(f"Loaded metadata with {len(metadata)} entries")
    return metadata

# Generate query vector using OpenAI embeddings
def generate_query_vector(query_str):
    embedding = embeddings_provider.embed_query(query_str)
    return np.array(embedding, dtype=np.float32)

# Search FAISS
def search_faiss_index(index, query_vector, k=5):
    D, I = index.search(np.array([query_vector]), k)
    return D, I

# === MAIN ===
query_str = "SE2603"  # Now this will properly match existing embeddings
query_vector = generate_query_vector(query_str)

# Load index and metadata
index = load_faiss_index(index_path)
metadata = load_pkl_metadata(pkl_path)

# Search
distances, indices = search_faiss_index(index, query_vector)

# Print
print(f"\nTop {len(distances[0])} results for query: '{query_str}'")
for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
    print(f"Rank {rank+1}: Index = {idx}, Distance = {dist}")
    if idx < len(metadata):
        print(f"Metadata: {metadata[idx]}")
    else:
        print("Metadata: Not found")
