from functools import lru_cache
import chromadb
from sentence_transformers import SentenceTransformer
from backend.core.config import settings, resolve_path
from backend.database.db import list_memories

@lru_cache(maxsize=1)
def get_embedder():
    return SentenceTransformer(settings.embedding_model)

@lru_cache(maxsize=1)
def get_collection():
    path = resolve_path(settings.chroma_path)
    path.mkdir(parents=True,exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection("memora_user_memories",metadata={"hnsw:space":"cosine"})

def index_memory(memory_id,user_id,content):
    vector = get_embedder().encode(content).tolist()
    get_collection().upsert(ids=[str(memory_id)],embeddings=[vector],documents=[content],
                            metadatas=[{"user_id":user_id}])

def search_memories(user_id,query,limit=5):
    collection = get_collection()
    if collection.count() == 0:
        return []
    vector = get_embedder().encode(query).tolist()
    result = collection.query(query_embeddings=[vector],n_results=min(limit,collection.count()),
                              where={"user_id":user_id},include=["documents","distances"])
    docs = result.get("documents",[[]])[0]
    distances = result.get("distances",[[]])[0]
    return [doc for doc,distance in zip(docs,distances) if distance <= 0.65]

def remove_index_entry(memory_id):
    get_collection().delete(ids=[str(memory_id)])

def remove_user_index(user_id):
    collection = get_collection()
    result = collection.get(where={"user_id":user_id},include=["metadatas"])
    if result.get("ids"):
        collection.delete(ids=result["ids"])
