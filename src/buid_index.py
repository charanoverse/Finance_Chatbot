import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = "./data"
INDEX_DIR = "./index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 300  # approx characters, not strict words


def load_documents(data_dir):
    """Load all .txt files from data/ directory."""
    docs = []
    for fname in os.listdir(data_dir):
        if fname.endswith(".txt"):
            path = os.path.join(data_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                docs.append({"filename": fname, "content": text})
    return docs


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split long text into smaller chunks."""
    words = text.split()
    chunks, cur_chunk = [], []

    for word in words:
        cur_chunk.append(word)
        if len(" ".join(cur_chunk)) >= chunk_size:
            chunks.append(" ".join(cur_chunk))
            cur_chunk = []

    if cur_chunk:
        chunks.append(" ".join(cur_chunk))

    return chunks


def build_index(docs, model):
    """Create FAISS index and metadata list."""
    embeddings = []
    metadata = []

    for doc in docs:
        chunks = chunk_text(doc["content"], CHUNK_SIZE)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk)
            embeddings.append(emb)
            metadata.append({
                "filename": doc["filename"],
                "chunk_id": idx,
                "content": chunk
            })

    embeddings = np.array(embeddings).astype("float32")

    # FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, metadata


def save_index(index, metadata, out_dir=INDEX_DIR):
    """Save FAISS index and metadata JSON."""
    os.makedirs(out_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(out_dir, "faiss.index"))

    with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def main():
    print("📂 Loading documents...")
    docs = load_documents(DATA_DIR)
    print(f"Loaded {len(docs)} documents.")

    print("🔎 Initializing model...")
    model = SentenceTransformer(MODEL_NAME)

    print("⚡ Building index...")
    index, metadata = build_index(docs, model)

    print("💾 Saving index & metadata...")
    save_index(index, metadata)

    print(f"✅ Done! {len(metadata)} chunks indexed.")
    print("Files created: index/faiss.index and index/metadata.json")


if __name__ == "__main__":
    main()
