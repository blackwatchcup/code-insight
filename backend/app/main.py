from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.docs import router as docs_router
from app.api.features import router as features_router
from app.api.graph import router as graph_router
from app.api.parser import router as parser_router
from app.api.projects import router as projects_router
from app.core.config import settings
from app.core.init_db import init_db
from app.core.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(projects_router, prefix="/api/v1/projects")
app.include_router(parser_router, prefix="/api/v1/parser")
app.include_router(features_router, prefix="/api/v1/features")
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(docs_router, prefix="/api/v1")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/import/{project_id}")
async def websocket_import(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
