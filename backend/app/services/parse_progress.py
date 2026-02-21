from dataclasses import dataclass
from typing import Optional, Callable, Awaitable
from enum import Enum

from app.core.websocket import manager


class ParseStage(str, Enum):
    INITIALIZING = "initializing"
    SCANNING = "scanning"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ParseProgress:
    stage: ParseStage
    current: int
    total: int
    message: str
    file_path: Optional[str] = None

    @property
    def percentage(self) -> int:
        if self.total <= 0:
            return 0
        return min(100, int(self.current / self.total * 100))

    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "message": self.message,
            "file_path": self.file_path,
        }


class ProgressTracker:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.progress: Optional[ParseProgress] = None
        self._callbacks: list[Callable[[ParseProgress], Awaitable[None]]] = []

    async def update(
        self,
        stage: ParseStage,
        current: int,
        total: int,
        message: str,
        file_path: Optional[str] = None,
    ):
        self.progress = ParseProgress(
            stage=stage,
            current=current,
            total=total,
            message=message,
            file_path=file_path,
        )

        await self._notify_progress()

    async def _notify_progress(self):
        if not self.progress:
            return

        try:
            await manager.send_progress(
                self.project_id,
                self.progress.stage.value,
                self.progress.percentage,
                self.progress.message,
            )
        except Exception:
            pass

        for callback in self._callbacks:
            try:
                await callback(self.progress)
            except Exception:
                pass

    def add_callback(self, callback: Callable[[ParseProgress], Awaitable[None]]):
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ParseProgress], Awaitable[None]]):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start(self, total: int, message: str = "Starting parse..."):
        await self.update(
            stage=ParseStage.INITIALIZING,
            current=0,
            total=total,
            message=message,
        )

    async def scanning(self, current: int, total: int, message: str = "Scanning files..."):
        await self.update(
            stage=ParseStage.SCANNING,
            current=current,
            total=total,
            message=message,
        )

    async def parsing(
        self,
        current: int,
        total: int,
        file_path: Optional[str] = None,
        message: str = "Parsing files...",
    ):
        await self.update(
            stage=ParseStage.PARSING,
            current=current,
            total=total,
            message=message,
            file_path=file_path,
        )

    async def analyzing(self, current: int, total: int, message: str = "Analyzing code..."):
        await self.update(
            stage=ParseStage.ANALYZING,
            current=current,
            total=total,
            message=message,
        )

    async def indexing(self, current: int, total: int, message: str = "Building index..."):
        await self.update(
            stage=ParseStage.INDEXING,
            current=current,
            total=total,
            message=message,
        )

    async def complete(self, message: str = "Parse completed"):
        await self.update(
            stage=ParseStage.COMPLETED,
            current=100,
            total=100,
            message=message,
        )

    async def error(self, message: str):
        await self.update(
            stage=ParseStage.ERROR,
            current=0,
            total=0,
            message=message,
        )

    def get_progress(self) -> Optional[ParseProgress]:
        return self.progress

    def is_complete(self) -> bool:
        return self.progress is not None and self.progress.stage == ParseStage.COMPLETED

    def has_error(self) -> bool:
        return self.progress is not None and self.progress.stage == ParseStage.ERROR
