import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.project import Project, ProjectStatus, SourceType
from app.services.import_service import ImportService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def import_service(db_session):
    return ImportService(db_session)


class TestImportService:
    def test_extract_name_from_github_url(self, import_service):
        url = "https://github.com/user/my-project"
        assert import_service._extract_name(url) == "my-project"

    def test_extract_name_from_gitlab_url(self, import_service):
        url = "https://gitlab.com/company/awesome-app"
        assert import_service._extract_name(url) == "awesome-app"

    def test_extract_name_from_gitee_url(self, import_service):
        url = "https://gitee.com/user/test_repo"
        assert import_service._extract_name(url) == "test_repo"

    def test_extract_name_from_git_url(self, import_service):
        url = "git@git.example.com:team/project.git"
        assert import_service._extract_name(url) == "project"

    def test_extract_name_from_zip_url(self, import_service):
        url = "https://example.com/downloads/myapp.zip"
        assert import_service._extract_name(url) == "myapp"

    def test_detect_source_type_github(self, import_service):
        assert (
            import_service._detect_source_type("https://github.com/user/repo") == SourceType.GITHUB
        )
        assert (
            import_service._detect_source_type("https://GITHUB.COM/user/repo") == SourceType.GITHUB
        )

    def test_detect_source_type_gitlab(self, import_service):
        assert (
            import_service._detect_source_type("https://gitlab.com/user/repo") == SourceType.GITLAB
        )
        assert (
            import_service._detect_source_type("https://gitlab.company.com/user/repo")
            == SourceType.GITLAB
        )

    def test_detect_source_type_gitee(self, import_service):
        assert import_service._detect_source_type("https://gitee.com/user/repo") == SourceType.GITEE

    def test_detect_source_type_zip(self, import_service):
        assert import_service._detect_source_type("https://example.com/file.zip") == SourceType.ZIP

    def test_detect_source_type_generic_git(self, import_service):
        assert (
            import_service._detect_source_type("https://git.example.com/user/repo")
            == SourceType.GIT
        )

    @pytest.mark.asyncio
    async def test_import_from_git_creates_project(self, import_service, db_session, tmp_path):
        import_service.projects_dir = tmp_path

        mock_repo = MagicMock()

        with patch("app.services.import_service.Repo.clone_from") as mock_clone:
            mock_clone.return_value = mock_repo

            project = await import_service.import_from_git(
                url="https://github.com/test/test-project",
                branch="main",
                name="test_project",
            )

        assert project is not None
        assert "test_project" in project.name
        assert project.source_type == SourceType.GITHUB
        assert project.source_url == "https://github.com/test/test-project"
        assert project.branch == "main"
        assert project.status == ProjectStatus.PENDING

        db_project = db_session.query(Project).filter_by(id=project.id).first()
        assert db_project is not None

    @pytest.mark.asyncio
    async def test_import_from_zip_creates_project(self, import_service, db_session, tmp_path):
        import_service.projects_dir = tmp_path

        zip_content = self._create_test_zip()

        with patch("app.services.import_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content = lambda chunk_size: [zip_content]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            project = await import_service.import_from_zip(
                url="https://example.com/project.zip",
                name="test_zip_project",
            )

        assert project is not None
        assert "test_zip_project" in project.name
        assert project.source_type == SourceType.ZIP
        assert project.source_url == "https://example.com/project.zip"
        assert project.status == ProjectStatus.PENDING

    def _create_test_zip(self) -> bytes:
        import io
        import zipfile

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("test/app.py", "print('hello')")
        buffer.seek(0)
        return buffer.read()

    def test_count_files(self, import_service, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\nprint('world')")
        (tmp_path / "app.js").write_text("console.log('test');")
        (tmp_path / "README.md").write_text("# README")

        file_count, line_count = import_service._count_files(tmp_path)

        assert file_count == 2
        assert line_count == 3

    def test_count_files_ignores_git_directory(self, import_service, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[core]")

        file_count, _ = import_service._count_files(tmp_path)

        assert file_count == 1

    def test_count_files_ignores_node_modules(self, import_service, tmp_path):
        (tmp_path / "app.js").write_text("console.log('test');")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("module.exports = {};")

        file_count, _ = import_service._count_files(tmp_path)

        assert file_count == 1
