import requests

# 测试项目信息API端点
def test_project_info():
    print("=== Testing Project Info API ===")
    
    # 首先获取项目列表
    projects_url = "http://localhost:8000/api/v1/projects"
    response = requests.get(projects_url)
    
    if response.status_code == 200:
        projects = response.json().get('data', {}).get('items', [])
        print(f"Found {len(projects)} projects")
        
        if projects:
            # 测试第一个项目的信息
            project_id = projects[0]['id']
            project_name = projects[0]['name']
            print(f"Testing project: {project_name} (ID: {project_id})")
            
            # 测试项目信息端点
            info_url = f"http://localhost:8000/api/v1/projects/{project_id}/info"
            info_response = requests.get(info_url)
            
            if info_response.status_code == 200:
                info_data = info_response.json().get('data', {})
                print("✓ Project info endpoint successful!")
                print(f"Description: {info_data.get('description', '')[:100]}...")
                print(f"Architecture: {info_data.get('architecture', '')[:100]}...")
            else:
                print(f"✗ Project info endpoint failed with status code: {info_response.status_code}")
                print(f"Response: {info_response.json()}")
        else:
            print("No projects found. Please create a project first.")
    else:
        print(f"✗ Failed to get projects with status code: {response.status_code}")
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_project_info()
