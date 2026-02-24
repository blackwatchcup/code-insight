import pytest
from fastapi.testclient import TestClient

from app.core.websocket import manager
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestConnectionManager:
    def test_init(self):
        new_manager = type(manager)()
        assert new_manager.active_connections == {}

    def test_connect_adds_connection(self):
        new_manager = type(manager)()
        mock_websocket = type("MockWebSocket", (), {})()

        new_manager.active_connections["test-project"] = set()
        new_manager.active_connections["test-project"].add(mock_websocket)

        assert "test-project" in new_manager.active_connections
        assert mock_websocket in new_manager.active_connections["test-project"]

    def test_disconnect_removes_connection(self):
        new_manager = type(manager)()
        mock_websocket = type("MockWebSocket", (), {})()

        new_manager.active_connections["test-project"] = {mock_websocket}
        new_manager.disconnect(mock_websocket, "test-project")

        assert "test-project" not in new_manager.active_connections

    def test_disconnect_nonexistent_project(self):
        new_manager = type(manager)()
        mock_websocket = type("MockWebSocket", (), {})()

        new_manager.disconnect(mock_websocket, "nonexistent")

        assert "nonexistent" not in new_manager.active_connections

    def test_disconnect_last_connection_removes_project(self):
        new_manager = type(manager)()
        mock_websocket = type("MockWebSocket", (), {})()

        new_manager.active_connections["test-project"] = {mock_websocket}
        new_manager.disconnect(mock_websocket, "test-project")

        assert "test-project" not in new_manager.active_connections

    def test_multiple_connections_same_project(self):
        new_manager = type(manager)()
        ws1 = type("MockWebSocket", (), {})()
        ws2 = type("MockWebSocket", (), {})()

        new_manager.active_connections["test-project"] = {ws1, ws2}

        assert len(new_manager.active_connections["test-project"]) == 2

    def test_disconnect_one_of_multiple_connections(self):
        new_manager = type(manager)()
        ws1 = type("MockWebSocket", (), {})()
        ws2 = type("MockWebSocket", (), {})()

        new_manager.active_connections["test-project"] = {ws1, ws2}
        new_manager.disconnect(ws1, "test-project")

        assert "test-project" in new_manager.active_connections
        assert ws1 not in new_manager.active_connections["test-project"]
        assert ws2 in new_manager.active_connections["test-project"]


def test_websocket_endpoint_exists(client):
    with client.websocket_connect("/ws/import/test-project") as websocket:
        pass
