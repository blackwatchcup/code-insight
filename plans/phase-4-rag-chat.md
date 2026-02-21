# Phase 4: RAG问答系统 - 执行计划

**目标**：实现基于RAG的智能问答系统，支持三种问答模式  
**任务数**：10个  
**预计时间**：2周  
**分支**：feature/phase-4-rag-chat  
**依赖**：Phase 2 完成

---

## 任务 4.1：代码向量化

### 描述
实现代码片段的向量化处理。

### 执行步骤

1. 创建Embedding服务 `app/rag/embedder.py`
```python
from typing import List
from dataclasses import dataclass
from openai import OpenAI
from app.core.config import settings

@dataclass
class CodeChunk:
    id: str
    content: str
    file_path: str
    line_start: int
    line_end: int
    chunk_type: str  # function, class, file
    name: str
    language: str

class Embedder:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def chunk_code(self, parse_result) -> List[CodeChunk]:
        chunks = []
        
        # 按函数分块
        for func in parse_result.functions:
            chunks.append(CodeChunk(
                id=f"{parse_result.file_path}:{func.name}",
                content=func.body,
                file_path=parse_result.file_path,
                line_start=func.start_line,
                line_end=func.end_line,
                chunk_type="function",
                name=func.name,
                language=parse_result.language
            ))
        
        # 按类分块
        for cls in parse_result.classes:
            chunks.append(CodeChunk(
                id=f"{parse_result.file_path}:{cls.name}",
                content="",  # 类的完整内容
                file_path=parse_result.file_path,
                line_start=cls.start_line,
                line_end=cls.end_line,
                chunk_type="class",
                name=cls.name,
                language=parse_result.language
            ))
        
        return chunks
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def embed_chunks(self, chunks: List[CodeChunk]) -> List[dict]:
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed(texts)
        
        return [
            {
                "id": chunk.id,
                "embedding": emb,
                "metadata": {
                    "file_path": chunk.file_path,
                    "line_start": chunk.line_start,
                    "line_end": chunk.line_end,
                    "chunk_type": chunk.chunk_type,
                    "name": chunk.name,
                    "language": chunk.language
                },
                "document": chunk.content
            }
            for chunk, emb in zip(chunks, embeddings)
        ]
```

### 验收标准
- [ ] 可分块代码
- [ ] 可生成Embedding
- [ ] 处理批量请求

### 提交信息
```
feat(rag): add code embedding service
```

---

## 任务 4.2：ChromaDB集成

### 描述
集成ChromaDB向量数据库。

### 执行步骤

1. 创建向量存储服务 `app/rag/vector_store.py`
```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from app.core.config import settings

class VectorStore:
    def __init__(self, project_id: str):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=f"project_{project_id}",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add(self, items: List[Dict]):
        self.collection.add(
            ids=[item["id"] for item in items],
            embeddings=[item["embedding"] for item in items],
            metadatas=[item["metadata"] for item in items],
            documents=[item["document"] for item in items]
        )
    
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0]
        }
    
    def delete(self, ids: List[str]):
        self.collection.delete(ids=ids)
    
    def delete_by_file(self, file_path: str):
        self.collection.delete(
            where={"file_path": file_path}
        )
    
    def count(self) -> int:
        return self.collection.count()
```

### 验收标准
- [ ] 可创建集合
- [ ] 可添加向量
- [ ] 可搜索向量
- [ ] 可删除向量

### 提交信息
```
feat(rag): add chromadb vector store integration
```

---

## 任务 4.3：语义检索

### 描述
实现基于语义相似度的代码检索。

### 执行步骤

1. 创建检索器 `app/rag/retriever.py`
```python
from typing import List, Dict
from dataclasses import dataclass
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore
from app.core.config import settings

@dataclass
class SearchResult:
    id: str
    content: str
    file_path: str
    line_start: int
    line_end: int
    score: float
    metadata: Dict

class Retriever:
    def __init__(self, project_id: str):
        self.embedder = Embedder()
        self.store = VectorStore(project_id)
        self.similarity_threshold = 0.7
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Dict = None
    ) -> List[SearchResult]:
        # 生成查询向量
        query_embedding = self.embedder.embed([query])[0]
        
        # 搜索
        results = self.store.search(
            query_embedding=query_embedding,
            n_results=top_k,
            where=filters
        )
        
        # 转换结果
        search_results = []
        for i, doc_id in enumerate(results["ids"]):
            # 计算相似度 (1 - distance for cosine)
            similarity = 1 - results["distances"][i]
            
            # 过滤低相似度结果
            if similarity < self.similarity_threshold:
                continue
            
            search_results.append(SearchResult(
                id=doc_id,
                content=results["documents"][i],
                file_path=results["metadatas"][i]["file_path"],
                line_start=results["metadatas"][i]["line_start"],
                line_end=results["metadatas"][i]["line_end"],
                score=similarity,
                metadata=results["metadatas"][i]
            ))
        
        return search_results
    
    async def search_by_type(
        self, 
        query: str, 
        chunk_type: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        return await self.search(
            query=query,
            top_k=top_k,
            filters={"chunk_type": chunk_type}
        )
```

