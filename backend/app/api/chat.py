import asyncio
import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.rag.qa_service import QAType
from app.services.rag_service import RAGService, get_rag_service

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    qa_type: Optional[str] = None
    top_k: int = 5
    chat_mode: str = "project"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # "project" or "freeform"


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


class SessionListResponse(BaseModel):
    code: int = 200
    data: List[dict]


class SessionResponse(BaseModel):
    code: int = 200
    data: dict


@router.post("/ask", response_model=AskResponse, tags=["Chat"])
async def ask_question(
    request: AskRequest,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db),
):
    qa_type = None
    if request.qa_type:
        try:
            qa_type = QAType(request.qa_type)
        except ValueError:
            pass

    llm_config = None
    if request.model or request.api_key or request.base_url:
        from app.llm.service import LLMConfig
        llm_config = LLMConfig(
            model=request.model if request.model else "deepseek-chat",
            api_key=request.api_key if request.api_key else None,
            base_url=request.base_url if request.base_url else None,
        )

    response = await rag_service.ask(
        question=request.question,
        project_id=request.project_id,
        session_id=request.session_id,
        qa_type=qa_type,
        top_k=request.top_k,
        chat_mode=request.chat_mode,
        llm_config=llm_config,
        db=db,
    )

    return AskResponse(code=200, data=response.to_dict())


@router.post("/ask/stream", tags=["Chat"])
async def ask_question_stream(
    request: AskRequest,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db),
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
                top_k=request.top_k,
                chat_mode=request.chat_mode,
                db=db,
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
        },
    )


@router.post("/search", response_model=SearchResponse, tags=["Chat"])
async def search_code(
    request: SearchRequest,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    results = rag_service.search(
        query=request.query,
        project_id=request.project_id,
        top_k=request.top_k,
        threshold=request.threshold,
    )

    return SearchResponse(code=200, data=results)


@router.post("/index", response_model=IndexResponse, tags=["Chat"])
async def index_project(
    request: IndexRequest,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db),
):
    from app.models.project import ProjectStatus
    from app.services.project_service import ProjectService

    result = await rag_service.index_project(
        project_id=request.project_id,
        project_path=request.project_path,
        file_extensions=request.file_extensions,
    )

    # Update project status to READY after successful indexing
    if result.get("success"):
        project_service = ProjectService(db)
        project = project_service.get_project(request.project_id)
        if project:
            from sqlalchemy import update

            db.execute(
                update(Project)
                .where(Project.id == request.project_id)
                .values(status=ProjectStatus.READY)
            )
            db.commit()

    return IndexResponse(code=200, data=result)


