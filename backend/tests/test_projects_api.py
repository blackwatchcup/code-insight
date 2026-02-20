import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("print('hello')\n")
        yield tmpdir


class TestCreateProjectAPI:
    def test_create_project_success(self, client: TestClient, sample_project_dir: str):
        response = client.post(
            "/api/v1/projects/",
            json={"name": "Test Project", "source_type": "local", "local_path": sample_project_dir},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "Test Project"
        assert data["data"]["source_type"] == "local"
        assert data["data"]["status"] == "pending"
        assert data["data"]["file_count"] >= 0

    def test_create_project_invalid_path(self, client: TestClient):
        response = client.post(
            "/api/v1/projects/",
            json={"name": "Test", "source_type": "local", "local_path": "/nonexistent"},
        )
        
        assert response.status_code == 400

    def test_create_project_empty_name(self, client: TestClient, sample_project_dir: str):
        response = client.post(
            "/api/v1/projects/",
            json={"name": "", "source_type": "local", "local_path": sample_project_dir},
        )
        
        assert response.status_code == 422

    def test_create_project_empty_path(self, client: TestClient):
        response = client.post(
            "/api/v1/projects/",
            json={"name": "Test", "source_type": "local", "local_path": ""},
        )
        
        assert response.status_code == 422

    def test_create_project_unsupported_source_type(self, client: TestClient):
        response = client.post(
            "/api/v1/projects/",
            json={"name": "Test", "source_type": "github", "local_path": "/some/path"},
        )
        
        assert response.status_code == 400


class TestListProjectsAPI:
    def test_list_projects_empty(self, client: TestClient):
        response = client.get("/api/v1/projects/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] == []

    def test_list_projects_with_data(self, client: TestClient, sample_project_dir: str):
        client.post(
            "/api/v1/projects/",
            json={"name": "Project 1", "source_type": "local", "local_path": sample_project_dir},
        )
        
        response = client.get("/api/v1/projects/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Project 1"


class TestGetProjectAPI:
    def test_get_project_success(self, client: TestClient, sample_project_dir: str):
        create_response = client.post(
            "/api/v1/projects/",
            json={"name": "Test", "source_type": "local", "local_path": sample_project_dir},
        )
        project_id = create_response.json()["data"]["id"]
        
        response = client.get(f"/api/v1/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == project_id

    def test_get_project_not_found(self, client: TestClient):
        response = client.get("/api/v1/projects/99999")
        
        assert response.status_code == 404


class TestDeleteProjectAPI:
    def test_delete_project_success(self, client: TestClient, sample_project_dir: str):
        create_response = client.post(
            "/api/v1/projects/",
            json={"name": "Test", "source_type": "local", "local_path": sample_project_dir},
        )
        project_id = create_response.json()["data"]["id"]
        
        response = client.delete(f"/api/v1/projects/{project_id}")
        
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] is True

    def test_delete_project_not_found(self, client: TestClient):
        response = client.delete("/api/v1/projects/99999")
        
        assert response.status_code == 404