### 验收标准
- [ ] 可语义搜索
- [ ] 支持相似度阈值
- [ ] 支持过滤条件

### 提交信息
```
feat(rag): add semantic retriever
```

---

## 任务 4.4：LLM服务层

### 描述
封装OpenAI/Claude API调用。

### 执行步骤

1. 创建LLM基类 `app/llm/base.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator

class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self, 
        messages: List[Dict], 
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        pass
```

2. 创建OpenAI服务 `app/llm/openai_service.py`
```python
from openai import AsyncOpenAI
from app.llm.base import BaseLLM
from app.core.config import settings

class OpenAIService(BaseLLM):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate(
        self, 
        messages: List[Dict], 
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    async def generate_stream(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

3. 创建Claude服务 `app/llm/claude_service.py`
```python
from anthropic import AsyncAnthropic
from app.llm.base import BaseLLM
from app.core.config import settings

class ClaudeService(BaseLLM):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = "claude-3-opus-20240229"
    
    async def generate(
        self, 
        messages: List[Dict], 
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.content[0].text
```

### 验收标准
- [ ] OpenAI API可调用
- [ ] Claude API可调用
- [ ] 支持流式输出

### 提交信息
```
feat(llm): add openai and claude service layer
```

---

## 任务 4.5：实现型问答

### 描述
实现严格基于代码库的问答模式。

### 执行步骤

1. 创建Prompt模板 `app/llm/prompts.py`
```python
IMPLEMENTATION_SYSTEM_PROMPT = """你是一个代码库问答助手。你的回答必须严格基于提供的代码上下文。

规则：
1. 只使用 <context> 中提供的代码片段回答问题
2. 如果 <context> 中没有相关信息，回复："根据当前项目代码库，未找到与该问题相关的信息。"
3. 每个回答必须标注引用来源，格式：[来源: file_path:行号]
4. 不要使用你的通用编程知识进行推测或补充
5. 如果信息不确定，明确说明"代码库中信息不完整"

引用格式示例：
- 用户登录接口定义 [来源: backend/api/auth.py:45]
"""

IMPLEMENTATION_USER_PROMPT = """基于以下代码上下文回答问题：

<context>
{context}
</context>

问题：{question}

请严格基于上述代码回答，并标注引用来源。"""
```

2. 创建问答服务 `app/services/chat_service.py`
```python
from typing import List, Dict, Optional
from app.rag.retriever import Retriever, SearchResult
from app.llm.openai_service import OpenAIService
from app.llm.prompts import IMPLEMENTATION_SYSTEM_PROMPT, IMPLEMENTATION_USER_PROMPT
from dataclasses import dataclass

@dataclass
class ChatResponse:
    answer: str
    references: List[Dict]
    confidence: float
    mode: str

class ChatService:
    def __init__(self, project_id: str):
        self.retriever = Retriever(project_id)
        self.llm = OpenAIService()
    
    async def chat_implementation(
        self, 
        question: str,
        top_k: int = 5
    ) -> ChatResponse:
        # 1. 检索相关代码
        results = await self.retriever.search(question, top_k=top_k)
        
        # 2. 检查是否有足够相关的结果
        if not results:
            return ChatResponse(
                answer="根据当前项目代码库，未找到与该问题相关的信息。",
                references=[],
                confidence=0.0,
                mode="implementation"
            )
        
        # 3. 构建上下文
        context = self._build_context(results)
        
        # 4. 生成回答
        messages = [
            {"role": "system", "content": IMPLEMENTATION_SYSTEM_PROMPT},
            {"role": "user", "content": IMPLEMENTATION_USER_PROMPT.format(
                context=context,
                question=question
            )}
        ]
        
        answer = await self.llm.generate(messages)
        
        # 5. 计算置信度
        confidence = sum(r.score for r in results) / len(results)
        
        return ChatResponse(
            answer=answer,
            references=self._format_references(results),
            confidence=confidence,
            mode="implementation"
        )
    
    def _build_context(self, results: List[SearchResult]) -> str:
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] 文件: {result.file_path} (行 {result.line_start}-{result.line_end})\n"
                f"```{result.metadata.get('language', '')}\n"
                f"{result.content}\n"
                f"```\n"
            )
        return "\n".join(context_parts)
    
    def _format_references(self, results: List[SearchResult]) -> List[Dict]:
        return [
            {
                "file_path": r.file_path,
                "line_start": r.line_start,
                "line_end": r.line_end,
                "snippet": r.content[:200] + "..." if len(r.content) > 200 else r.content
            }
            for r in results
        ]
