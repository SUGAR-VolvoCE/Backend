import os
import pickle
import faiss
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import numpy as np
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATION ===
PDF_PATH = "data/manuals/volvo_manual.pdf"
INDEX_PATH = "data/faiss_index/manuals.faiss"
TEXT_MAP_PATH = "data/faiss_index/id_to_text.pkl"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def get_embedding(text: str, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")  
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# === STEP 1: Read and Chunk PDF ===
def read_pdf_chunks(path):
    reader = PdfReader(path)
    all_text = " ".join([page.extract_text() or "" for page in reader.pages])
    chunks = []
    for i in range(0, len(all_text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunks.append(all_text[i:i + CHUNK_SIZE])
    return chunks

# === STEP 2: Embed Chunks ===
def embed_chunks(chunks):
    embeddings = []
    for i, chunk in enumerate(chunks):
        try:
            emb = get_embedding(chunk, model="text-embedding-ada-002")
            embeddings.append((i, emb))
        except Exception as e:
            print(f"Skipping chunk {i}: {e}")
    return embeddings

# === STEP 3: Build FAISS Index ===
def build_faiss_index(embeddings):
    dimension = len(embeddings[0][1])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array([emb for _, emb in embeddings]).astype("float32")
    index.add(vectors)
    return index

# === MAIN SCRIPT ===
def main():
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

    print("Reading PDF...")
    chunks = read_pdf_chunks(PDF_PATH)

    print(f"Embedding {len(chunks)} chunks...")
    embeddings = embed_chunks(chunks)

    print("Building FAISS index...")
    index = build_faiss_index(embeddings)

    print("Saving index...")
    faiss.write_index(index, INDEX_PATH)

    print("Saving text mapping...")
    id_to_text = {i: chunks[idx] for i, (idx, _) in enumerate(embeddings)}
    with open(TEXT_MAP_PATH, "wb") as f:
        pickle.dump(id_to_text, f)

    print("✅ Done! FAISS index and text mapping saved.")

if __name__ == "__main__":
    main()
