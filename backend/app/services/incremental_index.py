import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileChange:
    path: str
    change_type: str
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChangeSet:
    added: List[FileChange] = field(default_factory=list)
    modified: List[FileChange] = field(default_factory=list)
    deleted: List[FileChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)

    def to_dict(self) -> Dict:
        return {
            "added": [{"path": c.path, "hash": c.new_hash} for c in self.added],
            "modified": [
                {
                    "path": c.path,
                    "old_hash": c.old_hash,
                    "new_hash": c.new_hash,
                }
                for c in self.modified
            ],
            "deleted": [{"path": c.path, "hash": c.old_hash} for c in self.deleted],
            "total": self.total_changes,
        }


class IncrementalIndexer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.cache_dir = self.project_path / ".codeinsight"
        self.hash_file = self.cache_dir / "file_hashes.json"
        self.metadata_file = self.cache_dir / "metadata.json"
        self.hashes: Dict[str, str] = {}
        self.metadata: Dict[str, Dict] = {}
        self._ensure_cache_dir()
        self._load_hashes()
        self._load_metadata()

    def _ensure_cache_dir(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_hashes(self):
        if self.hash_file.exists():
            try:
                self.hashes = json.loads(self.hash_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                self.hashes = {}

    def _save_hashes(self):
        self.hash_file.write_text(
            json.dumps(self.hashes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_metadata(self):
        if self.metadata_file.exists():
            try:
                self.metadata = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                self.metadata = {}

    def _save_metadata(self):
        self.metadata_file.write_text(
            json.dumps(self.metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def detect_changes(
        self,
        file_paths: Optional[List[str]] = None,
        skip_dirs: Optional[Set[str]] = None,
    ) -> ChangeSet:
        current_hashes: Dict[str, str] = {}
        changes = ChangeSet()

        default_skip_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".codeinsight",
        }
        skip_dirs = skip_dirs or default_skip_dirs

        if file_paths:
            files_to_check = [Path(f) for f in file_paths]
        else:
            files_to_check = self._iter_project_files(skip_dirs)

        for file_path in files_to_check:
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(self.project_path))

            try:
                file_hash = self._compute_hash(file_path)
            except (IOError, PermissionError):
                continue

            current_hashes[rel_path] = file_hash

            if rel_path not in self.hashes:
                changes.added.append(
                    FileChange(
                        path=rel_path,
                        change_type="added",
                        new_hash=file_hash,
                    )
                )
            elif self.hashes[rel_path] != file_hash:
                changes.modified.append(
                    FileChange(
                        path=rel_path,
                        change_type="modified",
                        old_hash=self.hashes[rel_path],
                        new_hash=file_hash,
                    )
                )

        for old_path in self.hashes:
            if old_path not in current_hashes:
                changes.deleted.append(
                    FileChange(
                        path=old_path,
                        change_type="deleted",
                        old_hash=self.hashes[old_path],
                    )
                )

        self.hashes = current_hashes
        self._save_hashes()

        return changes

    def _iter_project_files(self, skip_dirs: Set[str]):
        for root, dirs, files in self.project_path.walk():
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for file in files:
                if file.startswith("."):
                    continue
                yield root / file

    def _compute_hash(self, file_path: Path) -> str:
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def get_file_hash(self, rel_path: str) -> Optional[str]:
        return self.hashes.get(rel_path)

    def has_file_changed(self, file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return True

        rel_path = str(path.relative_to(self.project_path))
        current_hash = self._compute_hash(path)
        stored_hash = self.hashes.get(rel_path)

        return stored_hash != current_hash

    def mark_file_processed(self, file_path: str, metadata: Optional[Dict] = None):
        path = Path(file_path)
        rel_path = str(path.relative_to(self.project_path))

        if path.exists():
            self.hashes[rel_path] = self._compute_hash(path)

        if metadata:
            self.metadata[rel_path] = metadata

        self._save_hashes()
        self._save_metadata()

    def get_file_metadata(self, file_path: str) -> Optional[Dict]:
        rel_path = str(Path(file_path).relative_to(self.project_path))
        return self.metadata.get(rel_path)

    def clear_cache(self):
        self.hashes = {}
        self.metadata = {}
        self._save_hashes()
        self._save_metadata()

    def get_stats(self) -> Dict:
        return {
            "total_tracked_files": len(self.hashes),
            "cache_dir": str(self.cache_dir),
            "last_scan": self.metadata.get("_last_scan", "never"),
        }

    def update_last_scan_time(self):
        self.metadata["_last_scan"] = datetime.now().isoformat()
        self._save_metadata()
