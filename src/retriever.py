import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = "C:/Users/Admin/Desktop/Finance_bot/index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class Retriever:
    def __init__(self, index_dir=INDEX_DIR, model_name=MODEL_NAME):
        # Load FAISS index
        index_path = os.path.join(index_dir, "faiss.index")
        if not os.path.exists(index_path):
            raise FileNotFoundError("FAISS index not found. Run build_index.py first.")
        self.index = faiss.read_index(index_path)

        # Load metadata
        meta_path = os.path.join(index_dir, "metadata.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # Load embedding model
        self.model = SentenceTransformer(model_name)

    def retrieve(self, query, top_k=3):
        """Return top_k results for query."""
        query_emb = self.model.encode([query]).astype("float32")

        # Search FAISS index
        distances, indices = self.index.search(query_emb, top_k)

        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = self.metadata[idx]
            results.append({
                "content": meta["content"],
                "source": meta["filename"],
                "score": float(score)
            })

        return results


# --------------------
# Test runner
# --------------------
if __name__ == "__main__":
    retriever = Retriever()
    while True:
        query = input("\nEnter a query (or 'quit'): ")
        if query.lower() == "quit":
            break

        results = retriever.retrieve(query, top_k=3)
        print("\nTop results:")
        for r in results:
            print(f"- [source: {r['source']}] (score={r['score']:.4f})")
            print(f"  {r['content'][:200]}...\n")
