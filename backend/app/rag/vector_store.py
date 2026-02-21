from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os

@dataclass
class VectorStoreConfig:
    persist_directory: str = "./data/chroma"
    collection_name: str = "code_embeddings"
    embedding_dimension: int = 1536

class ChromaStore:
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig()
        os.makedirs(self.config.persist_directory, exist_ok=True)
        
        import chromadb
        from chromadb.config import Settings
        
        self._client = chromadb.PersistentClient(path=self.config.persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None
    ) -> None:
        if ids is None:
            ids = [doc["id"] for doc in documents]
        
        contents = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
    
    def query(
        self, 
        query_embedding: List[float], 
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
    
    def delete_by_project(self, project_id: str) -> None:
        self._collection.delete(
            where={"project_id": project_id}
        )
    
    def delete_by_ids(self, ids: List[str]) -> None:
        self._collection.delete(ids=ids)
    
    def count(self) -> int:
        return self._collection.count()
    
    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict] = None) -> Dict:
        return self._collection.get(ids=ids, where=where)
    
    def update_document(
        self, 
        doc_id: str, 
        embedding: List[float],
        document: str,
        metadata: Dict
    ) -> None:
        self._collection.update(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata]
        )
