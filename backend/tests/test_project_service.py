import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.database import Base
from app.models import Project, ProjectStatus, SourceType
from app.services.project_service import ProjectService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def project_service(db_session: Session):
    return ProjectService(db_session)


@pytest.fixture
def sample_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("print('hello')\nprint('world')\n")
        yield tmpdir


class TestProjectService:
    def test_create_from_local_success(
        self, project_service: ProjectService, sample_project_dir: str
    ):
        import asyncio

        project = asyncio.run(
            project_service.create_from_local("Test Project", sample_project_dir)
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.source_type == SourceType.LOCAL
        assert project.status == ProjectStatus.PENDING
        assert project.file_count == 1
        assert project.line_count == 2

    def test_create_from_local_invalid_path(self, project_service: ProjectService):
        import asyncio

        with pytest.raises(ValueError, match="does not exist"):
            asyncio.run(
                project_service.create_from_local("Test", "/nonexistent/path")
            )

    def test_create_from_local_file_not_directory(
        self, project_service: ProjectService
    ):
        import asyncio

        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="not a directory"):
                asyncio.run(
                    project_service.create_from_local("Test", tmpfile.name)
                )

    def test_get_project(self, project_service: ProjectService, sample_project_dir: str):
        import asyncio

        created = asyncio.run(
            project_service.create_from_local("Test", sample_project_dir)
        )
        
        found = project_service.get_project(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "Test"

    def test_get_project_not_found(self, project_service: ProjectService):
        result = project_service.get_project(99999)
        assert result is None

    def test_list_projects(self, project_service: ProjectService, sample_project_dir: str):
        import asyncio

        asyncio.run(project_service.create_from_local("Project 1", sample_project_dir))
        asyncio.run(project_service.create_from_local("Project 2", sample_project_dir))

        projects = project_service.list_projects()
        assert len(projects) == 2

    def test_delete_project(self, project_service: ProjectService, sample_project_dir: str):
        import asyncio

        created = asyncio.run(
            project_service.create_from_local("Test", sample_project_dir)
        )
        
        local_path = created.local_path
        assert os.path.exists(local_path)
        
        result = project_service.delete_project(created.id)
        assert result is True
        
        assert project_service.get_project(created.id) is None
        assert not os.path.exists(local_path)

    def test_delete_project_not_found(self, project_service: ProjectService):
        result = project_service.delete_project(99999)
        assert result is False


class TestCountFilesAndLines:
    def test_count_supported_files(self, project_service: ProjectService):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("line1\nline2\nline3\n")
            
            js_file = Path(tmpdir) / "test.js"
            js_file.write_text("line1\n")
            
            txt_file = Path(tmpdir) / "readme.txt"
            txt_file.write_text("ignored\n")
            
            file_count, line_count = project_service._count_files_and_lines(Path(tmpdir))
            
            assert file_count == 2
            assert line_count == 4

    def test_skip_ignored_directories(self, project_service: ProjectService):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("line1\n")
            
            node_modules = Path(tmpdir) / "node_modules"
            node_modules.mkdir()
            skipped_file = node_modules / "skipped.py"
            skipped_file.write_text("should be skipped\n")
            
            file_count, line_count = project_service._count_files_and_lines(Path(tmpdir))
            
            assert file_count == 1
            assert line_count == 1
