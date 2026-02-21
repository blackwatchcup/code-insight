from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import asyncio

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.rag_service import get_rag_service, RAGService
from app.rag.qa_service import QAType

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    qa_type: Optional[str] = None
    top_k: int = 5

class AskResponse(BaseModel):
    code: int = 200
    data: dict

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    top_k: int = 5
    threshold: Optional[float] = None

class SearchResponse(BaseModel):
    code: int = 200
    data: List[dict]

class IndexRequest(BaseModel):
    project_id: str
    project_path: str
    file_extensions: Optional[List[str]] = None

class IndexResponse(BaseModel):
    code: int = 200
    data: dict

class HistoryResponse(BaseModel):
    code: int = 200
    data: List[dict]

@router.post("/ask", response_model=AskResponse, tags=["Chat"])
async def ask_question(
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    qa_type = None
    if request.qa_type:
        try:
            qa_type = QAType(request.qa_type)
        except ValueError:
            pass
    
    response = await rag_service.ask(
        question=request.question,
        project_id=request.project_id,
        session_id=request.session_id,
        qa_type=qa_type,
        top_k=request.top_k
    )
    
    return AskResponse(code=200, data=response.to_dict())

@router.post("/ask/stream", tags=["Chat"])
async def ask_question_stream(
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    qa_type = None
    if request.qa_type:
        try:
            qa_type = QAType(request.qa_type)
        except ValueError:
            pass
    
    async def generate():
        try:
            async for chunk in rag_service.ask_stream(
                question=request.question,
                project_id=request.project_id,
                session_id=request.session_id,
                qa_type=qa_type,
                top_k=request.top_k
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.post("/search", response_model=SearchResponse, tags=["Chat"])
async def search_code(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    results = rag_service.search(
        query=request.query,
        project_id=request.project_id,
        top_k=request.top_k,
        threshold=request.threshold
    )
    
    return SearchResponse(code=200, data=results)

@router.post("/index", response_model=IndexResponse, tags=["Chat"])
async def index_project(
    request: IndexRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    result = await rag_service.index_project(
        project_id=request.project_id,
        project_path=request.project_path,
        file_extensions=request.file_extensions
    )
    
    return IndexResponse(code=200, data=result)

@router.delete("/index/{project_id}", tags=["Chat"])
async def delete_project_index(
    project_id: str,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    result = rag_service.delete_project_index(project_id)
    return {"code": 200, "data": result}

@router.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_chat_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    history = rag_service.get_chat_history(session_id, limit)
    return HistoryResponse(code=200, data=history)

@router.delete("/history/{session_id}", tags=["Chat"])
async def clear_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    rag_service.clear_chat_history(session_id)
    return {"code": 200, "data": {"message": "History cleared"}}

@router.get("/stats", tags=["Chat"])
async def get_stats(
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    stats = rag_service.get_stats()
    return {"code": 200, "data": stats}
