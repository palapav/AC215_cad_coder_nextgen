from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, os

def build_vector_store(text_dir="/data/raw/texts", index_path="/data/processed/rag.index"):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    docs, embeddings = [], []
    for fname in os.listdir(text_dir):
        text = open(os.path.join(text_dir, fname)).read()
        chunks = RecursiveCharacterTextSplitter(chunk_size=500).split_text(text)
        embeddings.extend(model.encode(chunks))
        docs.extend(chunks)
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))
    faiss.write_index(index, index_path)
    print("✅ RAG index built:", index_path)

if __name__ == "__main__":
    build_vector_store()