```

### 验收标准
- [ ] 只使用检索到的代码回答
- [ ] 无结果时明确说明
- [ ] 引用代码位置

### 提交信息
```
feat(chat): add implementation mode chat
```

---

## 任务 4.6：规划型问答

### 描述
实现基于LLM行业知识的问答模式。

### 执行步骤

1. 添加Prompt模板
```python
PLANNING_SYSTEM_PROMPT = """你是一个资深的软件架构师和技术顾问。你的任务是提供专业的技术建议和最佳实践。

规则：
1. 基于你的专业知识和行业经验回答问题
2. 提供具体、可操作的建议
3. 引用行业标准和最佳实践
4. 考虑不同场景下的权衡
5. 提供代码示例时使用最佳实践

回答结构：
1. 概述
2. 推荐方案
3. 实现步骤
4. 注意事项
5. 代码示例（如适用）"""

PLANNING_USER_PROMPT = """问题：{question}

请基于你的专业知识提供建议和最佳实践。"""
```

2. 实现规划型问答
```python
async def chat_planning(self, question: str) -> ChatResponse:
    messages = [
        {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
        {"role": "user", "content": PLANNING_USER_PROMPT.format(question=question)}
    ]
    
    answer = await self.llm.generate(messages, temperature=0.8)
    
    return ChatResponse(
        answer=answer,
        references=[],  # 无代码引用
        confidence=1.0,  # 基于LLM知识
        mode="planning"
    )
```

### 验收标准
- [ ] 不依赖代码库
- [ ] 提供专业建议
- [ ] 结构化回答

### 提交信息
```
feat(chat): add planning mode chat
```

---

## 任务 4.7：混合型问答

### 描述
结合代码现状和改进建议的问答模式。

### 执行步骤

1. 添加Prompt模板
```python
HYBRID_SYSTEM_PROMPT = """你是一个代码库分析和改进顾问。你需要：
1. 首先分析项目中已有的实现
2. 然后提供改进建议和最佳实践

回答结构：
📍 当前实现状态：
- 列出项目中的相关实现
- 标注代码位置 [来源: file_path:行号]

💡 改进建议：
- 基于行业最佳实践的建议
- 具体的优化方向
- 可能的扩展功能"""

HYBRID_USER_PROMPT = """基于以下代码上下文和问题：

<context>
{context}
</context>

问题：{question}

请先说明当前项目中的实现状态，再提供改进建议。"""
```

2. 实现混合型问答
```python
async def chat_hybrid(self, question: str, top_k: int = 5) -> ChatResponse:
    # 1. 检索相关代码
    results = await self.retriever.search(question, top_k=top_k)
    
    # 2. 构建上下文（即使为空也继续）
    context = self._build_context(results) if results else "项目中未找到相关代码。"
    
    # 3. 生成回答
    messages = [
        {"role": "system", "content": HYBRID_SYSTEM_PROMPT},
        {"role": "user", "content": HYBRID_USER_PROMPT.format(
            context=context,
            question=question
        )}
    ]
    
    answer = await self.llm.generate(messages, temperature=0.7)
    
    confidence = sum(r.score for r in results) / len(results) if results else 0.5
    
    return ChatResponse(
        answer=answer,
        references=self._format_references(results) if results else [],
        confidence=confidence,
        mode="hybrid"
    )
```

### 验收标准
- [ ] 先说明现状
- [ ] 再提供建议
- [ ] 两者清晰区分

### 提交信息
```
feat(chat): add hybrid mode chat
```

---

## 任务 4.8：引用溯源

### 描述
在回答中准确标注代码引用位置。

### 执行步骤

1. 创建引用验证器 `app/services/reference_validator.py`
```python
from pathlib import Path
from typing import List, Dict

class ReferenceValidator:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def validate(self, references: List[Dict]) -> List[Dict]:
        validated = []
        
        for ref in references:
            file_path = self.project_path / ref["file_path"]
            
            if not file_path.exists():
                ref["valid"] = False
                ref["error"] = "文件不存在"
                validated.append(ref)
                continue
            
            # 读取文件验证行号
            lines = file_path.read_text(encoding="utf-8", errors="ignore").split("\n")
            
            if ref["line_start"] > len(lines):
                ref["valid"] = False
                ref["error"] = "行号超出范围"
            else:
                ref["valid"] = True
                # 获取实际代码片段
                end_line = min(ref["line_end"], len(lines))
                ref["actual_content"] = "\n".join(
                    lines[ref["line_start"]-1:end_line]
                )
            
            validated.append(ref)
        
        return validated
    
    def format_reference(self, ref: Dict) -> str:
        if not ref.get("valid", True):
            return f"[引用无效: {ref.get('error')}]"
        
        return f"[来源: {ref['file_path']}:{ref['line_start']}]"
```

### 验收标准
- [ ] 验证文件存在
- [ ] 验证行号有效
- [ ] 提取实际内容

### 提交信息
```
feat(chat): add reference validation and formatting
```

---

## 任务 4.9：流式响应

### 描述
实现SSE流式返回答案。

### 执行步骤

1. 创建流式问答API
```python
# app/api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.chat_service import ChatService
import json

router = APIRouter()

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    chat_service = ChatService(request.project_id)
    
    async def generate():
        yield f"data: {json.dumps({'event': 'start'})}\n\n"
        
        if request.mode == "implementation":
            # 先返回检索结果
            results = await chat_service.retriever.search(request.question)
            for result in results:
                yield f"data: {json.dumps({'event': 'reference', 'data': {}})}\n\n"
            
            # 流式返回回答
            messages = chat_service._build_implementation_messages(request.question, results)
            async for token in chat_service.llm.generate_stream(messages):
                yield f"data: {json.dumps({'event': 'token', 'data': {'content': token}})}\n\n"
        
        elif request.mode == "planning":
            async for token in chat_service.llm.generate_stream(
                chat_service._build_planning_messages(request.question)
            ):
                yield f"data: {json.dumps({'event': 'token', 'data': {'content': token}})}\n\n"
        
        yield f"data: {json.dumps({'event': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 验收标准
- [ ] SSE格式正确
- [ ] 实时返回token
- [ ] 正确结束流

### 提交信息
```
feat(chat): add streaming response support
```

---

## 任务 4.10：对话历史

### 描述
实现多轮对话上下文管理。

### 执行步骤

1. 创建会话管理 `app/services/session_service.py`
```python
from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str
    references: List[Dict]
    created_at: datetime

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[Message]] = {}
        self.max_history = 10
    
    def get_history(self, session_id: str) -> List[Message]:
        return self.sessions.get(session_id, [])
    
    def add_message(self, session_id: str, message: Message):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append(message)
        
        # 限制历史长度
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history * 2:]
    
    def build_context(self, session_id: str) -> List[Dict]:
        history = self.get_history(session_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]
```

2. 集成到问答服务
```python
async def chat_with_history(
    self, 
    question: str, 
    session_id: str,
    mode: str
) -> ChatResponse:
    # 获取历史上下文
    history = self.session_manager.build_context(session_id)
    
    # 添加新问题
    history.append({"role": "user", "content": question})
    
    # 根据模式生成回答
    if mode == "implementation":
        response = await self.chat_implementation(question)
    elif mode == "planning":
        response = await self.chat_planning(question)
    else:
        response = await self.chat_hybrid(question)
    
    # 保存消息
    self.session_manager.add_message(session_id, Message(
        role="user",
        content=question,
        references=[],
        created_at=datetime.now()
    ))
    self.session_manager.add_message(session_id, Message(
        role="assistant",
        content=response.answer,
        references=response.references,
        created_at=datetime.now()
    ))
    
    return response
```

### 验收标准
- [ ] 可保存会话
- [ ] 可获取历史
- [ ] 限制历史长度

### 提交信息
```
feat(chat): add conversation history management
```

---

## Phase 4 完成标准

- [ ] 代码可向量化
- [ ] ChromaDB可存储检索
- [ ] 语义搜索可用
- [ ] LLM服务可用
- [ ] 实现型问答可用
- [ ] 规划型问答可用
- [ ] 混合型问答可用
- [ ] 引用可溯源
- [ ] 流式响应可用
- [ ] 对话历史可管理

## 下一阶段

完成 Phase 4 后，进入 Phase 5: 可视化与文档
