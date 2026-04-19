import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH

_model = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _model.encode(texts, convert_to_numpy=True).tolist()


def embed_query(query: str) -> list[float]:
    return _model.encode([query], convert_to_numpy=True)[0].tolist()


def ingest_client_data(client_id: str, documents: list[str]) -> chromadb.Collection:
    """
    Takes pre-loaded client documents, chunks, embeds locally,
    and stores in a per-client ChromaDB collection.
    """
    db = chromadb.PersistentClient(path=CHROMA_PATH)

    # Always delete and recreate so re-runs don't fail on duplicate IDs
    try:
        db.delete_collection(name=f"client_{client_id}")
    except Exception:
        pass
    collection = db.create_collection(name=f"client_{client_id}")

    all_chunks, all_ids = [], []
    for i, doc in enumerate(documents):
        for j, chunk in enumerate(chunk_text(doc)):
            all_chunks.append(chunk)
            all_ids.append(f"{client_id}_{i}_{j}")

    embeddings = embed_texts(all_chunks)
    collection.add(documents=all_chunks, embeddings=embeddings, ids=all_ids)

    print(f"Ingested {len(all_chunks)} chunks for client '{client_id}'")
    return collection


def get_collection(client_id: str) -> chromadb.Collection:
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    return db.get_collection(name=f"client_{client_id}")


def query_collection(client_id: str, query: str, n_results: int = 5) -> list[str]:
    collection = get_collection(client_id)
    embedding = embed_query(query)
    results = collection.query(query_embeddings=[embedding], n_results=n_results)
    return results["documents"][0]
