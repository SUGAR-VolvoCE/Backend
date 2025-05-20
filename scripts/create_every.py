import os
import pickle
import faiss
import numpy as np
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

# === Load environment ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === CONFIGURATION ===
PDFS_ROOT = "data/manuals"
INDEX_ROOT = "data/faiss_index"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE = 20
EMBEDDING_MODEL = "text-embedding-ada-002"

# === Functions ===

def get_embeddings_batch(texts, model=EMBEDDING_MODEL):
    cleaned_texts = [t.replace("\n", " ") for t in texts]
    response = client.embeddings.create(input=cleaned_texts, model=model)
    return [r.embedding for r in response.data]

def read_pdf_chunks(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = " ".join([page.extract_text() or "" for page in reader.pages])
        if not text.strip():
            print(f"⚠️ Skipping {pdf_path}: no extractable text.")
            return []
    except Exception as e:
        print(f"❌ Failed to read {pdf_path}: {e}")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

def embed_chunks(chunks):
    embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        try:
            batch_embeddings = get_embeddings_batch(batch)
            embeddings.extend([(i + j, emb) for j, emb in enumerate(batch_embeddings)])
        except Exception as e:
            print(f"❌ Error embedding batch at chunk {i}: {e}")
    return embeddings

def build_faiss_index(embeddings):
    dim = len(embeddings[0][1])
    index = faiss.IndexFlatL2(dim)
    vectors = np.array([emb for _, emb in embeddings], dtype="float32")
    index.add(vectors)
    return index

def find_all_pdfs(root_dir):
    return [
        os.path.join(dirpath, file)
        for dirpath, _, files in os.walk(root_dir)
        for file in files
        if file.lower().endswith(".pdf")
    ]

def process_machine(machine_name):
    print(f"\n🔧 Processing machine: {machine_name}")
    pdf_dir = os.path.join(PDFS_ROOT, machine_name)
    index_root = os.path.join(INDEX_ROOT, machine_name)
    os.makedirs(index_root, exist_ok=True)

    pdf_files = find_all_pdfs(pdf_dir)
    print(f"📄 Found {len(pdf_files)} PDFs.")

    for pdf_path in pdf_files:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"\n→ Reading PDF: {pdf_name}")

        chunks = read_pdf_chunks(pdf_path)
        if not chunks:
            continue

        print(f"   Embedding {len(chunks)} chunks...")
        embeddings = embed_chunks(chunks)

        if not embeddings:
            print(f"⚠️ Skipping {pdf_name}: no valid embeddings.")
            continue

        index_dir = os.path.join(index_root, pdf_name)
        os.makedirs(index_dir, exist_ok=True)

        print(f"🔨 Building FAISS index for {pdf_name}...")
        index = build_faiss_index(embeddings)

        id_to_text = {
            global_id: chunks[local_id]
            for global_id, (local_id, _) in enumerate(embeddings)
        }

        print(f"💾 Saving index to {index_dir}...")
        faiss.write_index(index, os.path.join(index_dir, "index.faiss"))
        with open(os.path.join(index_dir, "index.pkl"), "wb") as f:
            pickle.dump(id_to_text, f)

        print(f"✅ Finished processing: {pdf_name}")


def main():
    machine_name = "WLOL60H"  # 👈 Change this to target a different folder
    process_machine(machine_name)

if __name__ == "__main__":
    main()