@router.delete("/index/{project_id}", tags=["Chat"])
async def delete_project_index(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    result = rag_service.delete_project_index(project_id)
    return {"code": 200, "data": result}


@router.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_chat_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    history = rag_service.get_chat_history(session_id, limit)
    return HistoryResponse(code=200, data=history)


@router.delete("/history/{session_id}", tags=["Chat"])
async def clear_chat_history(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    rag_service.clear_chat_history(session_id)
    return {"code": 200, "data": {"message": "History cleared"}}


@router.get("/sessions", response_model=SessionListResponse, tags=["Chat"])
async def list_chat_sessions(
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    """List all chat sessions with metadata."""
    sessions = rag_service.list_sessions(project_id, limit, offset)
    return SessionListResponse(code=200, data=sessions)


@router.delete("/sessions/{session_id}", tags=["Chat"])
async def delete_chat_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    """Delete a chat session and all its messages."""
    success = rag_service.delete_session(session_id)
    if success:
        return {"code": 200, "data": {"message": "Session deleted"}}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/stats", tags=["Chat"])
async def get_stats(
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    stats = rag_service.get_stats()
    return {"code": 200, "data": stats}


@router.get("/project-summary/{project_id}", tags=["Chat"])
async def get_project_summary(
    project_id: str,
    top_k: int = Query(20, ge=5, le=50),
    current_user: Optional[User] = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    """Generate a comprehensive summary of a project."""
    summary = await rag_service.generate_project_summary(
        project_id=project_id,
        top_k=top_k,
    )
    return {"code": 200, "data": summary}


# ===================== 智能聊天 API =====================

class SmartAskRequest(BaseModel):
    """智能聊天请求"""
    question: str
    project_id: str
    session_id: Optional[str] = None
    mode: Literal["smart", "full_context", "code_only", "documentation"] = "smart"
    top_k: int = 5
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class SmartAskResponse(BaseModel):
    """智能聊天响应"""
    code: int = 200
    data: dict


@router.post("/smart-ask", response_model=SmartAskResponse, tags=["Smart Chat"])
async def smart_ask_question(
    request: SmartAskRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    智能聊天接口 - 模拟OpenCode的动态数据获取流程
    
    流程：
    1. 分析用户问题，确定需要什么数据（README、摘要、代码等）
    2. 收集所需数据
    3. 构建智能上下文
    4. 调用LLM生成回答
    
    模式说明：
    - smart: 智能模式，动态分析需要什么数据
    - full_context: 完整上下文模式，使用所有可用上下文
    - code_only: 仅代码模式，只使用RAG检索的代码
    - documentation: 文档模式，只使用README和摘要
    """
    from app.services.smart_chat_service import SmartChatService, SmartChatMode
    from app.llm.service import LLMConfig
    
    # 配置LLM
    llm_config = None
    if request.model or request.api_key or request.base_url:
        llm_config = LLMConfig(
            model=request.model or "deepseek-chat",
            api_key=request.api_key,
            base_url=request.base_url,
        )
    
    # 获取RAG服务
    rag_service = get_rag_service()
    
    # 创建智能聊天服务
    smart_chat = SmartChatService(
        db=db,
        llm=rag_service.llm if not llm_config else None,
        retriever=rag_service.retriever,
    )
    
    # 转换模式
    mode_map = {
        "smart": SmartChatMode.SMART,
        "full_context": SmartChatMode.FULL_CONTEXT,
        "code_only": SmartChatMode.CODE_ONLY,
        "documentation": SmartChatMode.DOCUMENTATION,
    }
    
    try:
        response = await smart_chat.smart_chat(
            question=request.question,
            project_id=request.project_id,
            session_id=request.session_id,
            mode=mode_map.get(request.mode, SmartChatMode.SMART),
            top_k=request.top_k,
        )
        return SmartAskResponse(code=200, data=response.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能聊天失败: {str(e)}")


@router.post("/smart-ask/stream", tags=["Smart Chat"])
async def smart_ask_question_stream(
    request: SmartAskRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    智能聊天流式接口 - 支持流式输出
    """
    from app.services.smart_chat_service import SmartChatService, SmartChatMode
    
    # 获取RAG服务
    rag_service = get_rag_service()
    
    # 创建智能聊天服务
    smart_chat = SmartChatService(
        db=db,
        llm=rag_service.llm,
        retriever=rag_service.retriever,
    )
    
    # 转换模式
    mode_map = {
        "smart": SmartChatMode.SMART,
        "full_context": SmartChatMode.FULL_CONTEXT,
        "code_only": SmartChatMode.CODE_ONLY,
        "documentation": SmartChatMode.DOCUMENTATION,
    }
    
    async def generate():
        try:
            async for chunk in smart_chat.smart_chat_stream(
                question=request.question,
                project_id=request.project_id,
                session_id=request.session_id,
                mode=mode_map.get(request.mode, SmartChatMode.SMART),
                top_k=request.top_k,
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
        },
    )


@router.post("/analyze-needs/{project_id}", tags=["Smart Chat"])
async def analyze_data_needs(
    project_id: str,
    question: str = Query(..., description="用户问题"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    分析用户问题需要什么数据
    
    返回：
    - needs: 需要的数据类型列表
    - search_keywords: 搜索关键词（如果需要代码）
    - reason: 原因说明
    """
    from app.services.project_context_service import ProjectContextService
    
    context_service = ProjectContextService(db)
    
    try:
        result = await context_service.analyze_data_needs(project_id, question)
        return {"code": 200, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/generate-summary/{project_id}", tags=["Smart Chat"])
async def generate_project_llm_summary(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    使用LLM生成项目摘要
    
    摘要将保存到数据库，用于后续智能聊天
    """
    from app.services.project_context_service import ProjectContextService
    
    context_service = ProjectContextService(db)
    
    try:
        summary = await context_service.generate_project_summary(project_id)
        if summary:
            return {"code": 200, "data": {"summary": summary}}
        else:
            raise HTTPException(status_code=404, detail="项目不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成摘要失败: {str(e)}")


@router.get("/project-context/{project_id}", tags=["Smart Chat"])
async def get_project_context(
    project_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取项目的完整上下文信息
    
    包括：
    - README内容
    - 项目摘要
    - 技术栈
    - 文件数和代码行数
    """
    from app.services.project_context_service import ProjectContextService
    
    context_service = ProjectContextService(db)
    
    context = context_service.get_context(project_id)
    if context:
        return {
            "code": 200,
            "data": {
                "project_id": context.project_id,
                "project_name": context.project_name,
                "has_readme": context.readme_content is not None,
                "has_summary": context.project_summary is not None,
                "tech_stack": context.tech_stack,
                "file_count": context.file_count,
                "line_count": context.line_count,
                "source_type": context.source_type,
                "branch": context.branch,
            }
        }
    else:
        raise HTTPException(status_code=404, detail="项目不存在")

