import requests

base_url = "http://localhost:8000"

def test_health():
    response = requests.get(f"{base_url}/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_list_projects():
    response = requests.get(f"{base_url}/api/v1/projects/")
    print(f"List projects: {response.status_code} - {response.text}")

def test_create_project():
    data = {
        "name": "test_project",
        "source_type": "local",
        "local_path": "C:\\Users\\Alan ZA Zhang\\Desktop\\test"
    }
    response = requests.post(f"{base_url}/api/v1/projects/", json=data)
    print(f"Create project: {response.status_code} - {response.text}")

def test_get_project(project_id):
    response = requests.get(f"{base_url}/api/v1/projects/{project_id}")
    print(f"Get project: {response.status_code} - {response.text}")

def test_delete_project(project_id):
    response = requests.delete(f"{base_url}/api/v1/projects/{project_id}")
    print(f"Delete project: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_health()
    test_list_projects()
    test_create_project()
    test_get_project(1)
    test_delete_project(1)
