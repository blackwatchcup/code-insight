from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.abspath(r'C:\Users\Alan ZA Zhang\Desktop\newcode\code-insight\backend'))

# Import the app
from app.main import app

client = TestClient(app)

def test_health_check():
    print("Testing health check...")
    response = client.get("/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    assert response.status_code == 200

def test_projects():
    print("\nTesting projects endpoint...")
    response = client.get("/api/v1/projects/")
    print(f"Projects: {response.status_code} - {response.json()}")
    assert response.status_code == 200

def test_auth_register():
    print("\nTesting auth register...")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser3",
            "email": "testuser3@example.com",
            "password": "test123"
        }
    )
    print(f"Register: {response.status_code} - {response.text}")

def test_auth_login():
    print("\nTesting auth login...")
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "test123"
        }
    )
    print(f"Login: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_health_check()
    test_projects()
    test_auth_register()
    test_auth_login()
    print("\nAll tests completed!")
