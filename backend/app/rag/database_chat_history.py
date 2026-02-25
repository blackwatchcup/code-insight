from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import update as sql_update

from app.core.database import SessionLocal
from app.models.chat_message import ChatMessage, ChatSession


class DatabaseChatHistoryManager:
    def __init__(self) -> None:
        pass

    def get_or_create_session(
        self,
        session_id: str,
        project_id: Optional[str] = None,
        chat_mode: str = "project",
        title: Optional[str] = None,
    ) -> ChatSession:
        """Get existing session or create a new one."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if not session:
                session = ChatSession(
                    id=session_id,
                    project_id=project_id,
                    chat_mode=chat_mode,
                    title=title,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            else:
                # Update session if needed
                if project_id is not None:
                    current_project_id = getattr(session, 'project_id', None)
                    if current_project_id != project_id:
                        setattr(session, 'project_id', project_id)
                if chat_mode:
                    current_mode = getattr(session, 'chat_mode', None)
                    if current_mode != chat_mode:
                        setattr(session, 'chat_mode', chat_mode)
                db.commit()
            
            return session
        except Exception as e:
            db.rollback()
            print(f"Error getting/creating session: {e}")
            raise
        finally:
            db.close()

    def update_session_title(self, session_id: str, title: str) -> None:
        """Update session title based on first user message."""
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            if session:
                current_title = getattr(session, 'title', None)
                if not current_title:
                    new_title = title[:50] + ("..." if len(title) > 50 else "")
                    setattr(session, 'title', new_title)
                    db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error updating session title: {e}")
        finally:
            db.close()

    def list_sessions(
        self,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all chat sessions with metadata."""
        db = SessionLocal()
        try:
            query = db.query(ChatSession).order_by(
                ChatSession.updated_at.desc()
            )
            
            if project_id:
                query = query.filter(ChatSession.project_id == project_id)
            
            sessions = query.offset(offset).limit(limit).all()
            
            result: List[Dict[str, Any]] = []
            for session in sessions:
                # Get message count
                msg_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).count()
                
                # Get last message preview
                last_msg = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).order_by(ChatMessage.timestamp.desc()).first()
                
                # Build title
                session_title = getattr(session, 'title', None)
                if not session_title:
                    if last_msg:
                        content = getattr(last_msg, 'content', '')
                        session_title = content[:30] + "..." if content else "新对话"
                    else:
                        session_title = "新对话"
                
                created_at_val = getattr(session, 'created_at', None)
                updated_at_val = getattr(session, 'updated_at', None)
                
                result.append({
                    "id": session.id,
                    "title": session_title,
                    "project_id": getattr(session, 'project_id', None),
                    "chat_mode": getattr(session, 'chat_mode', 'project'),
                    "created_at": created_at_val.isoformat() if created_at_val else None,
                    "updated_at": updated_at_val.isoformat() if updated_at_val else None,
                    "message_count": msg_count,
                })
            
            return result
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        db = SessionLocal()
        try:
            # Delete messages first
            db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete()
            
            # Delete session
            db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).delete()
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting session: {e}")
            return False
        finally:
            db.close()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        project_id: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        chat_mode: str = "project",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        db = SessionLocal()
        try:
            message = ChatMessage(
                id=f"{session_id}_{datetime.now().timestamp()}_{role}",
                session_id=session_id,
                project_id=project_id,
                role=role,
                content=content,
                sources=sources,
                chat_mode=chat_mode,
                extra_data=extra_data,
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Update session's updated_at timestamp
            db.execute(
                sql_update(ChatSession)
                .where(ChatSession.id == session_id)
                .values(updated_at=datetime.utcnow())
            )
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error adding message: {e}")
            raise
        finally:
            db.close()

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp.asc())
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            result: List[Dict[str, Any]] = []
            for msg in messages:
                ts = getattr(msg, 'timestamp', None)
                result.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": ts.isoformat() if ts else None,
                    "sources": msg.sources,
                    "chat_mode": getattr(msg, 'chat_mode', 'project'),
                    "extra_data": msg.extra_data,
                })
            return result
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
        finally:
            db.close()

    def clear_history(self, session_id: str) -> None:
        db = SessionLocal()
        try:
            db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error clearing history: {e}")
            raise
        finally:
            db.close()

    def get_context_for_llm(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        history = self.get_history(session_id, limit)
        return [{"role": msg["role"], "content": msg["content"]} for msg in history]

    def get_session_ids(self) -> List[str]:
        db = SessionLocal()
        try:
            session_ids = db.query(ChatMessage.session_id).distinct().all()
            return [sid[0] for sid in session_ids]
        except Exception as e:
            print(f"Error getting session IDs: {e}")
            return []
        finally:
            db.close()

    def get_message_count(self, session_id: str) -> int:
        db = SessionLocal()
        try:
            return db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).count()
        except Exception as e:
            print(f"Error getting message count: {e}")
            return 0
        finally:
            db.close()

    def export_history(self, session_id: str) -> Dict[str, Any]:
        history = self.get_history(session_id)
        return {
            "session_id": session_id,
            "messages": history,
        }

    def import_history(self, session_id: str, data: Dict[str, Any]) -> None:
        messages = data.get("messages", [])
        for msg_data in messages:
            self.add_message(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                sources=msg_data.get("sources"),
                chat_mode=msg_data.get("chat_mode", "project"),
                extra_data=msg_data.get("extra_data"),
            )
