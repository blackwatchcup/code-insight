import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.version import Version
from app.services.project_service import ProjectService


class VersionService:
    def __init__(self, db: Session):
        self.db = db
        self.project_service = ProjectService(db)

    def create_version(
        self,
        project_id: str,
        version_number: str,
        description: Optional[str] = None,
        commit_hash: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Version:
        """Create a new version snapshot for a project."""
        project = self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Count files and lines
        project_path = Path(project.local_path)
        file_count = 0
        line_count = 0

        if project_path.exists():
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not self._should_skip(file_path):
                    file_count += 1
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        line_count += content.count("\n") + 1
                    except Exception:
                        pass

        version = Version(
            id=str(uuid.uuid4()),
            project_id=project_id,
            version_number=version_number,
            description=description,
            commit_hash=commit_hash,
            created_by=created_by,
            file_count=file_count,
            line_count=line_count,
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        return version

    def list_versions(self, project_id: str) -> List[Version]:
        """List all versions for a project."""
        return (
            self.db.query(Version)
            .filter(Version.project_id == project_id)
            .order_by(Version.created_at.desc())
            .all()
        )

    def get_version(self, version_id: str) -> Optional[Version]:
        """Get a specific version by ID."""
        return self.db.query(Version).filter(Version.id == version_id).first()

    def delete_version(self, version_id: str) -> bool:
        """Delete a version."""
        version = self.get_version(version_id)
        if not version:
            return False

        self.db.delete(version)
        self.db.commit()
        return True

    def compare_versions(
        self, project_id: str, version_id_1: str, version_id_2: str
    ) -> Dict:
        """Compare two versions of a project."""
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        if v1.project_id != project_id or v2.project_id != project_id:
            raise ValueError("Versions do not belong to the same project")

        # Simple comparison for now
        # In a real implementation, you would compare actual file contents
        diff = {
            "version_1": v1.to_dict(),
            "version_2": v2.to_dict(),
            "file_count_diff": v2.file_count - v1.file_count,
            "line_count_diff": v2.line_count - v1.line_count,
            "changes": [],
        }

        # Placeholder for file-level diff
        # In production, you would use a diff library to compare actual files
        if v2.file_count > v1.file_count:
            diff["changes"].append(
                {
                    "type": "files_added",
                    "count": v2.file_count - v1.file_count,
                    "description": f"Added {v2.file_count - v1.file_count} files",
                }
            )
        elif v2.file_count < v1.file_count:
            diff["changes"].append(
                {
                    "type": "files_removed",
                    "count": v1.file_count - v2.file_count,
                    "description": f"Removed {v1.file_count - v2.file_count} files",
                }
            )

        return diff

    def create_version_from_git_commit(
        self,
        project_id: str,
        commit_hash: str,
        version_number: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Version:
        """Create a version from a specific git commit."""
        project = self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if not git_dir.exists():
            raise ValueError("Project is not a git repository")
        
        try:
            import subprocess
            # Checkout the commit
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            
            # Count files and lines
            file_count = 0
            line_count = 0

            if project_dir.exists():
                for file_path in project_dir.rglob("*"):
                    if file_path.is_file() and not self._should_skip(file_path):
                        file_count += 1
                        try:
                            content = file_path.read_text(encoding="utf-8", errors="ignore")
                            line_count += content.count("\n") + 1
                        except Exception:
                            pass
            
            # Get commit info
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%s", commit_hash],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                text=True
            )
            commit_message = result.stdout.strip()
            
            if not description:
                description = f"Git commit: {commit_message}"
            
            version = Version(
                id=str(uuid.uuid4()),
                project_id=project_id,
                version_number=version_number,
                description=description,
                commit_hash=commit_hash,
                created_by=created_by,
                file_count=file_count,
                line_count=line_count,
            )

            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)
            
            # Checkout back to original branch
            subprocess.run(
                ["git", "checkout", "HEAD"],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )

            return version
        except Exception as e:
            raise ValueError(f"Failed to create version from git commit: {str(e)}")

    def compare_git_versions(
        self, project_id: str, commit_hash_1: str, commit_hash_2: str
    ) -> Dict:
        """Compare two git commits of a project."""
        project = self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if not git_dir.exists():
            raise ValueError("Project is not a git repository")
        
        try:
            import subprocess
            # Get commit info for both versions
            result1 = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%H|%s|%an|%ad", commit_hash_1],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                encoding='utf-8',
                text=True
            )
            result2 = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%H|%s|%an|%ad", commit_hash_2],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                encoding='utf-8',
                text=True
            )
            
            # Parse commit info
            def parse_commit_info(output):
                if not output:
                    return {}
                parts = output.strip().split('|', 3)
                if len(parts) >= 4:
                    return {
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3]
                    }
                return {}
            
            commit1 = parse_commit_info(result1.stdout)
            commit2 = parse_commit_info(result2.stdout)
            
            # Get file diff with status
            diff_result = subprocess.run(
                ["git", "diff", commit_hash_1, commit_hash_2, "--name-status"],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                encoding='utf-8',
                text=True
            )
            
            changes = []
            added = 0
            modified = 0
            deleted = 0
            
            if diff_result.stdout:
                for line in diff_result.stdout.strip().split('\n'):
                    if line:
                        status, file_path = line.split('\t', 1)
                        if status == 'A':
                            added += 1
                            changes.append({"type": "added", "file": file_path})
                        elif status == 'M':
                            modified += 1
                            changes.append({"type": "modified", "file": file_path})
                        elif status == 'D':
                            deleted += 1
                            changes.append({"type": "deleted", "file": file_path})
            
            # Get detailed code changes for modified files
            detailed_changes = []
            for change in changes:
                if change["type"] == "modified":
                    try:
                        # Get detailed diff for this file
                        file_diff_result = subprocess.run(
                            ["git", "diff", commit_hash_1, commit_hash_2, "--", change["file"]],
                            cwd=str(project_dir),
                            check=True,
                            capture_output=True,
                            encoding='utf-8',
                            text=True
                        )
                        change["diff"] = file_diff_result.stdout
                    except Exception:
                        # If we can't get detailed diff, just skip it
                        pass
            
            diff = {
                "commit_1": commit1,
                "commit_2": commit2,
                "file_changes": {
                    "added": added,
                    "modified": modified,
                    "deleted": deleted
                },
                "changes": changes
            }
            
            return diff
        except Exception as e:
            raise ValueError(f"Failed to compare git versions: {str(e)}")

    def _should_skip(self, file_path: Path) -> bool:
        """Check if a file should be skipped during counting."""
        skip_dirs = {
            ".git",
            ".github",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".pytest_cache",
            "migrations",
            "docs",
        }

        for part in file_path.parts:
            if part in skip_dirs:
                return True

        if file_path.suffix in [".min.js", ".min.css", ".map", ".lock", ".log"]:
            return True

        return False
