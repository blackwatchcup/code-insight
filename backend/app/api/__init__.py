from .auth import router as auth_router
from .chat import router as chat_router
from .features import router as features_router
from .parser import router as parser_router
from .projects import router as projects_router

__all__ = ["auth_router", "projects_router", "parser_router", "features_router", "chat_router"]
