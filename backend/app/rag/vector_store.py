import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr) + 1e-8))


@dataclass
class VectorStoreConfig:
    persist_directory: str = "./data/chroma"
    collection_name: str = "code_embeddings"
    embedding_dimension: int = 1536


class ChromaStore:
    """
    Simple in-memory vector store that mimics ChromaDB interface.
    Used as a fallback when ChromaDB has compatibility issues.
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig()
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._metadatas: Dict[str, Dict[str, Any]] = {}
        self._id_to_idx: Dict[str, int] = {}
        self._idx_counter = 0

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> None:
        if ids is None:
            ids = [doc["id"] for doc in documents]

        for i, (doc_id, doc, embedding) in enumerate(zip(ids, documents, embeddings)):
            self._documents[doc_id] = doc
            self._embeddings[doc_id] = embedding
            self._metadatas[doc_id] = doc.get("metadata", {})
            self._id_to_idx[doc_id] = self._idx_counter
            self._idx_counter += 1

    def query(
        self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        similarities = []

        for doc_id, embedding in self._embeddings.items():
            if where:
                metadata = self._metadatas.get(doc_id, {})
                match = all(metadata.get(k) == v for k, v in where.items())
                if not match:
                    continue

            sim = _cosine_similarity(query_embedding, embedding)
            similarities.append((doc_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:n_results]

        return {
            "ids": [[r[0] for r in top_results]],
            "documents": [[self._documents[r[0]]["content"] for r in top_results]],
            "metadatas": [[self._metadatas[r[0]] for r in top_results]],
            "distances": [[1 - r[1] for r in top_results]],
        }

    def delete_by_project(self, project_id: str) -> None:
        to_delete = [
            doc_id
            for doc_id, meta in self._metadatas.items()
            if meta.get("project_id") == project_id
        ]
        for doc_id in to_delete:
            self._documents.pop(doc_id, None)
            self._embeddings.pop(doc_id, None)
            self._metadatas.pop(doc_id, None)
            self._id_to_idx.pop(doc_id, None)

    def delete_by_ids(self, ids: List[str]) -> None:
        for doc_id in ids:
            self._documents.pop(doc_id, None)
            self._embeddings.pop(doc_id, None)
            self._metadatas.pop(doc_id, None)
            self._id_to_idx.pop(doc_id, None)

    def count(self) -> int:
        return len(self._documents)

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict] = None) -> Dict:
        result_ids = []
        result_documents = []
        result_metadatas = []

        for doc_id, meta in self._metadatas.items():
            if ids and doc_id not in ids:
                continue
            if where:
                match = all(meta.get(k) == v for k, v in where.items())
                if not match:
                    continue

            result_ids.append(doc_id)
            result_documents.append(self._documents[doc_id]["content"])
            result_metadatas.append(meta)

        return {"ids": result_ids, "documents": result_documents, "metadatas": result_metadatas}

    def update_document(
        self, doc_id: str, embedding: List[float], document: str, metadata: Dict
    ) -> None:
        self._documents[doc_id] = {"id": doc_id, "content": document}
        self._embeddings[doc_id] = embedding
        self._metadatas[doc_id] = metadata
