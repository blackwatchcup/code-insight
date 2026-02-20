import pytest
from datetime import datetime

from app.core.database import Base
from app.models import Chat, Feature, File, Project, ProjectStatus, SourceType


class TestSourceType:
    def test_source_type_values(self):
        assert SourceType.LOCAL.value == "local"
        assert SourceType.GITHUB.value == "github"
        assert SourceType.GITLAB.value == "gitlab"

    def test_source_type_is_string_enum(self):
        assert isinstance(SourceType.LOCAL, str)
        assert SourceType.LOCAL == "local"


class TestProjectStatus:
    def test_project_status_values(self):
        assert ProjectStatus.PENDING.value == "pending"
        assert ProjectStatus.ANALYZING.value == "analyzing"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.FAILED.value == "failed"

    def test_project_status_is_string_enum(self):
        assert isinstance(ProjectStatus.PENDING, str)
        assert ProjectStatus.PENDING == "pending"


class TestProjectModel:
    def test_project_table_name(self):
        assert Project.__tablename__ == "projects"

    def test_project_has_required_columns(self):
        columns = [c.name for c in Project.__table__.columns]
        assert "id" in columns
        assert "name" in columns
        assert "source_type" in columns
        assert "source_url" in columns
        assert "local_path" in columns
        assert "branch" in columns
        assert "status" in columns
        assert "file_count" in columns
        assert "line_count" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_project_has_relationships(self):
        assert hasattr(Project, "files")
        assert hasattr(Project, "chats")
        assert hasattr(Project, "features")


class TestFileModel:
    def test_file_table_name(self):
        assert File.__tablename__ == "files"

    def test_file_has_required_columns(self):
        columns = [c.name for c in File.__table__.columns]
        assert "id" in columns
        assert "project_id" in columns
        assert "path" in columns
        assert "language" in columns
        assert "content" in columns
        assert "summary" in columns
        assert "created_at" in columns

    def test_file_has_project_relationship(self):
        assert hasattr(File, "project")


class TestChatModel:
    def test_chat_table_name(self):
        assert Chat.__tablename__ == "chats"

    def test_chat_has_required_columns(self):
        columns = [c.name for c in Chat.__table__.columns]
        assert "id" in columns
        assert "project_id" in columns
        assert "title" in columns
        assert "mode" in columns
        assert "created_at" in columns

    def test_chat_has_project_relationship(self):
        assert hasattr(Chat, "project")


class TestFeatureModel:
    def test_feature_table_name(self):
        assert Feature.__tablename__ == "features"

    def test_feature_has_required_columns(self):
        columns = [c.name for c in Feature.__table__.columns]
        assert "id" in columns
        assert "project_id" in columns
        assert "name" in columns
        assert "type" in columns
        assert "description" in columns
        assert "file_paths" in columns
        assert "created_at" in columns

    def test_feature_has_project_relationship(self):
        assert hasattr(Feature, "project")


class TestBase:
    def test_base_is_declarative_base(self):
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")
