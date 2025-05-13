import os
import pickle
import faiss
import numpy as np
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === CONFIGURATION ===
PDFS_ROOT = "data/manuals"  # 📂 Folder containing machine folders
INDEX_ROOT = "data/faiss_index"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def get_embedding(text: str, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")  
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def read_pdf_chunks(path):
    reader = PdfReader(path)
    all_text = " ".join([page.extract_text() or "" for page in reader.pages])

    # Use a smarter splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_text(all_text)
    return chunks


def embed_chunks(chunks):
    embeddings = []
    for i, chunk in enumerate(chunks):
        try:
            emb = get_embedding(chunk, model="text-embedding-ada-002")
            embeddings.append((i, emb))
        except Exception as e:
            print(f"Skipping chunk {i}: {e}")
    return embeddings

def build_faiss_index(all_embeddings):
    dimension = len(all_embeddings[0][1])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array([emb for _, emb in all_embeddings]).astype("float32")
    index.add(vectors)
    return index

def find_all_pdfs(root_folder):
    pdf_files = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for file in filenames:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, file))
    return pdf_files

def process_machine(machine_name):
    pdf_folder = os.path.join(PDFS_ROOT, machine_name)
    index_folder = os.path.join(INDEX_ROOT, machine_name)

    os.makedirs(index_folder, exist_ok=True)

    all_chunks = []
    all_embeddings = []
    id_to_text = {}
    global_chunk_id = 0

    pdf_files = find_all_pdfs(pdf_folder)
    print(f"Found {len(pdf_files)} PDFs inside {machine_name}")

    for pdf_path in pdf_files:
        print(f"Reading {os.path.relpath(pdf_path, PDFS_ROOT)}...")
        chunks = read_pdf_chunks(pdf_path)

        print(f"Embedding {len(chunks)} chunks from {os.path.basename(pdf_path)}...")
        embeddings = embed_chunks(chunks)

        for (local_idx, emb) in embeddings:
            all_embeddings.append((global_chunk_id, emb))
            id_to_text[global_chunk_id] = chunks[local_idx]
            global_chunk_id += 1

    print(f"Total chunks embedded for {machine_name}: {len(all_embeddings)}")

    print("Building FAISS index...")
    index = build_faiss_index(all_embeddings)

    print("Saving index...")
    faiss.write_index(index, os.path.join(index_folder, "index.faiss"))

    print("Saving text mapping...")
    with open(os.path.join(index_folder, "index.pkl"), "wb") as f:
        pickle.dump(id_to_text, f)

    print(f"✅ Done! Index and mapping saved for {machine_name}.")

def main():
    machine_name = "EC220D"  # 👈 Machine folder name
    process_machine(machine_name)

if __name__ == "__main__":
    main()