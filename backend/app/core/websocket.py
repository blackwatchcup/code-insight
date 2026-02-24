import json
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        self.active_connections[project_id].discard(websocket)

    async def send_progress(self, project_id: str, stage: str, progress: int, message: str):
        if project_id not in self.active_connections:
            return

        data = {
            "event": "progress",
            "data": {"stage": stage, "progress": progress, "message": message},
        }

        for connection in self.active_connections[project_id]:
            await connection.send_json(data)


manager = ConnectionManager()
