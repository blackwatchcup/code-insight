from dataclasses import dataclass, field
from typing import List, Optional
import tiktoken
import os
import hashlib
import numpy as np

@dataclass
class EmbeddingConfig:
    model_name: str = "local"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 8191
    use_local: bool = True
    embedding_dim: int = 384

@dataclass
class CodeChunk:
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    metadata: dict = field(default_factory=dict)

class LocalEmbedder:
    """Simple local embedder using character n-grams and hashing."""
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self._model = None
        self._use_sentence_transformers = False
    
    def _try_load_sentence_transformers(self):
        """Try to load sentence-transformers model."""
        if self._model is not None:
            return self._use_sentence_transformers
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            self._use_sentence_transformers = True
            print("Loaded sentence-transformers model: all-MiniLM-L6-v2")
            return True
        except ImportError:
            print("sentence-transformers not installed, using hash-based embedding")
            self._use_sentence_transformers = False
            return False
        except Exception as e:
            print(f"Failed to load sentence-transformers: {e}")
            self._use_sentence_transformers = False
            return False
    
    def embed(self, text: str) -> List[float]:
        if self._try_load_sentence_transformers() and self._model:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        return self._hash_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self._try_load_sentence_transformers() and self._model:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return [e.tolist() for e in embeddings]
        
        return [self._hash_embed(text) for text in texts]
    
    def _hash_embed(self, text: str) -> List[float]:
        """Generate embedding using n-gram hashing."""
        text = text.lower()
        ngrams = self._get_ngrams(text, n=3)
        
        embedding = np.zeros(self.dim, dtype=np.float32)
        
        for ngram in ngrams:
            hash_bytes = hashlib.md5(ngram.encode()).digest()
            hash_int = int.from_bytes(hash_bytes[:4], 'little')
            idx = hash_int % self.dim
            
            sign_bytes = hashlib.sha1(ngram.encode()).digest()
            sign = 1 if sign_bytes[0] % 2 == 0 else -1
            
            embedding[idx] += sign
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()
    
    def _get_ngrams(self, text: str, n: int = 3) -> List[str]:
        """Extract character n-grams from text."""
        text = ' ' + text + ' '
        return [text[i:i+n] for i in range(len(text) - n + 1)]

class CodeEmbedder:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.api_key = config.api_key if config else os.getenv("OPENAI_API_KEY")
        self.base_url = config.base_url if config else os.getenv("EMBEDDING_BASE_URL")
        self.use_local = config.use_local if config else True
        
        try:
            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None
        
        self._local_embedder = None
        self._api_available = None
    
    def _get_local_embedder(self) -> LocalEmbedder:
        if self._local_embedder is None:
            self._local_embedder = LocalEmbedder(dim=self.config.embedding_dim)
        return self._local_embedder
    
    def _check_api_available(self) -> bool:
        """Check if API embedding is available."""
        if self._api_available is not None:
            return self._api_available
        
        if not self.api_key:
            self._api_available = False
            return False
        
        try:
            import openai
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            client = openai.OpenAI(**client_kwargs)
            client.models.list()
            self._api_available = True
            return True
        except Exception:
            self._api_available = False
            return False
    
    def embed(self, text: str) -> List[float]:
        if self.use_local or not self._check_api_available():
            return self._get_local_embedder().embed(text)
        return self._get_api_embedding(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self.use_local or not self._check_api_available():
            return self._get_local_embedder().embed_batch(texts)
        return [self._get_api_embedding(text) for text in texts]
    
    def _get_api_embedding(self, text: str) -> List[float]:
        import openai
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = openai.OpenAI(**client_kwargs)
        text = text.replace("\n", " ")
        response = client.embeddings.create(
            model=self.config.model_name,
            input=text
        )
        return response.data[0].embedding
    
    def chunk_code(self, code: str, file_path: str = "") -> List[CodeChunk]:
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_start = 1
        current_tokens = 0
        
        for i, line in enumerate(lines, 1):
            if self._encoding:
                line_tokens = len(self._encoding.encode(line))
            else:
                line_tokens = len(line.split())
            
            if current_tokens + line_tokens > self.config.chunk_size or \
               (len(current_chunk) > 0 and len(current_chunk) >= 50):
                if current_chunk:
                    chunks.append(CodeChunk(
                        id=f"{file_path}:{current_start}:{i-1}",
                        content='\n'.join(current_chunk),
                        file_path=file_path,
                        start_line=current_start,
                        end_line=i-1
                    ))
                current_chunk = [line]
                current_start = i
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        if current_chunk:
            chunks.append(CodeChunk(
                id=f"{file_path}:{current_start}:{len(lines)}",
                content='\n'.join(current_chunk),
                file_path=file_path,
                start_line=current_start,
                end_line=len(lines)
            ))
        
        return chunks
    
    def count_tokens(self, text: str) -> int:
        if self._encoding:
            return len(self._encoding.encode(text))
        return len(text.split())
