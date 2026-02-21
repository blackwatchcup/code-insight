from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.rag.embedder import CodeEmbedder
from app.rag.vector_store import ChromaStore

@dataclass
class RetrievalResult:
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata
        }

class SemanticRetriever:
    def __init__(
        self, 
        embedder: CodeEmbedder, 
        store: ChromaStore,
        default_top_k: int = 5
    ):
        self.embedder = embedder
        self.store = store
        self.default_top_k = default_top_k
    
    def retrieve(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        project_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        top_k = top_k or self.default_top_k
        
        if self.store.count() == 0:
            return []
        
        try:
            query_embedding = self.embedder.embed(query)
        except Exception as e:
            print(f"Warning: Embedding failed: {e}")
            return []
        
        where_filter = None
        if project_id:
            where_filter = {"project_id": project_id}
        
        results = self.store.query(
            query_embedding=query_embedding,
            n_results=top_k,
            where=where_filter
        )
        
        retrieval_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                score = 1 - results["distances"][0][i]
                
                if threshold and score < threshold:
                    continue
                
                retrieval_results.append(RetrievalResult(
                    id=doc_id,
                    content=results["documents"][0][i],
                    score=score,
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {}
                ))
        
        return retrieval_results
    
    def retrieve_by_code(
        self, 
        code: str, 
        top_k: Optional[int] = None,
        project_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        top_k = top_k or self.default_top_k
        
        if self.store.count() == 0:
            return []
        
        try:
            code_embedding = self.embedder.embed(code)
        except Exception as e:
            print(f"Warning: Embedding failed: {e}")
            return []
        
        where_filter = None
        if project_id:
            where_filter = {"project_id": project_id}
        
        results = self.store.query(
            query_embedding=code_embedding,
            n_results=top_k,
            where=where_filter
        )
        
        retrieval_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                retrieval_results.append(RetrievalResult(
                    id=doc_id,
                    content=results["documents"][0][i],
                    score=1 - results["distances"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {}
                ))
        
        return retrieval_results
    
    def hybrid_retrieve(
        self, 
        query: str,
        keywords: List[str],
        top_k: int = 5,
        project_id: Optional[str] = None
    ) -> List[RetrievalResult]:
        semantic_results = self.retrieve(query, top_k=top_k * 2, project_id=project_id)
        
        keyword_results = []
        if keywords:
            for kw in keywords:
                kw_lower = kw.lower()
                for result in semantic_results:
                    if kw_lower in result.content.lower():
                        if result not in keyword_results:
                            keyword_results.append(result)
        
        combined = {}
        for result in semantic_results:
            combined[result.id] = result
            combined[result.id].score *= 0.7
        
        for result in keyword_results:
            if result.id in combined:
                combined[result.id].score += 0.3
            else:
                combined[result.id] = result
        
        sorted_results = sorted(
            combined.values(), 
            key=lambda x: x.score, 
            reverse=True
        )
        
        return sorted_results[:top_k]
