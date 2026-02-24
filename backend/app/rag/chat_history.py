from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class ChatHistoryManager:
    def __init__(self, max_history: int = 100):
        self.histories: Dict[str, List[ChatMessage]] = defaultdict(list)
        self.max_history = max_history

    def add_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> None:
        message = ChatMessage(
            role=role, content=content, timestamp=datetime.now(), metadata=metadata or {}
        )
        self.histories[session_id].append(message)

        if len(self.histories[session_id]) > self.max_history:
            self.histories[session_id] = self.histories[session_id][-self.max_history :]

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        history = self.histories.get(session_id, [])
        if limit:
            return history[-limit:]
        return history

    def clear_history(self, session_id: str) -> None:
        if session_id in self.histories:
            del self.histories[session_id]

    def get_context_for_llm(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        history = self.get_history(session_id, limit)
        return [{"role": msg.role, "content": msg.content} for msg in history]

    def get_session_ids(self) -> List[str]:
        return list(self.histories.keys())

    def get_message_count(self, session_id: str) -> int:
        return len(self.histories.get(session_id, []))

    def export_history(self, session_id: str) -> Dict:
        history = self.get_history(session_id)
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in history
            ],
        }

    def import_history(self, session_id: str, data: Dict) -> None:
        for msg_data in data.get("messages", []):
            self.add_message(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                metadata=msg_data.get("metadata"),
            )
