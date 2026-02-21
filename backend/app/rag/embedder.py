from dataclasses import dataclass, field
from typing import List, Optional
import tiktoken
import os

@dataclass
class EmbeddingConfig:
    model_name: str = "text-embedding-ada-002"
    api_key: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 8191

@dataclass
class CodeChunk:
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    metadata: dict = field(default_factory=dict)

class CodeEmbedder:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.api_key = config.api_key if config else os.getenv("OPENAI_API_KEY")
        self._encoding = tiktoken.encoding_for_model(self.config.model_name)
    
    def embed(self, text: str) -> List[float]:
        return self._get_embedding(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._get_embedding(text) for text in texts]
    
    def _get_embedding(self, text: str) -> List[float]:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
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
            line_tokens = len(self._encoding.encode(line))
            
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
        return len(self._encoding.encode(text))
