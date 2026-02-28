#!/usr/bin/env python3
"""Test project update API directly"""
import requests
import json

def test_update_api():
    base_url = "http://127.0.0.1:8000/api/v1"
    project_id = "de84cb3a"

    print("=== Testing Project Update API ===\n")

    # Test 1: Get project info first
    print("1. Getting project info...")
    try:
        response = requests.get(f"{base_url}/projects/{project_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error getting project: {e}")
        return

    # Test 2: Update project
    print("\n2. Updating project...")
    try:
        response = requests.post(f"{base_url}/projects/{project_id}/update")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("\n✅ Project update successful!")
            data = response.json()
            print(f"Updated file count: {data.get('data', {}).get('file_count', 'N/A')}")
            print(f"Updated line count: {data.get('data', {}).get('line_count', 'N/A')}")
        else:
            print(f"\n❌ Project update failed with status {response.status_code}")
    except Exception as e:
        print(f"Error updating project: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Get git branches
    print("\n3. Getting git branches...")
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/git/branches")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error getting branches: {e}")

    # Test 4: Get git commits
    print("\n4. Getting git commits...")
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/git/commits?limit=5")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        commits = data.get('data', {}).get('commits', [])
        print(f"Found {len(commits)} commits")
        for commit in commits:
            print(f"  - {commit.get('hash', '')[:8]}: {commit.get('message', 'N/A')}")
    except Exception as e:
        print(f"Error getting commits: {e}")

    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_update_api()
